"""Bounded, ephemeral file screening using Presidio's image and structured SDKs."""
import base64
import csv
import io
import json
import logging
import shutil
from contextlib import contextmanager
from threading import BoundedSemaphore

from fastapi import HTTPException

from app.ai.screening_service import DEFAULT_LIMITATIONS, EXCLUDE_ENTITIES, get_screening_provider
from app.core.config import get_settings
from app.models.screening import ScreeningEvent
from app.services.user_service import UserService

logger = logging.getLogger("jomo.ai.files")
_slots = BoundedSemaphore(1)


def invalid(message="The file is invalid or exceeds the supported structure limits."):
    return HTTPException(422, detail={"code": "INVALID_SCREENING_FILE", "message": message})


@contextmanager
def scan_slot():
    if not _slots.acquire(blocking=False):
        raise HTTPException(429, detail={"code": "SCREENING_BUSY", "message": "A file scan is in progress. Please retry shortly."}, headers={"Retry-After": "2"})
    try:
        yield
    finally:
        _slots.release()


def require_provider():
    provider = get_screening_provider()
    if provider is None:
        raise HTTPException(503, detail={"code": "SCREENING_UNAVAILABLE"})
    return provider


def image_engine(provider):
    # Tesseract is a local executable, not an external OCR service.
    if not shutil.which("tesseract"):
        raise HTTPException(503, detail={"code": "OCR_UNAVAILABLE"})
    from presidio_image_redactor import ImageAnalyzerEngine, ImageRedactorEngine
    return ImageRedactorEngine(image_analyzer_engine=ImageAnalyzerEngine(analyzer_engine=provider._analyzer))


def structured_sdk():
    import pandas as pd
    from presidio_structured import JsonAnalysisBuilder, JsonDataProcessor, PandasAnalysisBuilder, StructuredAnalysis, StructuredEngine
    from presidio_anonymizer.entities import OperatorConfig
    return pd, JsonAnalysisBuilder, JsonDataProcessor, PandasAnalysisBuilder, StructuredAnalysis, StructuredEngine, OperatorConfig


def result_base(provider, engine, categories, count, **file):
    limitations = list(DEFAULT_LIMITATIONS)
    if not provider.ner_enabled:
        limitations.append("The language model is unavailable; Presidio checked pattern-based identifiers only.")
    return dict(status="completed", engine=engine, ner_enabled=provider.ner_enabled,
                detected_categories=sorted(categories), flagged_fields=count,
                limitations=limitations, **file)


def flatten_json(data):
    """Use generated keys with the SDK, preserving arbitrary user keys and lists."""
    flat = {}
    nodes = 0
    characters = 0

    def visit(value, depth=0):
        nonlocal nodes, characters
        nodes += 1
        if depth > 12 or nodes > 5000:
            raise invalid()
        if isinstance(value, dict):
            for key, child in value.items():
                if len(key) > 200:
                    raise invalid()
                visit(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                visit(child, depth + 1)
        elif value is not None and not isinstance(value, bool):
            text = str(value)
            characters += len(text)
            if len(text) > 10000 or characters > 100000 or len(flat) >= 2000:
                raise invalid()
            flat[f"value_{len(flat)}"] = text
    visit(data)
    return flat


def restore_json(data, replacements):
    index = 0

    def visit(value):
        nonlocal index
        if isinstance(value, dict):
            return {key: visit(child) for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child) for child in value]
        if value is None or isinstance(value, bool):
            return value
        key = f"value_{index}"
        index += 1
        return replacements.get(key, value)
    return visit(data)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise invalid("JSON contains duplicate object keys.")
        obj[key] = value
    return obj


def reject_constant(value):
    raise invalid("JSON must not contain NaN or Infinity.")


def csv_safe(value):
    # A downloaded CSV must not turn user-supplied cells into spreadsheet formulas.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r")) else value


class FileScreeningService:
    def __init__(self, db):
        self.db = db

    def audit(self, user_id, kind, categories):
        UserService(self.db).get_or_create_profile(user_id)
        self.db.add(ScreeningEvent(user_id=user_id, screening_type=kind, source="user_submitted",
                                   detected_categories=sorted(categories) or None, result_status="completed"))
        self.db.commit()

    def screen_image(self, user_id, content, media_type):
        with scan_slot():
            if media_type not in ("image/png", "image/jpeg"):
                raise HTTPException(415, detail={"code": "UNSUPPORTED_SCREENING_FILE", "message": "Choose a PNG or JPEG image."})
            self.check_size(content)
            provider = require_provider()
            try:
                from PIL import Image, ImageOps, UnidentifiedImageError
                try:
                    with Image.open(io.BytesIO(content)) as original:
                        if original.format not in ("PNG", "JPEG"):
                            raise invalid("Choose a valid PNG or JPEG image.")
                        if original.width * original.height > get_settings().SCREENING_IMAGE_MAX_PIXELS:
                            raise invalid("Use an image of at most 4 million pixels.")
                        oriented = ImageOps.exif_transpose(original)
                        rgba = oriented.convert("RGBA")
                        image = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
                except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                    raise invalid("Choose a valid PNG or JPEG image.") from None
                engine = image_engine(provider)
                entities = [entity for entity in provider._analyzer.get_supported_entities(language="en") if entity not in EXCLUDE_ENTITIES]
                redacted, boxes = engine.redact_and_return_bbox(image, fill=(0, 0, 0),
                    ocr_kwargs={"lang": "eng", "timeout": 20}, language="en", entities=entities)
                # A fresh pixel-only PNG strips EXIF, source metadata and filenames.
                clean = Image.frombytes("RGB", redacted.size, redacted.convert("RGB").tobytes())
                output = io.BytesIO()
                clean.save(output, format="PNG")
                if output.tell() > 2500000:
                    raise invalid("The redacted image is too large. Resize the image and try again.")
                categories = {box.entity_type for box in boxes}
                result = result_base(provider, "presidio-image-redactor", categories, len(boxes),
                    format="image", media_type="image/png", filename="redacted.png",
                    content_base64=base64.b64encode(output.getvalue()).decode("ascii"))
                result["limitations"].append("OCR can miss small, blurry or handwritten text. This does not redact faces or guarantee anonymity.")
                self.audit(user_id, "image", categories)
                return result
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning("Image screening failed (%s).", type(exc).__name__)
                raise HTTPException(503, detail={"code": "OCR_UNAVAILABLE"}) from None

    def screen_structured(self, user_id, content, format):
        with scan_slot():
            self.check_size(content)
            if len(content) > 262144:
                raise invalid("CSV and JSON uploads must be at most 256 KiB.")
            try:
                source = content.decode("utf-8-sig")
            except UnicodeError:
                raise invalid("Save the CSV or JSON file using UTF-8 encoding.") from None
            if format == "json":
                try:
                    data = json.loads(source, object_pairs_hook=unique_object, parse_constant=reject_constant)
                    if not isinstance(data, (dict, list)):
                        raise invalid("JSON must contain an object or array.")
                    flat = flatten_json(data)
                except (ValueError, RecursionError):
                    raise invalid("Upload a valid JSON object or array.") from None
            else:
                try:
                    rows = list(csv.reader(io.StringIO(source), strict=True))
                except csv.Error:
                    raise invalid("Upload a valid comma-separated CSV file.") from None
                if not rows or not 1 <= len(rows[0]) <= 50 or not 2 <= len(rows) <= 201:
                    raise invalid("CSV requires headers, 1–200 data rows, and at most 50 columns.")
                if any(not h.strip() for h in rows[0]) or len(set(rows[0])) != len(rows[0]) or any(len(r) != len(rows[0]) for r in rows):
                    raise invalid("CSV headers must be unique and every row must have the same number of columns.")
                if sum(len(cell) for row in rows for cell in row) > 100000 or any(len(cell) > 10000 for row in rows for cell in row):
                    raise invalid()
            provider = require_provider()
            try:
                pd, JsonBuilder, JsonProcessor, PandasBuilder, Analysis, Engine, Operator = structured_sdk()
                operators = {"DEFAULT": Operator("replace", {"new_value": "[REDACTED]"})}
                if format == "json":
                    analysis = JsonBuilder(analyzer=provider._analyzer, n_process=1).generate_analysis(flat, language="en") if flat else Analysis(entity_mapping={})
                    mapping = {key: entity for key, entity in analysis.entity_mapping.items() if entity not in EXCLUDE_ENTITIES}
                    operated = Engine(data_processor=JsonProcessor()).anonymize(flat.copy(), Analysis(entity_mapping=mapping), operators)
                    redacted = restore_json(data, {key: operated[key] for key in mapping})
                    output = json.dumps(redacted, ensure_ascii=False, indent=2, allow_nan=False)
                else:
                    # Generated column IDs keep sensitive user headers out of SDK logs.
                    ids = [f"column_{i}" for i in range(len(rows[0]))]
                    frame = pd.DataFrame(rows[1:], columns=ids, dtype=str)
                    analysis = PandasBuilder(analyzer=provider._analyzer, n_process=1).generate_analysis(frame, language="en", selection_strategy="highest_confidence")
                    mapping = {key: entity for key, entity in analysis.entity_mapping.items() if entity not in EXCLUDE_ENTITIES}
                    redacted = Engine().anonymize(frame.copy(), Analysis(entity_mapping=mapping), operators)
                    buffer = io.StringIO(newline="")
                    writer = csv.writer(buffer)
                    writer.writerow([csv_safe(cell) for cell in rows[0]])
                    writer.writerows([csv_safe(str(cell)) for cell in row] for row in redacted.itertuples(index=False, name=None))
                    output = buffer.getvalue()
                categories = set(mapping.values())
                result = result_base(provider, "presidio-structured", categories, len(mapping), format=format,
                    media_type="application/json" if format == "json" else "text/csv;charset=utf-8",
                    filename=f"redacted.{format}", content=output)
                result["limitations"].append("Detected JSON values or entire CSV columns are replaced. Object keys and column headers are preserved and are not screened.")
                if format == "csv":
                    result["limitations"].append("Formula-like CSV cells are escaped for spreadsheet downloads.")
                self.audit(user_id, "structured", categories)
                return result
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning("Structured screening failed (%s).", type(exc).__name__)
                raise HTTPException(503, detail={"code": "STRUCTURED_UNAVAILABLE"}) from None

    @staticmethod
    def check_size(content):
        if not content:
            raise invalid("Choose a file containing data.")
        if len(content) > get_settings().SCREENING_UPLOAD_MAX_BYTES:
            raise HTTPException(413, detail={"code": "SCREENING_FILE_TOO_LARGE", "message": "The upload exceeds the 2 MiB file limit."})

"""Presidio-backed text screening provider.

Implements the ``TextScreeningProvider`` Protocol from ``app.ai.interfaces`` and
maps Presidio results onto the existing ``ScreenTextResponse`` contract so the
HTTP layer and response shape are unchanged.

``get_screening_provider`` returns ``None`` when Presidio is disabled or cannot
initialize. The API reports unavailability; it never substitutes another engine.
"""
from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings

logger = logging.getLogger("jomo.ai.screening")

# Standard limitations surfaced with every screening result (blueprint §4.4 F
# and §5.6: "Do not display a green 'safe' status merely because no detector
# triggered").
DEFAULT_LIMITATIONS: List[str] = [
    "Automated screening can miss sensitive information.",
    "A result with no detections does not guarantee that text is safe.",
]

# Presidio entity types that are personal/identifiable. We mark every detection
# as "pii"; harmful-content indicators are a separate (P1) capability not yet
# implemented in this provider.
PII_CATEGORY = "pii"

# NER numeric/temporal entity types that are not PII and tend to produce false
# positives on digit runs (phone/card fragments misread as dates or numbers).
# Excluded before dedupe so they cannot hijack real pattern detections.
EXCLUDE_ENTITIES = {
    "DATE_TIME",
    "CARDINAL",
    "ORDINAL",
    "QUANTITY",
    "MONEY",
    "PERCENT",
    "TIME",
}


class PresidioScreeningProvider:
    """Screens text for PII using Presidio and returns the screening contract."""

    def __init__(self, analyzer: Any, ner_enabled: bool) -> None:
        self._analyzer = analyzer
        self.ner_enabled = ner_enabled

    def screen(self, text: str, language: str = "en") -> Dict[str, Any]:
        # Presidio imports spaCy and its compiled extensions. Keep that optional
        # dependency out of application startup so restricted Windows machines
        # can still use unrelated features when screening is unavailable.
        from app.ai.privacy.redactor import dedupe_results, redact

        if language != "en":
            raise ValueError("This deployment supports English screening only.")
        results = self._analyzer.analyze(text=text, language=language) if text else []
        results = [r for r in results if r.entity_type not in EXCLUDE_ENTITIES]
        results = dedupe_results(results)

        detections: List[Dict[str, Any]] = [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": float(r.score),
                "category": PII_CATEGORY,
            }
            for r in results
        ]
        redacted = redact(text, results)

        return {
            "status": "completed",
            "has_potential_pii": len(detections) > 0,
            "has_harmful_content_indicators": False,
            "detections": detections,
            "redacted_text": redacted,
            "limitations": list(DEFAULT_LIMITATIONS) + ([] if self.ner_enabled else [
                "The language model is unavailable; this scan checks pattern-based identifiers only."
            ]),
            "ner_enabled": self.ner_enabled,
        }


# Module-level cache so the (relatively expensive) analyzer is built once.
_provider_cache: Dict[tuple, Optional[PresidioScreeningProvider]] = {}
_provider_lock = Lock()


def get_screening_provider(
    settings: Optional[Settings] = None,
) -> Optional[PresidioScreeningProvider]:
    """Return a cached Presidio screening provider, or ``None`` on failure.

    Returns ``None`` (so the caller reports unavailability) when Presidio is
    disabled via ``AI_PRESIDIO_ENABLED`` or when analyzer construction raises.
    """
    settings = settings or get_settings()
    if not settings.AI_PRESIDIO_ENABLED:
        return None

    cache_key = (settings.AI_PRESIDIO_ENABLED, settings.AI_SPACY_MODEL)
    with _provider_lock:
        if cache_key not in _provider_cache:
            _provider_cache[cache_key] = _build_provider(settings)
        return _provider_cache[cache_key]


def _build_provider(settings: Settings) -> Optional[PresidioScreeningProvider]:

    try:
        # Import lazily: some Windows Application Control policies block spaCy's
        # native DLLs. Import failures make screening unavailable without affecting
        # unrelated application features.
        from app.ai.privacy.analyzer import build_analyzer

        analyzer, ner_enabled = build_analyzer(settings)
        provider = PresidioScreeningProvider(analyzer, ner_enabled=ner_enabled)
        # Verify that the matching Anonymizer is available before advertising Presidio.
        from app.ai.privacy.redactor import redact
        redact("", [])
        logger.info("Privacy Guardian initialized: provider=presidio ner_enabled=%s", ner_enabled)
        return provider
    except Exception as exc:  # noqa: BLE001 - report screening unavailability
        logger.warning("Presidio screening unavailable (%s).", type(exc).__name__)
        return None

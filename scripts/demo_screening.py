#!/usr/bin/env python3
"""
JOMO Privacy Guardian — Presidio text screening demo.

Runs the Presidio + spaCy + Singapore-recogniser screening on sample text
directly (no server needed). Cross-platform: Linux/macOS and Windows.

Usage (from the repo root, using the project venv):

    # Linux / macOS
    /home/s4mgoh/.venv/bin/python scripts/demo_screening.py
    /home/s4mgoh/.venv/bin/python scripts/demo_screening.py "your own text"

    # Windows (PowerShell), with the venv activated
    python scripts\\demo_screening.py
    python scripts\\demo_screening.py "your own text"

The script prints the original text, the redacted text, each detected PII
entity (type, score, span), and the standard limitations. A "pattern-only"
mode line means the optional spaCy model is not installed; the Privacy
Guardian still works but without NER-based person/location detection.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the backend `app` package importable regardless of the current directory.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.ai.screening_service import get_screening_provider  # noqa: E402

DEFAULT_SAMPLES = [
    "You can email me at wei.ming@example.com or call +65 9123 4567. My NRIC is S1234567A.",
    "Hi, I'm Wei Ming. Meet me at Marina Bay. Card on file: 4111 1111 1111 1111.",
    "Reminder: bring a jacket for the walk later — nothing sensitive here.",
]

RULE = "=" * 64


def _print_one(text: str, result: dict) -> None:
    print(f"ORIGINAL          : {text}")
    print(f"REDACTED          : {result['redacted_text']}")
    print(f"has_potential_pii : {result['has_potential_pii']}")
    if result["detections"]:
        print("detections:")
        for d in result["detections"]:
            snippet = text[d["start"]:d["end"]]
            print(f"  - {d['entity_type']:<18} score={d['score']:.2f}  -> {snippet!r}")
    else:
        print("detections: (none)")
    print("limitations:")
    for line in result["limitations"]:
        print(f"  - {line}")


def main() -> None:
    provider = get_screening_provider()
    if provider is None:
        print(
            "Presidio screening is unavailable. Ensure presidio-analyzer, "
            "presidio-anonymizer and spacy are installed (see backend/requirements.txt) "
            "and AI_PRESIDIO_ENABLED is true."
        )
        sys.exit(1)

    mode = (
        "spaCy NER enabled"
        if getattr(provider, "ner_enabled", False)
        else "pattern-only (no NER — install en_core_web_sm to enable names/places)"
    )
    texts = sys.argv[1:] or DEFAULT_SAMPLES

    print(RULE)
    print("JOMO Privacy Guardian — Presidio text screening demo")
    print(f"Mode: {mode}")
    print(RULE)

    for text in texts:
        print()
        _print_one(text, provider.screen(text, "en"))
        print(RULE)


if __name__ == "__main__":
    main()

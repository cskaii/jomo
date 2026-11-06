"""Builds a Presidio ``AnalyzerEngine`` with Singapore recognisers.

Two operating modes (blueprint §0.2 "Graceful fallback"):

1. NER-enabled: when the configured spaCy model (default ``en_core_web_sm``) is
   installed, Presidio's ``SpacyNlpEngine`` runs NER so names/places/organisations
   (PERSON, LOCATION, ORG, ...) are detected in addition to pattern recognisers.
2. Pattern-only: when the spaCy model is missing (common on fresh machines and
   on Windows teammates' setups), a ``NoOpNlpEngine`` is used. All pattern
   recognisers (email, credit card, IP, URL, SG NRIC, SG phone, ...) still run;
   only NER-based entities are unavailable.

Callers should treat analyzer construction as potentially failing: ``build``
raises on hard errors so the API can report screening unavailability.
"""
from __future__ import annotations

import logging
from typing import Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NoOpNlpEngine, SpacyNlpEngine
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from app.ai.privacy.recognizers import get_custom_recognizers
from app.core.config import Settings

logger = logging.getLogger("jomo.ai.privacy")


def _spacy_model_available(model_name: str) -> bool:
    """Return True if the spaCy model package is installed.

    Importantly this does NOT trigger a download: Presidio's ``SpacyNlpEngine``
    auto-downloads missing models, and spaCy's failed download can terminate the
    process. We pre-check with ``spacy.util.is_package`` so a missing model
    silently selects the pattern-only fallback instead.
    """
    try:
        import spacy

        return bool(spacy.util.is_package(model_name))
    except Exception:  # noqa: BLE001 - spaCy not installed / any probe failure
        return False


def build_analyzer(settings: Settings) -> Tuple[AnalyzerEngine, bool]:
    """Return ``(analyzer, ner_enabled)``.

    Uses the spaCy NER path only when the configured model is actually
    installed; otherwise it falls back to a pattern-only ``NoOpNlpEngine``
    analyzer (blueprint §0.2 "Graceful fallback"). Custom Singapore recognisers
    are registered in both paths.
    """
    model_name = settings.AI_SPACY_MODEL
    custom_recognizers = get_custom_recognizers()

    # --- NER-enabled path (only when the model is present) ----------------
    if _spacy_model_available(model_name):
        try:
            nlp_engine = SpacyNlpEngine(
                models=[{"lang_code": "en", "model_name": model_name}]
            )
            nlp_engine.load()
            registry = RecognizerRegistryProvider(
                nlp_engine=nlp_engine,
                registry_configuration={"supported_languages": ["en"]},
            ).create_recognizer_registry()
            registry.remove_recognizer("EmailRecognizer", language="en")
            for recognizer in custom_recognizers:
                registry.add_recognizer(recognizer)
            analyzer = AnalyzerEngine(
                registry=registry, nlp_engine=nlp_engine, supported_languages=["en"]
            )
            logger.info(
                "Presidio analyzer ready (spaCy NER enabled, model=%s)", model_name
            )
            return analyzer, True
        except Exception as exc:  # noqa: BLE001 - any NLP init issue => pattern-only
            logger.warning(
                "spaCy NER failed to initialise (%s); using pattern-only fallback.",
                type(exc).__name__,
            )
    else:
        logger.info(
            "spaCy model '%s' not installed; using pattern-only Presidio.",
            model_name,
        )

    # --- Pattern-only fallback -------------------------------------------
    nlp_engine = NoOpNlpEngine(
        models=[{"lang_code": "en", "model_name": model_name}]
    )
    nlp_engine.load()
    registry = RecognizerRegistryProvider(
        nlp_engine=nlp_engine,
        registry_configuration={"supported_languages": ["en"]},
    ).create_recognizer_registry()
    registry.remove_recognizer("EmailRecognizer", language="en")
    for recognizer in custom_recognizers:
        registry.add_recognizer(recognizer)
    analyzer = AnalyzerEngine(
        registry=registry, nlp_engine=nlp_engine, supported_languages=["en"]
    )
    logger.info("Presidio analyzer ready (pattern-only, NER disabled).")
    return analyzer, False

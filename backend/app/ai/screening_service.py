"""Presidio-backed text screening provider.

Implements the ``TextScreeningProvider`` Protocol from ``app.ai.interfaces`` and
maps Presidio results onto the existing ``ScreenTextResponse`` contract so the
HTTP layer and response shape are unchanged.

This module is optional: ``get_screening_provider`` returns ``None`` when
Presidio is disabled or fails to initialise, so ``PrivacyService`` falls back to
its built-in regex recognisers (blueprint §0.2 "Graceful fallback").
"""
from __future__ import annotations

import logging
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
        # can still run the garden and use the deterministic regex fallback.
        from app.ai.privacy.redactor import dedupe_results, redact

        results = self._analyzer.analyze(text=text, language=language)
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
            "limitations": list(DEFAULT_LIMITATIONS),
            "ner_enabled": self.ner_enabled,
        }


# Module-level cache so the (relatively expensive) analyzer is built once.
_provider_cache: Dict[str, Optional[PresidioScreeningProvider]] = {}


def get_screening_provider(
    settings: Optional[Settings] = None,
) -> Optional[PresidioScreeningProvider]:
    """Return a cached Presidio screening provider, or ``None`` on failure.

    Returns ``None`` (so the caller falls back to regex) when Presidio is
    disabled via ``AI_PRESIDIO_ENABLED`` or when analyzer construction raises.
    """
    settings = settings or get_settings()
    cache_key = "provider"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    if not settings.AI_PRESIDIO_ENABLED:
        logger.info("Presidio screening disabled (AI_PRESIDIO_ENABLED=false).")
        _provider_cache[cache_key] = None
        return None

    try:
        # Import lazily: some Windows Application Control policies block spaCy's
        # native DLLs. Import failures are expected to select the regex fallback
        # instead of preventing the entire API from starting.
        from app.ai.privacy.analyzer import build_analyzer

        analyzer, ner_enabled = build_analyzer(settings)
        provider = PresidioScreeningProvider(analyzer, ner_enabled=ner_enabled)
        _provider_cache[cache_key] = provider
        return provider
    except Exception as exc:  # noqa: BLE001 - fall back to regex on any failure
        logger.warning("Presidio screening unavailable (%s); using regex fallback.", exc)
        _provider_cache[cache_key] = None
        return None

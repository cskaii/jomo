"""Offset-safe deterministic redaction into ``[REDACTED]``.

We redact directly from Presidio ``RecognizerResult`` spans rather than via the
AnonymizerEngine, so the output token is exactly ``[REDACTED]`` and the behaviour
is deterministic and easy to reason about (docs/ai-design.md §2).
"""
from __future__ import annotations

from typing import Iterable, List

from presidio_analyzer import RecognizerResult

REDACTED_TOKEN = "[REDACTED]"


def dedupe_results(results: Iterable[RecognizerResult]) -> List[RecognizerResult]:
    """Collapse overlapping detections to one result per text span.

    Presidio can emit several results for the same span (e.g. ``PHONE_NUMBER``
    and our ``SG_PHONE_NUMBER``, or ``URL`` inside an ``EMAIL_ADDRESS``, or NER
    ``ORGANIZATION`` overlapping a ``CREDIT_CARD``). We keep the highest-scoring
    result for each non-overlapping region: process results in score-desc order
    (longer span breaks ties) and skip anything that overlaps an already-kept
    span. This prefers purpose-built pattern recognisers over lower-confidence
    NER noise.
    """
    ordered = sorted(
        results, key=lambda r: (-r.score, -(r.end - r.start), r.start)
    )
    kept: List[RecognizerResult] = []
    for r in ordered:
        if any(not (r.end <= k.start or r.start >= k.end) for k in kept):
            # overlaps an already-kept span with equal-or-higher priority
            continue
        kept.append(r)
    return kept


def redact(text: str, results: Iterable[RecognizerResult]) -> str:
    """Replace every detected span with ``[REDACTED]`` in reverse offset order."""
    out = text
    for r in sorted(dedupe_results(results), key=lambda r: r.start, reverse=True):
        out = out[: r.start] + REDACTED_TOKEN + out[r.end:]
    return out

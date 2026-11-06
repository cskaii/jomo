"""Custom Presidio recognisers for Singapore-specific PII.

These complement Presidio's built-in recognisers (EMAIL_ADDRESS, CREDIT_CARD,
IP_ADDRESS, URL, PHONE_NUMBER, ...) which are loaded automatically by the
recogniser registry. Singapore national ID and local phone formats are not in
Presidio's default set, so we register them here (blueprint §0.4 and
docs/ai-design.md §1).
"""
from __future__ import annotations

from typing import List

from presidio_analyzer import EntityRecognizer, Pattern, PatternRecognizer

# Public entity type names used in DetectionItem responses.
SG_NRIC_FIN = "SG_NRIC_FIN"
SG_PHONE_NUMBER = "SG_PHONE_NUMBER"

# Singapore NRIC / FIN: one letter [S,T,F,G,M], seven digits, one check letter.
# e.g. S1234567A, G1234567X
_NRIC_PATTERN = Pattern(
    name="sg_nric_fin_regex",
    regex=r"\b[STFGMstfgm]\d{7}[A-Za-z]\b",
    score=0.90,
)

# Singapore mobile/landline numbers: optional +65 country code, then an 8 or 9
# prefix 8-digit number, with optional space/dash separators.
# e.g. +65 9123 4567, 8123-4567, +6591234567
_SG_PHONE_PATTERN = Pattern(
    name="sg_phone_regex",
    regex=r"(?<!\d)(?:\+65[\s-]?)?[89]\d{3}[\s-]?\d{4}(?!\d)",
    score=0.90,
)


def get_custom_recognizers() -> List[EntityRecognizer]:
    """Return custom Singapore PII recognisers to register with the analyzer."""
    return [
        PatternRecognizer(
            supported_entity=SG_NRIC_FIN,
            patterns=[_NRIC_PATTERN],
            supported_language="en",
            name="SG NRIC/FIN Recognizer",
        ),
        PatternRecognizer(
            supported_entity=SG_PHONE_NUMBER,
            patterns=[_SG_PHONE_PATTERN],
            supported_language="en",
            name="SG Phone Recognizer",
        ),
    ]

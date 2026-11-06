"""JOMO AI service layer.

Narrow, testable AI capabilities (blueprint §1.2 / §6.2):
    - PII detection & text redaction (Presidio + spaCy + custom recognisers)
    - Harmful-content indicators (deterministic rules, P1)
    - Wellbeing recommendations (Python rules)
    - Mission recommendations (curated catalogue; optional Strands agent)

AI must never own user accounts, points, group membership, garden balances,
or activity completion. It is advisory only (blueprint §0.2).
"""

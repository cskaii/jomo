"""Privacy screening sub-package: PII detection and redaction.

Backed by Microsoft Presidio. Falls back to pattern-only analysis when the
spaCy NLP model is unavailable so the app keeps working (blueprint §0.2
"Graceful fallback").
"""

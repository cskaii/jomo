# JOMO — AI Architecture & Heuristics Design

## 1. Modular Tooling Approach

Rather than routing all user interactions to an opaque LLM, JOMO employs targeted, explainable, and privacy-preserving primitives:

1. **PII Detection:** Regex and Presidio heuristics configured for Singapore and international patterns (Emails, SG Phone numbers `+65 8xxx / 9xxx`, SG NRIC/FIN formats, Credit Cards).
2. **Redaction:** Offset-safe deterministic string anonymization into `[REDACTED]`.
3. **Wellbeing Coach:** Rule-based suggestions triggered by aggregate screen time thresholds rather than intrusive surveillance.
4. **Mission Recommender:** Curated catalogue with duration and category filtering, providing deterministic fallback when external AI models are inactive.

---

## 2. Implementation layout (`backend/app/ai/`)

```
ai/
├── interfaces.py            # Protocols: TextScreeningProvider, WellbeingProvider, MissionProvider
├── screening_service.py     # PresidioScreeningProvider + get_screening_provider() (cached, optional)
└── privacy/
    ├── recognizers.py        # Custom SG recognisers: SG_NRIC_FIN, SG_PHONE_NUMBER
    ├── analyzer.py          # build_analyzer(): spaCy NER if model present, else NoOpNlpEngine pattern-only
    └── redactor.py          # Offset-safe deterministic redaction to "[REDACTED]"
```

`PrivacyService.screen_text` calls `get_screening_provider()`; when it returns
`None` (Presidio disabled or failed to init) it falls back to the deterministic
regex recognisers kept inside the service. The HTTP contract
(`ScreenTextResponse`) and the `ScreeningEvent` audit record (no raw text
stored) are unchanged either way.

## 3. Setup (cross-platform)

```bash
# Core AI dependencies (already pinned in requirements.txt)
pip install presidio-analyzer presidio-anonymizer spacy

# OPTIONAL NER model — enables PERSON/LOCATION/ORG detection.
# If you skip this, screening still works (pattern-only). Linux/macOS/Windows:
python -m spacy download en_core_web_sm
```

Notes for the team:

- The spaCy model is **optional**. The Privacy Guardian runs pattern-only
  Presidio (email, credit card, IP, URL, SG NRIC/FIN, SG phone, ...) without it.
- `AI_PRESIDIO_ENABLED=false` disables Presidio entirely and uses the regex
  fallback only — useful for environments without the Presidio packages.
- `AI_SPACY_MODEL` selects the NLP model name (default `en_core_web_sm`).

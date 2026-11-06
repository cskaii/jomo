# Privacy Guardian: Microsoft Presidio

Text submitted to Privacy Guardian is analyzed by Microsoft Presidio Analyzer and redacted by Presidio Anonymizer. No alternative regex service or external LLM is used. Presidio itself includes pattern recognisers and supports custom recognisers for Singapore phone numbers and NRIC/FIN-like formats.

The English spaCy model runs inside the same backend to detect possible names and locations. The prototype defaults to `en_core_web_sm` to reduce model size. Blueprint section 10 recommends `en_core_web_lg`; that model can be selected with `AI_SPACY_MODEL=en_core_web_lg` after installing it and checking hosting resources. Neither model proves that every name or address will be found.

## Install

From the backend directory:

```sh
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set `AI_PRESIDIO_ENABLED=true` and `AI_SPACY_MODEL=en_core_web_sm`, then restart the backend. On Render, select the Docker runtime and use `backend/Dockerfile`; it installs the Python packages, Tesseract OCR and the English model. See `docs/privacy-file-screening.md` for exact dashboard settings.

## Request handling

`POST /api/v1/ai/privacy/text` accepts an authenticated request with `text`, `checks: ["pii"]` and `language: "en"`. Text is limited to 10,000 characters. Presidio runs in a worker thread so inference does not block the API's event loop. The analyzer is warmed at startup and cached per model configuration.

The result includes detection types, character offsets, scores, a draft with `[REDACTED]` replacements, limitations, `engine: "presidio"` and `ner_enabled`. The frontend displays the actual engine and mode. If the spaCy model is missing, Presidio still supports pattern-based identification and clearly reports the lack of named-entity detection. It never downloads a model during a screening request.

If Presidio is disabled, fails to initialize or cannot complete a scan, the endpoint returns HTTP 503 `SCREENING_UNAVAILABLE`; it does not claim success or run another detector. Only English is currently accepted. Harmful-content classification is outside this PII feature.

## Privacy

Original text and detection values are not stored or logged. Audit events contain category names only. Error logs contain exception classes, never exception messages which might include the submitted text. Presidio email validation uses the bundled domain-suffix list without network requests or shared disk cache. All screening happens within the JOMO backend.

## Tests

`python -m pytest -q` exercises real Presidio detection and anonymization, offline email checks, unavailable-engine behavior, input privacy, authorization and request limits. Named-entity tests require the selected spaCy model. A scan without detections never establishes that text is safe.

## Images and structured files

Privacy Guardian also exposes Presidio Image Redactor for PNG/JPEG images and Presidio Structured for UTF-8 CSV/JSON. Both share the same configured text analyzer and Singapore recognisers. Authenticated uploads require explicit per-request consent. Original images and data files are not retained in Supabase; only category names are audited. The OCR wrapper may create temporary processing files in the container. See `docs/privacy-file-screening.md` for limits and deployment details.

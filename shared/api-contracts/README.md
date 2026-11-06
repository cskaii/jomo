# JOMO OpenAPI Specifications

This directory contains the machine-readable API contracts shared across frontend, API middleware, and backend agents.

## Contract File

- `openapi.json`: The authoritative OpenAPI 3.1.0 contract exported directly from the FastAPI application.

## Synchronization

When backend endpoints or schemas change, regenerate `openapi.json` by running:

```bash
cd backend
python -c "import json; from app.main import app; from pathlib import Path; Path('../shared/api-contracts/openapi.json').write_text(json.dumps(app.openapi(), indent=2))"
```

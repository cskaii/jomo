# JOMO — Multi-Agent Engineering & Contribution Guide

This document establishes development protocols for human developers and specialized coding agents working on JOMO.

## 1. Division of Ownership

Refer to `blueprint.md` Section 20 for agent assignments:

- **Agent 1 (Frontend):** Owns `frontend/`, UI styling, responsive design, components, and client-side validation.
- **Agent 2 (API/Middleware):** Owns `backend/app/api/`, middlewares, rate limiting, and OpenAPI contract sync.
- **Agent 3 (Backend/Database):** Owns `backend/app/models/`, `repositories/`, `services/`, and Alembic migrations.
- **Agent 4 (AI Integration):** Owns `backend/app/ai/`, Presidio PII recognisers, wellbeing rules, and mission recommenders.

## 2. API Contract Discipline

- When modifying API endpoints, update `backend/app/api/` and re-export `shared/api-contracts/openapi.json`.
- Do not introduce conflicting endpoint paths or non-standard error structures.
- All endpoints must adhere to the standard response envelope:
  - Success: `{"data": ..., "request_id": "..."}`
  - Error: `{"error": {"code": "...", "message": "...", "details": ...}, "request_id": "..."}`

## 3. Database Migration Invariants

- Never edit production schema without an Alembic migration.
- Always run `alembic upgrade head` before committing domain model modifications.
- Store sensitive tokens as SHA-256 hashes (`group_invites.token_hash`), never raw plaintext.
- Point transactions are append-only. Use compensating records rather than row mutations.

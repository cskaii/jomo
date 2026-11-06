# JOMO — System Architecture Document

## 1. Executive Summary

JOMO ("Joy of Missing Out") is a privacy-first web application designed to help young adults and students understand their digital habits, make intentional offline choices, engage in real-world activities individually or with friend circles, earn server-verified rewards, and grow virtual sanctuaries (gardens).

**Tagline:** Less scrolling. More living.

## 2. High-Level Architecture

```
User (Browser / PWA)
        │
        ▼ HTTPS (JSON)
FastAPI Middleware / API Layer
 ├── Security Headers & Rate Limiting
 ├── Authentication & Context Verification
 └── Request Validation (Pydantic v2)
        │
        ├──► Backend Domain Services (Business Invariants)
        │     ├── UserService & FriendshipService
        │     ├── GroupService & ActivityService
        │     ├── PointsService (Idempotent Ledger)
        │     ├── GardenService & LocationService
        │     └── ProofService
        │
        ├──► AI Service Boundary
        │     ├── Privacy Guardian (Local Presidio Heuristics + Redactor)
        │     ├── Wellbeing Coach (Deterministic Rules)
        │     └── Mission Catalogue
        │
        └──► Persistence Layer
              └── PostgreSQL / SQLAlchemy 2.0 / Alembic
```

## 3. Core Architectural Principles

1. **Server-Authoritative Rewards:** The frontend never decides points, eligibility, or garden balance. Points are calculated exclusively on the server and written to an immutable transactional ledger (`point_transactions`).
2. **AI is Advisory:** AI outputs suggestions, detects patterns, or redacts text; it cannot unilaterally grant points or take punitive actions.
3. **Privacy First & Transparent Claims:** JOMO never claims to lock third-party native apps or perform cross-app surveillance in the web MVP. It features voluntary focus sessions and opt-in text screening.
4. **Strict Request/Response Contracts:** Every endpoint conforms to standard success (`{"data": ..., "request_id": "..."}`) and error envelopes.

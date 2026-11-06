# JOMO — API Contract Documentation

All endpoints are hosted under `/api/v1` and detailed in `shared/api-contracts/openapi.json`.

## Standard Response Envelopes

### Success Envelope
```json
{
  "data": { ... },
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

### Error Envelope
```json
{
  "error": {
    "code": "GROUP_MEMBERSHIP_REQUIRED",
    "message": "You must be a member of this group to perform this action.",
    "details": null
  },
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

## Primary Endpoint Categories

1. **Auth & Profile:** `/users/me`, `/users/me/preferences`, `/auth/dev-session`
2. **Usage & Insights:** `/insights/summary`, `/insights/daily`, `/insights/categories`, `/insights/manual`, `/insights/import`
3. **Friends & Groups:** `/friends`, `/friend-requests`, `/groups`, `/groups/{id}`, `/groups/{id}/invites`, `/group-invites/{token}/accept`
4. **Activities:** `/activities`, `/activities/{id}`, `/activities/{id}/publish`, `/activities/{id}/start`, `/activities/{id}/join`, `/activities/{id}/end`, `/activities/{id}/complete`
5. **Focus Sessions:** `/activities/{id}/focus-sessions`, `/focus-sessions/{id}/end`
6. **Location Check-ins:** `/activities/{id}/check-ins`, `/activities/{id}/check-ins/me`
7. **Proofs & Peer Confirmation:** `/activities/{id}/proofs`, `/proofs/{id}/confirm`
8. **Sanctuary Gardens & Shop:** `/gardens`, `/gardens/{id}/inventory`, `/gardens/{id}/ledger`, `/shop/items`, `/gardens/{id}/purchases`
9. **Privacy Guardian & Wellbeing:** `/ai/privacy/text`, `/ai/wellbeing/recommendation`, `/ai/missions/recommend`

## Middleware integration (2026-11-06)

- Protected endpoints require `Authorization: Bearer <Supabase access token>`. The API verifies the token with the configured Supabase Auth server and derives the acting UUID from the verified user response.
- Local demo identities and `/auth/dev-session` require `DEV_AUTH_ENABLED=true` AND `APP_ENV=development` or `test`. The code defaults to disabled. Production configuration rejects enabling demo authentication.
- CORS exposes `X-Request-Id`, `Retry-After` and `WWW-Authenticate` to allowed origins. Request IDs are UUID strings; invalid supplied values are replaced. Keep the body `request_id` and HTTP status when handling errors.
- Standard errors include 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 501 and 503. Rejected credentials include `WWW-Authenticate: Bearer`; quota failures include `Retry-After` in seconds.
- JSON bodies default to at most 1 MiB actual bytes, including chunked bodies. Compressed request bodies are unsupported. Screening text is additionally limited by `SCREENING_MAX_TEXT_LENGTH` (maximum 10,000 characters).
- Activity browsing accepts `limit=1..100` (default 50), `offset>=0` (default 0), and a valid shared status enum. Response data remains an array.
- Proof upload metadata permits JPEG/PNG/WebP, a safe basename and declared size <=10 MiB. Actual private storage is not connected: upload URL creation and photo registration return `501 STORAGE_NOT_CONFIGURED`. Do not use the former mock URL. Eligible group confirmations still work.
- Per-user policies: general 120/minute, screening 20/minute, invites 10/hour, activity creation 20/hour, upload URL requests 10/hour and proof submissions 10/hour. The configurable IP ceiling defaults to 600/minute. Counters are single-process; distributed deployments need a shared limiter. Supabase owns real login/account throttling.
- Private activity access, focus ownership and current eligible proof-review membership are enforced server-side. Invalid lifecycle operations return 409; completion requests cannot bypass proof requirements.

See `change.md` for the file-by-file implementation, test evidence, configuration and remaining frontend/backend/storage responsibilities. The generated OpenAPI schema is refreshed from `app.openapi()`.

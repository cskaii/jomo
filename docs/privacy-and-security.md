# JOMO — Privacy, Security, and Compliance

## 1. Compliance with Singapore PDPA

- Explicit opt-in consent for sensitive operations (location check-ins, screening, notifications).
- Data minimisation: Coordinates are coarsened to ~100m approximate precision and expired after 24 hours.
- Photos are stored in private object storage, stripped of metadata where feasible, and reviewed only by authorized participants.

## 2. No Covert Monitoring Policy

- Browsers cannot and must not perform covert cross-app surveillance, keylogging, or notification scraping.
- Privacy Guardian functions strictly on text deliberately pasted or submitted by the user.
- Focus Sessions use voluntary timers rather than impossible client-side OS app locks.

## 3. Threat Mitigation

- **Duplicate Rewards:** Prevented via transactional idempotency keys (`activity-completion:{participant_id}`) and unique DB constraints.
- **Unauthorized Actions:** Enforced server-side using object-level authorization (group membership checks, activity participant ownership checks).
- **Injection & Tampering:** Parameterized ORM queries, Pydantic type validation, and rate limiting against brute force.

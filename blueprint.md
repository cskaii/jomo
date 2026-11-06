# JOMO — Complete Technical & Product Implementation Blueprint

**Product:** JOMO — Joy of Missing Out  
**Tagline:** Less scrolling. More living.  
**Document purpose:** Single source of truth for frontend, API/middleware, backend, database, AI, and integration coding agents.  
**Target release:** Hackathon web MVP, with a documented native-mobile roadmap.  
**Primary users:** Students and young adults who want to be more intentional about their digital habits and spend more meaningful time offline.

---

# 0. Instructions for all coding agents

This document is the implementation contract. All agents must follow it unless the project lead explicitly approves a change.

## 0.1 Product objective

JOMO helps people:

1. Understand their digital habits through usage insights.
2. Make intentional decisions about when to use their devices.
3. Spend time on real-world activities, individually or with friends.
4. Earn points for verified offline activity.
5. Grow individual and shared virtual gardens using those points.
6. Identify potentially harmful content and accidental sharing of personal information through privacy-preserving screening.

JOMO must be positive and non-judgmental. It should encourage healthy choices, not shame people for screen time.

## 0.2 Product principles

- **Privacy first:** collect the minimum data necessary.
- **User control:** location sharing, focus sessions, content screening, and photo submission must be transparent and controllable.
- **No covert surveillance:** never silently inspect other apps or messages.
- **No false claims:** do not say JOMO blocks apps or monitors every message unless the relevant native capability is genuinely implemented and authorised.
- **Server-authoritative rewards:** the backend calculates points and validates completion.
- **AI is advisory:** AI must not be the authority for awarding points, deciding whether a person is safe, or taking punitive action.
- **Graceful fallback:** predefined activities and deterministic rules must continue working if an AI model or external API is unavailable.
- **Modular implementation:** frontend, API, business logic, database, and AI must remain independently testable.

## 0.3 Mandatory MVP scope

The first web release should implement:

| Priority | Feature | MVP behaviour |
|---|---|---|
| P0 | Authentication | Register, log in, log out |
| P0 | Insights | Display available usage summaries and demo data |
| P0 | Friends | Create groups, invite friends, join and leave groups |
| P0 | Activities | Browse, create, start, join and complete activities |
| P0 | Focus session | Voluntary timer and reminders; no native app blocking |
| P0 | Location | Optional, activity-scoped location check-in |
| P0 | Photo proof | Optional activity photo or group confirmation |
| P0 | Points | Server-calculated reward and transaction history |
| P0 | Garden | Individual garden and one shared garden per group |
| P0 | Privacy Guardian | Screen text deliberately submitted to JOMO for possible PII |
| P0 | Wellbeing Coach | Rule-based suggestions from aggregated usage data |
| P1 | Harmful-content screening | Detect selected categories in text submitted to JOMO |
| P1 | Mission recommendations | Select and customise predefined activities |
| P2 | Strands agent | Optional AI mission generation |
| P2 | Image redaction | OCR-assisted detection of text in uploaded images |
| Future native | Device-wide usage | Read usage data through approved OS capabilities |
| Future native | App restrictions | Restrict selected apps through approved OS capabilities |
| Future native | Device-wide screening | Only if a platform-approved, consent-based design is technically and legally viable |

**Do not delay the P0 features to implement P2 features.**

## 0.4 Non-negotiable technical decisions

| Area | Decision |
|---|---|
| Frontend | Next.js + React + TypeScript |
| UI styling | Tailwind CSS |
| API/middleware | FastAPI |
| Backend language | Python |
| Database | PostgreSQL |
| Database hosting | Supabase PostgreSQL is an option |
| Authentication | Supabase Auth or a separately implemented secure auth provider; choose one |
| Database access | SQLAlchemy 2.x + Alembic, or Supabase client with a clearly defined data-access layer |
| Validation | Pydantic on API boundaries; Zod on frontend boundaries |
| AI PII screening | Microsoft Presidio + spaCy + custom recognisers |
| Harmful-content screening | Local classifier or deterministic rules for the MVP; optional local model later |
| Wellbeing recommendations | Python rules |
| Mission generation | Curated mission catalogue first; optional Strands agent |
| Image handling | Pillow; optional OCR with Tesseract |
| Realtime updates | Optional Supabase Realtime or WebSocket |
| API format | JSON over HTTPS |
| Time format | ISO 8601 UTC in API/database; convert to local time in UI |
| IDs | UUID |
| Tests | Pytest for backend; Vitest/Jest and Playwright for frontend |
| Version control | Git + GitHub |

Do not create multiple competing backend frameworks. FastAPI is the HTTP API layer and the entry point into the Python backend services.

---

# 1. System architecture

## 1.1 High-level architecture

```mermaid
flowchart TB
    U[User]
    FE[Frontend - Next.js / React]
    MW[API Layer / Middleware - FastAPI]
    AUTH[Authentication Provider]
    BE[Backend Business Services]
    DB[(PostgreSQL)]
    AI[AI Service Layer]
    STORAGE[Private Object Storage]
    NOTIFY[Notification Service]
    OS[Future Native Android / iOS APIs]

    U --> FE
    FE -->|HTTPS JSON| MW
    MW --> AUTH
    MW --> BE
    BE --> DB
    BE --> AI
    BE --> STORAGE
    BE --> NOTIFY
    OS -.->|Authorised device data| FE
    OS -.->|Native capability adapter| MW
```

## 1.2 Responsibility boundaries

### Frontend

The frontend is responsible for:

- Displaying the application.
- Collecting user input.
- Managing page-level UI state.
- Requesting device permissions when a feature requires them.
- Showing location and focus-session status.
- Uploading photos.
- Displaying AI screening results.
- Calling the API.
- Showing loading, success, error, and empty states.

The frontend must not:

- Calculate authoritative points.
- Directly modify garden balances.
- Decide whether an activity is officially completed.
- Trust client-supplied user IDs as proof of identity.
- Store AI provider credentials.
- Directly connect to the database using privileged credentials.
- Decide whether a submitted photo earns a reward.

### API layer / middleware

The API layer is the controlled entry point between the frontend and backend.

It is responsible for:

- Authentication verification.
- Request validation.
- Permission and membership checks.
- Rate limiting.
- Input-size limits.
- Calling backend services.
- Returning consistent responses.
- Mapping internal errors to safe HTTP responses.
- Request IDs and safe audit events.
- Enforcing upload limits.
- Applying security headers and CORS rules.

The API layer must not contain all business logic. It should delegate operations to backend services.

### Backend

The backend owns:

- User profile and preferences.
- Friends and group membership.
- Group invitations.
- Activity creation and lifecycle.
- Activity participants.
- Location check-ins and location privacy rules.
- Focus-session records.
- Usage summaries.
- Mission records.
- Photo-proof records.
- Points and point transactions.
- Garden ownership and inventory.
- Reward validation.
- Notifications and in-app events.

The backend is the source of truth for application state.

### AI service layer

The AI layer provides narrow, testable capabilities:

1. PII detection and text redaction.
2. Harmful-content indicators.
3. Wellbeing recommendations.
4. Optional mission generation.
5. Optional OCR-based image screening.

AI must not own user accounts, points, group membership, garden balances, or activity completion.

---

# 2. Important feasibility and privacy constraints

These constraints affect the product design, database, and implementation.

## 2.1 Device-wide content screening is not a web feature

The proposed feature of screening every message a user sends or receives across every app, 24/7, cannot be implemented by an ordinary website or PWA.

A browser cannot freely read the contents of other applications, intercept their messages, or run an unrestricted permanent monitoring process.

A service worker is not a continuously running background daemon. Browsers may stop it and restart it only when an eligible event occurs. Background sync is for deferred work, not continuous message interception.

### Web MVP implementation

The web version should support:

- Text pasted or typed into JOMO's Privacy Guardian.
- Text submitted through JOMO's own forms or activity features.
- Text the user explicitly chooses to screen.
- Optional local processing in the browser where practical.
- Backend processing only when required and disclosed.

The interface should say:

> JOMO screens content that you choose to submit to the Privacy Guardian. It does not currently monitor messages in other applications.

### Future native implementation

A native Android/iOS app would require a separate technical and policy assessment. Do not assume either operating system permits unrestricted access to all messages.

Do not build a covert keyboard logger, notification scraper, accessibility-based surveillance tool, or other workaround to intercept private messages.

## 2.2 Device-wide usage statistics

The web MVP cannot reliably read total device-wide app usage.

For the MVP:

- Allow users to enter usage information manually.
- Support sample/demo usage records.
- Optionally import a user-selected usage report.
- Keep the usage-data provider abstract so native data can be added later.

Future Android and iOS integrations must use their respective approved frameworks and user permissions.

## 2.3 App locking

A website cannot lock Instagram, TikTok, Snapchat, or other native apps.

The web MVP should implement **Focus Sessions**, not claim to implement a device-wide app blocker.

A Focus Session can:

- Start a timer.
- Show the activity the user has joined.
- Display a reminder that the user chose to take a break.
- Track voluntary participation.
- Let a user pause or end their own session.
- Show other group members who voluntarily joined.

A group organiser must not remotely lock another person's device.

Future native app restrictions need platform-specific implementation, permissions, entitlements, and store-policy review.

## 2.4 Location tracking

Do not continuously collect location just because a user has an account or belongs to a group.

For the MVP:

1. Ask for location permission only when the user starts or joins a location-based activity.
2. Explain why location is requested.
3. Prefer an approximate location or a one-time check-in.
4. Store only the minimum location evidence needed.
5. Do not expose exact coordinates to every group member by default.
6. Stop collecting when the activity ends or the user leaves.
7. Provide a clear way to stop sharing.

A group activity does not need continuous live location to function. Use a one-time check-in and optional later check-in for the MVP.

If proximity verification is introduced later, use a documented, consent-based design. Do not silently track every member.

## 2.5 Photo proof

Photo proof should be optional and proportionate.

- Prefer an activity/object photo over a compulsory selfie.
- Do not implement face recognition in the MVP.
- Do not claim a photo proves a particular person completed an activity.
- Allow group confirmation as an alternative.
- Explain who can see the photo.
- Store photos in private object storage.
- Strip EXIF metadata where possible.
- Set a retention policy.
- Allow deletion subject to legitimate reward/audit requirements.

## 2.6 Singapore privacy considerations

Treat location, account details, photos, and identifiable content as personal data.

Before collecting data, explain the purpose and obtain the appropriate consent. Collect only what is reasonably necessary. Protect stored data, limit access, and define retention and deletion procedures.

The project team should review the Singapore Personal Data Protection Act and applicable PDPC guidance before a public launch. This blueprint is an engineering specification, not legal advice.

---

# 3. Product navigation and conceptual design

## 3.1 Main navigation

The primary tabs are:

1. **Insights**
2. **Friends**
3. **Activities**
4. **Garden**

Profile, settings, privacy controls, and account management can be accessed from the profile/avatar menu.

The Privacy Guardian can be accessed from the dashboard and/or a persistent safety entry point. It does not need to be a primary tab.

## 3.2 Insights

Purpose: help users understand their digital habits without shaming them.

Display:

- Today's total screen time, if available.
- Weekly average.
- Daily trend.
- Category breakdown.
- App breakdown, only where a legitimate data source exists.
- User-set goal.
- Progress towards the goal.
- Optional wellbeing suggestion.

Data source priority:

1. Native device usage integration, when available.
2. User-authorised import.
3. Manual entry.
4. Clearly labelled sample data for the hackathon demo.

Never display fabricated usage as if it were real device telemetry.

## 3.3 Friends

Purpose: connect users and manage friend groups.

Users can:

- Search for a friend using an approved identifier.
- Send and accept friend requests, if the friend-request model is enabled.
- Create a group.
- Invite users to a group.
- Accept or decline group invitations.
- View group members.
- Leave a group.
- View group activity history.
- Start a group activity if they are a member.

A group member can start an activity. The backend must check current membership before allowing this.

## 3.4 Activities

Purpose: make offline activities discoverable and easy to organise.

Users can:

- Browse suggested activities.
- Create a personal activity.
- Create a group activity.
- Start an activity.
- Join an active activity.
- Leave an activity.
- View the activity timer.
- Optionally check in with location.
- Submit photo proof or request group confirmation.
- Complete the activity.
- See points awarded.

Activities should have a clear lifecycle:

```text
DRAFT
  |
  v
PUBLISHED
  |
  v
ACTIVE
  |
  v
AWAITING_PROOF
  |
  v
UNDER_REVIEW (only if review is needed)
  |
  v
COMPLETED

Alternative terminal states:
CANCELLED
EXPIRED
REJECTED
```

The backend owns these transitions.

## 3.5 Garden

Purpose: turn offline activity into visible progress.

### Garden ownership model

Use two garden types:

- `PERSONAL`: owned by one user.
- `GROUP`: owned by one friend group.

Every user should have a personal garden record, even when they belong to groups. This preserves individual progress and prevents data loss when leaving a group.

Each group has its own shared garden.

If a user belongs to three groups, the user can access:

- Their personal garden.
- Group A garden.
- Group B garden.
- Group C garden.

The default Garden screen may show the most recently used or selected garden.

### Garden resources

Points can be spent on:

- Seeds.
- Plants.
- Decorations.
- Pets.
- Other cosmetic items.

Do not allow arbitrary client-side balance changes.

The backend must validate every purchase and record it in the points ledger.

### Reward principles

- Points are earned from eligible activity participation.
- Points are calculated by the server.
- A participant can receive points only once per eligible completion.
- Duplicate photo submissions must not award duplicate points.
- Group garden rewards are credited to the relevant group garden.
- Personal garden rewards are credited to the user's personal garden.
- Leaving a group does not transfer ownership of the group garden.
- A user's personal garden is never deleted merely because the user joins a group.

---

# 4. Frontend implementation blueprint

## 4.1 Frontend responsibilities

The frontend team owns:

- Responsive UI.
- Routing.
- Page layouts.
- Reusable components.
- Form validation.
- API client.
- Authentication state.
- Permission prompts.
- Loading/error states.
- Charts.
- Camera/photo upload interface.
- Focus-session timer.
- Toasts and notifications.
- Accessibility and responsive behaviour.

The frontend team does not own database schema or reward calculations.

## 4.2 Recommended folder structure

```text
frontend/
├── public/
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   │
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   └── forgot-password/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (main)/
│   │   │   ├── layout.tsx
│   │   │   ├── insights/
│   │   │   │   └── page.tsx
│   │   │   ├── friends/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── groups/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   ├── create/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── [groupId]/
│   │   │   │   │       └── page.tsx
│   │   │   ├── activities/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── create/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── [activityId]/
│   │   │   │       └── page.tsx
│   │   │   ├── garden/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [gardenId]/
│   │   │   │       └── page.tsx
│   │   │   ├── privacy-guardian/
│   │   │   │   └── page.tsx
│   │   │   ├── focus/
│   │   │   │   └── [sessionId]/
│   │   │   │       └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   │
│   │   └── api/
│   │       └── auth/
│   │           └── callback/
│   │               └── route.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── BottomNavigation.tsx
│   │   │   └── Header.tsx
│   │   │
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Loading.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ErrorState.tsx
│   │   │
│   │   ├── insights/
│   │   ├── friends/
│   │   ├── groups/
│   │   ├── activities/
│   │   ├── garden/
│   │   ├── privacy/
│   │   └── focus/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── insights/
│   │   ├── friends/
│   │   ├── groups/
│   │   ├── activities/
│   │   ├── gardens/
│   │   ├── privacy-guardian/
│   │   └── focus-sessions/
│   │
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── authService.ts
│   │   ├── insightsService.ts
│   │   ├── friendsService.ts
│   │   ├── groupsService.ts
│   │   ├── activitiesService.ts
│   │   ├── gardensService.ts
│   │   ├── privacyService.ts
│   │   └── focusService.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useCurrentUser.ts
│   │   ├── useLocationPermission.ts
│   │   ├── useFocusTimer.ts
│   │   └── useToast.ts
│   │
│   ├── types/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── group.ts
│   │   ├── activity.ts
│   │   ├── garden.ts
│   │   ├── privacy.ts
│   │   └── usage.ts
│   │
│   ├── schemas/
│   │   ├── auth.schema.ts
│   │   ├── activity.schema.ts
│   │   └── group.schema.ts
│   │
│   ├── lib/
│   │   ├── config.ts
│   │   ├── formatDate.ts
│   │   ├── formatDuration.ts
│   │   └── permissions.ts
│   │
│   └── middleware.ts
│
├── tests/
│   ├── unit/
│   └── e2e/
│
├── .env.example
├── package.json
├── tsconfig.json
├── next.config.ts
└── README.md
```

## 4.3 What each folder is for

| Folder | Responsibility | What to code |
|---|---|---|
| `app/` | Next.js routes and page composition | Route pages, layouts, auth callback |
| `components/` | Reusable UI | Cards, modals, charts, navigation, garden visuals |
| `features/` | Feature-specific UI logic | Feature hooks, state, components, view models |
| `services/` | HTTP calls | Functions calling the FastAPI endpoints |
| `hooks/` | Shared React hooks | Auth, timers, permissions, toast state |
| `types/` | Shared TypeScript contracts | Request and response interfaces |
| `schemas/` | Client-side validation | Zod schemas for forms and inputs |
| `lib/` | Utilities and configuration | Formatting, safe config, permission helpers |
| `public/` | Static assets | Images, logos, icons, fonts |
| `tests/` | Automated tests | Unit and browser tests |

Do not put all logic in `page.tsx`. Pages should compose feature components and call feature hooks or services.

## 4.4 Frontend pages and implementation tasks

### A. Authentication

Pages:

- `/login`
- `/register`
- `/forgot-password`

Tasks:

- Build registration and login forms.
- Validate input.
- Call the chosen authentication provider.
- Store session using its recommended secure flow.
- Redirect unauthenticated users to login.
- Load the current user from the API.
- Provide logout.

Do not put passwords in application tables unless the team is deliberately implementing a complete, security-reviewed authentication system. Prefer a dedicated authentication provider.

### B. Insights page

Components:

```text
components/insights/
├── UsageSummaryCard.tsx
├── UsageTrendChart.tsx
├── AppBreakdownChart.tsx
├── GoalProgressCard.tsx
└── WellbeingSuggestionCard.tsx
```

Tasks:

- Request usage summary from the API.
- Display the data source: device integration, import, manual, or demo.
- Display daily and weekly values.
- Display goal progress.
- Show a rule-based wellbeing recommendation.
- Handle missing usage data without inventing values.

Suggested chart library: Recharts.

### C. Friends and Groups

Components:

```text
components/friends/
├── FriendList.tsx
├── FriendCard.tsx
├── FriendSearch.tsx
└── FriendRequestCard.tsx

components/groups/
├── GroupList.tsx
├── GroupCard.tsx
├── CreateGroupForm.tsx
├── InviteMemberDialog.tsx
├── GroupMembersList.tsx
└── GroupActivityFeed.tsx
```

Tasks:

- Display the user's groups.
- Create a group.
- Invite by a secure invite code or link.
- Accept/decline invitations.
- Display members and membership roles.
- Allow a user to leave a group.
- Display group activities and shared garden entry point.

### D. Activities

Components:

```text
components/activities/
├── ActivityList.tsx
├── ActivityCard.tsx
├── ActivityDetails.tsx
├── CreateActivityForm.tsx
├── JoinActivityButton.tsx
├── ActivityStatusBadge.tsx
├── ActivityTimer.tsx
├── LocationCheckIn.tsx
├── PhotoProofUpload.tsx
└── CompletionSummary.tsx
```

Tasks:

- Browse available activities.
- Create personal or group activities.
- Validate activity duration and participant limits.
- Start or join an activity.
- Display status and timer.
- Ask for location permission only when needed.
- Submit optional check-in.
- Submit photo proof or request group confirmation.
- Display points only after the backend confirms the award.

### E. Garden

Components:

```text
components/garden/
├── GardenCanvas.tsx
├── GardenSelector.tsx
├── GardenInventory.tsx
├── SeedCard.tsx
├── PetCard.tsx
├── ResourceBalance.tsx
├── PurchaseDialog.tsx
└── GardenActivityHistory.tsx
```

Tasks:

- Fetch gardens the current user is allowed to view.
- Let users switch between personal and group gardens.
- Display points balance.
- Display owned items.
- Purchase seeds/pets/resources.
- Display garden growth.
- Never optimistically show a purchase as final until the API confirms it.

### F. Privacy Guardian

Components:

```text
components/privacy/
├── PrivacyTextInput.tsx
├── ScreeningResult.tsx
├── DetectionList.tsx
├── RedactedTextPreview.tsx
└── PrivacyNotice.tsx
```

Tasks:

- Let the user paste or type text.
- Explain what screening does.
- Submit only after a user action.
- Show possible PII categories and locations in the text.
- Show redacted output.
- Allow the user to copy the redacted output.
- Do not store raw text in browser local storage.
- Do not display a green "safe" status merely because no detector triggered.

### G. Focus Session

Components:

```text
components/focus/
├── FocusSessionPanel.tsx
├── FocusTimer.tsx
├── FocusControls.tsx
├── ParticipantStatus.tsx
└── FocusSessionSummary.tsx
```

Tasks:

- Start and stop a voluntary timer.
- Display the activity and participants.
- Let the current user leave.
- Show a clear explanation that web Focus Sessions do not block other native apps.
- Sync start/end state with the backend.

## 4.5 Frontend TypeScript contracts

All frontend services must use these shared types.

```typescript
export type UUID = string;
export type ISODateTime = string;

export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data: T;
  request_id: string;
}

export interface UserProfile {
  id: UUID;
  username: string;
  display_name: string;
  avatar_url: string | null;
  created_at: ISODateTime;
}

export interface UsageSummary {
  date: string;
  total_minutes: number;
  social_minutes: number | null;
  source: "native" | "manual" | "import" | "demo";
}

export interface GroupSummary {
  id: UUID;
  name: string;
  member_count: number;
  role: "owner" | "admin" | "member";
  created_at: ISODateTime;
}

export type ActivityStatus =
  | "draft"
  | "published"
  | "active"
  | "awaiting_proof"
  | "under_review"
  | "completed"
  | "cancelled"
  | "expired"
  | "rejected";

export interface ActivitySummary {
  id: UUID;
  title: string;
  description: string;
  duration_minutes: number;
  status: ActivityStatus;
  group_id: UUID | null;
  created_by: UUID;
  starts_at: ISODateTime | null;
  ends_at: ISODateTime | null;
  participant_count: number;
}

export interface GardenSummary {
  id: UUID;
  garden_type: "personal" | "group";
  owner_user_id: UUID | null;
  owner_group_id: UUID | null;
  name: string;
  points_balance: number;
}

export interface PrivacyDetection {
  entity_type: string;
  start: number;
  end: number;
  score: number;
  category: "pii" | "harmful_content";
  explanation?: string;
}

export interface PrivacyScreeningResult {
  status: "completed" | "partial";
  has_potential_pii: boolean;
  has_harmful_content_indicators: boolean;
  detections: PrivacyDetection[];
  redacted_text: string | null;
  limitations: string[];
}
```

The frontend may add presentation-only fields, but it must not redefine the meaning of API fields.

## 4.6 API client

All requests must go through one configured client.

```typescript
// src/services/apiClient.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("API base URL is not configured");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.error?.message ?? "Request failed");
  }

  return body.data as T;
}
```

Authentication headers/cookies must match the selected auth provider. Do not assume the example above is sufficient for every provider.

---

# 5. API layer / middleware blueprint

## 5.1 Why this layer exists

The middleware/API layer is the boundary between untrusted client input and trusted backend operations.

For this project, FastAPI can serve as both:

- The HTTP API layer.
- The application entry point into backend services.

A separate Node middleware server is unnecessary for the MVP.

## 5.2 Middleware folder structure

```text
backend/
└── app/
    ├── main.py
    │
    ├── api/
    │   ├── router.py
    │   ├── dependencies.py
    │   └── v1/
    │       ├── auth.py
    │       ├── users.py
    │       ├── insights.py
    │       ├── friends.py
    │       ├── groups.py
    │       ├── activities.py
    │       ├── focus.py
    │       ├── locations.py
    │       ├── proofs.py
    │       ├── gardens.py
    │       ├── privacy.py
    │       └── notifications.py
    │
    ├── middleware/
    │   ├── request_id.py
    │   ├── security_headers.py
    │   ├── rate_limit.py
    │   └── exception_handler.py
    │
    ├── schemas/
    │   ├── common.py
    │   ├── user.py
    │   ├── group.py
    │   ├── activity.py
    │   ├── garden.py
    │   ├── privacy.py
    │   └── usage.py
    │
    ├── core/
    │   ├── config.py
    │   ├── auth.py
    │   ├── permissions.py
    │   └── logging.py
    │
    ├── services/
    ├── repositories/
    ├── models/
    ├── ai/
    ├── db/
    └── tests/
```

This is a logical structure inside one backend application. The `api/`, `middleware/`, `schemas/`, and `core/` folders form the API/middleware boundary. The `services/`, `repositories/`, and `models/` folders contain backend implementation.

## 5.3 Middleware request flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as FastAPI API
    participant AU as Auth
    participant P as Permission Checks
    participant S as Backend Service
    participant D as Database
    F->>A: HTTPS request + auth
    A->>AU: Verify token/session
    AU-->>A: Authenticated user ID
    A->>P: Check ownership/membership
    P-->>A: Allowed or denied
    A->>S: Validated request + actor ID
    S->>D: Read/write data
    D-->>S: Result
    S-->>A: Domain result
    A-->>F: Standard JSON response
```

## 5.4 Middleware responsibilities

### Authentication

- Verify the user's session/token.
- Resolve the authenticated user ID.
- Reject invalid or expired sessions.
- Never trust a `user_id` in the request body as the acting user.

The acting user must come from the verified authentication context.

### Authorisation

Examples:

- Only group members can view a private group.
- Only a group member can start a group activity.
- Only an activity participant can submit proof for that participation.
- Only the owner can edit a personal garden.
- Only a group member can use a group's shared garden.
- A user cannot award themselves points.
- A user cannot submit proof for another participant.

### Validation

Use Pydantic request schemas.

Validate:

- String lengths.
- UUID format.
- Allowed enum values.
- Duration bounds.
- Participant limits.
- Upload MIME type and size.
- Location precision and validity.
- State transitions.
- Pagination limits.

### Rate limiting

Suggested initial limits, to be tuned after testing:

| Endpoint class | Example limit |
|---|---|
| Login attempts | Strict per-IP and per-account limit |
| Text screening | 20 requests/minute/user |
| Invite creation | 10 requests/hour/user |
| Activity creation | 20 requests/hour/user |
| Proof upload | 10 uploads/hour/user |
| General reads | 120 requests/minute/user |

These are starting values, not security guarantees.

### Error handling

Use a consistent error envelope:

```json
{
  "error": {
    "code": "GROUP_MEMBERSHIP_REQUIRED",
    "message": "You must be a member of this group to perform this action.",
    "details": null
  },
  "request_id": "uuid"
}
```

Never expose stack traces, SQL errors, model credentials, or raw internal exceptions to the frontend.

## 5.5 API endpoint specification

All endpoints are under `/api/v1`.

### Authentication and profile

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/users/me` | Current user's profile |
| PATCH | `/users/me` | Update profile |
| GET | `/users/me/preferences` | Get preferences |
| PATCH | `/users/me/preferences` | Update preferences |

Authentication provider endpoints may handle registration/login directly. The backend must still validate the authenticated session for application requests.

### Insights

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/insights/summary` | Summary for a date range |
| GET | `/insights/daily` | Daily usage records |
| GET | `/insights/categories` | Usage by category |
| POST | `/insights/manual` | Submit manual usage |
| POST | `/insights/import` | Submit a user-authorised import |

Query parameters should include `from` and `to`, with bounded date ranges.

### Friends and groups

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/friends` | List friends |
| POST | `/friend-requests` | Send a request |
| POST | `/friend-requests/{id}/accept` | Accept request |
| POST | `/friend-requests/{id}/decline` | Decline request |
| GET | `/groups` | List user's groups |
| POST | `/groups` | Create group |
| GET | `/groups/{group_id}` | Group details |
| PATCH | `/groups/{group_id}` | Update group |
| POST | `/groups/{group_id}/invites` | Create invite |
| POST | `/group-invites/{token}/accept` | Accept invite |
| POST | `/groups/{group_id}/leave` | Leave group |
| GET | `/groups/{group_id}/members` | List members |

### Activities

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/activities` | Browse activities |
| POST | `/activities` | Create activity |
| GET | `/activities/{id}` | Activity details |
| PATCH | `/activities/{id}` | Update eligible activity |
| POST | `/activities/{id}/publish` | Publish activity |
| POST | `/activities/{id}/start` | Start activity |
| POST | `/activities/{id}/join` | Join active activity |
| POST | `/activities/{id}/leave` | Leave activity |
| POST | `/activities/{id}/end` | End activity |
| GET | `/activities/{id}/participants` | Participant list |
| POST | `/activities/{id}/complete` | Request completion |

### Focus sessions

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/activities/{id}/focus-sessions` | Start own focus participation |
| POST | `/focus-sessions/{id}/end` | End own focus participation |
| GET | `/focus-sessions/{id}` | Get focus session status |

### Location

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/activities/{id}/check-ins` | Submit own check-in |
| GET | `/activities/{id}/check-ins/me` | Get own check-in status |
| DELETE | `/activities/{id}/check-ins/me` | Delete own check-in where permitted |

Do not create an endpoint that returns every group member's exact location to every other member.

### Proof

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/activities/{id}/proofs/upload-url` | Request upload URL |
| POST | `/activities/{id}/proofs` | Register proof metadata |
| GET | `/activities/{id}/proofs/me` | Get own proof status |
| POST | `/proofs/{id}/confirm` | Submit a group confirmation |
| DELETE | `/proofs/{id}` | Delete proof where permitted |

### Garden and points

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/gardens` | List accessible gardens |
| GET | `/gardens/{id}` | Garden details |
| GET | `/gardens/{id}/inventory` | Garden inventory |
| GET | `/gardens/{id}/ledger` | Points transactions |
| GET | `/shop/items` | Available items |
| POST | `/gardens/{id}/purchases` | Purchase item |
| POST | `/gardens/{id}/items/{item_id}/place` | Place an owned item |

There must be no public endpoint like `POST /points/add`. Points are awarded only through trusted backend workflows.

### AI

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ai/privacy/text` | Screen user-submitted text |
| POST | `/ai/privacy/image` | Optional image screening |
| POST | `/ai/wellbeing/recommendation` | Generate rule-based recommendation |
| POST | `/ai/missions/recommend` | Recommend catalogue activities |

## 5.6 API request and response contracts

### Create activity

Request:

```json
{
  "title": "Sunset Walk",
  "description": "Take a relaxed walk together.",
  "duration_minutes": 30,
  "visibility": "group",
  "group_id": "uuid",
  "max_participants": 6,
  "location_required": false,
  "proof_requirement": "photo_or_group_confirmation"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "title": "Sunset Walk",
    "status": "published",
    "created_by": "uuid",
    "group_id": "uuid",
    "duration_minutes": 30
  },
  "request_id": "uuid"
}
```

The backend must confirm that the authenticated user belongs to `group_id`.

### Start activity

Request:

```json
{
  "client_started_at": "2026-11-06T11:00:00+08:00"
}
```

The client time is informational only. The backend records its own authoritative `started_at`.

Response:

```json
{
  "data": {
    "activity_id": "uuid",
    "status": "active",
    "started_at": "2026-11-06T03:00:02Z"
  },
  "request_id": "uuid"
}
```

### Submit location check-in

Request:

```json
{
  "latitude": 1.3500,
  "longitude": 103.9000,
  "accuracy_meters": 50,
  "captured_at": "2026-11-06T11:05:00+08:00",
  "consent": true
}
```

Response:

```json
{
  "data": {
    "check_in_id": "uuid",
    "accepted": true,
    "precision": "approximate"
  },
  "request_id": "uuid"
}
```

Do not return the exact coordinates to other participants by default.

### Screen text

Request:

```json
{
  "text": "Please contact me at alex@example.com.",
  "checks": ["pii", "harmful_content"],
  "language": "en"
}
```

Response:

```json
{
  "data": {
    "status": "completed",
    "has_potential_pii": true,
    "has_harmful_content_indicators": false,
    "detections": [
      {
        "entity_type": "EMAIL_ADDRESS",
        "start": 21,
        "end": 38,
        "score": 0.95,
        "category": "pii"
      }
    ],
    "redacted_text": "Please contact me at [REDACTED].",
    "limitations": [
      "Automated screening can miss sensitive information.",
      "A result with no detections does not guarantee that text is safe."
    ]
  },
  "request_id": "uuid"
}
```

The example offsets and scores are illustrative. Actual results depend on the text and recognisers.

---

# 6. Backend implementation blueprint

## 6.1 Backend responsibilities

The backend is responsible for the application's business rules and persistent data.

It must:

- Authenticate the actor through the API dependency layer.
- Enforce group and activity membership.
- Enforce activity state transitions.
- Record server-side timestamps.
- Calculate eligible activity duration.
- Calculate points.
- Prevent duplicate rewards.
- Manage garden ownership.
- Validate purchases.
- Record an immutable points ledger.
- Handle photo metadata.
- Enforce privacy and deletion rules.
- Call AI services through a defined interface.

## 6.2 Recommended backend folder structure

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── users.py
│   │       ├── insights.py
│   │       ├── friends.py
│   │       ├── groups.py
│   │       ├── activities.py
│   │       ├── focus.py
│   │       ├── locations.py
│   │       ├── proofs.py
│   │       ├── gardens.py
│   │       ├── privacy.py
│   │       └── notifications.py
│   │
│   ├── middleware/
│   │   ├── request_id.py
│   │   ├── rate_limit.py
│   │   ├── security_headers.py
│   │   └── exception_handler.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   ├── logging.py
│   │   └── constants.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── friendship.py
│   │   ├── group.py
│   │   ├── activity.py
│   │   ├── location.py
│   │   ├── proof.py
│   │   ├── usage.py
│   │   ├── points.py
│   │   └── garden.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── activity.py
│   │   ├── location.py
│   │   ├── proof.py
│   │   ├── points.py
│   │   ├── garden.py
│   │   └── privacy.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── group_repository.py
│   │   ├── activity_repository.py
│   │   ├── points_repository.py
│   │   └── garden_repository.py
│   │
│   ├── services/
│   │   ├── user_service.py
│   │   ├── friendship_service.py
│   │   ├── group_service.py
│   │   ├── activity_service.py
│   │   ├── focus_service.py
│   │   ├── location_service.py
│   │   ├── proof_service.py
│   │   ├── points_service.py
│   │   ├── garden_service.py
│   │   ├── usage_service.py
│   │   └── notification_service.py
│   │
│   ├── ai/
│   │   ├── interfaces.py
│   │   ├── screening_service.py
│   │   ├── privacy/
│   │   │   ├── analyzer.py
│   │   │   ├── recognizers.py
│   │   │   └── redactor.py
│   │   ├── harmful_content/
│   │   │   ├── classifier.py
│   │   │   └── rules.py
│   │   ├── wellbeing/
│   │   │   └── recommender.py
│   │   ├── missions/
│   │   │   ├── catalogue.py
│   │   │   ├── recommender.py
│   │   │   └── agent.py
│   │   └── images/
│   │       ├── ocr.py
│   │       └── redactor.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── seed.py
│   │
│   └── utils/
│       ├── datetime.py
│       ├── ids.py
│       └── storage.py
│
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── fixtures/
│
├── scripts/
│   ├── create_demo_data.py
│   └── check_environment.py
│
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

## 6.3 Folder responsibilities

| Folder | Purpose |
|---|---|
| `api/` | HTTP routes and request/response handling |
| `middleware/` | Cross-cutting HTTP concerns |
| `core/` | Configuration, authentication, permissions, logging |
| `models/` | Database ORM models |
| `schemas/` | Pydantic API schemas |
| `repositories/` | Database query operations |
| `services/` | Business rules and workflows |
| `ai/` | AI capabilities and adapters |
| `db/` | Database engine, sessions, base metadata, seed data |
| `utils/` | Shared utilities |
| `migrations/` | Alembic database migrations |
| `tests/` | Unit, integration, and security tests |

## 6.4 Service boundaries

### User service

- Create/update profile.
- Read user preferences.
- Create the user's personal garden during onboarding.
- Handle account deletion workflow.

### Friendship service

- Send friend requests.
- Accept/decline requests.
- Remove friendship.
- Prevent duplicate or self-friend requests.

### Group service

- Create group.
- Invite members.
- Accept/decline invites.
- Change member roles.
- Leave group.
- Check membership.
- Ensure group garden exists.

### Activity service

- Create and publish activity.
- Start activity.
- Join/leave.
- End activity.
- Validate activity lifecycle.
- Request completion.
- Coordinate proof and points workflows.

### Location service

- Validate user consent.
- Record activity-scoped check-ins.
- Apply precision reduction where appropriate.
- Enforce retention.
- Return only the minimum information needed.

### Proof service

- Generate secure upload URLs.
- Validate registered uploads.
- Store proof metadata.
- Coordinate group confirmation.
- Mark proof as pending, accepted, or rejected.
- Delete or expire files according to policy.

### Points service

- Calculate eligible points.
- Check idempotency.
- Insert point transactions.
- Update the relevant balance within a database transaction.
- Never accept client-supplied reward amounts.

### Garden service

- Create personal/group gardens.
- List accessible gardens.
- Purchase items.
- Place items.
- Update garden growth.
- Check inventory and balance.

### Usage service

- Store usage summaries.
- Normalise source formats.
- Reject impossible values.
- Aggregate data by date and category.
- Provide summaries to Insights and Wellbeing Coach.

---

# 7. Database design

## 7.1 Database principles

Use PostgreSQL.

Use UUID primary keys for application entities.

Use `TIMESTAMPTZ` for timestamps. Store timestamps in UTC and convert to local time in the frontend.

Use foreign keys for referential integrity.

Use database constraints for invariants where possible.

Use migrations. Do not modify production tables manually without a migration.

Do not store passwords in application tables if using a dedicated authentication provider.

## 7.2 Entity relationship overview

```mermaid
erDiagram
    USERS ||--|| USER_PREFERENCES : has
    USERS ||--o{ FRIENDSHIPS : participates
    USERS ||--o{ GROUP_MEMBERS : joins
    GROUPS ||--o{ GROUP_MEMBERS : contains
    GROUPS ||--o{ GROUP_INVITES : issues
    USERS ||--o{ ACTIVITIES : creates
    GROUPS o|--o{ ACTIVITIES : hosts
    ACTIVITIES ||--o{ ACTIVITY_PARTICIPANTS : has
    USERS ||--o{ ACTIVITY_PARTICIPANTS : joins
    ACTIVITIES ||--o{ ACTIVITY_CHECK_INS : records
    USERS ||--o{ ACTIVITY_CHECK_INS : submits
    ACTIVITIES ||--o{ PROOF_SUBMISSIONS : requires
    USERS ||--o{ PROOF_SUBMISSIONS : submits
    PROOF_SUBMISSIONS ||--o{ PROOF_CONFIRMATIONS : receives
    USERS ||--o{ USAGE_SUMMARIES : owns
    USERS ||--o{ GARDENS : owns_personal
    GROUPS ||--|| GARDENS : owns_group
    GARDENS ||--o{ GARDEN_ITEMS : contains
    GARDENS ||--o{ POINT_TRANSACTIONS : records
    USERS ||--o{ POINT_TRANSACTIONS : earns_or_spends
    GARDEN_CATALOG_ITEMS ||--o{ GARDEN_ITEMS : defines
    USERS ||--o{ NOTIFICATIONS : receives
```

The ERD is conceptual. The SQL definitions below are the authoritative schema proposal.

## 7.3 Core tables

### Table 1: `users`

Stores the application profile.

Authentication credentials should remain in the chosen auth provider.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | Must match auth provider user ID |
| `username` | VARCHAR(30) | UNIQUE | Public handle |
| `display_name` | VARCHAR(80) | | Display name |
| `avatar_url` | TEXT | | Optional private/public asset reference |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |
| `deleted_at` | TIMESTAMPTZ | | Nullable soft deletion |

### Table 2: `user_preferences`

| Column | Type | Key | Notes |
|---|---|---|---|
| `user_id` | UUID | PK, FK | References `users.id` |
| `timezone` | VARCHAR(64) | | Default `Asia/Singapore` only if appropriate |
| `language` | VARCHAR(10) | | |
| `daily_screen_goal_minutes` | INTEGER | | Nullable |
| `location_enabled` | BOOLEAN | | User preference, not blanket permission |
| `screening_enabled` | BOOLEAN | | In-app screening preference |
| `notifications_enabled` | BOOLEAN | | |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |

A stored preference does not replace an operating-system permission prompt.

### Table 3: `friendships`

Represents accepted friendships.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_low_id` | UUID | FK | References `users.id` |
| `user_high_id` | UUID | FK | References `users.id` |
| `created_at` | TIMESTAMPTZ | | |

Constraints:

- `user_low_id < user_high_id` using canonical UUID ordering.
- Unique (`user_low_id`, `user_high_id`).
- No self-friendship.

### Table 4: `friend_requests`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `sender_id` | UUID | FK | References `users.id` |
| `receiver_id` | UUID | FK | References `users.id` |
| `status` | VARCHAR(20) | | pending/accepted/declined/cancelled |
| `created_at` | TIMESTAMPTZ | | |
| `responded_at` | TIMESTAMPTZ | | Nullable |

Constraints:

- Sender and receiver must differ.
- Prevent duplicate pending requests between the same pair.
- Only the receiver can accept or decline.

### Table 5: `groups`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `name` | VARCHAR(80) | | |
| `description` | TEXT | | Nullable |
| `created_by` | UUID | FK | References `users.id` |
| `visibility` | VARCHAR(20) | | private/invite_only |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |
| `archived_at` | TIMESTAMPTZ | | Nullable |

### Table 6: `group_members`

Join table connecting users and groups.

| Column | Type | Key | Notes |
|---|---|---|---|
| `group_id` | UUID | PK part, FK | References `groups.id` |
| `user_id` | UUID | PK part, FK | References `users.id` |
| `role` | VARCHAR(20) | | owner/admin/member |
| `status` | VARCHAR(20) | | active/left/removed |
| `joined_at` | TIMESTAMPTZ | | |
| `left_at` | TIMESTAMPTZ | | Nullable |

Primary key: (`group_id`, `user_id`).

Use a membership history strategy if the team needs users to leave and rejoin without losing historical membership records. One option is a separate `group_membership_events` table. For the MVP, update the existing membership row and preserve `joined_at`/`left_at`; do not create duplicate active memberships.

### Table 7: `group_invites`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `group_id` | UUID | FK | References `groups.id` |
| `created_by` | UUID | FK | References `users.id` |
| `token_hash` | VARCHAR(128) | UNIQUE | Store hash, not raw invite token |
| `expires_at` | TIMESTAMPTZ | | |
| `max_uses` | INTEGER | | Nullable |
| `uses_count` | INTEGER | | Default 0 |
| `revoked_at` | TIMESTAMPTZ | | Nullable |
| `created_at` | TIMESTAMPTZ | | |

The raw invite token is shown to the invite creator once. Store only its hash.

### Table 8: `activities`

Represents an activity definition and its lifecycle.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `created_by` | UUID | FK | References `users.id` |
| `group_id` | UUID | FK | Nullable; references `groups.id` |
| `title` | VARCHAR(120) | | |
| `description` | TEXT | | |
| `category` | VARCHAR(40) | | outdoor/social/creative/etc. |
| `visibility` | VARCHAR(20) | | personal/group |
| `status` | VARCHAR(30) | | lifecycle enum |
| `duration_minutes` | INTEGER | | Planned duration |
| `max_participants` | INTEGER | | |
| `location_required` | BOOLEAN | | |
| `proof_requirement` | VARCHAR(40) | | none/photo/group_confirmation/photo_or_group_confirmation |
| `points_per_minute` | NUMERIC(6,2) | | Optional reward configuration; server-controlled |
| `max_reward_points` | INTEGER | | Reward cap |
| `published_at` | TIMESTAMPTZ | | |
| `started_at` | TIMESTAMPTZ | | Server-generated |
| `ended_at` | TIMESTAMPTZ | | Server-generated |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |

Rules:

- A personal activity has `group_id = NULL`.
- A group activity has a non-null `group_id`.
- A group activity creator must be an active group member.
- A group activity must not be visible to non-members unless explicitly designed as public.
- The client cannot set authoritative start/end timestamps.
- Validate `duration_minutes` and `max_reward_points` on the server.

### Table 9: `activity_participants`

One row per user participating in an activity.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `activity_id` | UUID | FK | References `activities.id` |
| `user_id` | UUID | FK | References `users.id` |
| `status` | VARCHAR(30) | | joined/active/left/awaiting_proof/completed/rejected |
| `joined_at` | TIMESTAMPTZ | | |
| `started_at` | TIMESTAMPTZ | | Nullable |
| `ended_at` | TIMESTAMPTZ | | Nullable |
| `eligible_minutes` | INTEGER | | Server-calculated |
| `points_awarded` | INTEGER | | Default 0 |
| `completed_at` | TIMESTAMPTZ | | Nullable |

Constraints:

- Unique (`activity_id`, `user_id`) for the MVP.
- One user cannot join the same activity twice.
- A participant can only submit proof for their own participation.
- Points are calculated after eligibility checks.

If repeat participation in the same activity is required later, replace the unique constraint with a participation-session model.

### Table 10: `activity_check_ins`

Stores minimal activity-scoped location evidence.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `activity_id` | UUID | FK | References `activities.id` |
| `participant_id` | UUID | FK | References `activity_participants.id` |
| `latitude` | NUMERIC(9,6) | | Nullable; avoid retaining exact coordinates if unnecessary |
| `longitude` | NUMERIC(9,6) | | Nullable |
| `accuracy_meters` | NUMERIC(8,2) | | |
| `precision_level` | VARCHAR(20) | | approximate/precise |
| `consent_at` | TIMESTAMPTZ | | |
| `captured_at` | TIMESTAMPTZ | | |
| `created_at` | TIMESTAMPTZ | | |
| `expires_at` | TIMESTAMPTZ | | |

Use a retention job to delete or coarsen records when no longer needed.

Do not use location as the sole proof that an activity happened.

### Table 11: `focus_sessions`

Records a participant's voluntary focus participation.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `activity_id` | UUID | FK | References `activities.id` |
| `participant_id` | UUID | FK | References `activity_participants.id` |
| `started_at` | TIMESTAMPTZ | | Server-generated |
| `ended_at` | TIMESTAMPTZ | | Nullable |
| `status` | VARCHAR(20) | | active/completed/cancelled |
| `created_at` | TIMESTAMPTZ | | |

A focus session records voluntary participation. It does not prove that native apps were blocked.

### Table 12: `proof_submissions`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `activity_id` | UUID | FK | References `activities.id` |
| `participant_id` | UUID | FK | References `activity_participants.id` |
| `proof_type` | VARCHAR(30) | | photo/group_confirmation |
| `storage_key` | TEXT | | Private storage key; nullable for group confirmation |
| `mime_type` | VARCHAR(100) | | Nullable |
| `file_size_bytes` | BIGINT | | Nullable |
| `status` | VARCHAR(20) | | pending/accepted/rejected |
| `submitted_at` | TIMESTAMPTZ | | |
| `reviewed_at` | TIMESTAMPTZ | | Nullable |
| `reviewed_by` | UUID | FK | Nullable; references `users.id` |
| `retention_until` | TIMESTAMPTZ | | Nullable |

Do not store image bytes directly in PostgreSQL. Store the object in private object storage and keep its storage key here.

### Table 13: `proof_confirmations`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `proof_id` | UUID | FK | References `proof_submissions.id` |
| `confirmed_by` | UUID | FK | References `users.id` |
| `decision` | VARCHAR(20) | | confirm/reject |
| `comment` | VARCHAR(300) | | Optional |
| `created_at` | TIMESTAMPTZ | | |

Constraint: unique (`proof_id`, `confirmed_by`).

The backend must ensure that the confirmer is an eligible participant or authorised reviewer and is not simply confirming their own submission where independent confirmation is required.

### Table 14: `usage_summaries`

Stores daily aggregate usage, not a permanent stream of every app event.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK | References `users.id` |
| `usage_date` | DATE | | |
| `total_minutes` | INTEGER | | |
| `social_minutes` | INTEGER | | Nullable |
| `category_breakdown` | JSONB | | Optional |
| `source` | VARCHAR(20) | | native/manual/import/demo |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |

Constraint: unique (`user_id`, `usage_date`, `source`).

Validate that minutes are non-negative and within sensible limits.

### Table 15: `garden_catalog_items`

Defines items users can purchase.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `name` | VARCHAR(80) | | |
| `description` | TEXT | | |
| `item_type` | VARCHAR(30) | | seed/plant/pet/decoration |
| `price_points` | INTEGER | | |
| `asset_key` | TEXT | | |
| `is_active` | BOOLEAN | | |
| `created_at` | TIMESTAMPTZ | | |

### Table 16: `gardens`

One personal garden per user and one shared garden per group.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `garden_type` | VARCHAR(20) | | personal/group |
| `owner_user_id` | UUID | FK | Nullable; references `users.id` |
| `owner_group_id` | UUID | FK | Nullable; references `groups.id` |
| `name` | VARCHAR(80) | | |
| `points_balance` | INTEGER | | Default 0; maintained transactionally |
| `growth_level` | INTEGER | | Default 1 |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |

Constraints:

- Personal garden: `owner_user_id` non-null and `owner_group_id` null.
- Group garden: `owner_group_id` non-null and `owner_user_id` null.
- Exactly one owner field must be populated.
- Unique personal garden per user.
- Unique group garden per group.

Use a PostgreSQL CHECK constraint for the owner-field rule and partial unique indexes for each owner type.

### Table 17: `garden_items`

Represents items owned or placed in a garden.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `garden_id` | UUID | FK | References `gardens.id` |
| `catalog_item_id` | UUID | FK | References `garden_catalog_items.id` |
| `quantity` | INTEGER | | Default 1 |
| `position_x` | NUMERIC(8,2) | | Nullable |
| `position_y` | NUMERIC(8,2) | | Nullable |
| `placed_at` | TIMESTAMPTZ | | Nullable |
| `created_at` | TIMESTAMPTZ | | |

For the MVP, a simple inventory list is sufficient. Garden placement coordinates can be added later.

### Table 18: `point_transactions`

The immutable points ledger.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `garden_id` | UUID | FK | References `gardens.id` |
| `user_id` | UUID | FK | References `users.id`; actor/beneficiary |
| `activity_participant_id` | UUID | FK | Nullable; references `activity_participants.id` |
| `transaction_type` | VARCHAR(20) | | earn/spend/refund/adjustment |
| `amount` | INTEGER | | Positive for earn/refund; negative for spend |
| `reason` | VARCHAR(100) | | |
| `idempotency_key` | VARCHAR(150) | UNIQUE | Prevent duplicate reward |
| `created_at` | TIMESTAMPTZ | | |

Rules:

- Never delete ledger rows to fix a balance.
- Use a compensating transaction for corrections.
- The backend calculates the amount.
- The database transaction updates the ledger and garden balance together.
- For a group garden, `user_id` records which participant caused the earning/spending action.

### Table 19: `notifications`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK | References `users.id` |
| `type` | VARCHAR(40) | | |
| `title` | VARCHAR(120) | | |
| `body` | TEXT | | |
| `payload` | JSONB | | Non-sensitive navigation metadata |
| `read_at` | TIMESTAMPTZ | | Nullable |
| `created_at` | TIMESTAMPTZ | | |

Do not put raw private messages or sensitive screening content in notification payloads.

### Table 20: `consent_records`

Records consent and preference changes for sensitive features.

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK | References `users.id` |
| `purpose` | VARCHAR(60) | | location/activity_photo/content_screening/usage_import |
| `policy_version` | VARCHAR(30) | | |
| `granted` | BOOLEAN | | |
| `recorded_at` | TIMESTAMPTZ | | |
| `revoked_at` | TIMESTAMPTZ | | Nullable |

A consent record is an audit record, not a substitute for a real permission check.

## 7.4 Optional AI audit table

For the MVP, do not persist raw screened content.

If an audit record is required, use metadata only:

### `screening_events`

| Column | Type | Key | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK | References `users.id` |
| `screening_type` | VARCHAR(30) | | pii/harmful_content/image |
| `source` | VARCHAR(30) | | user_submitted/jomo_form |
| `detected_categories` | JSONB | | Category names only |
| `result_status` | VARCHAR(20) | | completed/partial/error |
| `created_at` | TIMESTAMPTZ | | |

Do not store the raw text, detected values, or unredacted image in this table.

## 7.5 SQL migration starter

The following SQL illustrates the most important constraints. The backend agent should translate this into Alembic migrations and add the remaining indexes/constraints.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(30) UNIQUE NOT NULL,
    display_name VARCHAR(80) NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Singapore',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    daily_screen_goal_minutes INTEGER,
    location_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    screening_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
      daily_screen_goal_minutes IS NULL OR
      daily_screen_goal_minutes BETWEEN 1 AND 1440
    )
);

CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(80) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    visibility VARCHAR(20) NOT NULL DEFAULT 'invite_only',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ,
    CHECK (visibility IN ('private', 'invite_only'))
);

CREATE TABLE group_members (
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    left_at TIMESTAMPTZ,
    PRIMARY KEY (group_id, user_id),
    CHECK (role IN ('owner', 'admin', 'member')),
    CHECK (status IN ('active', 'left', 'removed'))
);

CREATE INDEX idx_group_members_user
ON group_members(user_id, status);

CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID NOT NULL REFERENCES users(id),
    group_id UUID REFERENCES groups(id),
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category VARCHAR(40) NOT NULL,
    visibility VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    duration_minutes INTEGER NOT NULL,
    max_participants INTEGER NOT NULL DEFAULT 10,
    location_required BOOLEAN NOT NULL DEFAULT FALSE,
    proof_requirement VARCHAR(40) NOT NULL DEFAULT 'photo_or_group_confirmation',
    max_reward_points INTEGER NOT NULL DEFAULT 100,
    published_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (duration_minutes BETWEEN 1 AND 480),
    CHECK (max_participants BETWEEN 1 AND 100),
    CHECK (max_reward_points BETWEEN 0 AND 10000),
    CHECK (visibility IN ('personal', 'group')),
    CHECK (
      (visibility = 'personal' AND group_id IS NULL) OR
      (visibility = 'group' AND group_id IS NOT NULL)
    )
);

CREATE TABLE activity_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id),
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(30) NOT NULL DEFAULT 'joined',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    eligible_minutes INTEGER NOT NULL DEFAULT 0,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    completed_at TIMESTAMPTZ,
    UNIQUE (activity_id, user_id),
    CHECK (eligible_minutes >= 0),
    CHECK (points_awarded >= 0)
);

CREATE TABLE gardens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    garden_type VARCHAR(20) NOT NULL,
    owner_user_id UUID REFERENCES users(id),
    owner_group_id UUID REFERENCES groups(id),
    name VARCHAR(80) NOT NULL,
    points_balance INTEGER NOT NULL DEFAULT 0,
    growth_level INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (points_balance >= 0),
    CHECK (growth_level >= 1),
    CHECK (
      (garden_type = 'personal'
       AND owner_user_id IS NOT NULL
       AND owner_group_id IS NULL)
      OR
      (garden_type = 'group'
       AND owner_user_id IS NULL
       AND owner_group_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_personal_garden_owner
ON gardens(owner_user_id)
WHERE garden_type = 'personal';

CREATE UNIQUE INDEX uq_group_garden_owner
ON gardens(owner_group_id)
WHERE garden_type = 'group';

CREATE TABLE point_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    garden_id UUID NOT NULL REFERENCES gardens(id),
    user_id UUID NOT NULL REFERENCES users(id),
    activity_participant_id UUID REFERENCES activity_participants(id),
    transaction_type VARCHAR(20) NOT NULL,
    amount INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL,
    idempotency_key VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (transaction_type IN ('earn', 'spend', 'refund', 'adjustment')),
    CHECK (amount <> 0)
);
```

The migration author must add the remaining tables from this document, including friendships, invites, proofs, usage, garden inventory, notifications, and consent.

## 7.6 Database indexes

Create indexes for common access patterns:

- `group_members(user_id, status)`
- `group_members(group_id, status)`
- `activities(group_id, status, created_at)`
- `activities(created_by, created_at)`
- `activity_participants(user_id, status)`
- `activity_participants(activity_id, status)`
- `usage_summaries(user_id, usage_date)`
- `point_transactions(garden_id, created_at)`
- `point_transactions(user_id, created_at)`
- `notifications(user_id, read_at, created_at)`
- `proof_submissions(activity_id, status)`

Do not add indexes indiscriminately. Check query plans when the data grows.

## 7.7 Database security

- Use a database role with only the permissions needed by the API.
- Never expose the database service-role key in the frontend.
- Enforce access control in the API and, if using Supabase directly, appropriate Row Level Security policies.
- Do not assume that UUIDs are secret or provide authorisation.
- Use parameterised queries/ORM.
- Keep migrations under version control.
- Back up data.
- Restrict production database access.
- Avoid logging personal data.

---

# 8. Activity, location, proof and reward workflows

## 8.1 Activity creation workflow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant S as Activity Service
    participant D as Database
    U->>F: Create activity
    F->>A: POST /activities
    A->>A: Authenticate + validate
    A->>S: create_activity(actor_id, input)
    S->>S: Check group membership
    S->>D: Insert activity
    D-->>S: Activity row
    S-->>A: Activity
    A-->>F: 201 Created
```

## 8.2 Starting an activity

1. User selects Start.
2. Frontend calls `POST /activities/{id}/start`.
3. API authenticates the user.
4. Backend checks:
   - Activity exists.
   - Activity is published.
   - User is the creator or an eligible group member, according to the activity policy.
   - Activity is not already active.
5. Backend records the authoritative start timestamp.
6. Backend creates or activates the participant record.
7. Frontend starts displaying the timer using the server timestamp.

For a group activity, any active group member can start it if the product policy allows this. Do not restrict start permission to the creator alone.

## 8.3 Joining an activity

1. User selects Join.
2. API checks group membership if the activity is group-only.
3. API checks capacity.
4. Backend creates the participant record.
5. User may begin a voluntary focus session.
6. User may opt into an activity check-in.

## 8.4 Location check-in

Recommended MVP:

- One check-in when joining or starting.
- Optional second check-in at completion.
- No continuous route tracking.
- No public display of exact coordinates.
- No automatic penalty if location permission is denied.

If the product later needs group proximity, the backend can compare coarse check-in locations within an agreed tolerance, but should return only a result such as `proximity_confirmed`, not expose everyone's coordinates.

## 8.5 Ending an activity

1. User selects End.
2. Frontend calls the end endpoint.
3. Backend records the server end timestamp.
4. Backend updates the participant's end time.
5. Activity moves to `awaiting_proof` if proof is required.
6. Frontend requests proof or group confirmation.

The server must not trust a client-supplied duration.

## 8.6 Proof and completion

Possible proof modes:

- `none`
- `photo`
- `group_confirmation`
- `photo_or_group_confirmation`

For a group confirmation:

- A participant submits a completion request.
- Eligible group participants confirm.
- Backend checks the confirmation threshold.
- Backend changes the proof status.
- Backend triggers reward calculation.

For a personal activity, a user can submit a photo or complete a no-proof activity, depending on the configured requirement.

## 8.7 Points calculation

The points service is the only place where points are calculated.

Example MVP formula:

```python
def calculate_points(
    eligible_minutes: int,
    points_per_minute: float,
    max_reward_points: int,
) -> int:
    if eligible_minutes <= 0:
        return 0

    raw_points = int(eligible_minutes * points_per_minute)
    return min(raw_points, max_reward_points)
```

Suggested initial policy:

- One point per eligible minute.
- Maximum 60 points per participant per activity.
- Minimum eligible duration: 5 minutes.
- Exclude time before the participant joined.
- Exclude time after the participant left.
- Do not award points until the configured proof/completion condition is satisfied.

The product team can tune the formula. It must remain server-side.

### Important: group activity duration

Do not award every group member the full activity duration if they joined late or left early.

Calculate each participant's eligible duration from their own timestamps:

```text
eligible duration =
participant ended_at - participant started_at
```

Then apply caps and validation.

If participants can pause, add explicit pause intervals rather than guessing.

### Idempotent reward transaction

The backend should use a database transaction:

1. Lock or otherwise safely serialise the participant reward operation.
2. Check whether an earning transaction already exists for that participant/activity.
3. Calculate points.
4. Insert the point transaction using a unique idempotency key.
5. Update garden balance.
6. Update participant points.
7. Commit.

Example idempotency key:

```text
activity-completion:{activity_participant_id}
```

A repeated API request must not award points twice.

## 8.8 Garden selection for rewards

Reward destination:

```python
def get_reward_garden(user_id, activity):
    if activity.group_id is not None:
        return get_group_garden(activity.group_id)

    return get_personal_garden(user_id)
```

This is a simple MVP rule. If a user participates in a personal activity while belonging to groups, points go to their personal garden. If the activity is a group activity, points go to that group's shared garden.

Do not automatically distribute a single reward to every garden the user can access.

## 8.9 Purchase workflow

1. Frontend requests catalogue.
2. User selects an item.
3. Frontend submits purchase.
4. Backend checks the user's access to the garden.
5. Backend loads the current catalogue price.
6. Backend checks the balance.
7. Backend creates a spend transaction.
8. Backend updates balance.
9. Backend creates inventory record.
10. Backend commits the transaction.

The frontend must never submit the price as authoritative.

---

# 9. AI architecture and implementation

## 9.1 AI design philosophy

JOMO should not use one large language model for every feature.

Use the simplest reliable tool for each task.

| AI feature | Recommended approach | Why |
|---|---|---|
| PII detection | Presidio + spaCy + custom recognisers | Local, structured detection |
| PII redaction | Presidio Anonymizer | Deterministic redaction |
| Harmful-content screening | Local classifier + explicit rules | Narrow classification task |
| Wellbeing Coach | Python rules | Transparent and predictable |
| Mission recommendations | Curated catalogue + filters | Safe and reliable |
| Mission generation | Optional Strands + LLM | Adds natural-language variation |
| Image text screening | OCR + Presidio | Optional extension |
| Photo activity verification | Human/group confirmation initially | Vision cannot prove identity/completion reliably |

## 9.2 AI folder structure

```text
backend/app/ai/
├── interfaces.py
├── screening_service.py
│
├── privacy/
│   ├── analyzer.py
│   ├── recognizers.py
│   ├── redactor.py
│   └── tests/
│
├── harmful_content/
│   ├── classifier.py
│   ├── rules.py
│   ├── labels.py
│   └── tests/
│
├── wellbeing/
│   ├── recommender.py
│   └── tests/
│
├── missions/
│   ├── catalogue.py
│   ├── recommender.py
│   ├── prompt_templates.py
│   ├── output_schema.py
│   ├── agent.py
│   └── tests/
│
└── images/
    ├── ocr.py
    ├── redactor.py
    └── tests/
```

## 9.3 Shared AI interface

All AI features should expose predictable inputs and outputs.

```python
from typing import Protocol, Any

class TextScreeningProvider(Protocol):
    def screen(self, text: str, language: str = "en") -> dict[str, Any]:
        ...

class WellbeingProvider(Protocol):
    def recommend(self, usage_summary: dict) -> dict:
        ...

class MissionProvider(Protocol):
    def recommend(self, request: dict) -> dict:
        ...
```

This lets the backend replace an implementation without changing the API contract.

---

# 10. Privacy Guardian: PII screening

## 10.1 Purpose

Detect information a user may accidentally expose, such as:

- Email addresses.
- Phone numbers.
- NRIC/FIN-like formats.
- Names.
- Addresses.
- Locations.
- Other identifiers supported by configured recognisers.

The system should say **potential personal information detected**, not claim certainty.

## 10.2 Recommended stack

- `presidio-analyzer`
- `presidio-anonymizer`
- `spacy`
- `en_core_web_lg`
- Custom Singapore-specific recognisers.
- Python.

No model training is required for the MVP.

## 10.3 Installation on Windows

Use Python 3.11 64-bit as a conservative hackathon baseline, then verify compatibility with the exact package versions being installed.

PowerShell:

```powershell
mkdir jomo-ai
cd jomo-ai

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install presidio-analyzer presidio-anonymizer
pip install spacy fastapi "uvicorn[standard]"

python -m spacy download en_core_web_lg

pip freeze > requirements.txt
```

If PowerShell activation is blocked:

```cmd
.venv\Scripts\activate.bat
```

## 10.4 PII analyzer

`privacy/analyzer.py`:

```python
import spacy

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from .recognizers import register_custom_recognizers

configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {
            "lang_code": "en",
            "model_name": "en_core_web_lg",
        }
    ],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

register_custom_recognizers(analyzer)
```

`privacy/recognizers.py`:

```python
from presidio_analyzer import Pattern, PatternRecognizer

def register_custom_recognizers(analyzer):
    singapore_phone = PatternRecognizer(
        supported_entity="SG_PHONE_NUMBER",
        patterns=[
            Pattern(
                name="sg_phone",
                regex=r"(?<!\d)(?:\+65[\s-]?)?[3689]\d{3}[\s-]?\d{4}(?!\d)",
                score=0.65,
            )
        ],
        context=["phone", "mobile", "call", "contact"],
    )

    singapore_id_format = PatternRecognizer(
        supported_entity="SG_NRIC_FIN_FORMAT",
        patterns=[
            Pattern(
                name="sg_id_format",
                regex=r"(?<![A-Z0-9])[STFGM]\d{7}[A-Z](?![A-Z0-9])",
                score=0.65,
            )
        ],
        context=["NRIC", "FIN", "identity number"],
    )

    analyzer.registry.add_recognizer(singapore_phone)
    analyzer.registry.add_recognizer(singapore_id_format)
```

Important limitations:

- The phone regex is a format heuristic and must be tested.
- The NRIC/FIN regex checks a format only.
- It does not validate checksum, issuance, identity, or ownership.
- A format match is not proof that the string belongs to a real person.
- Names and addresses may have false positives and false negatives.
- Test with fictional examples only.

## 10.5 Redaction

`privacy/redactor.py`:

```python
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .analyzer import analyzer

anonymizer = AnonymizerEngine()

def screen_and_redact(text: str) -> dict:
    findings = analyzer.analyze(
        text=text,
        language="en",
    )

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=findings,
        operators={
            "DEFAULT": OperatorConfig(
                "replace",
                {"new_value": "[REDACTED]"},
            )
        },
    )

    detections = [
        {
            "entity_type": item.entity_type,
            "start": item.start,
            "end": item.end,
            "score": round(item.score, 2),
            "category": "pii",
        }
        for item in findings
    ]

    return {
        "has_potential_pii": len(findings) > 0,
        "detections": detections,
        "redacted_text": anonymized.text,
        "limitations": [
            "Automated detection may miss personal information.",
            "A result with no detections does not guarantee that text is safe.",
        ],
    }
```

Do not return detected raw values as a separate field. The frontend already has the original text and can highlight it using offsets.

Scores are model/rule scores, not calibrated probabilities.

## 10.6 Privacy Guardian API

`POST /api/v1/ai/privacy/text`

Request:

```json
{
  "text": "Email me at alex@example.com or call 91234567.",
  "checks": ["pii"],
  "language": "en"
}
```

Response:

```json
{
  "data": {
    "status": "completed",
    "has_potential_pii": true,
    "detections": [
      {
        "entity_type": "EMAIL_ADDRESS",
        "start": 12,
        "end": 29,
        "score": 0.95,
        "category": "pii"
      }
    ],
    "redacted_text": "Email me at [REDACTED] or call [REDACTED].",
    "limitations": [
      "Automated detection may miss personal information."
    ]
  },
  "request_id": "uuid"
}
```

Actual detection results will vary.

## 10.7 Screening privacy requirements

- Do not log raw text.
- Do not store raw text in the database.
- Do not transmit raw text to a third-party LLM.
- Apply request size limits.
- Do not retain screening input by default.
- Do not put detected values in analytics.
- Do not use the text for model training.
- Do not return a "100% safe" result.
- Allow users to review redacted text before sharing it.

---

# 11. Harmful-content screening

## 11.1 Scope

This is distinct from PII detection.

Potential categories include:

- Threats or violent language.
- Harassment or targeted insults.
- Bullying indicators.
- Hate or discriminatory language.
- Sexual exploitation or coercion indicators.
- Self-harm-related indicators.

The MVP must not claim to reliably detect every instance of grooming, sextortion, cyberbullying, threats, or abuse.

## 11.2 MVP implementation

Use a narrow classifier or deterministic rules with transparent labels.

Recommended result categories:

```python
HARMFUL_LABELS = [
    "threat",
    "harassment",
    "hate_or_discrimination",
    "sexual_coercion_indicator",
    "self_harm_indicator",
    "unknown",
]
```

Return indicators and confidence/score information where supported.

Do not automatically punish, report, or contact another person based only on a classifier result.

A safer UX:

- Show a private warning.
- Explain which category triggered.
- Offer a chance to review/edit before sending.
- Allow the user to dismiss a false positive.
- Provide appropriate help resources for serious safety concerns.

For the hackathon, a simple rule-based demonstration may be acceptable if clearly labelled as a prototype. Do not present keyword matching as a robust AI classifier.

## 11.3 Local processing

If the team chooses a local model:

- Download the model before deployment.
- Pin the model version.
- Run inference inside the backend or on-device.
- Do not call an external inference API.
- Document the model's limitations.
- Test false positives and false negatives.
- Keep the model replaceable behind `TextScreeningProvider`.

"Local" means the inference runs on infrastructure controlled by the project, not that the data is automatically private. The team still needs access controls, retention controls, and secure hosting.

---

# 12. Wellbeing Coach

## 12.1 Purpose

Offer gentle, non-clinical suggestions based on aggregated usage.

Do not diagnose addiction, anxiety, depression, or other health conditions.

## 12.2 Implementation

`wellbeing/recommender.py`:

```python
def get_recommendation(data: dict) -> dict:
    today = data["daily_minutes"]
    weekly_average = data["weekly_average_minutes"]
    goal = data["goal_minutes"]

    if weekly_average <= 0:
        return {
            "type": "getting_started",
            "message": (
                "Start by observing your digital habits. "
                "You can set a personal goal when ready."
            ),
        }

    if today > weekly_average * 1.25:
        return {
            "type": "gentle_break",
            "message": (
                "You've spent more time online than usual. "
                "Would you like to try a 15-minute screen-free break?"
            ),
        }

    if today > goal:
        return {
            "type": "goal_support",
            "message": (
                "You've gone beyond today's goal. "
                "Would a smaller goal feel more manageable tomorrow?"
            ),
        }

    return {
        "type": "positive_feedback",
        "message": (
            "You're within your personal goal today. "
            "Keep making choices that work for you!"
        ),
    }
```

## 12.3 Input contract

```json
{
  "daily_minutes": 120,
  "weekly_average_minutes": 95,
  "goal_minutes": 100
}
```

Validation:

- `daily_minutes`: 0–1440.
- `weekly_average_minutes`: 0–1440.
- `goal_minutes`: 1–1440.

Use aggregated data only. Do not send raw messages or screenshots to this service.

---

# 13. Mission recommendation and optional Strands agent

## 13.1 MVP: catalogue-first

Do not ask an LLM to invent real venues.

Start with a curated catalogue of activities. Each activity should have:

- ID.
- Title.
- Description.
- Category.
- Duration.
- Minimum/maximum group size.
- Indoor/outdoor.
- Accessibility notes.
- Safety notes.
- Required resources.
- Proof type.
- Optional verified venue ID.

Example:

```json
{
  "id": "nature_walk_001",
  "title": "Nature Explorer",
  "description": "Find three different leaf shapes in a public park.",
  "category": "outdoor",
  "duration_minutes": 20,
  "min_group_size": 1,
  "max_group_size": 5,
  "proof_type": "activity_photo",
  "safety_notes": [
    "Stay in public areas.",
    "Do not touch unknown plants.",
    "Do not enter restricted areas."
  ]
}
```

This is an illustrative template, not a verified venue recommendation.

## 13.2 Recommendation logic

Filter the catalogue using:

- Group size.
- Available duration.
- Indoor/outdoor preference.
- Accessibility preference.
- Weather, if a verified weather source is integrated.
- User-selected location area, if permission is given.
- Activity category.

The recommender should return only activities that pass backend validation.

## 13.3 Optional Strands agent

Use Strands only if the catalogue-first implementation works.

Strands is an agent SDK, not a model. It requires a configured model provider and credentials.

Potential workflow:

```text
Frontend
  |
  v
POST /ai/missions/recommend
  |
  v
Mission Service
  |
  +--> Load eligible catalogue entries
  |
  +--> Validate group size and duration
  |
  +--> Optional Strands agent
          |
          +--> Generate structured mission wording
  |
  v
Backend validates structured output
  |
  v
Return mission recommendation
```

The agent must not:

- Invent real places.
- Access unrestricted user location.
- Award points.
- Create arbitrary database records.
- Override safety rules.
- Generate an unbounded activity.

## 13.4 Structured output

```json
{
  "title": "Nature Explorer",
  "description": "Find three different leaf shapes at a public park.",
  "category": "outdoor",
  "duration_minutes": 20,
  "catalogue_activity_id": "nature_walk_001",
  "proof_type": "activity_photo",
  "safety_notes": [
    "Stay in public areas.",
    "Do not touch unknown plants."
  ]
}
```

The backend must validate every field.

## 13.5 Fallback

If the agent is unavailable:

- Select a matching catalogue entry.
- Return the predefined activity.
- Do not block activity creation.

The user experience should not depend on an LLM being online.

---

# 14. Optional image screening

## 14.1 Purpose

The optional image-screening feature can detect text visible in an uploaded photo and screen that text for PII.

It does not:

- Detect every face.
- Prove who took the photo.
- Prove that the activity occurred.
- Guarantee that the image contains no personal information.
- Remove all privacy risks.

## 14.2 Pipeline

```mermaid
flowchart LR
    A[User selects image] --> B[Upload validation]
    B --> C[Strip metadata]
    C --> D[OCR]
    D --> E[Extracted text]
    E --> F[PII screening]
    F --> G[Optional redacted preview]
    G --> H[User reviews]
```

## 14.3 Tools

- Pillow for image handling.
- Tesseract OCR.
- Presidio Image Redactor only if the team has time to integrate and test it.

OCR can miss blurry, small, rotated, handwritten, or partially obscured text.

Do not make image redaction a P0 feature.

---

# 15. Frontend, API, backend and AI interface contract

This section is mandatory for cross-agent integration.

## 15.1 General rules

- Frontend communicates with FastAPI only.
- API validates and authenticates all requests.
- API calls backend services.
- Backend services own business logic.
- AI is called through backend interfaces.
- Database is accessed through backend repositories/services.
- AI services do not write directly to reward or garden tables.
- All timestamps use ISO 8601.
- All IDs use UUID strings.
- All API errors use the standard error format.

## 15.2 Data ownership matrix

| Data | Frontend | API/middleware | Backend | AI |
|---|---|---|---|---|
| User profile | Display/edit | Validate/auth | Owns/persists | No access by default |
| Usage summaries | Display | Validate | Owns/persists | Reads aggregates only |
| Groups | Display/actions | Authorise | Owns/persists | No access |
| Activities | Display/actions | Validate | Owns lifecycle | May recommend templates |
| Location | Permission + capture | Validate consent | Owns retention | No access |
| Proof photos | Capture/upload | Validate upload | Owns metadata/storage | Optional OCR only |
| Points | Display | Authorise | Calculates/records | No access |
| Gardens | Display/actions | Authorise | Owns inventory/balance | No access |
| Text screening | Submit/display | Validate | Coordinates | Detects indicators |
| Wellbeing | Display | Validate | Coordinates | Rules read aggregate usage |
| Mission generation | Display request | Validate | Owns final validation | Suggests structured content |

## 15.3 API contract ownership

The backend lead must publish the OpenAPI specification.

The frontend lead should generate or maintain TypeScript types from the OpenAPI schema where possible.

Do not independently invent endpoint names or field names in different agents.

## 15.4 Standard API response

Success:

```json
{
  "data": {},
  "request_id": "uuid"
}
```

Error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request is invalid.",
    "details": {
      "field": "duration_minutes"
    }
  },
  "request_id": "uuid"
}
```

## 15.5 Shared enum definitions

```text
ActivityStatus:
draft
published
active
awaiting_proof
under_review
completed
cancelled
expired
rejected

ParticipantStatus:
joined
active
left
awaiting_proof
completed
rejected

GardenType:
personal
group

ProofType:
none
photo
group_confirmation
photo_or_group_confirmation

ProofStatus:
pending
accepted
rejected

FocusStatus:
active
completed
cancelled

UsageSource:
native
manual
import
demo

GroupRole:
owner
admin
member
```

These names must match across Python, TypeScript, and database constraints.

---

# 16. Security, privacy and abuse prevention

## 16.1 Authentication and authorisation

- Verify authentication on every protected endpoint.
- Enforce object-level permissions.
- Check group membership server-side.
- Check activity participation server-side.
- Never rely on frontend route guards as security.
- Do not expose service-role credentials.

## 16.2 Location privacy

- Ask only when needed.
- Explain the purpose.
- Use foreground location first.
- Avoid background tracking in the MVP.
- Do not expose exact coordinates to group members.
- Define deletion/expiry.
- Provide stop-sharing controls.

## 16.3 Photo privacy

- Private storage bucket.
- Signed upload/download URLs.
- File size limit.
- MIME and file signature validation.
- Random server-generated storage names.
- EXIF stripping.
- Retention policy.
- Access checks before download.
- Delete files on account deletion where appropriate.

## 16.4 AI privacy

- No raw text logging.
- No raw image logging.
- No third-party LLM processing of private text in the MVP.
- No raw message retention.
- Restrict access to screening results.
- Return only necessary detections.
- Document model limitations.

## 16.5 Points abuse prevention

- Server-side calculations.
- Server-side timestamps.
- Idempotency keys.
- Maximum reward caps.
- Minimum duration.
- Proof/confirmation validation.
- Duplicate participant protection.
- Transactional ledger updates.
- Audit corrections with compensating transactions.

## 16.6 Group abuse prevention

- Invite expiry.
- Invite revocation.
- Member removal.
- Leave group.
- Group owner/admin role checks.
- No forced focus lock.
- No continuous public location.
- No public display of private proof by default.

## 16.7 Logging

Log:

- Request ID.
- Endpoint.
- Status code.
- Processing duration.
- Authenticated actor ID where appropriate.
- Safe error code.

Do not log:

- Passwords.
- Auth tokens.
- Raw screened text.
- Raw image contents.
- Exact location history.
- Invite tokens.
- Full private notification payloads.

---

# 17. Testing blueprint

## 17.1 Frontend tests

- Registration and login validation.
- Navigation.
- Insights empty state.
- Group creation.
- Group invite acceptance.
- Activity creation.
- Activity join/leave.
- Focus timer.
- Proof upload validation.
- Garden selection.
- Purchase error when points are insufficient.
- Privacy Guardian results and false-positive messaging.
- Mobile and desktop responsive layouts.

## 17.2 Backend tests

### Users and groups

- User can create a group.
- User cannot view a private group they do not belong to.
- User cannot invite without permission.
- Invite token expires.
- User cannot accept an invalid invite.
- User can leave a group.

### Activities

- Group member can start a group activity.
- Non-member cannot start a private group activity.
- User cannot join a full activity.
- User cannot join twice.
- User cannot end another user's participation.
- Client timestamps do not override server timestamps.
- Invalid state transitions are rejected.

### Location

- No check-in without consent.
- Invalid coordinates rejected.
- Exact location is not returned to other group members.
- Expired records are deleted or coarsened.

### Proof

- Only participant can submit proof for own participation.
- Unsupported file types rejected.
- Oversized files rejected.
- Duplicate confirmations rejected.
- Unauthorised users cannot access proof.

### Points

- Points calculated on server.
- Points not awarded before completion.
- Duplicate completion request does not duplicate points.
- Reward cap enforced.
- Personal activity rewards personal garden.
- Group activity rewards correct group garden.
- Insufficient balance blocks purchase.
- Purchase and ledger update are atomic.

## 17.3 AI tests

Use fictional test strings:

```text
alex@example.com
91234567
+65 9123 4567
S1234567D
Sarah Tan
I enjoy playing football.
The code is 12345678.
alex at example dot com
```

Expected observations:

- Email and common phone formats should be tested.
- NRIC/FIN-like format should be tested as a format match only.
- A common-looking number may produce false positives.
- Names may be missed or incorrectly identified.
- Obfuscated text may be missed.
- Harmless text must be included in false-positive testing.

For harmful-content screening, build a separate labelled test set. Do not use PII test cases as a substitute.

Track:

- True positives.
- False positives.
- False negatives.
- True negatives.

Precision:

```text
TP / (TP + FP)
```

Recall:

```text
TP / (TP + FN)
```

Do not claim high accuracy based on a handful of demo examples.

## 17.4 End-to-end demo test

1. Register two or more fictional users.
2. Create a friend group.
3. Invite another user.
4. Accept the invitation.
5. Show the shared garden.
6. Create a group activity.
7. Start the activity as a group member.
8. Join using another account.
9. Start voluntary Focus Sessions.
10. Submit an activity check-in if permission is granted.
11. End the activity.
12. Submit photo proof or group confirmation.
13. Confirm completion.
14. Show server-calculated points.
15. Show the shared garden balance increase.
16. Screen fictional text in Privacy Guardian.
17. Show the redacted result.
18. Show a wellbeing recommendation.

---

# 18. Environment setup

## 18.1 Prerequisites

Each Windows team member should install:

- Git.
- Node.js LTS.
- Python 3.11 64-bit.
- VS Code.
- PostgreSQL or access to the shared Supabase project.
- A browser.
- Optional Docker Desktop.

## 18.2 Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Recommended packages:

```powershell
npm install axios zod recharts lucide-react
npm install @tanstack/react-query
```

Use the Next.js and React versions selected by the project lead and commit the lockfile.

## 18.3 Backend setup

```powershell
cd backend

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic-settings
pip install sqlalchemy alembic psycopg[binary]
pip install pytest httpx
pip install presidio-analyzer presidio-anonymizer spacy

python -m spacy download en_core_web_lg
```

Run:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## 18.4 Environment variables

Frontend `.env.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_APP_NAME=JOMO
```

Backend `.env.example`:

```env
APP_ENV=development
APP_NAME=JOMO
API_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE

AUTH_PROVIDER=supabase
AUTH_ISSUER_URL=
AUTH_JWKS_URL=

STORAGE_PROVIDER=supabase
STORAGE_BUCKET=activity-proofs

CORS_ORIGINS=http://localhost:3000

SCREENING_MAX_TEXT_LENGTH=10000
SCREENING_STORE_RAW_TEXT=false

LOCATION_RETENTION_HOURS=24

AI_MISSION_PROVIDER=catalogue
AI_EXTERNAL_MODEL_ENABLED=false
```

Never commit real secrets. Commit `.env.example`, not `.env`.

---

# 19. Suggested repository structure

Use a monorepo so the team can share API contracts and coordinate changes.

```text
jomo/
├── frontend/
├── backend/
├── shared/
│   ├── api-contracts/
│   │   ├── openapi.json
│   │   └── README.md
│   ├── enums/
│   └── fixtures/
│
├── docs/
│   ├── architecture.md
│   ├── database-schema.md
│   ├── api-contract.md
│   ├── privacy-and-security.md
│   ├── ai-design.md
│   └── demo-script.md
│
├── scripts/
│   ├── setup-dev.ps1
│   └── seed-demo-data.ps1
│
├── .gitignore
├── README.md
└── CONTRIBUTING.md
```

The OpenAPI document is the contract between frontend and backend.

---

# 20. Team division and coding-agent assignments

For a four-person team:

## Agent 1 — Frontend

Owns:

- Next.js setup.
- Main navigation.
- Insights.
- Friends and Groups UI.
- Activities UI.
- Garden UI.
- Privacy Guardian UI.
- Focus Session UI.
- API client and TypeScript contracts.
- Responsive design.

Deliverables:

- Working frontend.
- Pages and components.
- API integration.
- Loading/error/empty states.
- Frontend tests.

## Agent 2 — API/middleware and integration

Owns:

- FastAPI app.
- Authentication dependency.
- Request validation.
- API routes.
- Error handling.
- Rate limiting.
- OpenAPI contract.
- CORS/security configuration.
- Frontend/backend integration.

Deliverables:

- Running API.
- Endpoint documentation.
- Consistent response envelope.
- Permission checks.
- Integration tests.

## Agent 3 — Backend/database

Owns:

- PostgreSQL schema.
- SQLAlchemy models.
- Alembic migrations.
- Repositories.
- User and group services.
- Activity lifecycle.
- Location and proof records.
- Points ledger.
- Garden inventory and purchases.
- Demo data and backend tests.

Deliverables:

- Database migrations.
- Business services.
- Transaction-safe rewards.
- Garden and activity workflows.
- Backend tests.

## Agent 4 — AI and product integration

Owns:

- Presidio installation.
- spaCy model setup.
- Singapore recognisers.
- PII redaction.
- Harmful-content prototype.
- Wellbeing rules.
- Mission catalogue.
- Optional Strands agent.
- AI tests.
- Safety/limitations copy.

Deliverables:

- Working Privacy Guardian.
- Wellbeing recommendation endpoint.
- Catalogue recommender.
- Optional AI mission generation.
- AI test results and limitations.

## 20.1 Shared integration rules

- All agents use the same Git repository.
- Each agent works on a separate feature branch.
- Do not modify another agent's module without coordination.
- Agree on API contracts before implementing integration.
- Commit small, reviewable changes.
- Do not commit secrets or private user data.
- Merge frequently.
- Run the full test suite before demo day.

---

# 21. Implementation order

## Phase 1 — Foundation

- Create repository.
- Set up frontend.
- Set up backend.
- Set up database.
- Configure authentication.
- Define OpenAPI contract.
- Create base migrations.
- Confirm local development works for all four team members.

## Phase 2 — Core social features

- User profile.
- Friends.
- Groups.
- Group invitations.
- Membership checks.
- Personal garden creation.
- Group garden creation.

## Phase 3 — Activity workflow

- Activity creation.
- Publish.
- Start.
- Join.
- Leave.
- End.
- Participant records.
- Focus timer.

## Phase 4 — Proof and points

- Photo upload.
- Group confirmation.
- Completion validation.
- Points calculation.
- Idempotent points ledger.
- Personal/group garden reward destination.
- Shop and inventory.

## Phase 5 — AI

- Presidio setup.
- Custom recognisers.
- Redaction.
- Privacy Guardian UI.
- Wellbeing rules.
- Harmful-content prototype if time permits.
- Mission catalogue.

## Phase 6 — Integration and testing

- Connect all pages to API.
- Test group activity flow.
- Test reward flow.
- Test permission denial.
- Test invalid/expired invites.
- Test duplicate requests.
- Test AI false positives.
- Test responsive UI.
- Prepare demo data.

## Phase 7 — Stretch work

Only after the above is stable:

- Strands agent.
- Nearby places integration.
- Image OCR.
- Realtime group updates.
- Native Android usage integration.
- Native app restrictions.
- Native iOS Screen Time integration.

---

# 22. Definition of done

A feature is not done just because the page exists.

## Frontend done

- Page renders.
- Form validation works.
- API is integrated.
- Loading state exists.
- Error state exists.
- Empty state exists.
- Responsive layout works.
- No secrets in browser code.
- No fake success states.

## API done

- Authenticated.
- Validated.
- Authorised.
- Correct status codes.
- Standard response envelope.
- Safe error handling.
- Documented in OpenAPI.
- Tested.

## Backend done

- Business rules implemented.
- Database changes migrated.
- Foreign keys and constraints added.
- Transactions used where needed.
- Duplicate operations handled.
- Unit and integration tests pass.

## AI done

- Runs locally or in controlled project infrastructure.
- Has an explicit input/output contract.
- Has test cases.
- Has limitations documented.
- Does not retain raw content unnecessarily.
- Has a deterministic fallback.
- Does not directly modify points or user permissions.

---

# 23. Final architecture decisions

| Question | Decision |
|---|---|
| Web or mobile first? | Web first |
| Main frontend | Next.js + React + TypeScript |
| Styling | Tailwind CSS |
| Middleware/API | FastAPI |
| Backend | Python services |
| Database | PostgreSQL |
| Auth | Dedicated auth provider |
| DB ORM/migrations | SQLAlchemy + Alembic |
| AI PII screening | Presidio + spaCy |
| Singapore PII | Custom format recognisers; test carefully |
| Harmful-content screening | Local classifier/rules; limited claims |
| Wellbeing Coach | Python rules |
| Mission recommendations | Curated catalogue |
| Mission generation | Optional Strands agent |
| Photo proof | Activity photo or group confirmation |
| Location | Activity-scoped, opt-in check-in |
| App usage statistics | Manual/demo/import in web MVP |
| App blocking | Voluntary Focus Session in web MVP |
| Garden | Personal garden plus one garden per group |
| Points | Backend-calculated immutable ledger |
| 24/7 cross-app screening | Not a web MVP capability |
| Model training | Not required for the MVP |

---

# 24. Official technical references

Use official documentation as the source of truth when implementing platform-specific capabilities.

## Frontend and web platform

- Next.js: https://nextjs.org/docs
- React: https://react.dev/learn
- TypeScript: https://www.typescriptlang.org/docs/
- Tailwind CSS: https://tailwindcss.com/docs
- MDN Service Workers: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
- MDN Background Sync: https://developer.mozilla.org/en-US/docs/Web/API/Background_Synchronization_API
- MDN Periodic Background Sync: https://developer.mozilla.org/en-US/docs/Web/API/Web_Periodic_Background_Synchronization_API

## Backend and database

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Supabase: https://supabase.com/docs

## AI

- Presidio installation: https://presidio.dataprivacystack.org/installation/
- Presidio Analyzer: https://presidio.dataprivacystack.org/analyzer/
- Presidio Anonymizer: https://presidio.dataprivacystack.org/anonymizer/
- Presidio custom recognisers: https://presidio.dataprivacystack.org/analyzer/adding_recognizers/
- spaCy: https://spacy.io/usage
- Strands Agents: https://strandsagents.com/docs/user-guide/sdk/quickstart/overview/
- Tesseract OCR: https://tesseract-ocr.github.io/tessdoc/

## Native mobile roadmap

- Android background location: https://developer.android.com/develop/sensors-and-location/location/background
- Android location permissions: https://developer.android.com/develop/sensors-and-location/location/permissions
- Google Play background location policy: https://support.google.com/googleplay/android-developer/answer/9799150
- Android UsageStatsManager: https://developer.android.com/reference/android/app/usage/UsageStatsManager
- Android DevicePolicyManager: https://developer.android.com/reference/android/app/admin/DevicePolicyManager
- Apple Screen Time frameworks: https://developer.apple.com/documentation/ScreenTimeAPIDocumentation
- Apple Family Controls entitlement: https://developer.apple.com/documentation/BundleResources/Entitlements/com.apple.developer.family-controls
- Apple app and website usage entitlement: https://developer.apple.com/documentation/BundleResources/Entitlements/com.apple.developer.family-controls.app-and-website-usage

## Singapore privacy

- Singapore Personal Data Protection Act: https://sso.agc.gov.sg/Act/PDPA2012
- Personal Data Protection Commission: https://www.pdpc.gov.sg/

---

# 25. Final instruction to implementation agents

Build JOMO as a modular, privacy-first web application.

The most important end-to-end workflow is:

```text
Register
  -> Create or join a friend group
  -> Create or join an activity
  -> Start a voluntary focus session
  -> Optionally check in
  -> Participate in the activity
  -> Submit photo proof or group confirmation
  -> Backend validates completion
  -> Backend calculates points
  -> Points are credited to the correct garden
  -> User purchases or grows garden items
```

The second important workflow is:

```text
User submits text to Privacy Guardian
  -> API validates request
  -> Local screening service detects possible PII
  -> Redactor creates a redacted version
  -> Frontend displays findings and limitations
  -> User decides what to do next
```

The third workflow is:

```text
Usage summary
  -> Backend aggregates usage
  -> Wellbeing rules evaluate the summary
  -> Frontend displays a gentle suggestion
```

**Do not build the entire future vision before the core product works.** A stable group-activity-to-garden reward loop, a functioning Privacy Guardian, and a clear explanation of privacy limitations will make a stronger and more credible hackathon prototype than an unfinished attempt at device-wide monitoring or app blocking.

**JOMO: Less scrolling. More living.**

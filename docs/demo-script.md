# JOMO — Hackathon MVP Demo Walkthrough Script

## 1. Onboarding & Sanctuary Initialization
1. Open JOMO web application (`http://localhost:3000`).
2. Click **Sign In / Demo Access**. The system automatically creates your profile and personal sanctuary.
3. Observe the **Insights** dashboard displaying digital habits and a personalized Wellbeing Coach recommendation.

## 2. Friend Circles & Shared Sanctuaries
1. Navigate to **Friends & Circles**.
2. Click **Create Circle** (e.g. "Weekend Explorers").
3. View the newly created circle and note that an Oasis shared garden was created alongside it.
4. Click **Invite** to generate a cryptographic invite token.

## 3. Offline Activity & Voluntary Focus
1. Navigate to **Offline Activities**.
2. Click **New Activity** (e.g. "Sunset Stroll", 30 minutes, Outdoor).
3. Click **Start Activity**. The voluntary focus timer activates.
4. Mark complete or submit proof.
5. The backend verifies participation, calculates eligible duration, and writes an idempotent point transaction.

## 4. Virtual Sanctuary & Shop
1. Navigate to **Virtual Sanctuary**.
2. Note the credited points balance.
3. Browse the **Sanctuary Shop** and purchase an item (e.g. "Sunflower Seed" or "Zen Bonsai").
4. See the item appear in your inventory with an updated ledger entry.

## 5. Privacy Guardian
1. Click **Privacy Guardian** in the top navigation.
2. Paste text containing a Singapore phone number, email, and NRIC (e.g. `Reach me at alex@example.com or 91234567, IC S1234567A`).
3. Click **Run Privacy Screening**.
4. Observe detected entity categories, confidence scores, safe redacted preview, and transparent system limitations.

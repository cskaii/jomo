"""Explicitly install the curated activity catalogue without creating demo users.

Run from backend after migration: python -m app.db.seed_activities
Existing definitions and user progress are preserved; repeat runs are safe.
"""
from app.db.session import SessionLocal
from app.services.progression_service import ProgressionService


def main():
    with SessionLocal() as db:
        ProgressionService(db).seed_catalog(explicit=True)
    print("Activity, mission and achievement catalogue installed; existing records preserved.")


if __name__ == "__main__":
    main()

"""Operator command: python -m app.db.retention [--check-only]. No object keys or personal data are printed."""
import argparse
from app.db.session import SessionLocal
from app.models.retention import StorageDeletion
from app.services.retention_service import cleanup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    options = parser.parse_args()
    with SessionLocal() as db:
        if not options.check_only:
            cleanup(db)
        pending = db.query(StorageDeletion).count()
        failed = db.query(StorageDeletion).filter(StorageDeletion.attempts > 0).count()
        print(f"Private object deletions pending: {pending}; previously failed: {failed}.")
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

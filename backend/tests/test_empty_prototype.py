from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import engine

def test_browsing_does_not_populate_catalogs(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "AUTO_SEED_CATALOG", False)
    with engine.begin() as connection:
        before = {
            table: connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
            for table in ("garden_catalog_items", "quests", "mission_definitions", "achievement_definitions")
        }
    session = client.post("/api/v1/auth/dev-session")
    assert session.status_code == 200
    headers = {"Authorization": "Bearer " + session.json()["data"]["access_token"]}
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    for route in ("/shop/items", "/quests", "/missions/daily", "/achievements"):
        assert client.get("/api/v1" + route, headers=headers).status_code == 200
    with engine.connect() as connection:
        for table, count in before.items():
            assert connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one() == count

def test_local_preview_is_disabled_for_supabase(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "DATABASE_URL", "postgresql+psycopg://localhost/example")
    assert client.post("/api/v1/auth/dev-session").status_code == 404

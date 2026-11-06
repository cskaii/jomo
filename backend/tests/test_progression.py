import uuid


def _headers():
    return {"Authorization": f"Bearer {uuid.uuid4()}"}


def test_progression_quest_and_mission_flow(client):
    headers = _headers()

    progression = client.get("/api/v1/progression", headers=headers)
    assert progression.status_code == 200
    assert progression.json()["data"]["level"] == 1
    assert progression.json()["data"]["garden_points"] == 0

    quests = client.get("/api/v1/quests", headers=headers)
    assert quests.status_code == 200
    assert len(quests.json()["data"]) == 35

    started = client.post("/api/v1/quests/Q001/start", headers=headers)
    assert started.status_code == 200
    instance_id = started.json()["data"]["id"]

    completed = client.post(
        f"/api/v1/quest-instances/{instance_id}/complete",
        headers=headers,
        json={"reflection": "A quiet reset."},
    )
    assert completed.status_code == 200
    reward = completed.json()["data"]
    assert reward["xp_awarded"] == 20
    # Garden points remain governed by JOMO's eligible-minute rule.
    assert reward["garden_points_awarded"] == 0

    duplicate = client.post(
        f"/api/v1/quest-instances/{instance_id}/complete",
        headers=headers,
        json={"reflection": "Duplicate request"},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["data"]["xp_awarded"] == 0

    daily = client.get("/api/v1/missions/daily", headers=headers)
    weekly = client.get("/api/v1/missions/weekly", headers=headers)
    assert daily.status_code == weekly.status_code == 200
    assert len(daily.json()["data"]) == len(weekly.json()["data"]) == 3

    achievements = client.get("/api/v1/achievements", headers=headers)
    assert achievements.status_code == 200
    assert len(achievements.json()["data"]) == 10


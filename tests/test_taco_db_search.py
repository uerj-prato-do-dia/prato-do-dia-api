from fastapi.testclient import TestClient

from prato_do_dia_api.db.session import init_db
from prato_do_dia_api.main import app

client = TestClient(app)


def test_taco_db_seeding_and_search() -> None:
    init_db()

    response = client.get("/api/v1/foods/search?query=arroz")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    first_item = data["items"][0]
    assert "Arroz" in first_item["name"]
    assert first_item["calories_kcal"] > 0


def test_taco_db_get_by_class_id() -> None:
    init_db()

    response = client.get("/api/v1/foods/4")
    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == 4
    assert "Arroz" in data["name"]
    assert data["calories_kcal"] == 128.0

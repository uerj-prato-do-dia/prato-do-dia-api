import asyncio
import json
from pathlib import Path

import httpx

from prato_do_dia_api.db.models import MealComponent, MealRecord
from prato_do_dia_api.db.session import SessionLocal
from prato_do_dia_api.main import app

TEST_IMAGE_PATH = Path("/home/gabe/projects/prato-do-dia/prato-do-dia-ml/data/input/imagem1.jpg")


async def get_meals_analyze_response() -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        # Abre a imagem de teste real
        with TEST_IMAGE_PATH.open("rb") as f:
            files = {"file": (TEST_IMAGE_PATH.name, f, "image/jpeg")}
            return await client.post("/meals/analyze", files=files)


def test_meals_analyze_endpoint() -> None:
    # Garante que a imagem de teste existe antes de rodar
    assert TEST_IMAGE_PATH.exists(), f"Image not found at {TEST_IMAGE_PATH}"

    # Garante que as tabelas de banco de dados estejam criadas
    from prato_do_dia_api.db.session import init_db

    init_db()

    response = asyncio.run(get_meals_analyze_response())

    assert response.status_code == 200
    json_data = response.json()

    # Valida o contrato do schema retornado
    assert "name" in json_data
    assert "calories" in json_data
    assert "protein" in json_data
    assert "carbs" in json_data
    assert "fat" in json_data
    assert "ingredients" in json_data
    assert "score" in json_data

    # Verifica se os tipos estão corretos
    assert isinstance(json_data["name"], str)
    assert isinstance(json_data["calories"], int)
    assert isinstance(json_data["protein"], float)
    assert isinstance(json_data["carbs"], float)
    assert isinstance(json_data["fat"], float)
    assert isinstance(json_data["ingredients"], list)
    assert isinstance(json_data["score"], float)

    # Verifica se os registros foram persistidos no banco de dados SQLite
    db = SessionLocal()
    try:
        # Busca a refeição mais recente no banco
        db_meal = db.query(MealRecord).order_by(MealRecord.id.desc()).first()
        assert db_meal is not None
        assert db_meal.estimated_name == json_data["name"]
        assert db_meal.calories == json_data["calories"]
        assert db_meal.protein == json_data["protein"]
        assert db_meal.carbs == json_data["carbs"]
        assert db_meal.fat == json_data["fat"]
        assert db_meal.score == json_data["score"]
        assert Path(db_meal.image_path).exists()

        # Busca os componentes associados a essa refeição
        db_components = db.query(MealComponent).filter(MealComponent.meal_id == db_meal.id).all()
        assert len(db_components) > 0

        for comp in db_components:
            assert comp.label != ""
            assert comp.confidence > 0.0

            # Valida se o polígono foi salvo como JSON válido
            poly = json.loads(comp.polygon)
            assert isinstance(poly, list)
            assert len(poly) > 0
            for pt in poly:
                assert isinstance(pt, list)
                assert len(pt) == 2
                assert isinstance(pt[0], (int, float))
                assert isinstance(pt[1], (int, float))
    finally:
        db.close()

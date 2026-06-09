import asyncio
from pathlib import Path

import httpx

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

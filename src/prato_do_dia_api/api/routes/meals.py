import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, UploadFile

from prato_do_dia_api.schemas.meal import MealAnalysisResponse
from prato_do_dia_api.services.ml_service import MLService
from prato_do_dia_api.services.nutrition_mapper import map_detections_to_nutrition

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("/analyze", response_model=MealAnalysisResponse)
async def analyze_meal(file: UploadFile = File(...)) -> MealAnalysisResponse:
    """Receives a photo, executes YOLOv11 + SAM 2 pipeline, and returns nutritional data."""
    # Cria arquivo temporário local para salvar a imagem recebida
    suffix = Path(file.filename or "image.jpg").suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        shutil.copyfileobj(file.file, temp_file)

    try:
        # Executa a inferência real do modelo através do MLService
        result = MLService.analyze_image(temp_path)

        # Extrai os IDs das classes detectadas
        class_ids = [detection.class_id for detection in result.detections]

        # Consolida e mapeia os valores nutricionais
        response = map_detections_to_nutrition(class_ids)

        return response
    finally:
        # Limpa o arquivo temporário do servidor
        if temp_path.exists():
            temp_path.unlink()

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from prato_do_dia_api.db.models import MealComponent, MealRecord
from prato_do_dia_api.db.session import get_db
from prato_do_dia_api.schemas.meal import MealAnalysisResponse, MealComponentResponse
from prato_do_dia_api.services.ml_service import UPLOADS_DIR, MLService
from prato_do_dia_api.services.nutrition_mapper import FOOD_PROFILES, map_detections_to_nutrition

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("/analyze", response_model=MealAnalysisResponse)
async def analyze_meal(file: UploadFile = File(...), db: Session = Depends(get_db)) -> MealAnalysisResponse:
    """Receives a photo, executes YOLOv11 + SAM 2 pipeline, persists data, and returns nutrition."""
    # Gera um UUID único para esta refeição para evitar qualquer conflito
    meal_uuid = str(uuid.uuid4())
    suffix = Path(file.filename or "image.jpg").suffix
    image_name = f"{meal_uuid}{suffix}"

    # Garante a existência do diretório de uploads e salva a imagem original permanentemente
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    persistent_path = UPLOADS_DIR / image_name

    try:
        # Abre a imagem com o Pillow para validar o formato e remover metadados EXIF
        file.file.seek(0)
        with Image.open(file.file) as img:
            # Trata canais alpha se for salvar como JPEG
            save_format = img.format or "JPEG"
            if suffix.lower() in (".jpg", ".jpeg") and img.mode in ("RGBA", "LA"):
                img_to_save = img.convert("RGB")
            else:
                img_to_save = img

            # Salva a imagem sem os metadados EXIF (exif= None) com alta qualidade para o ML
            img_to_save.save(persistent_path, format=save_format, quality=95)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"O arquivo enviado não é uma imagem válida ou está corrompido: {e}",
        ) from e

    try:
        # Executa a inferência real do modelo através do MLService
        result = MLService.analyze_image(persistent_path)

        # Extrai os IDs das classes detectadas
        class_ids = [detection.class_id for detection in result.detections]

        # Consolida e mapeia os valores nutricionais do prato
        response = map_detections_to_nutrition(class_ids)
        response.image_url = f"/static/uploads/{image_name}"
        response.overlay_url = f"/static/overlays/{meal_uuid}_overlay.jpg"

        # Constrói a lista detalhada de componentes para a resposta
        components_list = []
        for det in result.detections:
            if det.class_id in FOOD_PROFILES:
                profile = FOOD_PROFILES[det.class_id]
                components_list.append(
                    MealComponentResponse(
                        label=str(profile["name"]),
                        confidence=float(det.confidence),
                        calories=int(profile["calories"]),
                        protein=float(profile["protein"]),
                        carbs=float(profile["carbs"]),
                        fat=float(profile["fat"]),
                    )
                )
        if not components_list:
            # Fallback mock components se nada for detectado
            components_list = [
                MealComponentResponse(label="Arroz", confidence=1.0, calories=130, protein=2.7, carbs=28.0, fat=0.3),
                MealComponentResponse(label="Feijão", confidence=1.0, calories=76, protein=4.8, carbs=14.0, fat=0.5),
                MealComponentResponse(
                    label="Frango Grelhado", confidence=1.0, calories=165, protein=31.0, carbs=0.0, fat=3.6
                ),
                MealComponentResponse(label="Salada", confidence=1.0, calories=15, protein=0.8, carbs=3.0, fat=0.1),
            ]
        response.components = components_list

        # Salva o cabeçalho da refeição no banco de dados
        db_meal = MealRecord(
            estimated_name=response.name,
            calories=response.calories,
            protein=response.protein,
            carbs=response.carbs,
            fat=response.fat,
            image_path=image_name,
            score=response.score,
        )
        db.add(db_meal)
        db.flush()  # Recupera o ID gerado pelo banco

        # Salva cada componente segmentado individualmente
        for seg in result.segmentations:
            if seg.class_id not in FOOD_PROFILES:
                continue
            profile = FOOD_PROFILES[seg.class_id]
            label = str(profile["name"])

            # Serializa os pontos do polígono em formato JSON string
            polygon_json = json.dumps([[p[0], p[1]] for p in seg.polygon])

            db_component = MealComponent(
                meal_id=db_meal.id,
                label=label,
                confidence=seg.confidence,
                polygon=polygon_json,
            )
            db.add(db_component)

        db.commit()
    except Exception:
        db.rollback()
        # Se falhar a IA ou a escrita de banco, remove o arquivo persistido para evitar lixo
        if persistent_path.exists():
            persistent_path.unlink()
        raise
    else:
        return response

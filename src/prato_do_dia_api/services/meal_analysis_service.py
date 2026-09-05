from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from prato_do_dia_ml.inference import (
    FoodPredictor,
    MLInferenceError,
    MLInvalidImageError,
    MLModelUnavailableError,
    PredictionResponse,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from prato_do_dia_api.core.config import Settings, get_settings
from prato_do_dia_api.core.errors import ApiError
from prato_do_dia_api.db.models import MealComponent as MealComponentRecord
from prato_do_dia_api.db.models import MealRecord
from prato_do_dia_api.schemas.v1 import (
    MealAnalysisResponse,
    MealComponent,
    MealImageInfo,
    MealSummary,
    MlModelFileStatus,
    MlStatusResponse,
    MlWarmupResponse,
    ModelInfo,
)
from prato_do_dia_api.services.nutrition_mapper import (
    DEFAULT_TACO_PROFILE,
    TACO_PROFILES,
    FoodProfile,
    calculate_portion,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
OVERLAYS_DIR = DATA_DIR / "overlays"
ASSET_DIRS = {"uploads": UPLOADS_DIR, "overlays": OVERLAYS_DIR}
ALLOWED_MIME_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
DEFERRED_IMAGE_MIME_TYPES = {"", "application/octet-stream"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}
EXPECTED_MODELS = (
    {"filename": "yolov11_food.onnx", "role": "detector"},
    {"filename": "sam2.1_hiera_tiny.encoder.onnx", "role": "sam_encoder"},
    {"filename": "sam2.1_hiera_tiny.decoder.onnx", "role": "sam_decoder"},
)
_PREDICTOR: PredictorProtocol | None = None


class PredictorProtocol(Protocol):
    def predict_bytes(self, image_bytes: bytes) -> PredictionResponse: ...


class MealAnalysisService:
    def __init__(self, settings: Settings | None = None, predictor: PredictorProtocol | None = None) -> None:
        self.settings = settings or get_settings()
        self._predictor = predictor

    def ml_status(self, *, verify_checksum: bool = False) -> MlStatusResponse:
        models_dir = self._models_dir()
        warnings: list[str] = []
        manifest_models = _read_model_manifest(models_dir, warnings)
        expected_models = manifest_models or [dict(model) for model in EXPECTED_MODELS]

        model_statuses = [
            _model_file_status(models_dir, model, verify_checksum=verify_checksum, warnings=warnings)
            for model in expected_models
        ]

        if any(not model.present for model in model_statuses):
            warnings.append("missing_model_files")
        available = bool(model_statuses) and all(model.present for model in model_statuses)
        return MlStatusResponse(
            status="available" if available else "unavailable",
            available=available,
            loaded=self.is_loaded(),
            models_dir=str(models_dir),
            models=model_statuses,
            warnings=_unique_warnings(warnings),
        )

    def warmup(self) -> MlWarmupResponse:
        already_loaded = self.is_loaded()
        started = time.perf_counter()
        try:
            predictor = self._get_predictor()
            if not already_loaded:
                # Perform dummy pass with 640x640 black image for ONNX graph compilation
                buf = BytesIO()
                dummy_img = Image.new("RGB", (640, 640), color="black")
                dummy_img.save(buf, format="JPEG")
                dummy_bytes = buf.getvalue()
                predictor.predict_bytes(dummy_bytes)
        except MLModelUnavailableError as exc:
            raise ApiError(503, "model_unavailable", "Os modelos de ML não estão disponíveis.") from exc
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(500, "inference_failed", f"Falha no aquecimento do modelo: {exc}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)
        return MlWarmupResponse(
            status="ready",
            available=True,
            loaded=True,
            load_duration_ms=duration_ms,
            already_loaded=already_loaded,
            warnings=[],
        )

    def is_loaded(self) -> bool:
        return self._predictor is not None or _PREDICTOR is not None

    async def analyze_upload(self, file: UploadFile, db: Session) -> MealAnalysisResponse:
        image_bytes = await self._read_upload(file)
        image_info, normalized_bytes = self._normalize_image(file.content_type, image_bytes)
        analysis_id = str(uuid.uuid4())
        image_name = f"{analysis_id}.jpg"
        upload_path = UPLOADS_DIR / image_name

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
        upload_path.write_bytes(normalized_bytes)

        try:
            prediction = self._get_predictor().predict_bytes(normalized_bytes)
            response = self._build_response(analysis_id, image_name, image_info, prediction)
            self._persist_response(db, response, image_name, prediction)
        except MLInvalidImageError as exc:
            upload_path.unlink(missing_ok=True)
            raise ApiError(400, "invalid_image", "A imagem enviada não é válida.") from exc
        except MLModelUnavailableError as exc:
            upload_path.unlink(missing_ok=True)
            raise ApiError(503, "model_unavailable", "Modelo de IA indisponível no servidor.") from exc
        except MLInferenceError as exc:
            upload_path.unlink(missing_ok=True)
            raise ApiError(500, "inference_failed", "Falha ao analisar a imagem.") from exc
        except SQLAlchemyError as exc:
            db.rollback()
            upload_path.unlink(missing_ok=True)
            raise ApiError(500, "database_error", "Falha ao salvar a análise.") from exc
        except ApiError:
            upload_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            upload_path.unlink(missing_ok=True)
            raise ApiError(500, "contract_error", "Resposta interna fora do contrato esperado.") from exc

        return response

    async def _read_upload(self, file: UploadFile) -> bytes:
        content_type = (file.content_type or "").lower().strip()
        allowed_types = {"image/jpeg", "image/png", "application/octet-stream", ""}
        if content_type not in allowed_types:
            raise ApiError(
                415,
                "unsupported_media_type",
                "Formato de arquivo não suportado. Envie apenas image/jpeg ou image/png.",
            )
        max_bytes = 5 * 1024 * 1024  # Strict 5MB limit
        data = await file.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ApiError(413, "file_too_large", "O arquivo excede o limite máximo permitido de 5MB.")
        if not data:
            raise ApiError(400, "invalid_image", "A imagem enviada não é válida ou está vazia.")
        return data

    def _normalize_image(self, _content_type: str | None, image_bytes: bytes) -> tuple[tuple[int, int], bytes]:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.load()
                self._validate_decoded_image(image)
                transposed = ImageOps.exif_transpose(image)
                normalized = transposed.convert("RGB")
                output = BytesIO()
                normalized.save(output, format="JPEG", quality=90)
                return (normalized.width, normalized.height), output.getvalue()
        except ApiError:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise ApiError(400, "invalid_image", "A imagem enviada não é válida.") from exc

    def _validate_decoded_image(self, image: Image.Image) -> None:
        if image.width > self.settings.max_image_width or image.height > self.settings.max_image_height:
            raise ApiError(400, "invalid_image", "A imagem excede as dimensões máximas permitidas.")
        if image.format not in ALLOWED_IMAGE_FORMATS:
            raise ApiError(415, "unsupported_media_type", "Formato de imagem não suportado.")

    def _get_predictor(self) -> PredictorProtocol:
        global _PREDICTOR

        if self._predictor is not None:
            return self._predictor
        if _PREDICTOR is None:
            _PREDICTOR = FoodPredictor.from_models_dir(self._models_dir())
        return _PREDICTOR

    def _models_dir(self) -> Path:
        return Path(self.settings.ml_models_dir) if self.settings.ml_models_dir else _default_models_dir(self.settings)

    def _build_response(
        self,
        analysis_id: str,
        image_name: str,
        image_size: tuple[int, int],
        prediction: PredictionResponse,
    ) -> MealAnalysisResponse:
        model = ModelInfo(
            pipeline=prediction.model_info.pipeline,
            version=prediction.model_info.version,
        )
        original_url = f"{self.settings.public_assets_base_path}/uploads/{image_name}"
        overlay_url = _copy_overlay_artifact(prediction, analysis_id, self.settings.public_assets_base_path)
        image = MealImageInfo(
            width=prediction.image_width or image_size[0],
            height=prediction.image_height or image_size[1],
            original_url=original_url,
            overlay_url=overlay_url,
        )

        components = [
            _component_from_instance(index, instance) for index, instance in enumerate(prediction.instances, 1)
        ]
        components = [component for component in components if component is not None]
        if not components:
            return MealAnalysisResponse(
                analysis_id=analysis_id,
                status="empty",
                image=image.model_copy(update={"overlay_url": None}),
                summary=None,
                components=[],
                warnings=["no_food_detected"],
                model=model,
            )

        total_weight = round(sum(component.estimated_grams for component in components), 1)
        summary = MealSummary(
            name="Refeição analisada",
            calories=sum(component.calories for component in components),
            protein=round(sum(component.protein for component in components), 1),
            carbs=round(sum(component.carbs for component in components), 1),
            fat=round(sum(component.fat for component in components), 1),
            fiber=round(sum(component.fiber for component in components), 1),
            total_weight_g=total_weight,
            score=round(
                sum(
                    TACO_PROFILES.get(_class_id_from_label(component.label), DEFAULT_TACO_PROFILE).score
                    for component in components
                )
                / len(components),
                1,
            ),
            is_estimated=True,
            source="TACO / TBCA (NEPA/UNICAMP & USP)",
        )
        return MealAnalysisResponse(
            analysis_id=analysis_id,
            status="success",
            image=image,
            summary=summary,
            components=components,
            warnings=["nutrition_is_estimated", "portion_size_not_measured"],
            model=model,
        )

    def _persist_response(
        self,
        db: Session,
        response: MealAnalysisResponse,
        image_name: str,
        prediction: PredictionResponse,
    ) -> None:
        if response.summary is None:
            db_meal = MealRecord(
                estimated_name="Nenhum alimento detectado",
                calories=0,
                protein=0.0,
                carbs=0.0,
                fat=0.0,
                image_path=image_name,
                score=0.0,
            )
        else:
            db_meal = MealRecord(
                estimated_name=response.summary.name,
                calories=response.summary.calories,
                protein=response.summary.protein,
                carbs=response.summary.carbs,
                fat=response.summary.fat,
                image_path=image_name,
                score=response.summary.score,
            )
        db.add(db_meal)
        db.flush()

        instances_by_id = {instance.instance_id: instance for instance in prediction.instances}
        for component in response.components:
            instance = instances_by_id.get(component.id)
            polygon = instance.polygon if instance is not None and instance.polygon is not None else []
            db.add(
                MealComponentRecord(
                    meal_id=db_meal.id,
                    label=component.display_name,
                    confidence=component.confidence,
                    polygon=json.dumps(polygon),
                )
            )
        db.commit()


def _default_models_dir(settings: Settings) -> Path:
    if settings.ml_root:
        return Path(settings.ml_root) / "models"
    return PROJECT_ROOT.parent / "prato-do-dia-ml" / "models"


def _read_model_manifest(models_dir: Path, warnings: list[str]) -> list[dict[str, object]]:
    manifest_path = models_dir / "model_manifest.json"
    if not manifest_path.exists():
        warnings.append("model_manifest_missing")
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        warnings.append("model_manifest_invalid")
        return []

    models = manifest.get("models")
    if not isinstance(models, list):
        warnings.append("model_manifest_invalid")
        return []
    return [model for model in models if isinstance(model, dict)]


def _model_file_status(
    models_dir: Path,
    model: dict[str, object],
    *,
    verify_checksum: bool,
    warnings: list[str],
) -> MlModelFileStatus:
    filename = str(model.get("filename", ""))
    role = str(model.get("role", "unknown"))
    expected_sha = model.get("sha256")
    expected_size = model.get("size_bytes")
    path = models_dir / filename

    if not filename or Path(filename).name != filename:
        warnings.append("model_manifest_invalid")
        return MlModelFileStatus(filename=filename, role=role, present=False)

    if not path.exists() or not path.is_file():
        return MlModelFileStatus(
            filename=filename,
            role=role,
            present=False,
            sha256=expected_sha if isinstance(expected_sha, str) else None,
        )

    size_bytes = path.stat().st_size
    checksum_ok: bool | None = None
    sha256 = expected_sha if isinstance(expected_sha, str) else None

    if isinstance(expected_size, int) and expected_size != size_bytes:
        warnings.append("model_size_mismatch")

    if verify_checksum:
        actual_sha = _sha256_file(path)
        sha256 = actual_sha
        checksum_ok = actual_sha == expected_sha if isinstance(expected_sha, str) else None

    return MlModelFileStatus(
        filename=filename,
        role=role,
        present=True,
        size_bytes=size_bytes,
        sha256=sha256,
        checksum_ok=checksum_ok,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_warnings(warnings: list[str]) -> list[str]:
    return list(dict.fromkeys(warnings))


_DEFAULT_PROFILE = FoodProfile("Outro Alimento", 100, 5.0, 15.0, 2.0, ("Acompanhamento",), 7.0)


def _component_from_instance(index: int, instance: Any) -> MealComponent | None:
    try:
        class_id = int(getattr(instance, "proposal_class_id", getattr(instance, "class_id", 0)))
    except (ValueError, TypeError):
        return None

    area_pct = getattr(instance, "relative_area_percentage", None)
    portion = calculate_portion(class_id, area_percentage=area_pct)
    bbox_raw = getattr(instance, "bbox", getattr(instance, "box", ()))
    bbox = [round(float(value), 2) for value in bbox_raw]

    return MealComponent(
        id=int(getattr(instance, "instance_id", None) or index),
        label=str(getattr(instance, "label", None) or getattr(instance, "class_name", str(class_id))),
        display_name=portion.name,
        confidence=round(float(getattr(instance, "confidence", 0.0)), 4),
        bbox=bbox,
        area_px=int(getattr(instance, "area_px", 0)),
        calories=portion.calories,
        protein=portion.protein,
        carbs=portion.carbs,
        fat=portion.fat,
        warnings=[],
    )


def _class_id_from_label(label: str) -> int:
    try:
        return int(label)
    except ValueError:
        return -1


def _copy_overlay_artifact(prediction: PredictionResponse, analysis_id: str, base_path: str) -> str | None:
    overlay = prediction.artifacts.get("overlay")
    if not overlay:
        return None
    source = Path(overlay)
    if not source.exists():
        return None
    filename = f"{analysis_id}_overlay.jpg"
    destination = OVERLAYS_DIR / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return f"{base_path}/overlays/{filename}"

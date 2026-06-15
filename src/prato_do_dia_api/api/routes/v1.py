from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from prato_do_dia_api.core.errors import ApiError
from prato_do_dia_api.db.session import get_db
from prato_do_dia_api.schemas.health import HealthResponse
from prato_do_dia_api.schemas.v1 import MealAnalysisResponse, MlStatusResponse, MlWarmupResponse
from prato_do_dia_api.services.meal_analysis_service import ASSET_DIRS, MealAnalysisService

router = APIRouter(prefix="/v1")


@router.get("/health", response_model=HealthResponse, tags=["health"])
def read_health_v1() -> HealthResponse:
    return HealthResponse(status="ok", service="prato-do-dia-api")


@router.get("/ml/status", response_model=MlStatusResponse, tags=["ml"])
def read_ml_status(verify_checksum: bool = Query(False)) -> MlStatusResponse:
    return MealAnalysisService().ml_status(verify_checksum=verify_checksum)


@router.post("/ml/warmup", response_model=MlWarmupResponse, tags=["ml"])
def warmup_ml() -> MlWarmupResponse:
    return MealAnalysisService().warmup()


@router.post("/meals/analyze", response_model=MealAnalysisResponse, tags=["meals"])
async def analyze_meal_v1(file: UploadFile = File(...), db: Session = Depends(get_db)) -> MealAnalysisResponse:
    return await MealAnalysisService().analyze_upload(file, db)


@router.get("/assets/{kind}/{filename}", tags=["assets"])
def read_asset(kind: str, filename: str) -> FileResponse:
    directory = ASSET_DIRS.get(kind)
    if directory is None:
        raise ApiError(404, "invalid_image", "Asset não encontrado.")
    if Path(filename).name != filename or filename in {".", ".."}:
        raise ApiError(404, "invalid_image", "Asset não encontrado.")

    path = (directory / filename).resolve()
    root = directory.resolve()
    if root not in path.parents:
        raise ApiError(404, "invalid_image", "Asset não encontrado.")
    if not path.exists() or not path.is_file():
        raise ApiError(404, "invalid_image", "Asset não encontrado.")
    return FileResponse(path)

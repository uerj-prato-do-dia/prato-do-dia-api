import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from prato_do_dia_api.api.routes.foods import router as foods_router
from prato_do_dia_api.api.routes.health import router as health_router
from prato_do_dia_api.api.routes.meals import router as meals_router
from prato_do_dia_api.api.routes.v1 import router as v1_router
from prato_do_dia_api.core.config import get_settings
from prato_do_dia_api.core.errors import ApiError, api_error_handler
from prato_do_dia_api.services.meal_analysis_service import (
    OVERLAYS_DIR,
    UPLOADS_DIR,
    MealAnalysisService,
)

logger = logging.getLogger("prato_do_dia_api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: Inicialização do DB e Warmup de ML
    from prato_do_dia_api.db.session import init_db

    init_db()

    logger.info("Iniciando warmup dos modelos de IA...")
    start_time = time.perf_counter()
    try:
        service = MealAnalysisService()
        warmup_res = service.warmup()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Modelos carregados e aquecidos com sucesso ({elapsed_ms:.1f}ms - "
            f"internamente {warmup_res.load_duration_ms}ms)."
        )
    except Exception as e:
        logger.warning(f"Não foi possível realizar o warmup dos modelos: {e}. O carregamento ocorrerá sob demanda.")

    yield

    logger.info("Finalizando aplicação Prato do Dia API...")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Prato do Dia API"}


UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="static_uploads")
app.mount("/static/overlays", StaticFiles(directory=str(OVERLAYS_DIR)), name="static_overlays")

app.include_router(health_router)
app.include_router(meals_router)
app.include_router(v1_router)
app.include_router(v1_router, prefix="/api")
app.include_router(foods_router, prefix="/api/v1")
app.add_exception_handler(ApiError, api_error_handler)

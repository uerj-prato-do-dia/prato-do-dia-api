from fastapi import FastAPI

from prato_do_dia_api.api.routes.health import router as health_router
from prato_do_dia_api.api.routes.meals import router as meals_router
from prato_do_dia_api.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
)


@app.on_event("startup")
def on_startup() -> None:
    from prato_do_dia_api.db.session import init_db
    init_db()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Prato do Dia API"}


app.include_router(health_router)
app.include_router(meals_router)

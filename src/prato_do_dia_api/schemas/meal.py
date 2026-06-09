from pydantic import BaseModel


class MealComponentResponse(BaseModel):
    label: str
    confidence: float
    calories: int
    protein: float
    carbs: float
    fat: float


class MealAnalysisResponse(BaseModel):
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    ingredients: list[str]
    score: float
    image_url: str | None = None
    overlay_url: str | None = None
    components: list[MealComponentResponse] = []

from pydantic import BaseModel, Field


class MealComponentResponse(BaseModel):
    label: str
    confidence: float
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float = 0.0
    estimated_grams: float = 100.0


class MealAnalysisResponse(BaseModel):
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float = 0.0
    total_weight_g: float = 400.0
    ingredients: list[str]
    score: float
    source: str = "TACO / TBCA (NEPA/UNICAMP & USP)"
    image_url: str | None = None
    overlay_url: str | None = None
    components: list[MealComponentResponse] = Field(default_factory=list)

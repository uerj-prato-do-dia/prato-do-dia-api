from pydantic import BaseModel


class MealAnalysisResponse(BaseModel):
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    ingredients: list[str]
    score: float

"""API endpoints for querying TACO / TBCA food items from the database."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from prato_do_dia_api.db.models import TacoFoodItem
from prato_do_dia_api.db.session import get_db

router = APIRouter(prefix="/foods", tags=["foods"])


class FoodItemResponse(BaseModel):
    id: int
    class_id: int | None
    category: str
    name: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    source: str

    model_config = {"from_attributes": True}


class FoodSearchResponse(BaseModel):
    total: int
    items: list[FoodItemResponse]


@router.get("/search", response_model=FoodSearchResponse)
def search_foods(
    query: str = Query(..., min_length=1, description="Food name search query (e.g., 'arroz', 'feijao')"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> FoodSearchResponse:
    """Search foods in TACO database by name or category."""
    search_pattern = f"%{query.strip()}%"
    results = (
        db.query(TacoFoodItem)
        .filter(
            (TacoFoodItem.name.ilike(search_pattern)) | (TacoFoodItem.category.ilike(search_pattern))
        )
        .limit(limit)
        .all()
    )
    items = [FoodItemResponse.model_validate(r) for r in results]
    return FoodSearchResponse(total=len(items), items=items)


@router.get("/{class_id}", response_model=FoodItemResponse)
def get_food_by_class_id(class_id: int, db: Session = Depends(get_db)) -> FoodItemResponse:
    """Get official TACO food profile by YOLO class ID."""
    food = db.query(TacoFoodItem).filter(TacoFoodItem.class_id == class_id).first()
    if not food:
        raise HTTPException(status_code=404, detail=f"Food item for class_id {class_id} not found.")
    return FoodItemResponse.model_validate(food)

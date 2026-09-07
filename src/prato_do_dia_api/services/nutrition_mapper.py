from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from prato_do_dia_api.db.models import TacoFoodItem
from prato_do_dia_api.schemas.meal import MealAnalysisResponse


@dataclass(frozen=True)
class TacoFoodProfile:
    """Official TACO/TBCA nutritional values per 100g of ready/cooked food."""

    name: str
    calories_100g: float
    protein_100g: float
    carbs_100g: float
    fat_100g: float
    fiber_100g: float
    ingredients: tuple[str, ...]
    score: float
    source: str = "TACO / TBCA"


@dataclass(frozen=True)
class CalculatedPortion:
    """Estimated portion weight and nutritional breakdown based on relative area."""

    class_id: int
    name: str
    estimated_grams: float
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float
    ingredients: tuple[str, ...]
    score: float


# Official TACO/TBCA Database per 100g for Canonical Classes [0..15]
TACO_PROFILES: dict[int, TacoFoodProfile] = {
    0: TacoFoodProfile("Tomate", 15.0, 1.1, 3.1, 0.2, 1.2, ("Tomate cru",), 10.0),
    1: TacoFoodProfile("Salada Verde", 14.0, 1.3, 2.4, 0.2, 1.7, ("Alface", "Rúcula"), 10.0),
    2: TacoFoodProfile("Feijão", 76.0, 4.8, 13.6, 0.5, 8.5, ("Feijão cozido",), 9.0),
    3: TacoFoodProfile("Batata Frita", 267.0, 5.0, 35.6, 13.1, 3.2, ("Batata frita", "Óleo"), 4.5),
    4: TacoFoodProfile("Arroz", 128.0, 2.5, 28.1, 0.2, 1.6, ("Arroz branco cozido",), 8.0),
    5: TacoFoodProfile("Carne Moída", 212.0, 26.5, 0.0, 11.2, 0.0, ("Carne bovina moída refogada",), 7.5),
    6: TacoFoodProfile("Purê de Batata", 112.0, 2.2, 16.8, 4.1, 1.5, ("Batata", "Leite", "Manteiga"), 8.0),
    7: TacoFoodProfile("Farofa", 406.0, 2.1, 80.3, 9.1, 6.8, ("Farinha de mandioca", "Manteiga"), 6.0),
    8: TacoFoodProfile("Cenoura", 34.0, 0.8, 7.7, 0.2, 3.2, ("Cenoura crua/cozida",), 10.0),
    9: TacoFoodProfile("Ovo Frito", 240.0, 15.6, 0.6, 18.6, 0.0, ("Ovo frito", "Óleo"), 9.0),
    10: TacoFoodProfile("Massa / Macarrão", 157.0, 5.8, 30.9, 0.9, 1.8, ("Macarrão espaguete cozido",), 7.0),
    11: TacoFoodProfile("Frango Grelhado", 165.0, 31.5, 0.0, 3.2, 0.0, ("Filé de peito de frango grelhado",), 9.0),
    12: TacoFoodProfile("Azeitona", 137.0, 1.0, 5.0, 14.0, 3.0, ("Azeitona",), 7.0),
    13: TacoFoodProfile("Batata Palha", 512.0, 4.3, 50.8, 32.5, 3.8, ("Batata palha",), 4.0),
    14: TacoFoodProfile("Estrogonofe", 178.0, 14.2, 4.8, 11.5, 0.5, ("Carne", "Creme de leite", "Cogumelos"), 6.0),
    15: TacoFoodProfile("Carne Bovina (Bife)", 219.0, 31.7, 0.0, 9.5, 0.0, ("Bife de carne bovina grelhado",), 8.0),
}

DEFAULT_TACO_PROFILE = TacoFoodProfile("Outro Alimento", 150.0, 5.0, 15.0, 3.0, 1.0, ("Acompanhamento",), 7.0)


def calculate_portion(
    class_id: int,
    area_percentage: float | None = None,
    total_plate_weight_g: float = 400.0,
    db: Session | None = None,
) -> CalculatedPortion:
    """Calculate estimated portion weight (g) and nutritional values based on TACO database and relative area."""
    profile = TACO_PROFILES.get(class_id, DEFAULT_TACO_PROFILE)

    if db is not None:
        db_item = db.query(TacoFoodItem).filter(TacoFoodItem.class_id == class_id).first()
        if db_item is not None:
            profile = TacoFoodProfile(
                name=db_item.name,
                calories_100g=db_item.calories_kcal,
                protein_100g=db_item.protein_g,
                carbs_100g=db_item.carbs_g,
                fat_100g=db_item.fat_g,
                fiber_100g=db_item.fiber_g,
                ingredients=(db_item.name,),
                score=8.0,
                source=db_item.source,
            )

    if area_percentage is not None and area_percentage > 0:
        grams = round(total_plate_weight_g * (area_percentage / 100.0), 1)
        grams = max(10.0, grams)  # Minimum portion floor
    else:
        grams = 100.0  # Default 100g portion if area is unspecified

    factor = grams / 100.0

    return CalculatedPortion(
        class_id=class_id,
        name=profile.name,
        estimated_grams=grams,
        calories=round(profile.calories_100g * factor),
        protein=round(profile.protein_100g * factor, 1),
        carbs=round(profile.carbs_100g * factor, 1),
        fat=round(profile.fat_100g * factor, 1),
        fiber=round(profile.fiber_100g * factor, 1),
        ingredients=profile.ingredients,
        score=profile.score,
    )


# --- Backward Compatibility Layer for Legacy Callers ---


@dataclass(frozen=True)
class FoodProfile:
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    ingredients: tuple[str, ...]
    score: float


FOOD_PROFILES: dict[int, FoodProfile] = {
    cid: FoodProfile(
        name=taco.name,
        calories=round(taco.calories_100g),
        protein=round(taco.protein_100g, 1),
        carbs=round(taco.carbs_100g, 1),
        fat=round(taco.fat_100g, 1),
        ingredients=taco.ingredients,
        score=taco.score,
    )
    for cid, taco in TACO_PROFILES.items()
}

FALLBACK_PROFILE = FoodProfile(
    "Prato Feito",
    650,
    25.0,
    45.0,
    15.0,
    ("Arroz", "Feijão", "Frango grelhado", "Salada"),
    8.2,
)


def map_detections_to_nutrition(class_ids: list[int]) -> MealAnalysisResponse:
    """Consolidates a list of detected class IDs into a legacy nutritional response."""
    food_ids = [cid for cid in class_ids if cid in FOOD_PROFILES]
    profiles = [FOOD_PROFILES[cid] for cid in set(food_ids)] or [FALLBACK_PROFILE]

    names = [profile.name for profile in profiles]
    name = " e ".join((", ".join(names[:-1]), names[-1])) if len(names) > 1 else names[0]
    ingredients = sorted({ingredient for profile in profiles for ingredient in profile.ingredients})

    return MealAnalysisResponse(
        name=name,
        calories=sum(profile.calories for profile in profiles),
        protein=round(sum(profile.protein for profile in profiles), 1),
        carbs=round(sum(profile.carbs for profile in profiles), 1),
        fat=round(sum(profile.fat for profile in profiles), 1),
        ingredients=ingredients,
        score=round(sum(profile.score for profile in profiles) / len(profiles), 1),
    )

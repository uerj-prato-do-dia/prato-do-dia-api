from dataclasses import dataclass

from prato_do_dia_api.schemas.meal import MealAnalysisResponse


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
    0: FoodProfile("Tomate", 20, 1.0, 4.0, 0.2, ("Tomate",), 10.0),
    1: FoodProfile("Salada Verde", 15, 1.2, 3.0, 0.1, ("Alface", "Rúcula"), 10.0),
    2: FoodProfile("Feijão", 130, 8.0, 24.0, 0.5, ("Feijão preto",), 9.0),
    3: FoodProfile("Batata Frita", 312, 3.4, 41.0, 15.0, ("Batata", "Óleo vegetal"), 4.5),
    4: FoodProfile("Arroz", 130, 2.7, 28.0, 0.3, ("Arroz branco",), 8.0),
    5: FoodProfile("Carne Moída", 250, 26.0, 0.0, 15.0, ("Carne bovina",), 7.5),
    6: FoodProfile("Batata Cozida", 87, 2.0, 20.0, 0.1, ("Batata",), 8.5),
    7: FoodProfile("Aspargos", 20, 2.2, 3.8, 0.1, ("Aspargos",), 9.5),
    8: FoodProfile("Cenoura", 41, 0.9, 10.0, 0.2, ("Cenoura",), 10.0),
    9: FoodProfile("Ovo", 155, 13.0, 1.1, 11.0, ("Ovo",), 9.0),
    10: FoodProfile("Outro Alimento", 100, 5.0, 15.0, 2.0, ("Acompanhamento",), 7.0),
    11: FoodProfile("Frango Grelhado", 165, 31.0, 0.0, 3.6, ("Frango",), 9.0),
    12: FoodProfile("Azeitona", 115, 0.8, 6.0, 11.0, ("Azeitona",), 7.0),
    13: FoodProfile("Batata Palha", 500, 6.0, 50.0, 30.0, ("Batata", "Gordura vegetal"), 4.0),
    14: FoodProfile("Estrogonofe", 350, 20.0, 10.0, 25.0, ("Carne", "Creme de leite", "Champignon"), 6.0),
    15: FoodProfile("Carne de Porco", 242, 27.0, 0.0, 14.0, ("Lombo suíno",), 8.0),
    46: FoodProfile("Banana", 89, 1.1, 22.8, 0.3, ("Banana",), 9.0),
    47: FoodProfile("Maçã", 52, 0.3, 13.8, 0.2, ("Maçã",), 9.5),
    48: FoodProfile("Sanduíche", 350, 15.0, 40.0, 12.0, ("Pão", "Queijo", "Presunto"), 7.0),
    49: FoodProfile("Laranja", 47, 0.9, 11.8, 0.1, ("Laranja",), 10.0),
    50: FoodProfile("Brócolis", 34, 2.8, 6.6, 0.4, ("Brócolis",), 10.0),
    51: FoodProfile("Cenoura", 41, 0.9, 10.0, 0.2, ("Cenoura",), 10.0),
    52: FoodProfile("Cachorro-Quente", 290, 10.0, 28.0, 16.0, ("Pão de leite", "Salsicha"), 4.0),
    53: FoodProfile("Pizza", 266, 11.0, 33.0, 10.0, ("Massa de pizza", "Queijo", "Tomate"), 5.5),
    54: FoodProfile("Rosquinha/Bolinho", 452, 4.9, 51.3, 25.2, ("Farinha", "Açúcar", "Gordura"), 3.0),
    55: FoodProfile("Bolo", 389, 2.5, 53.0, 15.0, ("Farinha", "Açúcar", "Ovos"), 3.5),
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

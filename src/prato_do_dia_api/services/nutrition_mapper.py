from prato_do_dia_api.schemas.meal import MealAnalysisResponse

# Mapeamento nutricional para as classes de alimentos do dataset customizado
FOOD_PROFILES: dict[int, dict[str, object]] = {
    0: {
        "name": "Tomate",
        "calories": 20,
        "protein": 1.0,
        "carbs": 4.0,
        "fat": 0.2,
        "ingredients": ["Tomate"],
        "score": 10.0,
    },
    1: {
        "name": "Salada Verde",
        "calories": 15,
        "protein": 1.2,
        "carbs": 3.0,
        "fat": 0.1,
        "ingredients": ["Alface", "Rúcula"],
        "score": 10.0,
    },
    2: {
        "name": "Feijão",
        "calories": 130,
        "protein": 8.0,
        "carbs": 24.0,
        "fat": 0.5,
        "ingredients": ["Feijão preto"],
        "score": 9.0,
    },
    3: {
        "name": "Batata Frita",
        "calories": 312,
        "protein": 3.4,
        "carbs": 41.0,
        "fat": 15.0,
        "ingredients": ["Batata", "Óleo vegetal"],
        "score": 4.5,
    },
    4: {
        "name": "Arroz",
        "calories": 130,
        "protein": 2.7,
        "carbs": 28.0,
        "fat": 0.3,
        "ingredients": ["Arroz branco"],
        "score": 8.0,
    },
    5: {
        "name": "Carne Moída",
        "calories": 250,
        "protein": 26.0,
        "carbs": 0.0,
        "fat": 15.0,
        "ingredients": ["Carne bovina"],
        "score": 7.5,
    },
    6: {
        "name": "Batata Cozida",
        "calories": 87,
        "protein": 2.0,
        "carbs": 20.0,
        "fat": 0.1,
        "ingredients": ["Batata"],
        "score": 8.5,
    },
    7: {
        "name": "Aspargos",
        "calories": 20,
        "protein": 2.2,
        "carbs": 3.8,
        "fat": 0.1,
        "ingredients": ["Aspargos"],
        "score": 9.5,
    },
    8: {
        "name": "Cenoura",
        "calories": 41,
        "protein": 0.9,
        "carbs": 10.0,
        "fat": 0.2,
        "ingredients": ["Cenoura"],
        "score": 10.0,
    },
    9: {
        "name": "Ovo",
        "calories": 155,
        "protein": 13.0,
        "carbs": 1.1,
        "fat": 11.0,
        "ingredients": ["Ovo"],
        "score": 9.0,
    },
    10: {
        "name": "Outro Alimento",
        "calories": 100,
        "protein": 5.0,
        "carbs": 15.0,
        "fat": 2.0,
        "ingredients": ["Acompanhamento"],
        "score": 7.0,
    },
    11: {
        "name": "Frango Grelhado",
        "calories": 165,
        "protein": 31.0,
        "carbs": 0.0,
        "fat": 3.6,
        "ingredients": ["Frango"],
        "score": 9.0,
    },
    12: {
        "name": "Azeitona",
        "calories": 115,
        "protein": 0.8,
        "carbs": 6.0,
        "fat": 11.0,
        "ingredients": ["Azeitona"],
        "score": 7.0,
    },
    13: {
        "name": "Batata Palha",
        "calories": 500,
        "protein": 6.0,
        "carbs": 50.0,
        "fat": 30.0,
        "ingredients": ["Batata", "Gordura vegetal"],
        "score": 4.0,
    },
    14: {
        "name": "Estrogonofe",
        "calories": 350,
        "protein": 20.0,
        "carbs": 10.0,
        "fat": 25.0,
        "ingredients": ["Carne", "Creme de leite", "Champignon"],
        "score": 6.0,
    },
    15: {
        "name": "Carne de Porco",
        "calories": 242,
        "protein": 27.0,
        "carbs": 0.0,
        "fat": 14.0,
        "ingredients": ["Lombo suíno"],
        "score": 8.0,
    },
    46: {
        "name": "Banana",
        "calories": 89,
        "protein": 1.1,
        "carbs": 22.8,
        "fat": 0.3,
        "ingredients": ["Banana"],
        "score": 9.0,
    },
    47: {
        "name": "Maçã",
        "calories": 52,
        "protein": 0.3,
        "carbs": 13.8,
        "fat": 0.2,
        "ingredients": ["Maçã"],
        "score": 9.5,
    },
    48: {
        "name": "Sanduíche",
        "calories": 350,
        "protein": 15.0,
        "carbs": 40.0,
        "fat": 12.0,
        "ingredients": ["Pão", "Queijo", "Presunto"],
        "score": 7.0,
    },
    49: {
        "name": "Laranja",
        "calories": 47,
        "protein": 0.9,
        "carbs": 11.8,
        "fat": 0.1,
        "ingredients": ["Laranja"],
        "score": 10.0,
    },
    50: {
        "name": "Brócolis",
        "calories": 34,
        "protein": 2.8,
        "carbs": 6.6,
        "fat": 0.4,
        "ingredients": ["Brócolis"],
        "score": 10.0,
    },
    51: {
        "name": "Cenoura",
        "calories": 41,
        "protein": 0.9,
        "carbs": 10.0,
        "fat": 0.2,
        "ingredients": ["Cenoura"],
        "score": 10.0,
    },
    52: {
        "name": "Cachorro-Quente",
        "calories": 290,
        "protein": 10.0,
        "carbs": 28.0,
        "fat": 16.0,
        "ingredients": ["Pão de leite", "Salsicha"],
        "score": 4.0,
    },
    53: {
        "name": "Pizza",
        "calories": 266,
        "protein": 11.0,
        "carbs": 33.0,
        "fat": 10.0,
        "ingredients": ["Massa de pizza", "Queijo", "Tomate"],
        "score": 5.5,
    },
    54: {
        "name": "Rosquinha/Bolinho",
        "calories": 452,
        "protein": 4.9,
        "carbs": 51.3,
        "fat": 25.2,
        "ingredients": ["Farinha", "Açúcar", "Gordura"],
        "score": 3.0,
    },
    55: {
        "name": "Bolo",
        "calories": 389,
        "protein": 2.5,
        "carbs": 53.0,
        "fat": 15.0,
        "ingredients": ["Farinha", "Açúcar", "Ovos"],
        "score": 3.5,
    },
}

FALLBACK_PROFILE = {
    "name": "Prato Feito",
    "calories": 650,
    "protein": 25.0,
    "carbs": 45.0,
    "fat": 15.0,
    "ingredients": ["Arroz", "Feijão", "Frango grelhado", "Salada"],
    "score": 8.2,
}


def map_detections_to_nutrition(class_ids: list[int]) -> MealAnalysisResponse:
    """Consolidates a list of detected class IDs into a single nutritional response."""
    # Filtra apenas as classes que representam comida no dataset
    food_ids = [cid for cid in class_ids if cid in FOOD_PROFILES]

    if not food_ids:
        # Se nada for detectado, retorna o prato feito simulado
        return MealAnalysisResponse(**FALLBACK_PROFILE)

    # Coleta perfis únicos de alimentos
    profiles = [FOOD_PROFILES[cid] for cid in set(food_ids)]

    # Concatena nomes (ex: "Arroz e Feijão")
    names = [str(p["name"]) for p in profiles]
    name = " e ".join((", ".join(names[:-1]), names[-1])) if len(names) > 1 else names[0]

    # Consolida valores somando calorias/macros e tirando a média do score
    calories = sum(int(p["calories"]) for p in profiles)
    protein = round(sum(float(p["protein"]) for p in profiles), 1)
    carbs = round(sum(float(p["carbs"]) for p in profiles), 1)
    fat = round(sum(float(p["fat"]) for p in profiles), 1)
    score = round(sum(float(p["score"]) for p in profiles) / len(profiles), 1)

    # Junta ingredientes e remove duplicatas
    ingredients_set: set[str] = set()
    for p in profiles:
        ingredients_set.update(p["ingredients"])

    return MealAnalysisResponse(
        name=name,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        ingredients=list(ingredients_set),
        score=score,
    )

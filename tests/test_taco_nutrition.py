from prato_do_dia_api.services.nutrition_mapper import TACO_PROFILES, calculate_portion


def test_taco_profiles_coverage() -> None:
    """Verify all 16 canonical food classes (IDs 0..15) are present in TACO database."""
    for class_id in range(16):
        assert class_id in TACO_PROFILES
        profile = TACO_PROFILES[class_id]
        assert profile.name
        assert profile.calories_100g > 0
        assert profile.source == "TACO / TBCA"


def test_calculate_portion_with_area_percentage() -> None:
    """Verify portion estimation scales correctly with relative area percentage."""
    # Arroz (class_id=4): 128 kcal / 100g. If it occupies 25% of a 400g plate -> 100g portion -> 128 kcal
    portion_arroz = calculate_portion(class_id=4, area_percentage=25.0, total_plate_weight_g=400.0)
    assert portion_arroz.estimated_grams == 100.0
    assert portion_arroz.calories == 128
    assert portion_arroz.protein == 2.5
    assert portion_arroz.carbs == 28.1

    # Feijão (class_id=2): 76 kcal / 100g. If it occupies 15% of a 400g plate -> 60g portion -> ~46 kcal
    portion_feijao = calculate_portion(class_id=2, area_percentage=15.0, total_plate_weight_g=400.0)
    assert portion_feijao.estimated_grams == 60.0
    assert portion_feijao.calories == round(76.0 * 0.6)
    assert portion_feijao.protein == round(4.8 * 0.6, 1)


def test_calculate_portion_unspecified_area() -> None:
    """Verify portion defaults to 100g baseline when area is unspecified."""
    portion = calculate_portion(class_id=11)  # Frango Grelhado
    assert portion.estimated_grams == 100.0
    assert portion.calories == 165
    assert portion.protein == 31.5

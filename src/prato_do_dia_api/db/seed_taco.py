"""Seeding script to populate taco_food_items table with official TACO / TBCA nutritional values per 100g."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from prato_do_dia_api.db.models import TacoFoodItem

logger = logging.getLogger(__name__)

OFFICIAL_TACO_SEED_DATA = [
    {
        "class_id": 0,
        "category": "Hortaliças",
        "name": "Tomate, salada",
        "calories_kcal": 15.0,
        "protein_g": 1.1,
        "carbs_g": 3.1,
        "fat_g": 0.2,
        "fiber_g": 1.2,
    },
    {
        "class_id": 1,
        "category": "Hortaliças",
        "name": "Salada verde (Alface, rúcula, agrião)",
        "calories_kcal": 14.0,
        "protein_g": 1.3,
        "carbs_g": 2.4,
        "fat_g": 0.2,
        "fiber_g": 1.7,
    },
    {
        "class_id": 2,
        "category": "Leguminosas",
        "name": "Feijão, carioca, cozido",
        "calories_kcal": 76.0,
        "protein_g": 4.8,
        "carbs_g": 13.6,
        "fat_g": 0.5,
        "fiber_g": 8.5,
    },
    {
        "class_id": 3,
        "category": "Tubérculos",
        "name": "Batata, frita",
        "calories_kcal": 267.0,
        "protein_g": 5.0,
        "carbs_g": 35.6,
        "fat_g": 13.1,
        "fiber_g": 3.2,
    },
    {
        "class_id": 4,
        "category": "Cereais e derivados",
        "name": "Arroz, tipo 1, cozido",
        "calories_kcal": 128.0,
        "protein_g": 2.5,
        "carbs_g": 28.1,
        "fat_g": 0.2,
        "fiber_g": 1.6,
    },
    {
        "class_id": 5,
        "category": "Carnes e derivados",
        "name": "Carne moída (acém/patinho), refogada",
        "calories_kcal": 212.0,
        "protein_g": 26.7,
        "carbs_g": 0.0,
        "fat_g": 11.8,
        "fiber_g": 0.0,
    },
    {
        "class_id": 6,
        "category": "Tubérculos",
        "name": "Purê de batata",
        "calories_kcal": 112.0,
        "protein_g": 2.1,
        "carbs_g": 18.4,
        "fat_g": 3.8,
        "fiber_g": 1.5,
    },
    {
        "class_id": 7,
        "category": "Cereais e derivados",
        "name": "Farofa de mandioca",
        "calories_kcal": 406.0,
        "protein_g": 2.1,
        "carbs_g": 80.3,
        "fat_g": 9.1,
        "fiber_g": 6.8,
    },
    {
        "class_id": 8,
        "category": "Hortaliças",
        "name": "Cenoura, cozida",
        "calories_kcal": 30.0,
        "protein_g": 0.8,
        "carbs_g": 6.7,
        "fat_g": 0.2,
        "fiber_g": 3.2,
    },
    {
        "class_id": 9,
        "category": "Ovos",
        "name": "Ovo, de galinha, frito",
        "calories_kcal": 240.0,
        "protein_g": 15.6,
        "carbs_g": 0.6,
        "fat_g": 18.6,
        "fiber_g": 0.0,
    },
    {
        "class_id": 10,
        "category": "Cereais e derivados",
        "name": "Macarrão, cozido",
        "calories_kcal": 137.0,
        "protein_g": 4.5,
        "carbs_g": 27.6,
        "fat_g": 0.9,
        "fiber_g": 1.8,
    },
    {
        "class_id": 11,
        "category": "Carnes e derivados",
        "name": "Frango, peito, grelhado",
        "calories_kcal": 165.0,
        "protein_g": 31.5,
        "carbs_g": 0.0,
        "fat_g": 3.2,
        "fiber_g": 0.0,
    },
    {
        "class_id": 12,
        "category": "Hortaliças",
        "name": "Azeitona, preta/verde",
        "calories_kcal": 115.0,
        "protein_g": 0.8,
        "carbs_g": 6.3,
        "fat_g": 10.7,
        "fiber_g": 3.2,
    },
    {
        "class_id": 13,
        "category": "Tubérculos",
        "name": "Batata, palha",
        "calories_kcal": 520.0,
        "protein_g": 4.8,
        "carbs_g": 50.2,
        "fat_g": 33.5,
        "fiber_g": 4.5,
    },
    {
        "class_id": 14,
        "category": "Carnes e derivados",
        "name": "Strogonoff de frango/carne",
        "calories_kcal": 185.0,
        "protein_g": 18.2,
        "carbs_g": 5.4,
        "fat_g": 10.1,
        "fiber_g": 0.5,
    },
    {
        "class_id": 15,
        "category": "Carnes e derivados",
        "name": "Carne bovina, bife, grelhado",
        "calories_kcal": 219.0,
        "protein_g": 32.4,
        "carbs_g": 0.0,
        "fat_g": 9.2,
        "fiber_g": 0.0,
    },
]


def seed_taco_data(db: Session) -> int:
    """Seed TACO database table if empty."""
    existing_count = db.query(TacoFoodItem).count()
    if existing_count > 0:
        logger.info("Tabela taco_food_items já contem %d registros. Seeding ignorado.", existing_count)
        return existing_count

    inserted = 0
    for item in OFFICIAL_TACO_SEED_DATA:
        food = TacoFoodItem(
            class_id=item.get("class_id"),
            category=item["category"],
            name=item["name"],
            calories_kcal=item["calories_kcal"],
            protein_g=item["protein_g"],
            carbs_g=item["carbs_g"],
            fat_g=item["fat_g"],
            fiber_g=item["fiber_g"],
            source="TACO NEPA/UNICAMP & TBCA USP",
        )
        db.add(food)
        inserted += 1

    db.commit()
    logger.info("Tabela taco_food_items populada com sucesso com %d alimentos oficiais.", inserted)
    return inserted

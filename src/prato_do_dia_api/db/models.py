from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from prato_do_dia_api.db.session import Base


class MealRecord(Base):
    __tablename__ = "meal_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    estimated_name: Mapped[str] = mapped_column(String(255), index=True)
    calories: Mapped[int] = mapped_column()
    protein: Mapped[float] = mapped_column()
    carbs: Mapped[float] = mapped_column()
    fat: Mapped[float] = mapped_column()
    image_path: Mapped[str] = mapped_column(String(512))
    score: Mapped[float] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    components: Mapped[list["MealComponent"]] = relationship(
        "MealComponent", back_populates="meal", cascade="all, delete-orphan"
    )


class MealComponent(Base):
    __tablename__ = "meal_components"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_records.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column()
    polygon: Mapped[str] = mapped_column(Text)  # JSON-serialized coordinates

    meal: Mapped["MealRecord"] = relationship("MealRecord", back_populates="components")


class TacoFoodItem(Base):
    __tablename__ = "taco_food_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int | None] = mapped_column(index=True, nullable=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    calories_kcal: Mapped[float] = mapped_column()
    protein_g: Mapped[float] = mapped_column()
    carbs_g: Mapped[float] = mapped_column()
    fat_g: Mapped[float] = mapped_column()
    fiber_g: Mapped[float] = mapped_column(default=0.0)
    source: Mapped[str] = mapped_column(String(100), default="TACO NEPA/UNICAMP & TBCA USP")


__all__ = ["Base", "MealComponent", "MealRecord", "TacoFoodItem"]

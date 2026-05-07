# schemas.py
from typing import List
from pydantic import BaseModel, Field, field_validator


# ========== Входные схемы ==========

class DishSaleInput(BaseModel):
    """Схема одного блюда во входном запросе."""

    dish: str = Field(
        ..., description="Название блюда", min_length=1, max_length=255
    )
    cost_price: float = Field(..., description="Себестоимость", gt=0)
    selling_price: float = Field(..., description="Цена продажи", gt=0)
    quantity: int = Field(
        ..., description="Количество проданных порций", gt=0
    )

    @field_validator("selling_price")
    @classmethod
    def validate_price_margin(cls, v: float, info) -> float:
        """Проверяем, что цена продажи не ниже себестоимости."""
        cost = info.data.get("cost_price")
        if cost is not None and v < cost:
            raise ValueError(
                f"Цена продажи ({v}) не может быть ниже себестоимости ({cost})"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "dish": "Паста Карбонара",
                "cost_price": 180,
                "selling_price": 450,
                "quantity": 12,
            }
        }


class SalesRequest(BaseModel):
    """Входной запрос: массив продаж."""

    sales: List[DishSaleInput] = Field(
        ..., description="Массив продаж за день", min_length=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sales": [
                    {
                        "dish": "Паста Карбонара",
                        "cost_price": 180,
                        "selling_price": 450,
                        "quantity": 12,
                    },
                    {
                        "dish": "Цезарь с курицей",
                        "cost_price": 140,
                        "selling_price": 390,
                        "quantity": 8,
                    },
                    {
                        "dish": "Маргарита",
                        "cost_price": 90,
                        "selling_price": 320,
                        "quantity": 25,
                    },
                ]
            }
        }


# ========== Выходные схемы ==========

class TopMarginDish(BaseModel):
    """Блюдо в топе по маржинальности."""

    dish: str
    margin_percent: float = Field(
        ..., description="Маржинальность в процентах"
    )
    revenue: float = Field(..., description="Выручка с этого блюда")


class LossMakingDish(BaseModel):
    """Убыточное блюдо (маржа ниже 30%)."""

    dish: str
    margin_percent: float = Field(
        ..., description="Маржинальность в процентах"
    )
    loss_amount: float = Field(
        ..., description="Потерянная прибыль относительно 30% маржи"
    )


class SalesAnalysisResponse(BaseModel):
    """Ответ эндпоинта /analyze_sales."""

    top_margin_dishes: List[TopMarginDish] = Field(
        ..., description="Топ-3 блюда по маржинальности"
    )
    loss_making: List[LossMakingDish] = Field(
        ..., description="Блюда с маржой ниже 30%"
    )
    total_revenue: float = Field(
        ..., description="Общая выручка за день", ge=0
    )
    total_margin: float = Field(..., description="Общая маржа за день")
    suggestions: List[str] = Field(
        ..., description="Рекомендации по улучшению"
    )


# ========== Внутренние схемы для БД ==========

class DishSaleDB(BaseModel):
    """Схема для сохранения в БД (расширенная версия DishSaleInput)."""

    dish_name: str
    cost_price: float
    selling_price: float
    quantity: int
    margin: float  # абсолютная маржа = (price - cost) * quantity
    margin_percent: float  # маржинальность в %
    total_revenue_per_dish: float  # selling_price * quantity


class DailySummaryDB(BaseModel):
    """Схема для агрегированной статистики."""

    sale_date: str  # ГГГГ-MM-ДД
    total_revenue: float
    total_margin: float
    top_dishes: List[TopMarginDish]
    loss_making_dishes: List[LossMakingDish]
    suggestions: List[str]

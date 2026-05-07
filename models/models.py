from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, Integer, DateTime, String, Text
from datetime import datetime
from typing import Optional

from database.db import Base


class DishSale(Base):
    """Модель продажи блюда за день."""

    __tablename__ = "dish_sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Дополнительные поля для аналитики (пока только структура)
    margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    margin_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_revenue_per_dish: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<DishSale(id={self.id}, dish={self.dish_name}, qty={self.quantity})>"


class DailySalesSummary(Base):
    """Модель для агрегированных данных по продажам за день."""

    __tablename__ = "daily_sales_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True, index=True)

    total_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_margin: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_margin_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    top_dishes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON строка с топ блюдами
    loss_making_dishes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON строка с убыточными
    suggestions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON строка с рекомендациями

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<DailySalesSummary(date={self.sale_date}, revenue={self.total_revenue})>"

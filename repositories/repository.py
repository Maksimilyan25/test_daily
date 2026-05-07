# repositories/sales_repository.py
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import DailySalesSummary, DishSale


class SalesRepository:
    """Репозиторий для работы с продажами."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия БД
        """
        self.session = session

    async def add_dish_sale(self, dish_sale: DishSale) -> DishSale:
        """
        Добавить продажу блюда.

        Args:
            dish_sale: Объект DishSale для сохранения

        Returns:
            DishSale: Сохранённый объект
        """
        self.session.add(dish_sale)
        return dish_sale

    async def add_dish_sales_bulk(
        self, dishes_data: List[dict]
    ) -> List[DishSale]:
        """
        Добавить несколько продаж блюд.

        Args:
            dishes_data: Список словарей с данными о продажах

        Returns:
            List[DishSale]: Список сохранённых объектов
        """
        dish_sales = []
        for dish in dishes_data:
            db_dish = DishSale(**dish)
            self.session.add(db_dish)
            dish_sales.append(db_dish)
        return dish_sales

    async def get_summary_by_date(
        self, date: datetime
    ) -> Optional[DailySalesSummary]:
        """
        Получить аналитику за конкретную дату.

        Args:
            date: Дата для поиска

        Returns:
            Optional[DailySalesSummary]: Аналитика или None
        """
        result = await self.session.execute(
            select(DailySalesSummary).where(
                DailySalesSummary.sale_date == date
            )
        )
        return result.scalar_one_or_none()

    async def save_summary(
        self,
        sale_date: datetime,
        total_revenue: float,
        total_margin: float,
        total_margin_percent: float,
        top_dishes_json: str,
        loss_making_dishes_json: str,
        suggestions_json: str,
    ) -> DailySalesSummary:
        """
        Сохранить новую аналитику.

        Args:
            sale_date: Дата анализа
            total_revenue: Общая выручка
            total_margin: Общая маржа
            total_margin_percent: Средняя маржинальность
            top_dishes_json: JSON с топ-блюдами
            loss_making_dishes_json: JSON с убыточными
            suggestions_json: JSON с рекомендациями

        Returns:
            DailySalesSummary: Сохранённый объект
        """
        summary = DailySalesSummary(
            sale_date=sale_date,
            total_revenue=total_revenue,
            total_margin=total_margin,
            total_margin_percent=total_margin_percent,
            top_dishes_json=top_dishes_json,
            loss_making_dishes_json=loss_making_dishes_json,
            suggestions_json=suggestions_json,
        )
        self.session.add(summary)
        return summary

    async def update_summary(
        self,
        summary: DailySalesSummary,
        total_revenue: float,
        total_margin: float,
        total_margin_percent: float,
        top_dishes_json: str,
        loss_making_dishes_json: str,
        suggestions_json: str,
    ) -> DailySalesSummary:
        """
        Обновить существующую аналитику.

        Args:
            summary: Существующий объект аналитики
            total_revenue: Общая выручка
            total_margin: Общая маржа
            total_margin_percent: Средняя маржинальность
            top_dishes_json: JSON с топ-блюдами
            loss_making_dishes_json: JSON с убыточными
            suggestions_json: JSON с рекомендациями

        Returns:
            DailySalesSummary: Обновлённый объект
        """
        summary.total_revenue = total_revenue
        summary.total_margin = total_margin
        summary.total_margin_percent = total_margin_percent
        summary.top_dishes_json = top_dishes_json
        summary.loss_making_dishes_json = loss_making_dishes_json
        summary.suggestions_json = suggestions_json
        return summary

    async def get_all_summaries(
        self, limit: int = 100, offset: int = 0
    ) -> List[DailySalesSummary]:
        """
        Получить список аналитик с пагинацией.

        Args:
            limit: Лимит записей
            offset: Смещение

        Returns:
            List[DailySalesSummary]: Список аналитик
        """
        result = await self.session.execute(
            select(DailySalesSummary)
            .order_by(DailySalesSummary.sale_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def delete_summary(self, summary: DailySalesSummary) -> None:
        """
        Удалить аналитику.

        Args:
            summary: Объект аналитики для удаления
        """
        await self.session.delete(summary)

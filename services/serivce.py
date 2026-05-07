# services/sales_service.py
from datetime import datetime
from typing import List, Tuple

from models.models import DailySalesSummary
from repositories.repository import SalesRepository
from schemas.schemas import DishSaleInput, LossMakingDish, TopMarginDish


class SalesService:
    """Сервис для анализа продаж."""

    def __init__(self, repository: SalesRepository):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с БД
        """
        self.repo = repository

    @staticmethod
    def calculate_dish_metrics(sale: DishSaleInput) -> dict:
        """
        Рассчитать метрики для одного блюда.

        Args:
            sale: Входные данные о продаже блюда

        Returns:
            dict с рассчитанными метриками
        """
        revenue = sale.selling_price * sale.quantity
        cost = sale.cost_price * sale.quantity
        margin = revenue - cost
        margin_percent = (margin / revenue) * 100 if revenue > 0 else 0

        return {
            "dish_name": sale.dish,
            "cost_price": sale.cost_price,
            "selling_price": sale.selling_price,
            "quantity": sale.quantity,
            "margin": margin,
            "margin_percent": margin_percent,
            "total_revenue_per_dish": revenue,
        }

    @staticmethod
    def get_top_margin_dishes(
        dishes_data: List[dict], top_n: int = 3
    ) -> List[TopMarginDish]:
        """
        Получить топ N блюд по маржинальности.

        Args:
            dishes_data: Список с данными о блюдах
            top_n: Количество блюд в топе

        Returns:
            List[TopMarginDish]: Список топовых блюд
        """
        sorted_by_margin = sorted(
            dishes_data, key=lambda x: x["margin_percent"], reverse=True
        )

        top_dishes = []
        for dish in sorted_by_margin[:top_n]:
            top_dishes.append(
                TopMarginDish(
                    dish=dish["dish_name"],
                    margin_percent=round(dish["margin_percent"], 2),
                    revenue=round(dish["total_revenue_per_dish"], 2),
                )
            )
        return top_dishes

    @staticmethod
    def get_loss_making_dishes(
        dishes_data: List[dict], threshold: float = 30.0
    ) -> List[LossMakingDish]:
        """
        Найти блюда с маржой ниже порога.

        Args:
            dishes_data: Список с данными о блюдах
            threshold: Порог маржинальности в процентах

        Returns:
            List[LossMakingDish]: Список убыточных блюд
        """
        loss_making = []
        for dish in dishes_data:
            if dish["margin_percent"] < threshold:
                target_margin = dish["total_revenue_per_dish"] * (
                    threshold / 100
                )
                loss_amount = target_margin - dish["margin"]
                loss_making.append(
                    LossMakingDish(
                        dish=dish["dish_name"],
                        margin_percent=round(dish["margin_percent"], 2),
                        loss_amount=round(max(loss_amount, 0), 2),
                    )
                )
        return loss_making

    @staticmethod
    def calculate_totals(
        dishes_data: List[dict],
    ) -> Tuple[float, float, float]:
        """
        Рассчитать общую выручку, маржу и среднюю маржу.

        Args:
            dishes_data: Список с данными о блюдах

        Returns:
            Tuple[total_revenue, total_margin, avg_margin_percent]
        """
        total_revenue = sum(d["total_revenue_per_dish"] for d in dishes_data)
        total_margin = sum(d["margin"] for d in dishes_data)
        avg_margin = (
            (total_margin / total_revenue) * 100 if total_revenue > 0 else 0
        )
        return total_revenue, total_margin, avg_margin

    @staticmethod
    def generate_suggestions(
        top_margin: List[TopMarginDish],
        loss_making: List[LossMakingDish],
        avg_margin: float,
        target_margin: float = 40.0,
    ) -> List[str]:
        """
        Сгенерировать рекомендации на основе анализа.

        Args:
            top_margin: Список топовых блюд
            loss_making: Список убыточных блюд
            avg_margin: Средняя маржинальность
            target_margin: Целевая маржинальность

        Returns:
            List[str]: Список рекомендаций
        """
        suggestions = []

        for dish in loss_making:
            suggestions.append(
                f"Рассмотрите увеличение цены на {dish.dish} "
                f"или снижение себестоимости"
            )

        for dish in top_margin[:2]:
            suggestions.append(
                f"Блюдо '{dish.dish}' имеет высокую маржинальность - "
                f"добавьте в рекомендации официантов"
            )

        if avg_margin < target_margin:
            suggestions.append(
                f"Средняя маржа ({round(avg_margin, 1)}%) ниже целевой "
                f"({target_margin}%) - проведите аудит цен"
            )

        return list(dict.fromkeys(suggestions))

    async def analyze_and_save(
        self, request_sales: List[DishSaleInput]
    ) -> dict:
        """
        Полный цикл анализа и сохранения продаж.

        Args:
            request_sales: Список продаж из запроса

        Returns:
            dict с результатами анализа
        """
        # 1. Рассчитываем данные для каждого блюда
        dishes_data = []
        for sale in request_sales:
            metrics = self.calculate_dish_metrics(sale)
            dishes_data.append(metrics)

        # 2. Топ-3 по маржинальности
        top_margin = self.get_top_margin_dishes(dishes_data, top_n=3)

        # 3. Блюда с маржой ниже 30%
        loss_making = self.get_loss_making_dishes(dishes_data, threshold=30.0)

        # 4. Общая статистика
        total_revenue, total_margin, avg_margin = self.calculate_totals(
            dishes_data
        )

        # 5. Рекомендации
        suggestions = self.generate_suggestions(
            top_margin=top_margin,
            loss_making=loss_making,
            avg_margin=avg_margin,
            target_margin=40.0,
        )

        # 6. Сохраняем в БД
        await self.repo.add_dish_sales_bulk(dishes_data)

        today = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        existing_summary = await self.repo.get_summary_by_date(today)

        if existing_summary:
            await self.repo.update_summary(
                summary=existing_summary,
                total_revenue=total_revenue,
                total_margin=total_margin,
                total_margin_percent=avg_margin,
                top_dishes_json=str([d.model_dump() for d in top_margin]),
                loss_making_dishes_json=str(
                    [d.model_dump() for d in loss_making]
                ),
                suggestions_json=str(suggestions),
            )
        else:
            await self.repo.save_summary(
                sale_date=today,
                total_revenue=total_revenue,
                total_margin=total_margin,
                total_margin_percent=avg_margin,
                top_dishes_json=str([d.model_dump() for d in top_margin]),
                loss_making_dishes_json=str(
                    [d.model_dump() for d in loss_making]
                ),
                suggestions_json=str(suggestions),
            )

        return {
            "top_margin_dishes": top_margin,
            "loss_making": loss_making,
            "total_revenue": round(total_revenue, 2),
            "total_margin": round(total_margin, 2),
            "suggestions": suggestions,
        }

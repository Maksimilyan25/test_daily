# routers/sales.py
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import select


from database.db import SessionDep
from models.models import DishSale, DailySalesSummary
from schemas.schemas import (
    SalesRequest,
    SalesAnalysisResponse,
    TopMarginDish,
    LossMakingDish,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/analyze_sales", response_model=SalesAnalysisResponse)
async def analyze_sales(
    request: SalesRequest,
    session: SessionDep
):
    """
    Анализ продаж:
    - считает маржинальность каждого блюда
    - определяет топ-3 по марже
    - находит блюда с маржой ниже 30%
    - генерирует рекомендации
    - сохраняет данные в БД
    """

    # 1. Рассчитываем данные для каждого блюда
    dishes_data = []
    for sale in request.sales:
        revenue = sale.selling_price * sale.quantity
        cost = sale.cost_price * sale.quantity
        margin = revenue - cost
        margin_percent = (margin / revenue) * 100 if revenue > 0 else 0

        dishes_data.append({
            "dish_name": sale.dish,
            "cost_price": sale.cost_price,
            "selling_price": sale.selling_price,
            "quantity": sale.quantity,
            "margin": margin,
            "margin_percent": margin_percent,
            "total_revenue_per_dish": revenue
        })

    # 2. Топ-3 по маржинальности
    sorted_by_margin = sorted(dishes_data, key=lambda x: x["margin_percent"], reverse=True)
    top_margin = []
    for dish in sorted_by_margin[:3]:
        top_margin.append(TopMarginDish(
            dish=dish["dish_name"],
            margin_percent=round(dish["margin_percent"], 2),
            revenue=round(dish["total_revenue_per_dish"], 2)
        ))

    # 3. Блюда с маржой ниже 30%
    loss_making = []
    for dish in dishes_data:
        if dish["margin_percent"] < 30:
            # Считаем потерянную прибыль относительно 30% маржи
            target_margin = dish["total_revenue_per_dish"] * 0.3
            loss_amount = target_margin - dish["margin"]
            loss_making.append(LossMakingDish(
                dish=dish["dish_name"],
                margin_percent=round(dish["margin_percent"], 2),
                loss_amount=round(loss_amount, 2) if loss_amount > 0 else 0
            ))

    # 4. Общая статистика
    total_revenue = sum(d["total_revenue_per_dish"] for d in dishes_data)
    total_margin = sum(d["margin"] for d in dishes_data)

    # 5. Генерация рекомендаций
    suggestions = []

    # Рекомендация для убыточных блюд
    for dish in loss_making:
        suggestions.append(
            f"Рассмотрите увеличение цены на {dish.dish} или снижение себестоимости")

    # Рекомендация для топовых блюд
    for dish in top_margin[:2]:
        suggestions.append(
            f"Блюдо '{dish.dish}' имеет высокую маржинальность - добавьте в рекомендации официантов")

    # Проверка на среднюю маржу
    avg_margin = (total_margin / total_revenue) * 100 if total_revenue > 0 else 0
    if avg_margin < 40:
        suggestions.append(
            f"Средняя маржа ({round(avg_margin, 1)}%) ниже целевой (40%) - проведите аудит цен")

    # Убираем дубликаты
    suggestions = list(dict.fromkeys(suggestions))

    # 6. Сохраняем каждую продажу в БД
    for dish in dishes_data:
        db_dish = DishSale(**dish)
        session.add(db_dish)

    # 7. Сохраняем агрегированную статистику
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Проверяем, была ли уже аналитика за сегодня
    existing = await session.execute(
        select(DailySalesSummary).where(DailySalesSummary.sale_date == today)
    )
    existing_summary = existing.scalar_one_or_none()

    if existing_summary:
        # Обновляем существующую
        existing_summary.total_revenue = total_revenue
        existing_summary.total_margin = total_margin
        existing_summary.top_dishes_json = str([d.model_dump() for d in top_margin])
        existing_summary.loss_making_dishes_json = str([d.model_dump() for d in loss_making])
        existing_summary.suggestions_json = str(suggestions)
    else:
        # Создаём новую
        summary = DailySalesSummary(
            sale_date=today,
            total_revenue=total_revenue,
            total_margin=total_margin,
            total_margin_percent=avg_margin,
            top_dishes_json=str([d.model_dump() for d in top_margin]),
            loss_making_dishes_json=str([d.model_dump() for d in loss_making]),
            suggestions_json=str(suggestions)
        )
        session.add(summary)

    # Коммитим все изменения
    await session.commit()

    # 8. Возвращаем результат
    return SalesAnalysisResponse(
        top_margin_dishes=top_margin,
        loss_making=loss_making,
        total_revenue=round(total_revenue, 2),
        total_margin=round(total_margin, 2),
        suggestions=suggestions
    )



@router.get("/summary/{date}")
async def get_summary(date: str, session: SessionDep):
    """Получить аналитику за конкретную дату (YYYY-MM-DD)"""
    from datetime import datetime
    target_date = datetime.strptime(date, "%Y-%m-%d")
    
    result = await session.execute(
        select(DailySalesSummary).where(DailySalesSummary.sale_date == target_date)
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Данные за эту дату не найдены")
    
    return summary
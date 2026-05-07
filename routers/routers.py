# routers/sales.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from database.db import SessionDep
from models.models import DailySalesSummary
from repositories.repository import SalesRepository
from schemas.schemas import SalesAnalysisResponse, SalesRequest
from services.serivce import SalesService

router = APIRouter(prefix="/sales", tags=["sales"])


def get_sales_service(session: SessionDep) -> SalesService:
    """
    Dependency для получения SalesService.

    Args:
        session: Сессия БД

    Returns:
        SalesService: Экземпляр сервиса
    """
    repository = SalesRepository(session)
    return SalesService(repository)


@router.post(
    "/analyze_sales",
    summary="Анализ продаж",
    response_model=SalesAnalysisResponse,
)
async def analyze_sales(
    request: SalesRequest,
    service: SalesService = Depends(get_sales_service),
    session: SessionDep = None,  # нужна для коммита
):
    """
    Анализ продаж:
    - считает маржинальность каждого блюда
    - определяет топ-3 по марже
    - находит блюда с маржой ниже 30%
    - генерирует рекомендации
    - сохраняет данные в БД
    """
    result = await service.analyze_and_save(request.sales)

    # Коммитим все изменения (репозиторий не коммитит сам)
    await session.commit()

    return SalesAnalysisResponse(**result)


@router.get("/summary/{date}", summary="История продажи")
async def get_summary(
    date: str,
    session: SessionDep,
):
    """Получить аналитику за конкретную дату (YYYY-MM-DD)"""
    target_date = datetime.strptime(date, "%Y-%m-%d")

    repository = SalesRepository(session)
    summary = await repository.get_summary_by_date(target_date)

    if not summary:
        raise HTTPException(
            status_code=404, detail="Данные за эту дату не найдены"
        )

    return summary


@router.get("/summaries", summary="Список продаж")
async def get_all_summaries(
    session: SessionDep,
    limit: int = 100,
    offset: int = 0,
):
    """Получить все аналитики с пагинацией."""
    repository = SalesRepository(session)
    summaries = await repository.get_all_summaries(limit=limit, offset=offset)
    return summaries

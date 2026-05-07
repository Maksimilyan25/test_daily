import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


class TestSalesAPI:
    """Тесты для API продаж."""

    @pytest.fixture
    def sample_sales_data(self):
        """Пример данных для POST запроса."""
        return {
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

    @pytest.fixture
    def sample_sales_with_loss(self):
        """Пример с убыточными блюдами."""
        return {
            "sales": [
                {
                    "dish": "По-флотски",
                    "cost_price": 110,
                    "selling_price": 120,
                    "quantity": 5,
                },
                {
                    "dish": "Маргарита",
                    "cost_price": 90,
                    "selling_price": 320,
                    "quantity": 25,
                },
            ]
        }


    async def test_post_analyze_sales_success(self, client: AsyncClient, sample_sales_data):
        """Тест POST - успешный анализ продаж."""
        response = await client.post("/sales/analyze_sales", json=sample_sales_data)

        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "top_margin_dishes" in data
        assert "loss_making" in data
        assert "total_revenue" in data
        assert "total_margin" in data
        assert "suggestions" in data

        # Проверяем топ-3
        assert len(data["top_margin_dishes"]) == 3

        # Первое место - Маргарита
        assert data["top_margin_dishes"][0]["dish"] == "Маргарита"
        assert data["top_margin_dishes"][0]["margin_percent"] > 70

        # Выручка положительная
        assert data["total_revenue"] > 0
        assert data["total_margin"] > 0

    async def test_post_analyze_sales_with_loss_making(self, client: AsyncClient, sample_sales_with_loss):
        """Тест POST - с убыточными блюдами."""
        response = await client.post("/sales/analyze_sales", json=sample_sales_with_loss)

        assert response.status_code == 200
        data = response.json()

        # Должны быть убыточные блюда
        assert len(data["loss_making"]) > 0

        # Проверяем убыточное блюдо
        loss_dish = data["loss_making"][0]
        assert "По-флотски" in loss_dish["dish"]
        assert loss_dish["margin_percent"] < 30

        # Должна быть рекомендация
        suggestions_text = " ".join(data["suggestions"])
        assert "Рассмотрите увеличение цены" in suggestions_text

    async def test_post_analyze_sales_invalid_data(self, client: AsyncClient):
        """Тест POST - неверные данные."""
        # Пустые данные
        response = await client.post("/sales/analyze_sales", json={"sales": []})
        assert response.status_code == 422

        # Цена продажи ниже себестоимости
        invalid_data = {
            "sales": [{
                "dish": "Тест",
                "cost_price": 200,
                "selling_price": 100,
                "quantity": 1,
            }]
        }
        response = await client.post("/sales/analyze_sales", json=invalid_data)
        assert response.status_code == 422

    async def test_get_summary_by_date_success(self, client: AsyncClient, sample_sales_data):
        """Тест GET - успешное получение аналитики."""
        from datetime import datetime

        # Сначала создаём данные
        await client.post("/sales/analyze_sales", json=sample_sales_data)

        # Получаем сегодняшнюю дату
        today = datetime.now().strftime("%Y-%m-%d")

        # Запрашиваем аналитику
        response = await client.get(f"/sales/summary/{today}")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "sale_date" in data
        assert "total_revenue" in data
        assert today in data["sale_date"]

    async def test_get_summary_by_date_not_found(self, client: AsyncClient):
        """Тест GET - дата не найдена."""
        response = await client.get("/sales/summary/2020-01-01")

        assert response.status_code == 404
        assert "не найдены" in response.json()["detail"]

    async def test_get_all_summaries_empty(self, client: AsyncClient):
        """Тест GET /summaries - пустой список."""
        response = await client.get("/sales/summaries")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_all_summaries_with_data(self, client: AsyncClient, sample_sales_data):
        """Тест GET /summaries - с данными."""
        # Создаём данные
        await client.post("/sales/analyze_sales", json=sample_sales_data)

        # Получаем список
        response = await client.get("/sales/summaries?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            first_item = data[0]
            expected_fields = [
                "id", "sale_date", "total_revenue", "total_margin",
                "total_margin_percent", "created_at"
            ]
            for field in expected_fields:
                assert field in first_item

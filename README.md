# Sales Analysis API

API для анализа ресторанных продаж: расчёт маржинальности блюд, выявление убыточных позиций и генерация рекомендаций.

##  Запуск через Docker

# Клонировать репозиторий
git clone git@github.com:Maksimilyan25/test_daily.git
cd test_daily

# Запустить контейнеры
docker compose up -d --build

# Проверить логи
docker logs test_daily-app-1

API будет доступно: http://localhost:8000/docs

## Эндпоинты

POST	/sales/analyze_sales	Анализ продаж за день
GET	/sales/summary/{date}	Получить аналитику за дату (YYYY-MM-DD)
GET	/sales/summaries	Список всех аналитик (пагинация: ?limit=100&offset=0)


Пример для POST Запроса в файле data.json

запуск тестов - pytest tests/ -v

POST: успешный анализ, убыточные блюда, валидация ошибок

GET: /summary: существующая/несуществующая дата

GET: /summaries: пустой список, данные с пагинацией

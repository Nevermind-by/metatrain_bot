# MetaTrain

Telegram-бот для расчёта калорий и БЖУ, учёта питания, веса и тренировочного прогресса.

## Стек

- Python 3.14+
- aiogram 3
- aiosqlite
- FastAPI
- Uvicorn
- pydantic-settings
- Ruff

## Возможности текущего MVP

- `/start` — регистрация и анкета пользователя
- профиль: пол, возраст, рост, вес, активность, цель
- расчёт дневных калорий и БЖУ по Mifflin-St Jeor
- `/profile` — просмотр и редактирование профиля
- `/food` — пошаговое добавление продукта с расчётом порции
- `/today` — питание за сегодня и остаток калорий
- `/delete_food <id>` — удаление записи питания
- `/history` — сводка питания за 7 дней
- `/weight` — запись текущего веса
- `/weights` — последние измерения веса
- `/workout` — запись тренировки
- `/workouts` — история тренировок
- `/dashboard` или `/stats` — общая сводка
- `/cancel` — отмена текущего ввода
- `/help` — список команд
- `/webapp` — кнопка запуска Telegram Web App, если задан `WEB_APP_URL`

## Локальный запуск

Создай `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_PATH=data/metatrain.db
WEB_APP_URL=https://your-public-domain.example.com
```

Установка зависимостей:

```bash
uv sync
```

Запуск бота:

```bash
uv run python -m app.bot.main
```

Запуск Web App/API отдельно:

```bash
uv run uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

После запуска API:

- `http://127.0.0.1:8000/` — Web App
- `http://127.0.0.1:8000/health` — health check
- `http://127.0.0.1:8000/docs` — Swagger UI

Для открытия Web App именно **в Telegram** нужен публичный HTTPS-адрес. Укажи его в `WEB_APP_URL`; локальный `127.0.0.1` предназначен для проверки в браузере.

Тесты:

```bash
uv run python -m unittest discover -s tests
```

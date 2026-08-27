# MetaTrain

Telegram-бот для расчёта калорий и БЖУ, учёта питания, веса и тренировочного прогресса.

## Стек

- Python 3.14+
- aiogram 3
- aiosqlite
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

## Запуск

Создай `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_PATH=data/metatrain.db
```

Установка:

```bash
uv sync
```

Запуск:

```bash
uv run python -m app.bot.main
```

Тесты:

```bash
uv run python -m unittest discover -s tests
```

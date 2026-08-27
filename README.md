# MetaTrain

Telegram-бот для расчёта калорий и БЖУ, учёта питания, веса и тренировочного прогресса.

## Стек

- Python 3.14+
- aiogram 3
- aiosqlite
- pydantic-settings
- Ruff

## Возможности MVP

- регистрация пользователя через `/start`
- анкета: пол, возраст, рост, вес, активность, цель
- расчёт дневных калорий и БЖУ по Mifflin-St Jeor
- просмотр и редактирование `/profile`
- дневник питания через `/food`
- сводка питания через `/today`
- запись веса через `/weight` и история `/weights`
- запись тренировок через `/workout` и история `/workouts`
- общая сводка `/dashboard` или `/stats`
- `/cancel` для отмены текущего ввода

## Запуск

Создай `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_PATH=data/metatrain.db
```

Установка зависимостей:

```bash
uv sync
```

Запуск:

```bash
uv run python -m app.bot.main
```

## Тесты

```bash
uv run python -m unittest discover -s tests
```

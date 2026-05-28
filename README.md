# CoffeePulse Sales Assistant

Приватный Telegram-бот для владельца CoffeePulse. Этот репозиторий содержит каркас Sales Assistant и ручное ведение лидов.

## Подготовка окружения

1. Скопируйте пример переменных:
   ```bash
   cp .env.example .env
   ```
2. Заполните `.env` своими значениями `BOT_TOKEN` и `OWNER_ID`.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 bot.py
```

## Запуск через Docker Compose

```bash
docker compose up --build -d
```

## Команды бота

- `/quick` — быстро добавить лида (по строкам или через `;`)
- `/leads` — последние лиды
- `/lead ID` — карточка лида
- `/search текст` — поиск по лидам
- `/status ID статус` — изменить статус
- `/score ID оценка` — изменить оценку

> Автоматическая холодная рассылка не используется.

## Проверки

```bash
python3 scripts/audit_project.py
python3 -m py_compile bot.py app/*.py scripts/*.py
```

# CoffeePulse Sales Assistant

Приватный Telegram-бот для владельца CoffeePulse. Этот репозиторий содержит каркас Sales Assistant без логики лидов.

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

## Проверки

```bash
python3 scripts/audit_project.py
python3 -m py_compile bot.py app/*.py scripts/*.py
```

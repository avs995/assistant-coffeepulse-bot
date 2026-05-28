# CoffeePulse Sales Assistant — Agent Rules

1. Не трогать `.env`.
2. Не удалять `data/`.
3. Не удалять и не перезаписывать базы данных (`*.db`, `*.sqlite`, `*.sqlite3`).
4. Не логировать токены и другие секреты.
5. Не добавлять автоспам.
6. Не делать массовую отправку сообщений.
7. Все изменения делать маленькими PR.
8. Перед коммитом запускать:
   - `python3 scripts/audit_project.py`
   - `python3 -m py_compile bot.py app/*.py scripts/*.py`

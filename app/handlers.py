from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.lead_service import (
    add_lead_note,
    create_lead,
    get_lead,
    list_lead_notes,
    list_recent_leads,
    list_status_history,
    search_leads,
    update_lead_score,
    update_lead_status,
)
from app.stats_service import get_stats

router = Router()

SCORE_LABEL_TO_CODE = {
    "высокая": "high",
    "средняя": "medium",
    "низкая": "low",
    "high": "high",
    "medium": "medium",
    "low": "low",
}
SCORE_CODE_TO_LABEL = {
    "high": "высокая",
    "medium": "средняя",
    "low": "низкая",
}

STATUS_LABEL_TO_CODE = {
    "новый": "new",
    "написать": "to_write",
    "написал": "written",
    "ответил": "replied",
    "демо": "demo",
    "тест": "trial",
    "отказ": "rejected",
    "клиент": "client",
    "new": "new",
    "to_write": "to_write",
    "written": "written",
    "replied": "replied",
    "demo": "demo",
    "trial": "trial",
    "rejected": "rejected",
    "client": "client",
}
STATUS_CODE_TO_LABEL = {
    "new": "новый",
    "to_write": "написать",
    "written": "написал",
    "replied": "ответил",
    "demo": "демо",
    "trial": "тест",
    "rejected": "отказ",
    "client": "клиент",
}

FIELD_MAP = {
    "компания": "company",
    "company": "company",
    "город": "city",
    "city": "city",
    "сфера": "niche",
    "niche": "niche",
    "источник": "source",
    "source": "source",
    "контакты": "contacts",
    "contacts": "contacts",
    "сайт": "website",
    "website": "website",
    "telegram": "telegram",
    "vk": "vk",
    "почему подходит": "fit_reason",
    "fit_reason": "fit_reason",
    "оценка": "score",
    "score": "score",
    "статус": "status",
    "status": "status",
    "заметки": "notes",
    "notes": "notes",
}

SCOPE_LABELS = {
    "all": "за все время",
    "week": "за последние 7 дней",
    "month": "за последние 30 дней",
}


def _format_score(score: str) -> str:
    return SCORE_CODE_TO_LABEL.get(score, score)


def _format_status(status: str | None) -> str:
    if status is None:
        return "—"
    return STATUS_CODE_TO_LABEL.get(status, status)


def _normalize_score(value: str) -> str | None:
    return SCORE_LABEL_TO_CODE.get(value.strip().lower())


def _normalize_status(value: str) -> str | None:
    return STATUS_LABEL_TO_CODE.get(value.strip().lower())


async def _ensure_owner(message: Message) -> bool:
    if message.from_user is None or message.from_user.id != settings.owner_id:
        await message.answer("Доступ закрыт.")
        return False
    return True


def _extract_payload(text: str, command: str) -> str:
    parts = text.split(maxsplit=1)
    if not parts:
        return ""
    command_name = parts[0].split("@", 1)[0]
    if command_name != command:
        return ""
    return parts[1].strip() if len(parts) > 1 else ""


def _parse_quick_payload(payload: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    normalized = payload.replace(";", "\n")
    for line in normalized.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        field = FIELD_MAP.get(key.strip().lower())
        if field:
            parsed[field] = value.strip()
    return parsed


def _parse_id_and_value(payload: str) -> tuple[int | None, str]:
    parts = payload.split(maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        return None, ""
    return int(parts[0]), parts[1].strip()


def _lead_short_card(lead: dict) -> str:
    city = lead.get("city") or "—"
    return (
        f"#{lead['id']} — {lead['company']}, {city}\n"
        f"Оценка: {_format_score(lead['score'])}\n"
        f"Статус: {_format_status(lead['status'])}"
    )


def _format_notes(lead_id: int, limit: int = 5) -> str:
    notes = list_lead_notes(lead_id, limit=limit)
    if not notes:
        return "—"
    return "\n\n".join(
        f"#{note['id']} от {note['created_at']}\n{note['note']}"
        for note in notes
    )


def _format_status_history(lead_id: int, limit: int = 10) -> str:
    history = list_status_history(lead_id, limit=limit)
    if not history:
        return "Истории статусов пока нет."
    return "\n".join(
        f"{item['created_at']}: "
        f"{_format_status(item['old_status'])} → "
        f"{_format_status(item['new_status'])}"
        for item in history
    )


def _clean(value: object) -> str:
    return str(value or "").strip()


def _company(lead: dict) -> str:
    return _clean(lead.get("company")) or "вашу компанию"


def _city_phrase(lead: dict) -> str:
    city = _clean(lead.get("city"))
    return f" в {city}" if city else ""


def _source_phrase(lead: dict) -> str:
    source = _clean(lead.get("source"))
    return f" через {source}" if source else ""


def _niche_phrase(lead: dict) -> str:
    niche = _clean(lead.get("niche")).lower()
    if "коф" in niche:
        return "кофейными автоматами"
    if "вендинг" in niche:
        return "вендингом"
    if niche:
        return niche
    return "кофейными автоматами или вендингом"


def _fit_reason_phrase(lead: dict) -> str:
    fit_reason = _clean(lead.get("fit_reason"))
    if not fit_reason:
        return ""
    return f"\n\nПочему пишу именно вам: {fit_reason}"


def _notes_context(notes: list[dict]) -> str:
    if not notes:
        return ""

    latest_note = _clean(notes[0].get("note"))
    if not latest_note:
        return ""

    return f"\n\nКонтекст по последнему контакту: {latest_note}"


def _build_first_message(lead: dict) -> str:
    company = _company(lead)
    city_phrase = _city_phrase(lead)
    source_phrase = _source_phrase(lead)
    niche_phrase = _niche_phrase(lead)
    fit_reason_phrase = _fit_reason_phrase(lead)

    return (
        "Здравствуйте.\n\n"
        f"Увидел {company}{city_phrase}{source_phrase}. "
        f"Правильно понимаю, вы занимаетесь {niche_phrase}?"
        f"{fit_reason_phrase}\n\n"
        "Я сделал Telegram-бота CoffeePulse для владельцев кофемашин: "
        "он показывает ежедневную выручку, примерную прибыль и предупреждает, "
        "если по точке долго нет продаж.\n\n"
        "Можно отправлю короткий пример отчета, чтобы вы за 1 минуту поняли, "
        "полезно ли это для ваших точек?"
    )


def _build_followup_message(lead: dict, notes: list[dict]) -> str:
    company = _company(lead)
    notes_context = _notes_context(notes)

    return (
        "Здравствуйте.\n\n"
        f"Возвращаюсь к вопросу по {company}."
        f"{notes_context}\n\n"
        "Суть CoffeePulse простая: владелец получает в Telegram ежедневный отчет "
        "по выручке, примерной прибыли и видит точки, где давно не было продаж.\n\n"
        "Подскажите, актуально посмотреть короткий пример такого отчета?"
    )


def _format_stats(stats: dict) -> str:
    status_counts = stats["status_counts"]
    scope_label = SCOPE_LABELS.get(stats["scope"], stats["scope"])

    return (
        f"Статистика лидов {scope_label}\n\n"
        f"Всего лидов: {stats['total']}\n\n"
        f"Новые: {status_counts['new']}\n"
        f"Кому написать: {status_counts['to_write']}\n"
        f"Написал: {status_counts['written']}\n"
        f"Ответили: {status_counts['replied']}\n"
        f"Демо: {status_counts['demo']}\n"
        f"Тест: {status_counts['trial']}\n"
        f"Отказ: {status_counts['rejected']}\n"
        f"Клиенты: {status_counts['client']}\n\n"
        f"Контактов сделано: {stats['contacted']}\n"
        f"Ответов: {stats['replied']}\n"
        f"Конверсия в ответ: {stats['reply_conversion']}%\n"
        f"Конверсия в клиента: {stats['client_conversion']}%"
    )


def _lead_full_card(lead: dict) -> str:
    return (
        f"Лид #{lead['id']}\n\n"
        f"Компания: {lead['company']}\n"
        f"Город: {lead.get('city') or ''}\n"
        f"Сфера: {lead.get('niche') or ''}\n"
        f"Источник: {lead.get('source') or ''}\n\n"
        f"Контакты: {lead.get('contacts') or ''}\n"
        f"Сайт: {lead.get('website') or ''}\n"
        f"Telegram: {lead.get('telegram') or ''}\n"
        f"VK: {lead.get('vk') or ''}\n\n"
        f"Почему подходит:\n{lead.get('fit_reason') or ''}\n\n"
        f"Оценка: {_format_score(lead['score'])}\n"
        f"Статус: {_format_status(lead['status'])}\n\n"
        f"Заметки из карточки:\n{lead.get('notes') or '—'}\n\n"
        f"Последние заметки:\n{_format_notes(lead['id'], limit=5)}\n\n"
        f"Создан: {lead['created_at']}\n"
        f"Обновлен: {lead['updated_at']}"
    )


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    await message.answer(
        "CoffeePulse Sales Assistant запущен.\n"
        "Доступные команды:\n"
        "/help"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    await message.answer(
        "CoffeePulse Sales Assistant — приватный помощник для ведения лидов CoffeePulse.\n"
        "В этом MVP бот помогает собирать лиды, готовить сообщения и вести статусы.\n"
        "\n"
        "/quick — быстро добавить лида\n"
        "/leads — последние лиды\n"
        "/lead ID — карточка лида\n"
        "/search текст — поиск лидов\n"
        "/status ID статус — изменить статус\n"
        "/score ID оценка — изменить оценку\n"
        "/note ID текст — добавить заметку\n"
        "/notes ID — последние заметки по лиду\n"
        "/history ID — история статусов\n"
        "/message ID — сгенерировать первое сообщение\n"
        "/followup ID — сгенерировать follow-up\n"
        "/stats — статистика за все время\n"
        "/stats week — статистика за 7 дней\n"
        "/stats month — статистика за 30 дней\n"
        "\n"
        "Автоматическая отправка сообщений лидам не используется."
    )


@router.message(Command("quick"))
async def cmd_quick(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/quick")
    parsed = _parse_quick_payload(payload)
    company = parsed.get("company", "").strip()

    if not company:
        await message.answer(
            "Компания обязательна.\n"
            "Пример:\n"
            "/quick Компания: КофеВенд; Город: Казань; Сфера: кофейные автоматы; Источник: 2ГИС"
        )
        return

    score = "medium"
    if parsed.get("score"):
        normalized_score = _normalize_score(parsed["score"])
        if normalized_score is None:
            await message.answer("Допустимые оценки: высокая, средняя, низкая, high, medium, low.")
            return
        score = normalized_score

    status = "new"
    if parsed.get("status"):
        normalized_status = _normalize_status(parsed["status"])
        if normalized_status is None:
            await message.answer("Допустимые статусы: новый, написать, написал, ответил, демо, тест, отказ, клиент.")
            return
        status = normalized_status

    try:
        lead = create_lead(
            company=company,
            city=parsed.get("city", ""),
            niche=parsed.get("niche", ""),
            source=parsed.get("source", ""),
            contacts=parsed.get("contacts", ""),
            website=parsed.get("website", ""),
            telegram=parsed.get("telegram", ""),
            vk=parsed.get("vk", ""),
            fit_reason=parsed.get("fit_reason", ""),
            score=score,
            status=status,
            notes=parsed.get("notes", ""),
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return

    await message.answer(
        f"Лид #{lead['id']} создан.\n\n"
        f"Компания: {lead['company']}\n"
        f"Город: {lead.get('city') or ''}\n"
        f"Сфера: {lead.get('niche') or ''}\n"
        f"Оценка: {_format_score(lead['score'])}\n"
        f"Статус: {_format_status(lead['status'])}"
    )


@router.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    leads = list_recent_leads(limit=10)
    if not leads:
        await message.answer("Лидов пока нет.")
        return

    cards = "\n\n".join(_lead_short_card(lead) for lead in leads)
    await message.answer(f"Последние лиды:\n\n{cards}")


@router.message(Command("lead"))
async def cmd_lead(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/lead")
    if not payload.isdigit():
        await message.answer("Использование: /lead 12")
        return

    lead = get_lead(int(payload))
    if lead is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(_lead_full_card(lead))


@router.message(Command("search"))
async def cmd_search(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/search")
    if not payload:
        await message.answer("Использование: /search Казань")
        return

    leads = search_leads(payload, limit=10)
    if not leads:
        await message.answer("Ничего не найдено.")
        return

    cards = "\n\n".join(_lead_short_card(lead) for lead in leads)
    await message.answer(f"Найдено:\n\n{cards}")


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    lead_id, status_raw = _parse_id_and_value(_extract_payload(message.text or "", "/status"))
    if lead_id is None:
        await message.answer("Использование: /status 12 написал")
        return

    status = _normalize_status(status_raw)
    if status is None:
        await message.answer("Допустимые статусы: new, to_write, written, replied, demo, trial, rejected, client.")
        return

    lead = update_lead_status(lead_id, status)
    if lead is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(f"Статус лида #{lead_id} изменен: {_format_status(status)}")


@router.message(Command("score"))
async def cmd_score(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    lead_id, score_raw = _parse_id_and_value(_extract_payload(message.text or "", "/score"))
    if lead_id is None:
        await message.answer("Использование: /score 12 высокая")
        return

    score = _normalize_score(score_raw)
    if score is None:
        await message.answer("Допустимые оценки: high, medium, low, высокая, средняя, низкая.")
        return

    lead = update_lead_score(lead_id, score)
    if lead is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(f"Оценка лида #{lead_id} изменена: {_format_score(score)}")


@router.message(Command("note"))
async def cmd_note(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    lead_id, note_text = _parse_id_and_value(_extract_payload(message.text or "", "/note"))
    if lead_id is None:
        await message.answer("Использование: /note 12 Текст заметки")
        return

    try:
        note = add_lead_note(lead_id, note_text)
    except ValueError:
        await message.answer("Текст заметки не может быть пустым.")
        return

    if note is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(
        f"Заметка #{note['id']} добавлена к лиду #{lead_id}.\n\n{note['note']}"
    )


@router.message(Command("notes"))
async def cmd_notes(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/notes")
    if not payload.isdigit():
        await message.answer("Использование: /notes 12")
        return

    lead_id = int(payload)
    if get_lead(lead_id) is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(f"Последние заметки по лиду #{lead_id}:\n\n{_format_notes(lead_id, limit=10)}")


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/history")
    if not payload.isdigit():
        await message.answer("Использование: /history 12")
        return

    lead_id = int(payload)
    if get_lead(lead_id) is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(f"История статусов лида #{lead_id}:\n\n{_format_status_history(lead_id)}")


@router.message(Command("message"))
async def cmd_message(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/message")
    if not payload.isdigit():
        await message.answer("Использование: /message 12")
        return

    lead_id = int(payload)
    lead = get_lead(lead_id)
    if lead is None:
        await message.answer("Лид не найден.")
        return

    await message.answer(
        f"Первое сообщение для лида #{lead_id}:\n\n"
        f"{_build_first_message(lead)}\n\n"
        "Отправка не выполнялась. Скопируйте текст и отправьте вручную."
    )


@router.message(Command("followup"))
async def cmd_followup(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/followup")
    if not payload.isdigit():
        await message.answer("Использование: /followup 12")
        return

    lead_id = int(payload)
    lead = get_lead(lead_id)
    if lead is None:
        await message.answer("Лид не найден.")
        return

    notes = list_lead_notes(lead_id, limit=3)
    await message.answer(
        f"Follow-up для лида #{lead_id}:\n\n"
        f"{_build_followup_message(lead, notes)}\n\n"
        "Отправка не выполнялась. Скопируйте текст и отправьте вручную."
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    payload = _extract_payload(message.text or "", "/stats").lower()
    scope = payload or "all"

    if scope not in {"all", "week", "month"}:
        await message.answer("Использование: /stats, /stats week или /stats month")
        return

    stats = get_stats(scope)
    await message.answer(_format_stats(stats))

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.lead_service import (
    create_lead,
    get_lead,
    list_recent_leads,
    search_leads,
    update_lead_score,
    update_lead_status,
)

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


def _format_score(score: str) -> str:
    return SCORE_CODE_TO_LABEL.get(score, score)


def _format_status(status: str) -> str:
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
        "\n"
        "Автоматическая холодная рассылка не используется."
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

    await message.answer(
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
        f"Заметки:\n{lead.get('notes') or ''}\n\n"
        f"Создан: {lead['created_at']}\n"
        f"Обновлен: {lead['updated_at']}"
    )


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

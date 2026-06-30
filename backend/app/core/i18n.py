"""Bot-side localization (RU/EN). No emoji anywhere, per TZ §17."""
from __future__ import annotations

TR: dict[str, dict[str, str]] = {
    # --- onboarding ---
    "welcome_title": {
        "ru": "NEBANK",
        "en": "NEBANK",
    },
    "welcome_body": {
        "ru": (
            "Личный финансовый помощник. Записывайте траты и доходы так, как удобно — "
            "текстом, голосом, фото чека или пересланной СМС из банка.\n\n"
            "Чат — быстрый слой: записать, посмотреть, поделиться. Приложение — полный дом: "
            "дашборд, история, бюджеты, цели, привычки, курсы.\n\n"
            "Для начала выберите язык и базовую валюту."
        ),
        "en": (
            "Your personal finance companion. Log spending and income the way that suits you — "
            "by text, voice, a photo of a receipt, or a forwarded bank SMS.\n\n"
            "Chat is the fast layer: capture, glance, share. The app is the full home: "
            "dashboard, history, budgets, goals, habits, rates.\n\n"
            "To begin, choose your language and base currency."
        ),
    },
    "choose_language": {"ru": "Язык", "en": "Language"},
    "choose_currency": {"ru": "Базовая валюта", "en": "Base currency"},
    "currency_set": {"ru": "Базовая валюта: {cur}", "en": "Base currency: {cur}"},
    "onboarding_done": {
        "ru": "Готово. Просто отправьте трату — например: кофе 200, такси 350.",
        "en": "All set. Just send an expense — for example: coffee 4, taxi 7.",
    },
    "open_app": {"ru": "Открыть приложение", "en": "Open app"},
    "open": {"ru": "Открыть", "en": "Open"},

    # --- capture ---
    "saved_one": {"ru": "Записано: {line}", "en": "Saved: {line}"},
    "saved_many": {"ru": "Записано {n} операций на {total}", "en": "Saved {n} entries, {total} total"},
    "undo": {"ru": "Отменить", "en": "Undo"},
    "change_category": {"ru": "Категория", "en": "Category"},
    "delete": {"ru": "Удалить", "en": "Delete"},
    "undone": {"ru": "Отменено", "en": "Undone"},
    "deleted": {"ru": "Удалено", "en": "Deleted"},
    "category_changed": {"ru": "Категория: {cat}", "en": "Category: {cat}"},
    "pick_category": {"ru": "Выберите категорию", "en": "Choose a category"},
    "not_understood": {
        "ru": "Не удалось распознать сумму. Пример: обед 450 или 0.0006 BTC.",
        "en": "Could not read an amount. Example: lunch 12 or 0.0006 BTC.",
    },
    "usdt_amount_q": {
        "ru": "Укажите сумму USDT для этой транзакции.",
        "en": "Please enter the USDT amount for this transaction.",
    },
    "sms_duplicate": {"ru": "Эта операция уже записана.", "en": "This entry was already recorded."},
    "photo_processing": {"ru": "Читаю изображение…", "en": "Reading the image…"},
    "voice_processing": {"ru": "Распознаю аудио…", "en": "Transcribing the audio…"},
    "voice_unavailable": {
        "ru": "Распознавание голоса сейчас недоступно на сервере. Напишите трату текстом.",
        "en": "Voice transcription is not available on the server. Please type the expense.",
    },

    # --- reports ---
    "report_now": {"ru": "Сегодня", "en": "Today"},
    "report_week": {"ru": "Неделя", "en": "Week"},
    "report_month": {"ru": "Месяц", "en": "Month"},
    "balance": {"ru": "Баланс", "en": "Balance"},
    "income": {"ru": "Доход", "en": "Income"},
    "expense": {"ru": "Расход", "en": "Expense"},
    "net": {"ru": "Итог", "en": "Net"},
    "no_data_period": {"ru": "За этот период операций нет.", "en": "No entries for this period."},
    "history_title": {"ru": "История", "en": "History"},
    "share_budget": {"ru": "Поделиться", "en": "Share"},
    "export_excel": {"ru": "Экспорт в Excel", "en": "Export to Excel"},
    "export_ready": {"ru": "Файл готов.", "en": "Your file is ready."},

    # --- settings ---
    "settings_title": {"ru": "Настройки", "en": "Settings"},
    "language_set": {"ru": "Язык: Русский", "en": "Language: English"},
    "menu_lang": {"ru": "Язык", "en": "Language"},
    "menu_currency": {"ru": "Валюта", "en": "Currency"},

    # --- premium ---
    "premium_title": {"ru": "NEBANK Premium", "en": "NEBANK Premium"},
    "premium_body": {
        "ru": (
            "Premium открывает: сканер чеков по фото и QR, авто-импорт из банковских уведомлений, "
            "расширенные отчёты, семейный доступ, достижения и экспорт, безлимит категорий и целей."
        ),
        "en": (
            "Premium unlocks: photo and QR receipt scanner, auto-import from bank notifications, "
            "advanced reports, family access, achievements and export, unlimited categories and goals."
        ),
    },
    "premium_buy": {"ru": "Оформить за {stars} Stars / мес", "en": "Subscribe for {stars} Stars / mo"},
    "premium_active": {"ru": "Premium активен до {date}.", "en": "Premium is active until {date}."},
    "premium_thanks": {
        "ru": "Спасибо. Premium активирован до {date}.",
        "en": "Thank you. Premium is active until {date}.",
    },
    "premium_only": {
        "ru": "Эта функция доступна в Premium.",
        "en": "This feature is available in Premium.",
    },

    # --- commands / misc ---
    "cmd_start": {"ru": "Начало и приветствие", "en": "Start and welcome"},
    "cmd_app": {"ru": "Открыть приложение", "en": "Open the app"},
    "cmd_report": {"ru": "Быстрый отчёт", "en": "Quick report"},
    "cmd_balance": {"ru": "Баланс", "en": "Balance"},
    "cmd_history": {"ru": "История по дням", "en": "History by day"},
    "cmd_export": {"ru": "Экспорт в Excel", "en": "Export to Excel"},
    "cmd_language": {"ru": "Сменить язык", "en": "Change language"},
    "cmd_currency": {"ru": "Базовая валюта", "en": "Base currency"},
    "cmd_premium": {"ru": "Premium-подписка", "en": "Premium subscription"},
    "cmd_help": {"ru": "Как пользоваться", "en": "How to use"},

    "help_body": {
        "ru": (
            "Отправьте трату текстом: кофе 200, такси 350.\n"
            "Голосом — наговорите сумму и место.\n"
            "Фото — сфотографируйте чек или QR.\n"
            "СМС из банка — просто перешлите её сюда.\n"
            "Крипто — пришлите ссылку на транзакцию.\n\n"
            "Команды: /report — отчёт, /balance — баланс, /history — история, /app — приложение."
        ),
        "en": (
            "Send an expense as text: coffee 4, taxi 7.\n"
            "By voice — say the amount and place.\n"
            "By photo — snap a receipt or QR code.\n"
            "Bank SMS — just forward it here.\n"
            "Crypto — send a transaction link.\n\n"
            "Commands: /report — report, /balance — balance, /history — history, /app — the app."
        ),
    },
    "choose_report_period": {"ru": "Выберите период", "en": "Choose a period"},
    "regular_or_once": {
        "ru": "Это регулярный платёж или разовый?",
        "en": "Is this a recurring payment or a one-off?",
    },
    "regular": {"ru": "Регулярный", "en": "Recurring"},
    "once": {"ru": "Разовый", "en": "One-off"},
    "sub_detected": {
        "ru": "Похоже на подписку: {name}. Напомнить перед следующим списанием?",
        "en": "Looks like a subscription: {name}. Remind you before the next charge?",
    },
    "yes": {"ru": "Да", "en": "Yes"},
    "no": {"ru": "Нет", "en": "No"},
    "remind_3d": {
        "ru": "Через 3 дня спишется подписка: {name}, {amount}.",
        "en": "In 3 days a subscription will charge: {name}, {amount}.",
    },
    "remind_1d": {
        "ru": "Завтра спишется подписка: {name}, {amount}.",
        "en": "Tomorrow a subscription will charge: {name}, {amount}.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = "ru" if lang == "ru" else "en"
    entry = TR.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text

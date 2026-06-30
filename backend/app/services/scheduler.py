"""Background jobs: subscription reminders 3d/1d before charge (TZ §12.4)."""
from __future__ import annotations

from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.bot.loader import bot
from app.core.currencies import fmt_amount
from app.core.i18n import t
from app.db import SessionLocal
from app.models import User
from app.services import subscriptions as subs

scheduler = AsyncIOScheduler()


async def reminder_tick() -> None:
    today = date.today()
    async with SessionLocal() as s:
        due = await subs.due_reminders(s, today)
        for sub, days_left in due:
            user = await s.get(User, sub.user_id)
            if not user:
                continue
            lang, cur = user.language, user.base_currency
            key = "remind_3d" if days_left == 3 else "remind_1d"
            text = t(lang, key, name=sub.name, amount=fmt_amount(float(sub.amount), sub.currency))
            try:
                await bot.send_message(user.telegram_id, text)
                if days_left == 3:
                    sub.remind_3d_sent_for = sub.next_charge
                else:
                    sub.remind_1d_sent_for = sub.next_charge
            except Exception:
                pass
        await s.commit()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(reminder_tick, "interval", hours=6, id="reminders", replace_existing=True)
        scheduler.start()

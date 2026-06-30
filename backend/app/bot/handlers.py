"""NEBANK bot handlers — the chat fast layer (TZ §2,4–11,14)."""
from __future__ import annotations

from datetime import date

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, LabeledPrice

from app.bot.keyboards import (
    after_capture_kb, category_pick_kb, currency_kb, language_kb, open_app_kb,
    period_kb, premium_kb, regular_once_kb,
)
from app.bot.loader import bot, dp
from app.bot.menu import set_user_commands
from app.bot.states import Capture
from app.bot.utils import get_or_create_user, line_for
from app.config import settings
from app.core.currencies import CRYPTO, fmt_amount
from app.core.i18n import t
from app.db import SessionLocal
from app.models import (
    Category, FamilyGroup, FamilyMember, Subscription, SubPeriod, Transaction,
    TxKind, TxSource, utcnow,
)
from app.services import payments, reports
from app.services import subscriptions as subs
from app.services import analytics
from app.services.categories import list_categories
from app.services.crypto import parse_crypto_link
from app.services.ocr import recognize
from app.services.parser import parse_bank_sms, parse_message
from app.services.parser.expense_parser import ParsedEntry
from app.services.transactions import create_transaction
from app.services.voice import transcribe
from sqlalchemy import select

router = Router()


# --------------------------------------------------------------- onboarding
@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandStart, state: FSMContext):
    await state.clear()
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        # deep-link payloads: family invite / referral
        payload = (command.args or "").strip()
        if payload.startswith("fam_"):
            code = payload[4:]
            group = (await s.execute(select(FamilyGroup).where(FamilyGroup.invite_code == code))).scalar_one_or_none()
            if group:
                exists = (await s.execute(select(FamilyMember).where(
                    FamilyMember.group_id == group.id, FamilyMember.user_id == user.id))).scalar_one_or_none()
                if not exists:
                    s.add(FamilyMember(group_id=group.id, user_id=user.id, role="member"))
        elif payload.startswith("ref_") and not user.referred_by:
            user.referred_by = payload[4:][:32]
        await s.commit()
        lang = user.language
        cur = user.base_currency

    await set_user_commands(message.chat.id, lang)
    text = f"<b>{t(lang,'welcome_title')}</b>\n\n{t(lang,'welcome_body')}"
    await message.answer(text)
    await message.answer(t(lang, "choose_language"), reply_markup=language_kb(lang))
    await message.answer(t(lang, "choose_currency"), reply_markup=currency_kb(cur))


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(cb: types.CallbackQuery):
    lang = cb.data.split(":")[1]
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        user.language = lang
        user.voice_lang = lang
        await s.commit()
    await set_user_commands(cb.message.chat.id, lang)
    try:
        await cb.message.edit_reply_markup(reply_markup=language_kb(lang))
    except Exception:
        pass
    await cb.answer(t(lang, "language_set"))


@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(cb: types.CallbackQuery):
    code = cb.data.split(":")[1]
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        user.base_currency = code
        first_time = not user.onboarded
        user.onboarded = True
        await s.commit()
        lang = user.language
    try:
        await cb.message.edit_reply_markup(reply_markup=currency_kb(code))
    except Exception:
        pass
    await cb.answer(t(lang, "currency_set", cur=code))
    if first_time:
        await cb.message.answer(t(lang, "onboarding_done"), reply_markup=open_app_kb(lang))


# ----------------------------------------------------------------- commands
@router.message(Command("app"))
async def cmd_app(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    await message.answer(t(user.language, "open_app"), reply_markup=open_app_kb(user.language))


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    await message.answer(t(user.language, "help_body"))


@router.message(Command("language"))
async def cmd_language(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    await message.answer(t(user.language, "menu_lang"), reply_markup=language_kb(user.language))


@router.message(Command("currency"))
async def cmd_currency(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    await message.answer(t(user.language, "menu_currency"), reply_markup=currency_kb(user.base_currency))


@router.message(Command("report"))
async def cmd_report(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    await message.answer(t(user.language, "choose_report_period"), reply_markup=period_kb(user.language))


@router.callback_query(F.data.startswith("rep:"))
async def cb_report(cb: types.CallbackQuery):
    period = cb.data.split(":")[1]
    await cb.answer()
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        start, end = analytics.period_bounds(period)
        tot = await analytics.totals(s, user.id, start, end)
        cats = await analytics.by_category(s, user.id, start, end, TxKind.expense)
        await s.commit()
        lang, cur = user.language, user.base_currency
    png = reports.render_report(period=period, lang=lang, currency=cur,
                                income=tot.income, expense=tot.expense, categories=cats)
    caption = (f"{t(lang,'expense')}: {fmt_amount(tot.expense,cur)}   "
               f"{t(lang,'income')}: {fmt_amount(tot.income,cur)}   "
               f"{t(lang,'net')}: {fmt_amount(tot.net,cur)}")
    await cb.message.answer_photo(BufferedInputFile(png, "report.png"), caption=caption,
                                  reply_markup=open_app_kb(lang))


@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        start, end = analytics.period_bounds("month")
        tot = await analytics.totals(s, user.id, start, end)
        await s.commit()
        lang, cur = user.language, user.base_currency
    await message.answer(
        f"<b>{t(lang,'balance')}</b>\n"
        f"{t(lang,'income')}: {fmt_amount(tot.income,cur)}\n"
        f"{t(lang,'expense')}: {fmt_amount(tot.expense,cur)}\n"
        f"{t(lang,'net')}: {fmt_amount(tot.net,cur)}",
        reply_markup=open_app_kb(lang))


@router.message(Command("history"))
async def cmd_history(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        rows = (await s.execute(
            select(Transaction, Category.name).outerjoin(Category, Category.id == Transaction.category_id)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.occurred_at.desc(), Transaction.id.desc()).limit(15))).all()
        await s.commit()
        lang, cur = user.language, user.base_currency
    if not rows:
        await message.answer(t(lang, "no_data_period"), reply_markup=open_app_kb(lang))
        return
    lines = [f"<b>{t(lang,'history_title')}</b>"]
    last_day = None
    for tx, cat in rows:
        if tx.occurred_at != last_day:
            lines.append(f"\n<b>{tx.occurred_at.isoformat()}</b>")
            last_day = tx.occurred_at
        sign = "+" if tx.kind == TxKind.income else "−"
        lines.append(f"{sign} {fmt_amount(float(tx.amount),cur)} · {tx.title or cat or ''}")
    await message.answer("\n".join(lines), reply_markup=open_app_kb(lang))


@router.message(Command("export"))
async def cmd_export(message: types.Message):
    from app.services.export import export_xlsx
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        prem = payments.is_premium(user)
        lang = user.language
        if not prem:
            await s.commit()
            await message.answer(t(lang, "premium_only"), reply_markup=premium_kb(lang, settings.premium_price_stars))
            return
        data = await export_xlsx(s, user.id, user.base_currency, lang)
        await s.commit()
    await message.answer_document(BufferedInputFile(data, "nebank-export.xlsx"),
                                  caption=t(lang, "export_ready"))


# ------------------------------------------------------------------ premium
@router.message(Command("premium"))
async def cmd_premium(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
        lang = user.language
        if payments.is_premium(user):
            await message.answer(t(lang, "premium_active",
                                   date=user.premium_until.date().isoformat()))
            return
    await message.answer(f"<b>{t(lang,'premium_title')}</b>\n\n{t(lang,'premium_body')}",
                         reply_markup=premium_kb(lang, settings.premium_price_stars))


@router.callback_query(F.data == "buy_premium")
async def cb_buy_premium(cb: types.CallbackQuery):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        await s.commit()
        lang = user.language
    await cb.answer()
    await bot.send_invoice(
        chat_id=cb.message.chat.id,
        title=t(lang, "premium_title"),
        description=t(lang, "premium_body"),
        payload=payments.PREMIUM_PAYLOAD,
        currency="XTR",
        prices=[LabeledPrice(label="NEBANK Premium", amount=settings.premium_price_stars)],
    )


@router.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(message: types.Message):
    sp = message.successful_payment
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await payments.activate_premium(s, user, sp.total_amount,
                                        sp.telegram_payment_charge_id)
        await s.commit()
        lang = user.language
        until = user.premium_until.date().isoformat()
    await message.answer(t(lang, "premium_thanks", date=until), reply_markup=open_app_kb(lang))


# ------------------------------------------------------- capture: helpers
async def _commit_entries(message: types.Message, entries: list[ParsedEntry], source: TxSource,
                          dedup: str | None = None):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        lang, cur = user.language, user.base_currency
        created: list[Transaction] = []
        for e in entries:
            tx = await create_transaction(s, user, e, source=source, dedup_hash=dedup)
            if tx:
                created.append(tx)
        if not created and dedup:
            await s.commit()
            await message.answer(t(lang, "sms_duplicate"))
            return
        await s.commit()
        ids = [tx.id for tx in created]
        # subscription question if any landed in Subscriptions category
        sub_tx = None
        for tx in created:
            cat = await s.get(Category, tx.category_id) if tx.category_id else None
            if cat and cat.name.lower() in ("subscriptions", "подписки"):
                sub_tx = tx
        total = sum(float(tx.amount) for tx in created)

    if not created:
        await message.answer(t(lang, "not_understood"))
        return

    if len(created) == 1:
        e = entries[0]
        text = t(lang, "saved_one", line=line_for(e, cur))
    else:
        text = t(lang, "saved_many", n=len(created), total=fmt_amount(total, cur))
    await message.answer(text, reply_markup=after_capture_kb(lang, ids))

    if sub_tx is not None:
        await message.answer(t(lang, "regular_or_once"), reply_markup=regular_once_kb(lang, sub_tx.id))


# ---------------------------------------------------------------- voice
@router.message(F.voice | F.audio)
async def on_voice(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
        lang, voice_lang = user.language, user.voice_lang
    note = await message.answer(t(lang, "voice_processing"))
    file_id = message.voice.file_id if message.voice else message.audio.file_id
    tg_file = await bot.get_file(file_id)
    buf = await bot.download_file(tg_file.file_path)
    audio = buf.read()
    text = await transcribe(audio, voice_lang)
    try:
        await note.delete()
    except Exception:
        pass
    if not text:
        await message.answer(t(lang, "voice_unavailable"))
        return
    entries = parse_message(text, user.base_currency)
    if not entries:
        await message.answer(t(lang, "not_understood"))
        return
    await _commit_entries(message, entries, TxSource.voice)


# ---------------------------------------------------------------- photo
@router.message(F.photo | F.document)
async def on_photo(message: types.Message):
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
        lang, cur = user.language, user.base_currency
    note = await message.answer(t(lang, "photo_processing"))
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and (message.document.mime_type or "").startswith("image"):
        file_id = message.document.file_id
    else:
        try:
            await note.delete()
        except Exception:
            pass
        await message.answer(t(lang, "not_understood"))
        return
    tg_file = await bot.get_file(file_id)
    buf = await bot.download_file(tg_file.file_path)
    image_bytes = buf.read()

    entries: list[ParsedEntry] = []

    # 1) Best quality: vision model (only if an LLM key is configured).
    from app.services.vision import extract_from_image
    entries = await extract_from_image(image_bytes, cur, lang)

    # 2) Free fallback: Tesseract + QR.
    res = recognize(image_bytes) if not entries else None
    try:
        await note.delete()
    except Exception:
        pass

    if not entries and res is not None:
        from app.services.ocr import qr_to_amount
        receipt = "Чек" if lang == "ru" else "Receipt"
        # QR amount first (FNS receipts etc.)
        for payload in res.qr:
            amt = qr_to_amount(payload)
            if amt:
                entries.append(ParsedEntry(amount=amt, currency=cur, kind="expense",
                                           title=receipt, occurred_at=date.today(), raw=payload))
        if not entries and res.lines:
            # try parse each line; else use the receipt total
            for ln in res.lines:
                for e in parse_message(ln, cur):
                    if e.title:
                        entries.append(e)
            if not entries and res.total:
                entries.append(ParsedEntry(amount=res.total, currency=cur, kind="expense",
                                           title=receipt, occurred_at=date.today(), raw=res.text[:200]))
    if not entries:
        await message.answer(t(lang, "not_understood"))
        return
    await _commit_entries(message, entries[:10], TxSource.photo)


# ------------------------------------------------------- text (last resort)
@router.message(F.text, Capture.await_crypto_amount)
async def on_crypto_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    from app.services.parser.numbers import find_amount
    amt, _ = find_amount(message.text)
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
    if not amt:
        await message.answer(t(user.language, "not_understood"))
        return
    entry = ParsedEntry(amount=amt, currency=data["coin"], kind="expense",
                        title=data.get("coin"), occurred_at=date.today(),
                        crypto_network=data.get("network"), raw=data.get("txid", ""))
    await _commit_entries(message, [entry], TxSource.crypto)


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    async with SessionLocal() as s:
        user = await get_or_create_user(s, message.from_user)
        await s.commit()
        lang, cur = user.language, user.base_currency

    # 1) crypto transaction link
    if "http" in text.lower() or len(text) == 64 or text.startswith("0x"):
        ctx = await parse_crypto_link(text)
        if ctx:
            if ctx.needs_amount:
                await state.set_state(Capture.await_crypto_amount)
                await state.update_data(coin=ctx.coin, network=ctx.network, txid=ctx.txid)
                hint = t(lang, "usdt_amount_q") if ctx.coin == "USDT" else \
                    (f"Укажите сумму {ctx.coin}." if lang == "ru" else f"Enter the {ctx.coin} amount.")
                await message.answer(hint)
                return
            entry = ParsedEntry(amount=ctx.amount, currency=ctx.coin, kind="expense",
                                title=ctx.coin, occurred_at=date.today(),
                                crypto_network=ctx.network, raw=ctx.txid)
            await _commit_entries(message, [entry], TxSource.crypto)
            return

    # 2) forwarded bank SMS / push
    if message.forward_origin or message.forward_date:
        sms = parse_bank_sms(text, cur)
        if sms:
            entry = ParsedEntry(amount=sms.amount, currency=sms.currency, kind=sms.kind,
                                title=sms.merchant, occurred_at=date.today(), raw=text)
            await _commit_entries(message, [entry], TxSource.sms, dedup=sms.dedup_hash)
            return

    # 3) inline SMS pattern (not forwarded but looks like a bank SMS)
    sms = parse_bank_sms(text, cur)
    if sms and (sms.merchant or "bank" in text.lower() or "карт" in text.lower()):
        entry = ParsedEntry(amount=sms.amount, currency=sms.currency, kind=sms.kind,
                            title=sms.merchant, occurred_at=date.today(), raw=text)
        await _commit_entries(message, [entry], TxSource.sms, dedup=sms.dedup_hash)
        return

    # 4) plain expense/income text (multi-entry aware)
    entries = parse_message(text, cur)
    if not entries:
        await message.answer(t(lang, "not_understood"))
        return
    await _commit_entries(message, entries, TxSource.text)


# ------------------------------------------------------------- callbacks
def _parse_ids(s: str) -> list[int]:
    return [int(x) for x in s.split(",") if x.strip().isdigit()]


@router.callback_query(F.data.startswith("undo:"))
async def cb_undo(cb: types.CallbackQuery):
    ids = _parse_ids(cb.data.split(":", 1)[1])
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        for tx in (await s.execute(select(Transaction).where(
                Transaction.id.in_(ids), Transaction.user_id == user.id))).scalars():
            await s.delete(tx)
        await s.commit()
        lang = user.language
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.answer(t(lang, "undone"))
    await cb.message.answer(t(lang, "undone"))


@router.callback_query(F.data.startswith("del:"))
async def cb_del(cb: types.CallbackQuery):
    await cb_undo(cb)


@router.callback_query(F.data.startswith("cat:"))
async def cb_cat(cb: types.CallbackQuery):
    ids = _parse_ids(cb.data.split(":", 1)[1])
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        cats = await list_categories(s, user.id, TxKind.expense)
        await s.commit()
        lang = user.language
    await cb.answer()
    await cb.message.answer(t(lang, "pick_category"),
                            reply_markup=category_pick_kb(lang, cats, ids))


@router.callback_query(F.data.startswith("setcat:"))
async def cb_setcat(cb: types.CallbackQuery):
    _, cat_id, ids = cb.data.split(":", 2)
    cat_id = int(cat_id)
    ids = _parse_ids(ids)
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        cat = await s.get(Category, cat_id)
        if not cat or cat.user_id != user.id:
            await cb.answer()
            return
        for tx in (await s.execute(select(Transaction).where(
                Transaction.id.in_(ids), Transaction.user_id == user.id))).scalars():
            tx.category_id = cat_id
        await s.commit()
        lang = user.language
        name = cat.name
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.answer(t(lang, "category_changed", cat=name))
    await cb.message.answer(t(lang, "category_changed", cat=name))


@router.callback_query(F.data.startswith("reg:"))
async def cb_regular(cb: types.CallbackQuery):
    _, tx_id, is_reg = cb.data.split(":")
    async with SessionLocal() as s:
        user = await get_or_create_user(s, cb.from_user)
        tx = await s.get(Transaction, int(tx_id))
        lang = user.language
        if tx and tx.user_id == user.id and is_reg == "1":
            nc = subs.next_charge(SubPeriod.monthly, tx.occurred_at)
            s.add(Subscription(user_id=user.id, category_id=tx.category_id,
                               name=tx.title or "Subscription", amount=float(tx.amount),
                               currency=user.base_currency, period=SubPeriod.monthly,
                               next_charge=nc, fingerprint=subs.fingerprint(tx.title, float(tx.amount))))
        await s.commit()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.answer(t(lang, "yes") if is_reg == "1" else t(lang, "no"))


def register_handlers() -> None:
    dp.include_router(router)

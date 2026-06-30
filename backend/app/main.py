"""NEBANK service: FastAPI (Mini App API + static) + Telegram bot webhook."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.bot.handlers import register_handlers
from app.bot.loader import bot, dp
from app.bot.menu import set_default_commands
from app.config import settings
from app.db import Base, engine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nebank")

STATIC_DIR = os.environ.get("MINIAPP_DIR", "/app/miniapp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables (idempotent) — robust v1 bootstrap
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    register_handlers()

    if settings.bot_token:
        try:
            await set_default_commands()
        except Exception as exc:  # pragma: no cover
            log.warning("set_my_commands failed: %s", exc)
        if settings.use_webhook:
            try:
                await bot.set_webhook(
                    settings.webhook_url,
                    secret_token=settings.webhook_secret,
                    drop_pending_updates=True,
                    allowed_updates=dp.resolve_used_update_types(),
                )
                log.info("webhook set: %s", settings.webhook_url)
            except Exception as exc:  # pragma: no cover
                log.warning("set_webhook failed: %s", exc)
        from app.services.scheduler import start_scheduler
        start_scheduler()
    else:
        log.warning("BOT_TOKEN is empty — bot disabled; API still serves.")

    yield

    try:
        await bot.session.close()
    except Exception:
        pass


app = FastAPI(title="NEBANK", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "nebank"}


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request,
                           x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="bad secret")
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


# ---- static Mini App (SPA) ----
if os.path.isdir(STATIC_DIR):
    assets = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets):
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        if full_path.startswith(("api", "bot", "healthz", "assets")):
            raise HTTPException(status_code=404)
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

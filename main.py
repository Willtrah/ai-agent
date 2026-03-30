import asyncio
import logging
import os
import threading
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()

# ---------- Logging ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai-agent")

# ---------- Environment ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-2.5-flash")
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "/app/memory.db")
LOW_RAM_MODE = os.getenv("LOW_RAM_MODE", "true").lower() == "true"
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "3"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))
MAX_MEMORY_ITEMS = int(os.getenv("MAX_MEMORY_ITEMS", "10000"))
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))
TELEGRAM_ALLOWED_USERS_RAW = os.getenv("TELEGRAM_ALLOWED_USERS", "")
TELEGRAM_ALLOWED_USERS = {
    int(x.strip()) for x in TELEGRAM_ALLOWED_USERS_RAW.split(",") if x.strip().isdigit()
}

# ---------- App ----------
app = Flask(__name__)

BOOT_STATE: dict[str, Any] = {
    "booted": False,
    "telegram_started": False,
    "last_heartbeat": None,
    "last_error": None,
}


def env_report() -> dict[str, Any]:
    return {
        "telegram": bool(TELEGRAM_BOT_TOKEN),
        "openai": bool(OPENAI_API_KEY),
        "gemini": bool(GEMINI_API_KEY),
        "anthropic": bool(ANTHROPIC_API_KEY),
        "default_model": DEFAULT_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "memory_db_path": MEMORY_DB_PATH,
        "low_ram_mode": LOW_RAM_MODE,
        "max_concurrent_agents": MAX_CONCURRENT_AGENTS,
        "batch_size": BATCH_SIZE,
        "max_memory_items": MAX_MEMORY_ITEMS,
        "agent_timeout": AGENT_TIMEOUT,
        "allowed_users_count": len(TELEGRAM_ALLOWED_USERS),
    }


@app.get("/")
def home():
    return "AI Agent Running", 200


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "boot_state": BOOT_STATE,
            "env": env_report(),
        }
    )


@app.get("/status")
def status():
    return jsonify(
        {
            "message": "AI Multi-Agent System Started",
            "boot_state": BOOT_STATE,
            "env": env_report(),
        }
    )


# ---------- Background Worker ----------
def heartbeat_loop() -> None:
    logger.info("Background heartbeat worker started")
    while True:
        try:
            BOOT_STATE["last_heartbeat"] = int(time.time())
            logger.info("Heartbeat OK")
            time.sleep(60)
        except Exception as exc:  # pragma: no cover
            BOOT_STATE["last_error"] = str(exc)
            logger.exception("Heartbeat loop error: %s", exc)
            time.sleep(10)


# ---------- Telegram Bot ----------
def start_telegram_bot() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN missing; Telegram bot disabled")
        return

    try:
        from telegram import Update
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except Exception as exc:  # pragma: no cover
        BOOT_STATE["last_error"] = f"telegram import error: {exc}"
        logger.exception("Telegram imports failed")
        return

    async def reject_if_not_allowed(update: Update) -> bool:
        user = update.effective_user
        if not user:
            return True
        if TELEGRAM_ALLOWED_USERS and user.id not in TELEGRAM_ALLOWED_USERS:
            if update.message:
                await update.message.reply_text("Accès refusé.")
            return True
        return False

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_not_allowed(update):
            return
        await update.message.reply_text(
            "AI-System actif. Commandes: /status /health /ping"
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_not_allowed(update):
            return
        text = (
            "STATUT SYSTÈME\n"
            f"OpenAI: {'OK' if OPENAI_API_KEY else 'MANQUANT'}\n"
            f"Gemini: {'OK' if GEMINI_API_KEY else 'MANQUANT'}\n"
            f"Claude: {'OK' if ANTHROPIC_API_KEY else 'MANQUANT'}\n"
            f"Default model: {DEFAULT_MODEL}\n"
            f"Fallback model: {FALLBACK_MODEL}\n"
            f"Heartbeat: {BOOT_STATE['last_heartbeat']}"
        )
        await update.message.reply_text(text)

    async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_not_allowed(update):
            return
        await update.message.reply_text("/health disponible sur Railway")

    async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_not_allowed(update):
            return
        await update.message.reply_text("pong")

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_not_allowed(update):
            return
        user_text = update.message.text if update.message else ""
        await update.message.reply_text(
            "Requête reçue. Infrastructure active.\n"
            f"Message: {user_text[:500]}"
        )

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        BOOT_STATE["last_error"] = str(context.error)
        logger.exception("Telegram handler error: %s", context.error)

    async def runner() -> None:
        app_tg = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app_tg.add_handler(CommandHandler("start", cmd_start))
        app_tg.add_handler(CommandHandler("status", cmd_status))
        app_tg.add_handler(CommandHandler("health", cmd_health))
        app_tg.add_handler(CommandHandler("ping", cmd_ping))
        app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app_tg.add_error_handler(error_handler)

        logger.info("Starting Telegram polling...")
        BOOT_STATE["telegram_started"] = True
        await app_tg.initialize()
        await app_tg.start()
        await app_tg.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(3600)

    try:
        asyncio.run(runner())
    except Exception as exc:  # pragma: no cover
        BOOT_STATE["telegram_started"] = False
        BOOT_STATE["last_error"] = f"telegram runtime error: {exc}"
        logger.exception("Telegram bot crashed: %s", exc)


def boot_once() -> None:
    if BOOT_STATE["booted"]:
        return

    logger.info("AI Multi-Agent System Started")
    logger.info("Environment report: %s", env_report())

    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY missing")
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY missing")
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY missing")

    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    telegram_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    telegram_thread.start()

    BOOT_STATE["booted"] = True


boot_once()

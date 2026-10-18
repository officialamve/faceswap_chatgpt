import asyncio, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .config import Settings
from .handlers import start, help_cmd, status, reset, cancel, text_message, photo_message, process_queue
from .state import ConversationStore
from .jobs import JobManager
from .face_swap import InsightFaceEngine
from .storage import cleanup_abandoned
from .logging_config import configure_logging

settings = Settings.from_env()
configure_logging(settings.log_level)
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_abandoned(settings.temp_dir)
    tg = Application.builder().token(settings.bot_token).build()
    tg.bot_data["settings"] = settings
    tg.bot_data["flows"] = ConversationStore()
    tg.bot_data["jobs"] = JobManager(queue_size=1)
    tg.add_handler(CommandHandler("start", start))
    tg.add_handler(CommandHandler("help", help_cmd))
    tg.add_handler(CommandHandler("status", status))
    tg.add_handler(CommandHandler("reset", reset))
    tg.add_handler(CommandHandler("cancel", cancel))
    tg.add_handler(MessageHandler(filters.PHOTO, photo_message))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    await tg.initialize()
    await tg.start()
    app.state.telegram = tg
    app.state.worker = None
    app.state.ready = False
    # Fail closed when weights are absent/incompatible, but keep liveness endpoint available.
    try:
        engine = InsightFaceEngine(settings.source_face_model, settings.swap_model)
        tg.bot_data["engine"] = engine
        await tg.bot.set_webhook(url=f"{settings.webhook_url}/telegram/webhook", secret_token=settings.webhook_secret, allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)
        app.state.worker = asyncio.create_task(process_queue(tg), name="face-swap-worker")
        app.state.ready = True
    except Exception:
        log.exception("Inference engine is not ready; supply compatible, licensed model files and redeploy")
        tg.bot_data["engine"] = None
    try:
        yield
    finally:
        app.state.ready = False
        worker = getattr(app.state, "worker", None)
        if worker is not None:
            worker.cancel()
            try: await worker
            except asyncio.CancelledError: pass
        try: await tg.bot.delete_webhook(drop_pending_updates=False)
        except Exception: log.exception("Could not delete webhook during shutdown")
        await tg.stop()
        await tg.shutdown()

app = FastAPI(title="Private Face Swap Telegram Bot", docs_url=None, redoc_url=None, lifespan=lifespan)
@app.get("/healthz")
async def healthz(): return {"status": "ok"}
@app.get("/readyz")
async def readyz():
    if not getattr(app.state, "ready", False): raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready"}
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="forbidden")
    try: payload = await request.json()
    except Exception: raise HTTPException(status_code=400, detail="invalid update")
    tg = getattr(request.app.state, "telegram", None)
    if tg is None or not getattr(request.app.state, "ready", False): raise HTTPException(status_code=503, detail="not ready")
    update_id = payload.get("update_id") if isinstance(payload, dict) else None
    if isinstance(update_id, int):
        seen = tg.bot_data["jobs"].seen_updates
        if update_id in seen: return {"ok": True, "duplicate": True}
        seen.add(update_id)
        if len(seen) > 10000: seen.clear(); seen.add(update_id)
    try:
        update = Update.de_json(payload, tg.bot)
        # Telegram retries may deliver duplicate update IDs. PTB update processing is serialized here;
        # media/job duplicate protection is handled by one active job per admin.
        await tg.process_update(update)
    except Exception as exc:
        log.warning("Webhook update rejected (%s)", type(exc).__name__)
        raise HTTPException(status_code=400, detail="invalid update")
    return {"ok": True}

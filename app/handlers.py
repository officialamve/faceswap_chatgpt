import asyncio, logging, time
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from .authorization import is_admin
from .state import FlowState
from .image_utils import validate_image, normalize_image, ImageValidationError
from .storage import make_workspace, cleanup
from .jobs import Job
from .face_swap import FaceSwapError

log = logging.getLogger(__name__)
MENU = ReplyKeyboardMarkup([[KeyboardButton("Start Face Swap"), KeyboardButton("Cancel Current Job")], [KeyboardButton("Help"), KeyboardButton("Bot Status")]], resize_keyboard=True)

def allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user or not is_admin(user.id, context.application.bot_data["settings"].admin_id):
        if update.effective_message: asyncio.create_task(update.effective_message.reply_text("This bot is private and unavailable."))
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    await update.effective_message.reply_text("Private face-swap bot. Use only images you have rights and consent to use. Your local temporary files are deleted after processing.", reply_markup=MENU)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    await update.effective_message.reply_text("Press Start Face Swap, send one source-face photo, then one target photo. /cancel stops a queued job where possible; native inference may not stop instantly. /reset clears your workflow. /status shows service status.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    manager = context.application.bot_data["jobs"]
    await update.effective_message.reply_text(f"Bot online. Active job: {'yes' if update.effective_user.id in manager.active else 'no'}. Queue: {manager.queue.qsize()}.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    state = context.application.bot_data["flows"]
    state.reset(update.effective_user.id)
    workspace = context.user_data.pop("workspace", None)
    if workspace: cleanup(Path(workspace))
    context.user_data.clear()
    await update.effective_message.reply_text("Workflow reset and temporary inputs removed.", reply_markup=MENU)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    manager = context.application.bot_data["jobs"]
    cancelled = manager.cancel(update.effective_user.id)
    workspace = context.user_data.pop("workspace", None)
    if workspace and not manager.active.get(update.effective_user.id): cleanup(Path(workspace))
    context.application.bot_data["flows"].set(update.effective_user.id, FlowState.CANCELLED)
    await update.effective_message.reply_text("Cancellation requested." if cancelled else "No active job to cancel.", reply_markup=MENU)

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    text = (update.effective_message.text or "").strip()
    flow = context.application.bot_data["flows"]
    uid = update.effective_user.id
    if text == "Start Face Swap":
        workspace = context.user_data.pop("workspace", None)
        if workspace: cleanup(Path(workspace))
        context.user_data["workspace"] = str(make_workspace(context.application.bot_data["settings"].temp_dir))
        flow.set(uid, FlowState.SOURCE)
        await update.effective_message.reply_text("Send the source-face photograph (exactly one face).")
    elif text == "Cancel Current Job": await cancel(update, context)
    elif text == "Help": await help_cmd(update, context)
    elif text == "Bot Status": await status(update, context)
    else: await update.effective_message.reply_text("Choose Start Face Swap or use /help.", reply_markup=MENU)

async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update, context): return
    uid = update.effective_user.id
    flow = context.application.bot_data["flows"]
    current = flow.get(uid)
    if current not in {FlowState.SOURCE, FlowState.TARGET}:
        await update.effective_message.reply_text("Press Start Face Swap first.", reply_markup=MENU); return
    settings = context.application.bot_data["settings"]
    workspace = Path(context.user_data.get("workspace", ""))
    if not workspace.is_dir():
        await update.effective_message.reply_text("Workflow expired. Press Start Face Swap again."); flow.reset(uid); return
    photo = update.effective_message.photo[-1]
    if photo.file_size and photo.file_size > settings.max_input_bytes:
        await update.effective_message.reply_text("Image is too large. Send a smaller image."); return
    filename = "source.jpg" if current == FlowState.SOURCE else "target.jpg"
    path = workspace / filename
    try:
        tgfile = await context.bot.get_file(photo.file_id, read_timeout=settings.download_timeout, connect_timeout=settings.download_timeout)
        await tgfile.download_to_drive(custom_path=path, read_timeout=settings.download_timeout, write_timeout=settings.download_timeout)
        validate_image(path, max_bytes=settings.max_input_bytes, max_pixels=settings.max_image_pixels, max_dimension=settings.max_image_dimension)
        normalized = path.with_name(path.stem + ".normalized.jpg")
        normalize_image(path, normalized)
        normalized.replace(path)
    except Exception as exc:
        path.unlink(missing_ok=True)
        log.warning("Image receipt failed: %s", type(exc).__name__)
        await update.effective_message.reply_text("Could not accept that image. Send a valid JPEG/PNG/WebP image within the configured limits."); return
    if current == FlowState.SOURCE:
        flow.set(uid, FlowState.TARGET)
        await update.effective_message.reply_text("Source received. Now send the target photograph (exactly one face).")
        return
    manager = context.application.bot_data["jobs"]
    job = Job(uid, workspace / "source.jpg", path)
    try: manager.enqueue(job)
    except RuntimeError as exc:
        await update.effective_message.reply_text(str(exc)); return
    flow.set(uid, FlowState.QUEUED)
    await update.effective_message.reply_text("Processing started. I'll send the result when it is validated.")

async def process_queue(application):
    settings = application.bot_data["settings"]
    engine = application.bot_data["engine"]
    manager = application.bot_data["jobs"]
    while True:
        job = await manager.queue.get()
        start = time.monotonic()
        output = job.target.parent / "result.jpg"
        try:
            if job.cancelled: continue
            application.bot_data["flows"].set(job.user_id, FlowState.PROCESSING)
            job.task = asyncio.current_task()
            await asyncio.wait_for(asyncio.to_thread(engine.swap, job.source, job.target, output), timeout=max(0.1, settings.processing_timeout - (time.monotonic() - start)))
            if job.cancelled or time.monotonic() - start > settings.processing_timeout: raise asyncio.TimeoutError
            validate_image(output, max_bytes=settings.max_input_bytes * 2, max_pixels=settings.max_image_pixels, max_dimension=settings.max_image_dimension)
            with output.open("rb") as f:
                await application.bot.send_document(chat_id=job.user_id, document=f, filename="face-swap-result.jpg", caption=f"Face swap completed in {time.monotonic()-start:.1f}s.")
            application.bot_data["flows"].set(job.user_id, FlowState.COMPLETE)
        except asyncio.CancelledError:
            application.bot_data["flows"].set(job.user_id, FlowState.CANCELLED)
        except asyncio.TimeoutError:
            application.bot_data["flows"].set(job.user_id, FlowState.FAILED)
            await application.bot.send_message(job.user_id, "Processing timed out (600-second deadline). The native inference operation may finish in the background but its late result will not be sent.")
        except FaceSwapError as exc:
            application.bot_data["flows"].set(job.user_id, FlowState.FAILED)
            await application.bot.send_message(job.user_id, str(exc))
        except Exception as exc:
            log.exception("Job %s failed (%s)", job.id, type(exc).__name__)
            application.bot_data["flows"].set(job.user_id, FlowState.FAILED)
            try: await application.bot.send_message(job.user_id, "Processing failed. Check private service logs for diagnostics.")
            except Exception: pass
        finally:
            cleanup(job.source.parent)
            manager.finish(job)
            manager.queue.task_done()

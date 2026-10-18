# Private Telegram Face-Swap Bot

A single-admin Telegram bot scaffold for local CPU inference using an InsightFace-compatible face analysis model and ONNX face-swap model. It uses no paid inference API and has a 600-second processing deadline by default.

## Important blocker before deployment

**This repository does not include pretrained model weights.** The widely used `inswapper_128.onnx` and common InsightFace pretrained packs are not automatically safe to redistribute or use without restrictions. InsightFace's official project says its code is MIT-licensed but pretrained models are for non-commercial research and directs users to contact them for face-swap model licensing. See the official [InsightFace repository license notes](https://github.com/deepinsight/insightface#license) and [model licensing page](https://www.insightface.ai/solutions/face-swapping). This bot intentionally does not silently download these weights. Obtain compatible weights and written rights for your intended use, then place them in the paths configured below. No claim is made that a fully unrestricted pretrained model is available for free.

The free Render instance is also a poor fit for CPU face swapping: Render documents Free web services at 0.1 CPU / 512 MB RAM, idle spin-down after 15 minutes, and ephemeral filesystems. Model initialization/inference may exceed those resources. The code can be deployed to test the HTTP/webhook shell, but reliable face-swap inference on Render Free is **not verified and should not be expected**. See [Render Free limitations](https://render.com/docs/free) and [compute plans](https://render.com/docs/compute-plans).

## Features

- Numeric Telegram ID allowlist; unauthorized users are rejected before media download.
- Source-photo then target-photo workflow, one detectable face per image.
- Local ONNX inference; no paid per-swap API.
- Webhook endpoint protected by Telegram's secret-token header.
- `/start`, `/help`, `/status`, `/cancel`, `/reset`.
- Input byte, pixel, and dimension validation; EXIF orientation support is available in image utilities.
- Temporary workspaces and cleanup; structured operational logs without image contents or tokens.
- Health endpoints `/healthz` and `/readyz`.
- Unit tests and GitHub Actions workflow.

## Requirements and model layout

Python 3.11 on Linux is the intended runtime. CPU inference is configured. Install the pinned dependencies in `requirements.txt`.

Configure `SOURCE_FACE_MODEL` to an InsightFace `FaceAnalysis` model pack directory, and `SWAP_MODEL` to a compatible ONNX swap model. Model architecture compatibility matters. The source-face model directory must have the expected InsightFace model-pack layout; simply creating an empty directory will not work. Do not download weights from unofficial mirrors or commit weights to GitHub. The model must be licensed for your intended usage.

The standard model name `inswapper_128.onnx` is mentioned only as a common example, not as a license grant. Its model license is separate from this repository's MIT license.

## Environment variables

Copy `.env.example` to `.env` for local development and fill in values. Never commit `.env`.

- `BOT_TOKEN`: required Telegram bot token from [@BotFather](https://t.me/BotFather).
- `ADMIN_TELEGRAM_ID`: required positive numeric Telegram user ID. Do not use a username as authentication.
- `WEBHOOK_URL`: required public HTTPS base URL, e.g. `https://your-service.onrender.com`.
- `WEBHOOK_SECRET`: required URL-safe secret of at least 32 characters; Render blueprint can generate it.
- `PORT`: Render supplies this; defaults to 10000.
- `PROCESSING_TIMEOUT_SECONDS`: maximum processing deadline (default 600).
- `DOWNLOAD_TIMEOUT_SECONDS`: Telegram file transfer timeout.
- `MAX_INPUT_BYTES`, `MAX_IMAGE_PIXELS`, `MAX_IMAGE_DIMENSION`: input limits.
- `TEMP_DIR`: temporary workspace root.
- `SOURCE_FACE_MODEL`, `SWAP_MODEL`: paths to licensed compatible model files.
- `LOG_LEVEL`: log verbosity.

## Windows PowerShell: local checks

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Edit .env with a real token, numeric admin ID, HTTPS webhook URL, and secret.
python scripts/check_environment.py
pytest -q
ruff check app tests scripts
```

Local webhook testing needs a publicly reachable HTTPS URL. The webhook URL must match the URL where the service is actually reachable. A missing/incompatible model will intentionally prevent startup.

## GitHub push from PowerShell

```powershell
git init
git add .
git commit -m "Initial private face-swap bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/face-swap-telegram-bot.git
git push -u origin main
```

Create the empty GitHub repository first. Confirm `.env` and all model files are excluded before pushing:

```powershell
git status --short
git check-ignore .env models/inswapper_128.onnx
```

## Render deployment

1. Push the repository to GitHub.
2. In Render, create a new Blueprint and select this repository (or create a Docker web service from it).
3. Set `BOT_TOKEN`, `ADMIN_TELEGRAM_ID`, and `WEBHOOK_URL` in the Render environment. Keep `WEBHOOK_SECRET` generated/private.
4. Supply model files through a lawful, supported delivery method. The included image intentionally excludes model weights. Free Render does not offer persistent disks and its 512 MB/0.1 CPU resources are unlikely to support this stack reliably. Do not expect this model-dependent service to become ready until valid weights are present.
5. Check `/healthz` for liveness and `/readyz` for readiness. Check Render logs for startup/model initialization errors.

The blueprint uses Docker and binds to `0.0.0.0:$PORT`. It does not bypass Render plan limits or prevent sleep/restarts. Since local files are ephemeral, the service deletes job workspaces after processing and model files must be made available at startup.

## Telegram file limits

Telegram's Bot API `getFile` currently limits bot downloads to 20 MB; this app's default is lower (15 MiB). Output is sent as a document to preserve the generated image dimensions and avoid photo compression. Telegram documents general bot file upload limits separately; oversized files can fail at the platform boundary.

## Quality and reliability notes

- A swap is attempted only when exactly one face is detected in each image. This avoids silently choosing the wrong face but does not guarantee a natural result.
- The model's internal inference may run in a native worker thread. Python cannot safely kill arbitrary native inference instantly; the application enforces the deadline at the job level and must not deliver a late result as a success.
- The queue is in memory and limited to one pending job. Jobs do not survive restarts. A restart during processing can lose the job.
- `/cancel` marks an active job cancelled; native inference may continue until it returns, but a cancelled result must not be delivered.
- No artificial daily quota is implemented. Telegram, Render, hardware, network, and model license terms still impose limits.
- Deleting local files does not delete copies already delivered to Telegram or copies retained by Telegram infrastructure.

## Tests and verification status

Run `pytest -q` and `ruff check app tests scripts`. Unit tests use synthetic images and mocks/isolated helpers; they do **not** prove that actual model weights initialize or that a real face swap succeeds. The real integration test cannot pass until compatible, appropriately licensed model weights and suitable licensed fixtures are supplied. No live Render deployment or Telegram bot has been tested by this repository generation.

## Acceptance checklist

- [ ] Obtain and review licenses for both the face-analysis pack and swap weights.
- [ ] Verify models initialize with `python scripts/verify_model.py` and a real model smoke test.
- [ ] Run unit tests and lint in a clean environment.
- [ ] Configure bot token, admin ID, webhook URL and secret in Render.
- [ ] Confirm unauthorized users cannot upload/download media through the bot.
- [ ] Confirm `/healthz` and `/readyz` behave correctly.
- [ ] Test source and target photos, no-face/multi-face errors, cancellation, timeout and cleanup.
- [ ] Measure real inference latency and peak RAM on the chosen host before relying on the 600-second deadline.

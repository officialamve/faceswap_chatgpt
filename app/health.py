from fastapi import APIRouter, Request
router = APIRouter()
@router.get("/healthz")
async def healthz(): return {"status": "ok"}
@router.get("/readyz")
async def readyz(request: Request):
    if not getattr(request.app.state, "ready", False):
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}

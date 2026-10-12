from fastapi import FastAPI, Request

from app.api.router import api_router


app = FastAPI(
    title="WWF Polit-Assistant API",
    description="Backend API for the WWF Polit-Assistant.",
    version="0.1.0",
)

app.include_router(api_router)

from pathlib import Path
import hashlib
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

WEB_DIR = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


@app.get("/", include_in_schema=False)
def frontend():
    content = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    for filename in ("style.css", "i18n.js", "app.js"):
        revision = hashlib.sha256((WEB_DIR / filename).read_bytes()).hexdigest()[:12]
        content = content.replace(f"/assets/{filename}", f"/assets/{filename}?v={revision}")
    return HTMLResponse(content, headers={"Cache-Control": "no-store, max-age=0"})


@app.middleware("http")
async def frontend_cache_policy(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response

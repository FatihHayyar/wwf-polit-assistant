import hashlib
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router


app = FastAPI(
    title="WWF Polit-Assistant API",
    description="Backend API for the WWF Polit-Assistant.",
    version="0.1.0",
)

app.include_router(api_router)

WEB_DIR = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")

# The frontend uses no inline scripts or styles, so a strict policy applies.
# Swagger UI loads its assets from a CDN and is therefore excluded.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
)
API_DOC_PATHS = ("/docs", "/redoc", "/openapi.json")


def asset_names(html: str) -> list[str]:
    start = "/assets/"
    names = []
    for part in html.split(start)[1:]:
        name = part.split('"', 1)[0]
        if (WEB_DIR / name).is_file():
            names.append(name)
    return names


@app.get("/", include_in_schema=False)
def frontend():
    content = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    for filename in asset_names(content):
        revision = hashlib.sha256((WEB_DIR / filename).read_bytes()).hexdigest()[:12]
        content = content.replace(f'/assets/{filename}"', f'/assets/{filename}?v={revision}"')
    return HTMLResponse(content, headers={"Cache-Control": "no-store, max-age=0"})


@app.middleware("http")
async def security_and_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Email links carry tokens in the URL; never send them to other sites.
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if not path.startswith(API_DOC_PATHS):
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return response

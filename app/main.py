from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="WWF Polit-Assistant API",
    description="Backend API for the WWF Polit-Assistant.",
    version="0.1.0",
)

app.include_router(api_router)

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

WEB_DIR = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(WEB_DIR / "index.html")

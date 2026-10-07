from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="WWF Polit-Assistant API",
    description="Backend API for the WWF Polit-Assistant.",
    version="0.1.0",
)

app.include_router(api_router)

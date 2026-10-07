from fastapi import FastAPI

app = FastAPI(
    title="WWF Polit-Assistant API",
    description="Backend API for the WWF Polit-Assistant.",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
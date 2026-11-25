from fastapi import FastAPI
from app.db.database import check_database_connection
from app.api.webhooks import router as webhook_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="An AI agent that diagnoses and helps fix CI failures.",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(webhook_router)


@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running!",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


@app.get("/health/database")
def database_health_check():
    try:
        check_database_connection()

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }
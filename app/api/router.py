
from fastapi import APIRouter

from app.api.routes.affair_types import router as affair_types_router
from app.api.routes.affairs import router as affairs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.cantons import router as cantons_router
from app.api.routes.categories import router as categories_router
from app.api.routes.health import router as health_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.sync import router as sync_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(affairs_router)
api_router.include_router(categories_router)
api_router.include_router(cantons_router)
api_router.include_router(affair_types_router)
api_router.include_router(sync_router)
api_router.include_router(auth_router)
api_router.include_router(subscriptions_router)

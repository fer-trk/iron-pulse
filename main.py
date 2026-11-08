from contextlib import asynccontextmanager
import logging

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import get_current_user_sub
from app.routers.member import router as member_router
from app.routers.membership import router as membership_router
from app.routers.payment import router as payment_router
from app.routers.plan import router as plan_router
from app.routers.auth import router as auth_router
from app.routers.report import router as report_router
from app.routers.reservations import router as reservations_router
from app.routers.shifts import router as shifts_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("gymapi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🏋️  {settings.APP_NAME} arrancando...")
    yield
    logger.info("👋 GymAPI cerrando.")


app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para gestión integral de gimnasio. Madrid 2026.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
# Business routes require an active database user, including reports, exports
# and check-out. Keep login public and account creation separately admin-only.
business_router = APIRouter(
    prefix="/api/v1", dependencies=[Depends(get_current_user_sub)],
)
for router in (
    plan_router, member_router, membership_router, payment_router,
    shifts_router, reservations_router, report_router,
):
    business_router.include_router(router)
app.include_router(business_router)


@app.get("/", tags=["health"])
@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.redis_client import init_redis, close_redis
from contextlib import asynccontextmanager
from app.middleware.auth import SilentRefreshMiddleware 
from app.exceptions.handlers import register_auth_exception_handlers
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_redis()

    yield

    await close_redis()


app = FastAPI(lifespan=lifespan, redirect_slashes=False)


register_auth_exception_handlers(app)


from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router


app.add_middleware(SilentRefreshMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(auth_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")

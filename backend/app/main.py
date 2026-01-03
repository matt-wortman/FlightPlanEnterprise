from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.events import router as events_router
from app.api.routes.read_models import router as read_models_router
from app.api.routes.commands import router as command_router
from app.api.routes.plugins import router as plugins_router
from app.api.routes.ui import router as ui_router
from app.core.plugins.registry import plugin_registry

@asynccontextmanager
async def lifespan(_: FastAPI):
    plugin_registry.load_all()
    yield


app = FastAPI(title="FlightPlan Enterprise API", version="0.1.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(events_router)
app.include_router(read_models_router)
app.include_router(command_router)
app.include_router(plugins_router)
app.include_router(ui_router)

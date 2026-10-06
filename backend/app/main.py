from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .actions import get_registry  # noqa: F401  (imports the action modules)
from .api import register_routes
from .config import get_settings
from .export_api import router as export_router
from .files_api import router as files_router
from .mcp_server import route as mcp_route
from .mcp_server import running as mcp_running


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # The MCP transport's task group runs for as long as the app does.
    async with mcp_running():
        yield


app = FastAPI(title="Kolmi API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)
app.include_router(files_router)
app.include_router(export_router)
# Anyone's own AI, with a personal token: see app/mcp_server.py and docs/mcp.md.
app.router.routes.append(mcp_route())


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}

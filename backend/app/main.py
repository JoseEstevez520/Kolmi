from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .actions import get_registry  # noqa: F401  (imports the action modules)
from .api import register_routes
from .config import get_settings
from .files_api import router as files_router

app = FastAPI(title="Kolmi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)
app.include_router(files_router)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}

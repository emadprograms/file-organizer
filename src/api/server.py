import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.core.config import AppConfig
from src.core.exceptions import ConfigurationError
from src.api.routes import router

logger = logging.getLogger("file_organizer.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        config_env = os.getenv("FILE_ORGANIZER_CONFIG")
        if config_env:
            config_path = Path(config_env)
        else:
            config_path = Path("config.yaml")
            if not config_path.exists():
                config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
                
        config = AppConfig.load(config_path)
        app.state.config = config
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration on startup: {e}")
        raise e
    
    yield
    # Shutdown

app = FastAPI(title="File Organizer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

from fastapi.staticfiles import StaticFiles
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

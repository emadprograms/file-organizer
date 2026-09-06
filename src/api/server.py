import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.core.config import AppConfig
from src.core.exceptions import ConfigurationError
from src.api.routes import router

logger = logging.getLogger(f"file_organizer.{__name__}")

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

        # Pre-warm tree cache in a background thread so initial requests are instant
        import threading
        import asyncio
        from unittest.mock import MagicMock
        def _prewarm():
            try:
                from src.api.routes import get_tree
                mock_req = MagicMock()
                mock_req.app.state.config = config
                asyncio.run(get_tree(mock_req))
                logger.info("Tree cache pre-warmed successfully.")
            except Exception as ex:
                logger.warning(f"Tree cache pre-warm failed: {ex}")
        threading.Thread(target=_prewarm, daemon=True).start()
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

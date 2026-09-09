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
        config_env = os.getenv("FILE_ORGANIZER_CONFIG") or os.getenv("ORGANIZER_CONFIG")
        if config_env:
            config_path = Path(config_env)
        else:
            config_path = Path("config.yaml")
            if not config_path.exists():
                config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
                
        config = AppConfig.load(config_path)
        app.state.config = config
        logger.info("Configuration loaded successfully.")

        db_path = getattr(config, "db_path", None)
        app.state.db_path = db_path
        app.state.repo = None
        if db_path and (db_path == ":memory:" or Path(db_path).exists()):
            from src.db.connection import get_db_connection
            from src.db.repository import Repository
            from src.db.schema import init_db
            conn = get_db_connection(db_path)
            init_db(conn)
            app.state.repo = Repository(conn)
            logger.info(f"SQLite repository initialized from {db_path}")

        # Pre-warm tree cache in a background thread so initial requests are instant
        import threading
        import asyncio
        from unittest.mock import MagicMock
        def _prewarm():
            try:
                from src.api.routes import get_tree
                mock_req = MagicMock()
                mock_req.app.state.config = config
                mock_req.app.state.repo = app.state.repo
                mock_req.app.state.db_path = app.state.db_path
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
    if getattr(app.state, "repo", None) and hasattr(app.state.repo, "conn"):
        try:
            app.state.repo.conn.close()
        except Exception:
            pass

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

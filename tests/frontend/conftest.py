import re
from pathlib import Path
import pytest
from playwright.sync_api import BrowserContext

STATIC_DIR = Path(__file__).parent.parent.parent / "src" / "api" / "static"

@pytest.fixture(autouse=True)
def auto_route_static_assets(context: BrowserContext):
    def handle_static_assets(route):
        url = route.request.url
        if "/js/" in url:
            filename = url.split("/js/")[-1].split("?")[0]
            f = STATIC_DIR / "js" / filename
            ct = "application/javascript"
        elif "/css/" in url:
            filename = url.split("/css/")[-1].split("?")[0]
            f = STATIC_DIR / "css" / filename
            ct = "text/css"
        else:
            route.continue_()
            return

        if f.exists():
            route.fulfill(
                status=200,
                content_type=ct,
                body=f.read_text(encoding="utf-8")
            )
        else:
            route.fulfill(status=404, body="Not Found")

    context.route(re.compile(r".*/(js|css)/[^/]+\.(js|css).*"), handle_static_assets)

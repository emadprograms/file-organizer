import re
from pathlib import Path
import pytest
from playwright.sync_api import BrowserContext

STATIC_DIR = Path(__file__).parent.parent.parent / "src" / "api" / "static"

@pytest.fixture(autouse=True)
def auto_route_static_assets(context: BrowserContext):
    def handle_static_js(route):
        url = route.request.url
        filename = url.split("/js/")[-1].split("?")[0]
        js_file = STATIC_DIR / "js" / filename
        if js_file.exists():
            route.fulfill(
                status=200,
                content_type="application/javascript",
                body=js_file.read_text(encoding="utf-8")
            )
        else:
            route.fulfill(status=404, body="Not Found")

    context.route(re.compile(r".*/js/[^/]+\.js.*"), handle_static_js)

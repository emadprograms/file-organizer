import os
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

def test_dashboard_loads_static_file(page: Page):
    """Test that the frontend HTML loads and contains expected elements."""
    # Resolve the path to the static index.html
    html_path = Path(__file__).parent.parent.parent / "src" / "api" / "static" / "index.html"
    
    # Load the static file directly in the browser
    page.goto(f"file://{html_path.resolve()}")
    
    # Verify the title
    expect(page).to_have_title("File Organizer - Dashboard")
    
    # Verify core UI elements exist
    expect(page.locator("text=File Organizer")).to_be_visible()
    expect(page.locator("#house-list")).to_be_visible()
    expect(page.locator("#current-house-title")).to_be_visible()
    
    # The document panel is hidden until a house is selected
    expect(page.locator("#tab-timeline")).to_be_attached()
    expect(page.locator("#tab-categories")).to_be_attached()
    
    # Verify the welcome panel is visible instead
    expect(page.locator("#welcome-panel")).to_be_visible()
    expect(page.locator("text=No area selected")).to_be_visible()

    # Verify search UI is now co-located in the combined header bar
    expect(page.locator("#top-navbar #search-input")).to_be_visible()
    expect(page.locator("#search-input")).to_have_attribute("placeholder", "Search tenants or houses...")
    expect(page.locator("#search-results")).to_be_attached()

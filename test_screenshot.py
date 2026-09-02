import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://127.0.0.1:8000")
    page.wait_for_selector("text=Safra C")
    page.click("text=Safra C")
    page.wait_for_selector("text=1245")
    page.click("text=1245 - نصار أحمد الأنصاري")
    
    # Wait for timeline to load
    page.wait_for_selector("#document-list")
    
    # Click tenant
    page.click("text=نصار أحمد الأنصاري", strict=False)
    page.wait_for_timeout(1000)
    
    # Click Categories
    page.click("text=Categories")
    page.wait_for_timeout(1000)
    
    page.screenshot(path="screenshot.png")
    browser.close()
print("Screenshot saved to screenshot.png")

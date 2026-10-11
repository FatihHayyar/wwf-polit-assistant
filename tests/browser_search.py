"""Browser regression for unified search, using isolated SQLite fixtures."""
import threading
import time
from unittest.mock import patch
import uvicorn
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from test_monitoring import MonitoringTests
from app.main import app
from app.db.database import get_db


def main():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    fixture = MonitoringTests()
    with patch("test_monitoring.create_engine", return_value=engine):
        fixture.setUp()
    def session():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = session
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8767, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started: break
        time.sleep(.1)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width":1440,"height":1000})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto("http://127.0.0.1:8767")
            page.wait_for_selector(".result-card")
            assert page.locator("aside #datasets button").count() == 9
            assert page.locator(".type-filter").count() == 0
            page.locator('#datasets button[data-value="agendas"]').click()
            page.wait_for_timeout(700)
            assert page.locator(".type-tag").all_text_contents() == ["Traktanden", "Traktanden"]
            page.locator('input[name="q"]').fill('Solar')
            page.locator('#search-form button.primary').click()
            page.wait_for_timeout(700)
            assert page.locator('.result-card').count() == 1
            page.locator('#datasets button[data-value="affairs"]').click()
            page.wait_for_timeout(700)
            assert page.locator('input[name="q"]').input_value() == ''
            page.locator('#datasets button[data-value="agendas"]').click()
            page.wait_for_timeout(700)
            assert page.locator('input[name="q"]').input_value() == 'Solar'
            page.locator('button[type="reset"]').click()
            page.wait_for_timeout(700)
            page.locator(".result-card h2 button").first.click()
            page.wait_for_selector("#detail-dialog[open]")
            page.wait_for_timeout(500)
            assert "Sitzung" in page.locator("#detail-content").inner_text()
            assert "Windenergie" in page.locator("#detail-content").inner_text()
            assert not errors, errors
            page.locator('[data-close="detail-dialog"]').click()
            page.screenshot(path="logs/unified_search_preview.png", full_page=True)
            page.locator('button[type="reset"]').click()
            page.wait_for_timeout(700)
            assert page.locator("#datasets button.active").get_attribute("data-value") == "agendas"
            page.locator('#language').select_option('en')
            assert page.locator('#heading').inner_text() == 'Agendas'
            page.set_viewport_size({"width":390,"height":844})
            page.wait_for_timeout(300)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')

            browser.close()
            print("Nine-dataset navigation browser checks passed.")
    finally:
        server.should_exit = True
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()

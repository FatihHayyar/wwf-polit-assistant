"""Read-only UI smoke test using a locally installed Playwright and Edge.

Run with Playwright available on PYTHONPATH. No sync or email action is invoked.
"""
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

from app.main import app


def main():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.1)
        if not server.started:
            raise RuntimeError("Local UI server did not start")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://127.0.0.1:8765/?dataset=affairs&record=203543")
            page.locator(".record-title").wait_for()
            for language, heading, type_label in [("de","Geschäfte","Art"),("fr","Objets","Type"),("it","Oggetti","Tipo"),("en","Affairs","Type")]:
                page.locator('[data-close="detail-dialog"]').click()
                page.locator("header #language").select_option(language)
                page.goto("http://127.0.0.1:8765/?dataset=affairs&record=203543")
                page.locator(".record-title").wait_for()
                assert page.locator("html").get_attribute("lang") == language
                assert page.locator("#detail-title").inner_text() == heading
                labels = page.locator(".detail-fields dt").all_text_contents()
                assert labels.count(type_label) == 1
                assert all(label not in labels for label in ["id","body id","external id","created at","updated at"])
                assert page.locator(".record-title").inner_text().startswith("Alpinen Photovoltaik")
                assert not any("(0)" in value for value in page.locator(".related-section h3").all_text_contents())
                print(f"Browser detail check passed: {language}", flush=True)
            page.screenshot(path=str(Path(__file__).resolve().parents[1] / "logs" / "ui-detail-en.png"), full_page=True)
            page.locator('[data-close="detail-dialog"]').click()
            page.reload()
            page.locator(".record-title").wait_for()
            assert page.locator("html").get_attribute("lang") == "en"
            assert not errors, errors
            page.goto("http://127.0.0.1:8765/?dataset=agendas&record=341274")
            page.locator(".record-title").wait_for()
            assert "Séance du 06.12.2027" in page.locator(".record-title").inner_text()
            assert page.locator('#detail-content a.source-link').get_attribute("href") == "https://www.ville-fribourg.ch/agenda/seance-du-06-12-2027-conseil-general"
            page.locator("#detail-content .related-item").filter(has_text="Séance du 06.12.2027").click()
            page.wait_for_function("document.querySelector('#detail-title').textContent === 'Meetings' && document.querySelector('#detail-content .record-title') !== null")
            assert "Séance du 06.12.2027" in page.locator(".record-title").inner_text()
            print("Browser agenda check passed: actual meeting title, official source and linked meeting navigation.", flush=True)
            page.locator('[data-close="detail-dialog"]').click()
            page.set_viewport_size({"width":390,"height":844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            print("Browser checks passed: saved language, no JS errors, mobile width.", flush=True)
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()

"""Isolated browser checks: no live database writes and no actual email."""
import threading
import time
from unittest.mock import patch

import uvicorn
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Registers SQLite-compatible BigInteger compilation for test tables.
import test_monitoring
from app.db.database import Base, get_db
from app.main import app
from app.models import User
from app.models.classification import ClassificationCategory
from app.services.email_verification_service import create_login_token


def main():
    engine=create_engine("sqlite://",poolclass=StaticPool,connect_args={"check_same_thread":False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(id=1,email="browser@example.org",email_verified=True,is_active=True,is_admin=False))
        for category_id,code,parent in [(1,"climate_energy",None),(2,"renewable_heat",1),(3,"renewable_electricity",1),(4,"environment_policy",None),(5,"public_sector",4)]:
            db.add(ClassificationCategory(id=category_id,code=code,parent_id=parent,name_de=code,name_fr=code,name_it=code,name_rm=code,active=True,is_fallback=False,sort_order=category_id,classification_threshold=8))
        db.commit()
        token=create_login_token(db,user_id=1)
    def test_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db]=test_db
    server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=8766,log_level="error"))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    try:
        for _ in range(100):
            if server.started:break
            time.sleep(.1)
        with patch("app.api.routes.subscriptions.send_email") as send, sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",headless=True)
            context=browser.new_context(viewport={"width":1440,"height":1000})
            page=context.new_page();page.goto("http://127.0.0.1:8766/")
            page.locator("#language").select_option("en")
            assert page.locator("#datasets button").count()==9
            assert page.locator("#membership-login").is_visible()
            assert not page.locator("#membership-logout").is_visible()
            page.locator('#datasets button[data-value="meetings"]').click()
            page.locator('[name="q"]').fill("saved filter")
            page.locator("#membership-login").click()
            linked=context.new_page()
            try:linked.goto(f"http://127.0.0.1:8766/api/v1/auth/verify-login?token={token}")
            except Exception:
                if not linked.is_closed():raise
            page.wait_for_function("document.querySelector('#membership-summary').textContent.includes('browser@example.org')")
            assert page.locator("#heading").inner_text()=="Meetings"
            assert page.locator('[name="q"]').input_value()=="saved filter"
            assert not page.locator("#account-dialog").is_visible()
            if not page.locator("#subscription-dialog").is_visible():
                page.locator("#membership-view").click()
            page.locator(".topic-group").first.wait_for()
            assert page.locator(".topic-group").count()==2
            assert page.locator(".topic-group").first.locator(".topic-children label").count()==2
            page.locator(".topic-parent input").first.check()
            assert page.locator(".topic-group").first.locator(".topic-children input").first.is_disabled()
            page.locator('.subscription-toolbar button[type="submit"]').click()
            page.wait_for_function("document.querySelector('#subscription-message').textContent==='Subscriptions saved.'")
            saved=page.request.get("http://127.0.0.1:8766/api/v1/subscriptions").json()
            assert saved["category_ids"]==[1]
            assert send.call_count==1
            page.locator('button[data-close="subscription-dialog"]').click()
            assert page.locator("#membership-logout").is_visible()
            page.locator("#membership-logout").click()
            page.locator("#membership-register").wait_for(state="visible")
            assert not page.locator("#membership-view").is_visible()
            assert len(context.pages)>=1
            print("Membership browser checks passed: nine-item public navigation, cross-tab login without lost filters, grouped topics, parent coverage and saved subscriptions.")
            browser.close()
    finally:
        server.should_exit=True;thread.join(timeout=10)
        app.dependency_overrides.clear();engine.dispose()


if __name__ == "__main__":main()

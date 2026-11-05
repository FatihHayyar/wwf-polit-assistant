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
import test_monitoring  # noqa: F401
from app.db.database import Base, get_db
from app.main import app
from app.models import User
from app.models.entities import Affair
from app.models.classification import ClassificationCategory
from app.services.email_verification_service import create_login_token


def main():
    engine=create_engine("sqlite://",poolclass=StaticPool,connect_args={"check_same_thread":False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(id=1,email="browser@example.org",email_verified=True,is_active=True,is_admin=False))
        for category_id,code,parent in [(1,"climate_energy",None),(2,"renewable_heat",1),(3,"renewable_electricity",1),(4,"environment_policy",None),(5,"public_sector",4)]:
            db.add(ClassificationCategory(id=category_id,code=code,parent_id=parent,name_de=code,name_fr=code,name_it=code,name_rm=code,active=True,is_fallback=False,sort_order=category_id,classification_threshold=8))
        db.add(Affair(id=1,title_de="Solar Bern",type_harmonized_de="Motion"))
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
        with patch("app.api.routes.subscriptions.send_email") as send, patch("app.api.routes.auth.send_email") as auth_send, sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",headless=True)
            context=browser.new_context(viewport={"width":1440,"height":1000},bypass_csp=True)
            page=context.new_page();page.goto("http://127.0.0.1:8766/")
            page.locator("#language").select_option("en")
            assert page.locator("#datasets button").count()==9
            assert page.locator("#membership-login").is_visible()
            assert not page.locator("#membership-logout").is_visible()
            page.locator('#datasets button[data-value="meetings"]').click()
            page.locator('[name="q"]').fill("saved filter")
            page.locator("#membership-login").click()
            linked=context.new_page()
            # The email link opens a confirmation page; only its POST signs in.
            linked.goto(f"http://127.0.0.1:8766/api/v1/auth/verify-login?token={token}")
            try:linked.locator('form [type="submit"], form button').first.click()
            except Exception:
                if not linked.is_closed():raise
            page.wait_for_function("document.querySelector('#membership-summary').textContent.includes('browser@example.org')")
            assert page.locator("#heading").inner_text()=="Meetings"
            assert page.locator('[name="q"]').input_value()=="saved filter"
            assert not page.locator("#account-dialog").is_visible()
            # Signing in opens the subscription dialog by itself.
            page.locator("#subscription-dialog").wait_for(state="visible")
            # No name and no keyword field: only filters.
            page.locator("#profile-new").click()
            assert page.locator("#subscription-form input:not([type=checkbox]), #subscription-form textarea").count()==0
            page.locator(".topic-group").first.wait_for()
            assert page.locator(".topic-group").count()==2
            assert page.locator(".topic-group").first.locator(".topic-children label").count()==2
            page.locator(".topic-parent input").first.check()
            assert page.locator(".topic-group").first.locator(".topic-children input").first.is_disabled()
            page.locator('[name="affair_types"][value="Motion"]').check()
            # The button at the bottom saves and closes the dialog.
            page.locator("#subscription-save").click()
            page.wait_for_function("!document.querySelector('#subscription-dialog').open")
            page.wait_for_function("document.querySelector('#toast').textContent==='Subscription saved.'")
            profiles=page.request.get("http://127.0.0.1:8766/api/v1/subscriptions").json()["profiles"]
            assert [(p["category_ids"],p["affair_types"]) for p in profiles]==[([1],["Motion"])], profiles
            assert profiles[0]["name"]=="climate_energy · alle Kantone · Motion", profiles[0]["name"]
            assert send.call_count==1
            # A second subscription can be added next to the first; cards use the interface language.
            page.locator("#membership-view").click()
            page.locator("#profile-list h4").first.wait_for()
            assert page.locator("#profile-list h4").first.inner_text()=="Climate & energy · All cantons · Motion"
            page.locator("#profile-new").click()
            page.locator(".topic-parent input").nth(1).check()
            page.locator("#subscription-save").click()
            page.wait_for_function("!document.querySelector('#subscription-dialog').open")
            assert len(page.request.get("http://127.0.0.1:8766/api/v1/subscriptions").json()["profiles"])==2
            # One click follows a record from its detail view and appears in the subscription.
            page.evaluate("Polit.detail.show('affairs',1)")
            follow=page.locator("#detail-content .follow-button")
            follow.wait_for()
            assert follow.get_attribute("aria-pressed")=="false"
            follow.click()
            page.wait_for_function("document.querySelector('#detail-content .follow-button').getAttribute('aria-pressed')==='true'")
            page.locator('button[data-close="detail-dialog"]').click()
            page.locator("#membership-view").click()
            page.locator("#subscription-watches .watch-row").wait_for()
            assert "Solar Bern" in page.locator("#subscription-watches").inner_text()
            page.locator("#subscription-watches .watch-row button").nth(1).click()
            page.wait_for_function("!document.querySelector('#subscription-watches .watch-row')")
            assert page.request.get("http://127.0.0.1:8766/api/v1/subscriptions").json()["watches"]==[]
            page.locator('button[data-close="subscription-dialog"]').click()
            assert page.locator("#membership-logout").is_visible()
            page.locator("#membership-logout").click()
            page.locator("#membership-register").wait_for(state="visible")
            assert not page.locator("#membership-view").is_visible()
            assert len(context.pages)>=1
            # After logout the sign-in dialog starts empty: no old address or "link sent" message.
            page.locator("#membership-login").click()
            page.locator('#account-form [name="email"]').fill("earlier@example.org")
            page.evaluate("Polit.showStatus('account-message','Link sent')")
            page.locator('button[data-close="account-dialog"]').click()
            page.locator("#membership-login").click()
            assert page.locator('#account-form [name="email"]').input_value()==""
            assert page.locator("#account-message").inner_text()==""
            # Registering a known address asks to sign in and switches; the next click sends the sign-in link.
            form=page.locator("#account-form")
            form.locator('[name="action"]').select_option("register")
            form.locator('[name="email"]').fill("browser@example.org")
            form.locator("button").click()
            page.wait_for_function("document.querySelector('#account-message').textContent.includes('already registered')")
            assert form.locator('[name="action"]').input_value()=="login"
            assert auth_send.call_count==0
            form.locator("button").click()
            page.wait_for_function("document.querySelector('#account-message').textContent.includes('sign-in link')")
            assert auth_send.call_count==1
            # Signing in with an unknown address asks to register and switches.
            form.locator('[name="action"]').select_option("login")
            form.locator('[name="email"]').fill("stranger@example.org")
            form.locator("button").click()
            page.wait_for_function("document.querySelector('#account-message').textContent.includes('no account')")
            assert form.locator('[name="action"]').input_value()=="register"
            assert auth_send.call_count==1
            page.locator('button[data-close="account-dialog"]').click()
            print("Membership browser checks passed: nine-item public navigation, cross-tab login without lost filters, grouped topics, parent coverage, generated names, several subscriptions, save-and-close, one-click follow, a reset sign-in dialog and clear register/sign-in answers.")
            browser.close()
    finally:
        server.should_exit=True;thread.join(timeout=10)
        app.dependency_overrides.clear();engine.dispose()


if __name__ == "__main__":main()

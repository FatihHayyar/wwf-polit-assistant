// Exercise the running UI. Account writes and emails are intercepted in this
// isolated browser context; list/detail requests use the actual local server.
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const {chromium} = require(path.join(process.env.APPDATA, "npm/node_modules/artillery/node_modules/playwright-core"));
const base = process.env.UI_TEST_URL || "http://localhost:8000";
const output = path.resolve(__dirname, "../logs");

async function insideViewport(page, selector) {
  const box = await page.locator(selector).boundingBox();
  const viewport = page.viewportSize();
  assert.ok(box && box.x >= -1 && box.y >= -1 && box.x + box.width <= viewport.width + 1 && box.y + box.height <= viewport.height + 1,
    `${selector} must remain in view: ${JSON.stringify(box)}`);
}

async function main() {
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({channel:"msedge", headless:true});
  try {
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      const context = await browser.newContext({viewport});
      let signedIn = true;
      let subscriptions = {category_ids:[],canton_keys:[],datasets:[],keywords:[],watches:[],active:false};
      let recipients = [{email:"browser@example.org",verified:true}];
      await context.route("**/api/v1/auth/**", async route => {
        const url = new URL(route.request().url());
        if (url.pathname.endsWith("/me")) return route.fulfill({status:signedIn?200:401,json:signedIn?{email:"browser@example.org",email_verified:true}:{detail:"Not signed in"}});
        if (url.pathname.endsWith("/providers")) return route.fulfill({json:{google:false}});
        if (url.pathname.endsWith("/logout")) {signedIn=false; return route.fulfill({status:204});}
        if (url.pathname.endsWith("/login")) return route.fulfill({status:404,json:{detail:"This email address is not registered."}});
        if (url.pathname.endsWith("/register")) return route.fulfill({status:409,json:{detail:"This email address is already registered."}});
        return route.fulfill({status:400,json:{detail:"Unexpected test authentication request"}});
      });
      await context.route(/\/api\/v1\/subscriptions(?:\/|\?|$)/, async route => {
        if (route.request().url().includes("/recipients")) {
          if (route.request().method()==="PUT") recipients=route.request().postDataJSON().emails.map(email=>({email,verified:email==="browser@example.org"}));
          return route.fulfill({json:recipients});
        }
        if (route.request().method()==="PUT") subscriptions={...subscriptions,...route.request().postDataJSON(),active:true};
        return route.fulfill({json:subscriptions});
      });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      const response = await page.goto(base, {waitUntil:"networkidle"});
      assert.match(response.headers()["cache-control"], /no-store/);
      assert.ok(await page.locator('script[src*="app.js?v="]').count());
      await page.locator("#results .result-card h2 button").first().waitFor();
      const layout = await page.locator(".content-layout").boundingBox();
      const results = await page.locator("#results").boundingBox();
      assert.ok(results.width >= layout.width - 2, "Results must use the full content width");
      const manage = await page.locator("#membership-view").boundingBox();
      const logout = await page.locator("#membership-logout").boundingBox();
      assert.ok(Math.abs(manage.width-logout.width)<=1 && Math.abs(manage.height-logout.height)<=1, "Membership actions must have equal dimensions");
      assert.equal(await page.locator("#message").isVisible(), false);
      const label = viewport.width > 1000 ? "desktop" : "mobile";
      await page.screenshot({path:path.join(output,`ui_home_${label}.png`)});

      await page.locator("#results .result-card h2 button").first().click();
      await page.locator("#detail-content .record-title").waitFor();
      assert.equal(await page.locator("#detail-content").getByRole("button", {name:"Inhalt verfolgen",exact:true}).count(),0);
      await page.locator("#detail-content").evaluate(node => {
        for (const details of node.querySelectorAll("details")) details.open=true;
        if (node.scrollHeight <= node.clientHeight) { const content=document.createElement("p");content.textContent="Detailed political record. ".repeat(400);node.append(content); }
      });
      for (const fraction of [0,.5,1]) {
        await page.locator("#detail-content").evaluate((node,fraction)=>node.scrollTop=(node.scrollHeight-node.clientHeight)*fraction,fraction);
        await insideViewport(page,'[data-close="detail-dialog"]');
      }
      await page.screenshot({path:path.join(output,`ui_detail_${label}.png`)});
      await page.locator('[data-close="detail-dialog"]').click();
      await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
      assert.equal(await page.locator("#global-account-actions").count(),0);
      await page.locator("#membership-view").click();
      try {await page.locator("#subscription-dialog .dialog-body").waitFor({timeout:10000});}
      catch (error) {
        await page.screenshot({path:path.join(output,"ui_failure.png")});
        console.error("Account dialog diagnostics", await page.evaluate(()=>({message:document.querySelector("#message").textContent,categories:state.categories,subscriptions:state.subscriptions})), errors);
        throw error;
      }
      for (const fraction of [0,.5,1]) {
        await page.locator("#subscription-dialog .dialog-body").evaluate((node,fraction)=>node.scrollTop=(node.scrollHeight-node.clientHeight)*fraction,fraction);
        for (const selector of ['[data-close="subscription-dialog"]','.subscription-toolbar [type="submit"]',"#subscription-logout","#unsubscribe"]) await insideViewport(page,selector);
      }
      await insideViewport(page,"#delete-account");
      await page.screenshot({path:path.join(output,`ui_subscriptions_bottom_${label}.png`)});
      await page.locator("#subscription-dialog .dialog-body").evaluate(node=>node.scrollTop=0);
      await page.locator("#recipient-emails").fill("additional@example.org");
      await page.locator('.subscription-toolbar [type="submit"]').click();
      await page.waitForFunction(()=>document.querySelector("#subscription-message").textContent.includes("gespeichert"));
      assert.equal(await page.locator("#toast").isVisible(),true);
      await insideViewport(page,"#toast");
      const notice = await page.locator("#toast").boundingBox();
      const actions = await page.locator(".subscription-toolbar").boundingBox();
      assert.ok(notice.y+notice.height <= actions.y-4, "Saved notice must not cover persistent actions");
      await page.locator("#subscription-logout").click({trial:true});
      assert.match(await page.locator("#recipient-status").textContent(),/additional@example.org/);
      await page.screenshot({path:path.join(output,`ui_saved_${label}.png`)});
      await page.locator("#subscription-logout").click();
      await page.locator("#membership-login").waitFor();
      await page.locator("#membership-login").click();
      await page.locator('#account-form [name="email"]').fill("unknown@example.org");
      await page.locator("#account-form .primary").click();
      await page.waitForFunction(()=>document.querySelector("#account-message").textContent.includes("noch kein Konto"));
      assert.equal(await page.locator('#account-form [name="action"]').inputValue(),"register");
      await page.locator("#account-form .primary").click();
      await page.waitForFunction(()=>document.querySelector("#account-message").textContent.includes("bereits registriert"));
      assert.equal(await page.locator('#account-form [name="action"]').inputValue(),"login");
      await page.locator('[data-close="account-dialog"]').click();
      signedIn=true;
      await page.goto(base+"/?signed_in=1",{waitUntil:"networkidle"});
      await page.locator("#subscription-dialog .dialog-body").waitFor();
      assert.equal((await page.locator("body").innerText()).includes("Du bist jetzt angemeldet."),false);
      assert.equal(errors.length,0,`Browser errors: ${errors.join(", ")}`);
      console.log(`${label}: versioned assets, full-width results, balanced buttons, persistent close/actions, saved notice, recipients and login guidance verified.`);
      await context.close();
    }
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});

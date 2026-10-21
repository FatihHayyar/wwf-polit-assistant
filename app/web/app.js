"use strict";
// Entry point: translations, language switch and start-up.
(() => {
  const Polit = window.Polit;
  const { ui, state, t, $, api, showStatus, toast } = Polit;

  function translatePage() {
    document.documentElement.lang = state.language;
    state.names = ui.datasets(state.language);
    $("language").value = state.language;
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.placeholder = t(node.dataset.i18nPlaceholder);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
      node.setAttribute("aria-label", t(node.dataset.i18nAria));
    });
    Polit.search.renderDatasetNavigation();
    $("heading").textContent = state.names[state.dataset];
    Polit.search.renderFilterOptions();
    for (const id of ["account-message", "subscription-message"]) showStatus(id, "");
    Polit.account.renderMembership();
    Polit.search.renderContextNavigation();
  }

  /** Re-render open views in the new language without losing form input. */
  function changeLanguage(value) {
    state.language = value;
    ui.saveLanguage(value);
    translatePage();
    if (Polit.subscriptions.isOpen()) Polit.subscriptions.render();
    if (state.detail && $("detail-dialog").open) Polit.detail.render();
    if (state.result) Polit.search.renderResults(state.result);
  }

  async function loadDemoStatus() {
    try {
      const demo = await api("/api/v1/demo/status");
      state.demo = { enabled: demo.enabled, mailboxUrl: demo.mailbox_url };
    } catch {
      state.demo = { enabled: false, mailboxUrl: null };
    }
    $("demo-guide").hidden = !state.demo.enabled;
  }

  /** Handle links from emails, e.g. ?dataset=affairs&record=123. */
  async function handleUrlParameters() {
    const params = new URLSearchParams(location.search);
    const dataset = Object.hasOwn(state.names, params.get("dataset")) ? params.get("dataset") : "affairs";
    Polit.search.chooseDataset(dataset);
    if (params.get("record") && /^\d+$/.test(params.get("record"))) Polit.detail.show(dataset, Number(params.get("record")));
    if (params.get("recipient_verified") === "1") {
      toast(t("recipientVerified"));
      await Polit.subscriptions.open();
    }
    if (params.get("signed_in") === "1") {
      history.replaceState(null, "", "/");
      await Polit.account.announceSignIn();
      await Polit.subscriptions.open();
    }
  }

  async function init() {
    $("language").addEventListener("change", () => changeLanguage($("language").value));
    document.querySelectorAll("[data-close]").forEach((node) => {
      node.addEventListener("click", () => $(node.dataset.close).close());
    });
    Polit.search.bindEvents();
    Polit.account.bindEvents();
    Polit.subscriptions.bindEvents();
    Polit.ask.bindEvents();

    translatePage();
    try {
      const [categories, cantons, affairTypes] = await Promise.all(
        [api("/api/v1/categories"), api("/api/v1/cantons"), api("/api/v1/affair-types")]);
      state.categories = categories;
      state.cantons = cantons;
      state.affairTypes = affairTypes.map((item) => item.value);
      translatePage();
    } catch (error) {
      showStatus("message", error.message, true);
    }
    try {
      const providers = await api("/api/v1/auth/providers");
      $("google-login").hidden = !providers.google;
    } catch {
      // Google sign-in stays hidden.
    }
    await loadDemoStatus();
    await Polit.account.refresh();
    await handleUrlParameters();
  }

  init();
})();

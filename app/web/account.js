"use strict";
// Account dialog: passwordless sign-in links, sign-in sync across tabs, logout.
(() => {
  const Polit = window.Polit;
  const { state, t, $, api, errorText, showStatus } = Polit;

  async function refresh() {
    try {
      state.account = await api("/api/v1/auth/me");
    } catch {
      state.account = null;
    }
    $("logout").hidden = !state.account;
    renderMembership();
  }

  function renderMembership() {
    const signedIn = Boolean(state.account);
    const summary = signedIn ? t("accountActive", { email: state.account.email }) : "";
    $("membership-summary").textContent = summary;
    $("membership-login").hidden = signedIn;
    $("membership-register").hidden = signedIn;
    $("membership-view").hidden = !signedIn;
    $("membership-logout").hidden = !signedIn;
    $("account-form").hidden = signedIn;
    $("account-help").hidden = signedIn;
    $("account-summary").hidden = !signedIn;
    $("account-summary").textContent = summary;
    $("account-title").textContent = t(signedIn ? "account" : "login");
  }

  function openDialog(action) {
    $("account-form").elements.action.value = action;
    $("account-dialog").showModal();
  }

  // The email link opens in a new tab. That tab announces the sign-in so the
  // original tab can continue and the new tab can close itself.
  const authChannel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("polit-auth") : null;

  async function applySignIn() {
    await refresh();
    if (!state.account) return false;
    if ($("account-dialog").open) $("account-dialog").close();
    showStatus("message", "");
    await Polit.subscriptions.open();
    return true;
  }

  async function announceSignIn() {
    if (!state.account) return;
    const id = crypto.randomUUID();
    authChannel?.addEventListener("message", (event) => {
      if (event.data?.type === "ack" && event.data.id === id) window.close();
    });
    try {
      localStorage.setItem("polit-auth-updated", id);
    } catch {
      // Storage may be blocked; the BroadcastChannel still works.
    }
    authChannel?.postMessage({ type: "signed-in", id });
    showStatus("message", "");
  }

  async function logout(messageId, afterLogout) {
    try {
      await api("/api/v1/auth/logout", { method: "POST" });
      afterLogout?.();
      await refresh();
    } catch (error) {
      showStatus(messageId, errorText(error), true);
    }
  }

  async function requestLink(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    try {
      await api(`/api/v1/auth/${data.get("action")}`, {
        method: "POST",
        body: JSON.stringify({ email: data.get("email") }),
      });
      // Same message whether or not the address has an account.
      showStatus("account-message", t("linkSent"));
    } catch (error) {
      showStatus("account-message", errorText(error), true);
    }
  }

  function bindEvents() {
    authChannel?.addEventListener("message", async (event) => {
      if (event.data?.type === "signed-in" && await applySignIn()) {
        authChannel.postMessage({ type: "ack", id: event.data.id });
        window.focus();
      }
    });
    window.addEventListener("storage", (event) => {
      if (event.key === "polit-auth-updated") applySignIn();
    });
    window.addEventListener("focus", refresh);

    $("account-form").addEventListener("submit", requestLink);
    $("logout").addEventListener("click", () => logout("account-message", () => $("account-dialog").close()));
    $("membership-logout").addEventListener("click", () => logout("message"));
    $("membership-login").addEventListener("click", () => openDialog("login"));
    $("membership-register").addEventListener("click", () => openDialog("register"));
    $("google-login").addEventListener("click", (event) => {
      event.preventDefault();
      window.open("/api/v1/auth/google", "polit-google", "popup,width=520,height=700");
    });
  }

  Polit.account = { bindEvents, refresh, renderMembership, announceSignIn, logout };
})();

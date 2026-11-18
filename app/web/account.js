"use strict";
// Account dialog: passwordless sign-in links, sign-in sync across tabs, logout.
(() => {
  const Polit = window.Polit;
  const { state, t, $, api, errorText, showStatus, externalLink } = Polit;

  async function refresh() {
    const previous = state.account?.email;
    try {
      state.account = await api("/api/v1/auth/me");
    } catch {
      state.account = null;
    }
    // Followed records belong to the account; reload them after a switch.
    if (state.account?.email !== previous) state.subscriptions = null;
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

  /** Each opening starts empty: no address or message from an earlier request. */
  function resetDialog() {
    $("account-form").reset();
    showStatus("account-message", "");
  }

  function openDialog(action) {
    resetDialog();
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
      resetDialog();
      await refresh();
    } catch (error) {
      showStatus(messageId, errorText(error), true);
    }
  }

  async function requestLink(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const action = event.target.elements.action;
    try {
      const answer = await api(`/api/v1/auth/${data.get("action")}`, {
        method: "POST",
        body: JSON.stringify({ email: data.get("email") }),
      });
      showStatus("account-message", t(answer.result === "login_link" ? "loginLinkSent" : "verificationLinkSent"));
      // The demo sends nothing outside; point to the local test mailbox.
      const mailbox = state.demo.enabled ? externalLink(state.demo.mailboxUrl, t("demoOpenMailbox")) : null;
      if (mailbox) $("account-message").append(" ", t("demoMailboxHint"), " ", mailbox);
    } catch (error) {
      // Wrong choice: say so and switch, so the next click does the right thing.
      if (error.status === 409) {
        action.value = "login";
        showStatus("account-message", t("alreadyRegistered"), true);
      } else if (error.status === 404) {
        action.value = "register";
        showStatus("account-message", t("notRegistered"), true);
      } else {
        showStatus("account-message", errorText(error), true);
      }
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
    // The dialog is also opened directly (follow button, questions); clearing
    // on close covers every way of opening it.
    $("account-dialog").addEventListener("close", resetDialog);
    $("logout").addEventListener("click", () => logout("account-message", () => $("account-dialog").close()));
    $("membership-logout").addEventListener("click", () => logout("message"));
    $("membership-login").addEventListener("click", () => openDialog("login"));
    $("membership-register").addEventListener("click", () => openDialog("register"));
    $("google-login").addEventListener("click", (event) => {
      event.preventDefault();
      window.open("/api/v1/auth/google", "polit-google", "popup,width=520,height=700");
    });
  }

  Polit.account = { bindEvents, refresh, renderMembership, announceSignIn, logout, resetDialog };
})();

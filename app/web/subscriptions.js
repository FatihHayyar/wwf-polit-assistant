"use strict";
// Subscription dialog: notification recipients, several named subscription
// profiles, watched records and (in demo mode) a test notification.
(() => {
  const Polit = window.Polit;
  const { ui, state, t, $, el, button, api, errorText, showStatus, addOption, checkbox, categoryName,
    externalLink, toast } = Polit;

  // --- Recipients -----------------------------------------------------------

  function renderRecipientStatus(recipients) {
    $("recipient-status").replaceChildren();
    for (const row of recipients) {
      if (!row.verified) $("recipient-status").append(el("p", t("pendingRecipient", { email: row.email })));
    }
  }

  function renderRecipients(recipients) {
    $("recipient-own").checked = recipients.some((row) => row.email === state.account.email);
    $("recipient-emails").value = recipients.filter((row) => row.email !== state.account.email).map((row) => row.email).join("\n");
    renderRecipientStatus(recipients);
  }

  function selectedRecipients() {
    const own = $("recipient-own").checked ? [state.account.email] : [];
    const others = $("recipient-emails").value.split(/\r?\n/).map((value) => value.trim().toLowerCase()).filter(Boolean);
    return [...new Set([...own, ...others])];
  }

  async function saveRecipients(event) {
    event.preventDefault();
    const emails = selectedRecipients();
    if (!emails.length) {
      showStatus("subscription-message", t("recipientRequired"), true);
      return;
    }
    try {
      renderRecipientStatus(await api("/api/v1/subscriptions/recipients", { method: "PUT", body: JSON.stringify({ emails }) }));
      toast(t("recipientsSaved"));
      showStatus("subscription-message", "");
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  // --- Profiles -------------------------------------------------------------

  function summary(profile) {
    const all = t("profileAll");
    const types = profile.affair_types.length ? profile.affair_types.join(", ") : all;
    const datasets = profile.datasets.length ? profile.datasets.map((key) => state.names[key]).join(", ") : all;
    const topics = profile.category_ids.length
      ? profile.category_ids.map((id) => categoryName(findCategory(id) || { code: String(id) })).join(", ") : all;
    const lines = [
      `${t("topics")}: ${topics}`,
      `${t("cantons")}: ${profile.canton_names.length ? profile.canton_names.join(", ") : all}`,
      `${t("affairTypes")}: ${types}`,
      `${t("datasets")}: ${datasets}`,
    ];
    if (profile.keywords.length) lines.push(`${t("keywords")}: ${profile.keywords.join(", ")}`);
    return lines;
  }

  function findCategory(id) {
    for (const parent of state.categories) {
      if (parent.id === id) return parent;
      const child = parent.subcategories.find((row) => row.id === id);
      if (child) return child;
    }
    return null;
  }

  function renderProfiles() {
    const list = $("profile-list");
    list.replaceChildren();
    const profiles = state.subscriptions?.profiles || [];
    if (!profiles.length) list.append(el("p", t("profileEmpty"), "hint"));
    for (const profile of profiles) {
      const card = el("article", undefined, "profile-card");
      const heading = el("h4", profile.name);
      if (profile.paused) heading.append(el("span", t("profilePaused"), "tag paused"));
      card.append(heading);
      for (const line of summary(profile)) card.append(el("p", line, "card-meta"));
      const actions = el("div", undefined, "agenda-links");
      actions.append(
        button(t("profileEdit"), () => editProfile(profile)),
        button(t("profileDelete"), () => deleteProfile(profile)),
      );
      card.append(actions);
      list.append(card);
    }
    const max = state.subscriptions?.max_profiles || 10;
    $("profile-new").disabled = profiles.length >= max;
    $("profile-new").title = profiles.length >= max ? t("profileLimit", { max }) : "";
  }

  /** A selected main topic covers its subtopics, which are then disabled. */
  function renderTopics(selected) {
    $("subscription-categories").replaceChildren();
    for (const parent of state.categories) {
      const group = el("section", undefined, "topic-group");
      const heading = el("div", undefined, "topic-parent");
      const children = el("div", undefined, "topic-children");
      checkbox(heading, "category_ids", parent.id, categoryName(parent), selected.includes(parent.id));
      for (const child of parent.subcategories) {
        checkbox(children, "category_ids", child.id, categoryName(child), selected.includes(child.id));
      }
      const parentInput = heading.querySelector("input");
      const included = el("p", t("allSubtopics"), "topic-coverage");
      const update = () => {
        for (const input of children.querySelectorAll("input")) input.disabled = parentInput.checked;
        children.classList.toggle("covered", parentInput.checked);
        included.hidden = !parentInput.checked;
      };
      parentInput.addEventListener("change", update);
      update();
      group.append(heading, included, children);
      $("subscription-categories").append(group);
    }
  }

  function renderDatasets(selected) {
    const main = el("div", undefined, "dataset-group");
    const support = el("details", undefined, "dataset-group");
    support.append(el("summary", t("supportingRecords")));
    for (const [dataset, name] of Object.entries(state.names)) {
      checkbox(ui.primaryDatasets.includes(dataset) ? main : support, "datasets", dataset, name, selected.includes(dataset));
    }
    if (selected.some((dataset) => !ui.primaryDatasets.includes(dataset))) support.open = true;
    $("subscription-datasets").replaceChildren(main, support);
  }

  function renderProfileForm(profile) {
    state.editingProfile = profile;
    $("profile-form-title").textContent = t(profile.id ? "profileEditTitle" : "profileNewTitle");
    $("profile-name").value = profile.name;
    $("profile-active").checked = profile.active;
    renderTopics(profile.category_ids);
    $("subscription-cantons").replaceChildren();
    for (const canton of state.cantons) {
      checkbox($("subscription-cantons"), "canton_keys", canton.code, canton.name, profile.canton_keys.includes(canton.code));
    }
    $("subscription-affair-types").replaceChildren();
    for (const value of state.affairTypes) {
      checkbox($("subscription-affair-types"), "affair_types", value, value, profile.affair_types.includes(value));
    }
    renderDatasets(profile.datasets);
    $("subscription-keywords").value = profile.keywords.join("\n");
    $("profile-form").hidden = false;
    $("profile-name").focus();
  }

  function captureProfile() {
    const form = new FormData($("profile-form"));
    return {
      name: $("profile-name").value.trim(),
      active: $("profile-active").checked,
      category_ids: form.getAll("category_ids").map(Number),
      canton_keys: form.getAll("canton_keys"),
      affair_types: form.getAll("affair_types"),
      datasets: form.getAll("datasets"),
      keywords: $("subscription-keywords").value.split(/\r?\n/).map((value) => value.trim()).filter(Boolean),
    };
  }

  function editProfile(profile) {
    renderProfileForm(profile);
  }

  function newProfile() {
    renderProfileForm({ id: null, name: "", active: true, category_ids: [], canton_keys: [], affair_types: [], datasets: [], keywords: [] });
  }

  function closeProfileForm() {
    state.editingProfile = null;
    $("profile-form").hidden = true;
  }

  async function saveProfile(event) {
    event.preventDefault();
    const payload = captureProfile();
    const editing = state.editingProfile;
    try {
      await api(editing?.id ? `/api/v1/subscriptions/profiles/${editing.id}` : "/api/v1/subscriptions/profiles",
        { method: editing?.id ? "PUT" : "POST", body: JSON.stringify(payload) });
      closeProfileForm();
      await reload();
      const empty = !payload.category_ids.length && !payload.canton_keys.length && !payload.affair_types.length && !payload.keywords.length;
      toast(empty ? t("profileNoFilter") : t("profileSaved"));
      showStatus("subscription-message", "");
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  async function deleteProfile(profile) {
    if (!confirm(t("profileDeleteConfirm", { name: profile.name }))) return;
    try {
      await api(`/api/v1/subscriptions/profiles/${profile.id}`, { method: "DELETE" });
      if (state.editingProfile?.id === profile.id) closeProfileForm();
      await reload();
      toast(t("profileDeleted"));
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  // --- Watches ----------------------------------------------------------------

  function renderWatches() {
    $("watch-dataset").replaceChildren();
    for (const [key, name] of Object.entries(state.names)) addOption($("watch-dataset"), key, name);
    $("subscription-watches").replaceChildren();
    for (const watch of state.subscriptions?.watches || []) {
      const row = el("div");
      const open = button(`${state.names[watch.dataset]} #${watch.record_id}`, () => {
        $("subscription-dialog").close();
        Polit.detail.show(watch.dataset, watch.record_id);
      });
      const remove = button(t("unwatch"), async () => {
        try {
          await api(`/api/v1/subscriptions/watches/${watch.dataset}/${watch.record_id}`, { method: "DELETE" });
          state.subscriptions.watches = state.subscriptions.watches.filter((item) => item !== watch);
          row.remove();
        } catch (error) {
          showStatus("subscription-message", errorText(error), true);
        }
      });
      row.append(open, remove);
      $("subscription-watches").append(row);
    }
  }

  async function addWatch() {
    const id = Number($("watch-record").value);
    const dataset = $("watch-dataset").value;
    if (!Number.isInteger(id) || id <= 0) return;
    try {
      await api(`/api/v1/subscriptions/watches/${dataset}/${id}`, { method: "PUT" });
      await reload();
      $("watch-record").value = "";
      toast(t("watchSaved"));
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  // --- Dialog -----------------------------------------------------------------

  function render() {
    renderProfiles();
    renderWatches();
    if (state.editingProfile) renderProfileForm(captureProfileDraft());
  }

  /** Keep unsaved edits when the language changes. */
  function captureProfileDraft() {
    return { ...state.editingProfile, ...captureProfile() };
  }

  async function reload() {
    state.subscriptions = await api("/api/v1/subscriptions");
    renderProfiles();
    renderWatches();
  }

  async function open() {
    await Polit.account.refresh();
    if (!state.account) {
      $("account-dialog").showModal();
      return;
    }
    try {
      const [subscriptions, recipients] = await Promise.all([api("/api/v1/subscriptions"), api("/api/v1/subscriptions/recipients")]);
      state.subscriptions = subscriptions;
      closeProfileForm();
      renderProfiles();
      renderWatches();
      if (state.detail) {
        $("watch-dataset").value = state.detail.dataset;
        $("watch-record").value = state.detail.id;
      }
      renderRecipients(recipients);
      showStatus("subscription-message", "");
      await loadDemoTopics();
      $("subscription-dialog").showModal();
    } catch (error) {
      showStatus("message", errorText(error), true);
    }
  }

  async function stopAll() {
    if (!confirm(t("stopConfirm"))) return;
    try {
      await api("/api/v1/subscriptions", { method: "DELETE" });
      closeProfileForm();
      await reload();
      toast(t("stopped"));
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  async function deleteAccount() {
    if (!confirm(t("deleteConfirm"))) return;
    try {
      await api("/api/v1/auth/me", { method: "DELETE" });
      $("subscription-dialog").close();
      state.subscriptions = null;
      await Polit.account.refresh();
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
      toast(errorText(error), true);
    }
  }

  // --- Demo: test notification -----------------------------------------------

  async function loadDemoTopics() {
    $("demo-test").hidden = !state.demo.enabled;
    if (!state.demo.enabled) return;
    const { topics, preselected } = await api("/api/v1/demo/topics");
    $("demo-topic").replaceChildren();
    for (const topic of topics) addOption($("demo-topic"), topic.code, topic.name);
    if (preselected) $("demo-topic").value = preselected;
    $("demo-result").replaceChildren();
  }

  function renderDemoResult(result) {
    const container = $("demo-result");
    container.replaceChildren(el("p", t("demoCreated", {
      title: result.title,
      canton: result.canton || "–",
      topics: result.categories.join(", "),
    })));
    if (!result.notifications_for_user) {
      container.append(el("p", t("demoNoMatch"), "error"));
    } else if (result.emails_failed) {
      container.append(el("p", t("demoMailFailed"), "error"));
    } else {
      container.append(el("p", t("demoMailSent")));
    }
    const actions = el("div", undefined, "agenda-links");
    const mailbox = result.emails_sent && result.mailbox_url ? externalLink(result.mailbox_url, t("demoOpenMailbox")) : null;
    if (mailbox) actions.append(mailbox);
    actions.append(button(t("demoOpenAffair"), () => {
      $("subscription-dialog").close();
      Polit.detail.show("affairs", result.affair_id);
    }));
    container.append(actions);
  }

  /** Use the saved subscriptions and let the backend simulate a new affair. */
  async function sendDemoNotification() {
    if (!(state.subscriptions?.profiles || []).some((profile) => !profile.paused)) {
      $("demo-result").replaceChildren(el("p", t("demoNoProfile"), "error"));
      return;
    }
    const trigger = $("demo-send");
    trigger.disabled = true;
    $("demo-result").replaceChildren(el("p", t("demoSending")));
    try {
      const result = await api("/api/v1/demo/notifications", {
        method: "POST",
        body: JSON.stringify({ category_code: $("demo-topic").value }),
      });
      renderDemoResult(result);
    } catch (error) {
      $("demo-result").replaceChildren(el("p", errorText(error), "error"));
    } finally {
      trigger.disabled = false;
    }
  }

  function bindEvents() {
    $("membership-view").addEventListener("click", open);
    $("recipients-form").addEventListener("submit", saveRecipients);
    $("profile-new").addEventListener("click", newProfile);
    $("profile-form").addEventListener("submit", saveProfile);
    $("profile-cancel").addEventListener("click", closeProfileForm);
    $("unsubscribe").addEventListener("click", stopAll);
    $("subscription-logout").addEventListener("click", () => {
      Polit.account.logout("subscription-message", () => $("subscription-dialog").close());
    });
    $("delete-account").addEventListener("click", deleteAccount);
    $("watch-add").addEventListener("click", addWatch);
    $("demo-send").addEventListener("click", sendDemoNotification);
  }

  Polit.subscriptions = { bindEvents, open, render, reload, isOpen: () => $("subscription-dialog").open };
})();

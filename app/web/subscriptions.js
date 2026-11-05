"use strict";
// Subscription dialog: several subscriptions (filter combinations with
// generated names), individually followed records, notification recipients
// and (in demo mode) a test notification. One button at the bottom saves.
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
    state.recipients = recipients.map((row) => row.email).sort();
    $("recipient-own").checked = recipients.some((row) => row.email === state.account.email);
    $("recipient-emails").value = recipients.filter((row) => row.email !== state.account.email).map((row) => row.email).join("\n");
    renderRecipientStatus(recipients);
  }

  function selectedRecipients() {
    const own = $("recipient-own").checked ? [state.account.email] : [];
    const others = $("recipient-emails").value.split(/\r?\n/).map((value) => value.trim().toLowerCase()).filter(Boolean);
    return [...new Set([...own, ...others])];
  }

  /** Recipients are only sent when they changed, so no confirmation is resent. */
  async function saveRecipients() {
    const emails = selectedRecipients();
    if (emails.slice().sort().join("\n") === (state.recipients || []).join("\n")) return;
    renderRecipients(await api("/api/v1/subscriptions/recipients", { method: "PUT", body: JSON.stringify({ emails }) }));
  }

  // --- Subscriptions ---------------------------------------------------------

  function findCategory(id) {
    for (const parent of state.categories) {
      if (parent.id === id) return parent;
      const child = parent.subcategories.find((row) => row.id === id);
      if (child) return child;
    }
    return null;
  }

  function summary(profile) {
    const all = t("profileAll");
    const topics = profile.category_ids.length
      ? profile.category_ids.map((id) => categoryName(findCategory(id) || { code: String(id) })).join(", ") : all;
    return [
      `${t("topics")}: ${topics}`,
      `${t("cantons")}: ${profile.canton_names.length ? profile.canton_names.join(", ") : all}`,
      `${t("affairTypes")}: ${profile.affair_types.length ? profile.affair_types.join(", ") : all}`,
      `${t("datasets")}: ${profile.datasets.length ? profile.datasets.map((key) => state.names[key]).join(", ") : all}`,
    ];
  }

  /** Name in the interface language; the stored German name is used in emails. */
  function profileTitle(profile) {
    const part = (names, empty) => (!names.length ? empty
      : names.slice(0, 2).join(", ") + (names.length > 2 ? ` +${names.length - 2}` : ""));
    const topics = profile.category_ids.map((id) => categoryName(findCategory(id) || { code: String(id) }));
    const cantons = profile.canton_keys.map((code) => state.cantons.find((row) => row.code === code)?.name || code);
    const parts = [part(topics, t("allTopics")), part(cantons, t("allCantons"))];
    if (profile.affair_types.length) parts.push(part(profile.affair_types, ""));
    return parts.join(" · ");
  }

  function renderProfiles() {
    const list = $("profile-list");
    list.replaceChildren();
    const profiles = state.subscriptions?.profiles || [];
    if (!profiles.length) list.append(el("p", t("profileEmpty"), "hint"));
    for (const profile of profiles) {
      const card = el("article", undefined, "profile-card");
      if (state.editingProfile?.id === profile.id) card.classList.add("editing");
      const heading = el("h4", profileTitle(profile));
      if (profile.paused) heading.append(el("span", t("profilePaused"), "tag paused"));
      card.append(heading);
      for (const line of summary(profile)) card.append(el("p", line, "card-meta"));
      const actions = el("div", undefined, "agenda-links");
      actions.append(
        button(t("profileEdit"), () => renderProfileForm(profile)),
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

  function renderProfileForm(profile, scroll = true) {
    state.editingProfile = profile;
    $("profile-form-title").textContent = t(profile.id ? "profileEditTitle" : "profileNewTitle");
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
    $("subscription-form").hidden = false;
    renderProfiles();
    if (scroll) $("profile-form-title").scrollIntoView({ block: "start", behavior: "smooth" });
  }

  /** Disabled subtopics (covered by their main topic) are not sent. */
  function captureProfile() {
    const form = new FormData($("subscription-form"));
    return {
      active: $("profile-active").checked,
      category_ids: form.getAll("category_ids").map(Number),
      canton_keys: form.getAll("canton_keys"),
      affair_types: form.getAll("affair_types"),
      datasets: form.getAll("datasets"),
    };
  }

  function newProfile() {
    renderProfileForm({ id: null, active: true, category_ids: [], canton_keys: [], affair_types: [], datasets: [] });
  }

  function hideProfileForm() {
    state.editingProfile = null;
    $("subscription-form").hidden = true;
  }

  function closeProfileForm() {
    hideProfileForm();
    renderProfiles();
  }

  const hasFilters = (profile) =>
    Boolean(profile.category_ids.length || profile.canton_keys.length || profile.affair_types.length);

  async function saveProfile() {
    const editing = state.editingProfile;
    const payload = captureProfile();
    await api(editing.id ? `/api/v1/subscriptions/profiles/${editing.id}` : "/api/v1/subscriptions/profiles",
      { method: editing.id ? "PUT" : "POST", body: JSON.stringify(payload) });
    hideProfileForm();
    return payload;
  }

  /** The button at the bottom saves the open subscription and the recipients, then closes. */
  async function save() {
    if (!selectedRecipients().length) {
      showStatus("subscription-message", t("recipientRequired"), true);
      return;
    }
    const trigger = $("subscription-save");
    trigger.disabled = true;
    try {
      const profile = state.editingProfile ? await saveProfile() : null;
      await saveRecipients();
      state.subscriptions = await api("/api/v1/subscriptions");
      showStatus("subscription-message", "");
      $("subscription-dialog").close();
      toast(profile && profile.active && !hasFilters(profile) ? t("profileNoFilter") : t("profileSaved"));
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    } finally {
      trigger.disabled = false;
    }
  }

  async function deleteProfile(profile) {
    if (!confirm(t("profileDeleteConfirm", { name: profileTitle(profile) }))) return;
    try {
      await api(`/api/v1/subscriptions/profiles/${profile.id}`, { method: "DELETE" });
      if (state.editingProfile?.id === profile.id) hideProfileForm();
      state.subscriptions = await api("/api/v1/subscriptions");
      renderProfiles();
      toast(t("profileDeleted"));
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
    }
  }

  // --- Followed records -------------------------------------------------------

  function watchLabel(watch) {
    return `${state.names[watch.dataset]} · ${watch.title || `#${watch.record_id}`}`;
  }

  function renderWatches() {
    const container = $("subscription-watches");
    container.replaceChildren();
    const watches = state.subscriptions?.watches || [];
    if (!watches.length) container.append(el("p", t("watchEmpty"), "hint"));
    for (const watch of watches) {
      const row = el("div", undefined, "watch-row");
      const open = button(watchLabel(watch), () => {
        $("subscription-dialog").close();
        Polit.detail.show(watch.dataset, watch.record_id);
      }, "related-item");
      const remove = button(t("unwatch"), async () => {
        try {
          await unwatch(watch.dataset, watch.record_id);
          renderWatches();
        } catch (error) {
          showStatus("subscription-message", errorText(error), true);
        }
      });
      row.append(open, remove);
      container.append(row);
    }
  }

  function isWatched(dataset, id) {
    return (state.subscriptions?.watches || []).some((watch) => watch.dataset === dataset && watch.record_id === id);
  }

  async function unwatch(dataset, id) {
    await api(`/api/v1/subscriptions/watches/${dataset}/${id}`, { method: "DELETE" });
    state.subscriptions.watches = state.subscriptions.watches.filter((watch) => !(watch.dataset === dataset && watch.record_id === id));
  }

  /** One-click follow button for the detail view. */
  function followButton(dataset, id, title) {
    const node = button("", () => toggle(), "follow-button");
    const update = () => {
      const watched = isWatched(dataset, id);
      node.textContent = watched ? `★ ${t("following")}` : `☆ ${t("follow")}`;
      node.title = watched ? t("unwatch") : t("followHelp");
      node.setAttribute("aria-pressed", String(watched));
    };
    async function toggle() {
      await Polit.account.refresh();
      if (!state.account) {
        toast(t("followSignIn"));
        $("account-dialog").showModal();
        return;
      }
      node.disabled = true;
      try {
        if (!state.subscriptions) state.subscriptions = await api("/api/v1/subscriptions");
        if (isWatched(dataset, id)) {
          await unwatch(dataset, id);
          toast(t("unwatched"));
        } else {
          await api(`/api/v1/subscriptions/watches/${dataset}/${id}`, { method: "PUT" });
          state.subscriptions.watches.push({ dataset, record_id: id, title });
          toast(t("watchSaved"));
        }
      } catch (error) {
        toast(errorText(error), true);
      } finally {
        node.disabled = false;
        update();
      }
    }
    update();
    if (state.account && !state.subscriptions) {
      api("/api/v1/subscriptions").then((overview) => {
        state.subscriptions ||= overview;
        update();
      }).catch(() => {});
    }
    return node;
  }

  // --- Dialog -----------------------------------------------------------------

  /** Re-render after a language change and keep unsaved edits. */
  function render() {
    if (!state.subscriptions) return;
    if (state.editingProfile) renderProfileForm({ ...state.editingProfile, ...captureProfile() }, false);
    else renderProfiles();
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
      hideProfileForm();
      renderProfiles();
      renderWatches();
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
      state.subscriptions = await api("/api/v1/subscriptions");
      closeProfileForm();
      renderWatches();
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
      Polit.account.resetDialog();
      await Polit.account.refresh();
      toast(t("accountDeleted"));
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
    $("subscription-save").addEventListener("click", save);
    $("subscription-form").addEventListener("submit", (event) => {
      event.preventDefault();
      save();
    });
    $("profile-new").addEventListener("click", newProfile);
    $("profile-cancel").addEventListener("click", closeProfileForm);
    $("unsubscribe").addEventListener("click", stopAll);
    $("subscription-logout").addEventListener("click", () => {
      Polit.account.logout("subscription-message", () => $("subscription-dialog").close());
    });
    $("delete-account").addEventListener("click", deleteAccount);
    $("demo-send").addEventListener("click", sendDemoNotification);
  }

  Polit.subscriptions = { bindEvents, open, render, followButton, isOpen: () => $("subscription-dialog").open };
})();

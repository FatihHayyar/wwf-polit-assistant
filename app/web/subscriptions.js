"use strict";
// Subscription dialog: recipients, topics, cantons, datasets, keywords and
// watched records. In demo mode it also triggers a test notification.
(() => {
  const Polit = window.Polit;
  const { ui, state, t, $, el, button, api, errorText, showStatus, addOption, checkbox, categoryName,
    externalLink, toast } = Polit;

  /** Current form values, including unsaved recipient edits. */
  function capture() {
    const form = new FormData($("subscription-form"));
    return {
      ...state.subscriptions,
      recipientOwn: $("recipient-own").checked,
      recipientText: $("recipient-emails").value,
      category_ids: form.getAll("category_ids").map(Number),
      canton_keys: form.getAll("canton_keys"),
      datasets: form.getAll("datasets"),
      keywords: $("subscription-keywords").value.split(/\r?\n/),
    };
  }

  function renderWatches(current) {
    $("watch-dataset").replaceChildren();
    for (const [key, name] of Object.entries(state.names)) addOption($("watch-dataset"), key, name);
    $("subscription-watches").replaceChildren();
    for (const watch of current.watches) {
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

  /** A selected main topic covers its subtopics, which are then disabled. */
  function renderTopics(current) {
    for (const parent of state.categories) {
      const group = el("section", undefined, "topic-group");
      const heading = el("div", undefined, "topic-parent");
      const children = el("div", undefined, "topic-children");
      checkbox(heading, "category_ids", parent.id, categoryName(parent), current.category_ids.includes(parent.id));
      for (const child of parent.subcategories) {
        checkbox(children, "category_ids", child.id, categoryName(child), current.category_ids.includes(child.id));
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

  function renderDatasets(current) {
    const main = el("div", undefined, "dataset-group");
    const support = el("details", undefined, "dataset-group");
    support.append(el("summary", t("supportingRecords")));
    for (const [dataset, name] of Object.entries(state.names)) {
      const target = ui.primaryDatasets.includes(dataset) ? main : support;
      checkbox(target, "datasets", dataset, name, current.datasets.includes(dataset));
    }
    if (current.datasets.some((dataset) => !ui.primaryDatasets.includes(dataset))) support.open = true;
    $("subscription-datasets").append(main, support);
  }

  function render(current) {
    if (current.recipientOwn !== undefined) {
      $("recipient-own").checked = current.recipientOwn;
      $("recipient-emails").value = current.recipientText;
    }
    state.subscriptions = current;
    $("subscription-keywords").value = current.keywords.join("\n");
    renderWatches(current);
    for (const id of ["subscription-categories", "subscription-cantons", "subscription-datasets"]) $(id).replaceChildren();
    renderTopics(current);
    for (const canton of state.cantons) {
      checkbox($("subscription-cantons"), "canton_keys", canton.code, canton.name, current.canton_keys.includes(canton.code));
    }
    renderDatasets(current);
  }

  function renderRecipientStatus(recipients) {
    $("recipient-status").replaceChildren();
    for (const row of recipients) {
      if (!row.verified) $("recipient-status").append(el("p", t("pendingRecipient", { email: row.email })));
    }
  }

  function selectedRecipients() {
    const own = $("recipient-own").checked ? [state.account.email] : [];
    const others = $("recipient-emails").value.split(/\r?\n/).map((value) => value.trim().toLowerCase()).filter(Boolean);
    return [...new Set([...own, ...others])];
  }

  function setToolbarDisabled(disabled) {
    $("subscription-dialog").querySelectorAll(".subscription-toolbar button").forEach((node) => {
      node.disabled = disabled;
    });
  }

  /** Save the form; `clear` removes all subscriptions and watches. */
  async function save(clear = false) {
    if (state.saving) return false;
    const emails = selectedRecipients();
    if (!clear && !emails.length) {
      showStatus("subscription-message", t("recipientRequired"), true);
      return false;
    }
    state.saving = true;
    setToolbarDisabled(true);
    const data = capture();
    const payload = {
      category_ids: clear ? [] : data.category_ids,
      canton_keys: clear ? [] : data.canton_keys,
      datasets: clear ? [] : data.datasets,
      keywords: clear ? [] : data.keywords.map((value) => value.trim()).filter(Boolean),
      clear_watches: clear,
    };
    try {
      if (!clear) {
        renderRecipientStatus(await api("/api/v1/subscriptions/recipients", { method: "PUT", body: JSON.stringify({ emails }) }));
      }
      await api("/api/v1/subscriptions", { method: "PUT", body: JSON.stringify(payload) });
      state.subscriptions = { ...data, ...payload, watches: clear ? [] : data.watches };
      render(state.subscriptions);
      const message = t(clear ? "stopped" : "saved");
      showStatus("subscription-message", message);
      toast(message);
      return true;
    } catch (error) {
      showStatus("subscription-message", errorText(error), true);
      toast(errorText(error), true);
      return false;
    } finally {
      state.saving = false;
      setToolbarDisabled(false);
    }
  }

  async function open() {
    await Polit.account.refresh();
    if (!state.account) {
      $("account-dialog").showModal();
      return;
    }
    try {
      const [current, recipients] = await Promise.all([api("/api/v1/subscriptions"), api("/api/v1/subscriptions/recipients")]);
      render(current);
      if (state.detail) {
        $("watch-dataset").value = state.detail.dataset;
        $("watch-record").value = state.detail.id;
      }
      $("recipient-own").checked = recipients.some((row) => row.email === state.account.email);
      $("recipient-emails").value = recipients.filter((row) => row.email !== state.account.email).map((row) => row.email).join("\n");
      renderRecipientStatus(recipients);
      showStatus("subscription-message", "");
      await loadDemoTopics();
      $("subscription-dialog").showModal();
    } catch (error) {
      showStatus("message", errorText(error), true);
    }
  }

  async function addWatch() {
    const id = Number($("watch-record").value);
    const dataset = $("watch-dataset").value;
    if (!Number.isInteger(id) || id <= 0) return;
    try {
      const draft = capture();
      await api(`/api/v1/subscriptions/watches/${dataset}/${id}`, { method: "PUT" });
      if (!draft.watches.some((row) => row.dataset === dataset && row.record_id === id)) draft.watches.push({ dataset, record_id: id });
      render(draft);
      $("watch-record").value = "";
      toast(t("saved"));
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

  // --- Demo: test notification -------------------------------------------

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

  /** Save the current choices, then let the backend simulate a new affair. */
  async function sendDemoNotification() {
    const trigger = $("demo-send");
    trigger.disabled = true;
    $("demo-result").replaceChildren(el("p", t("demoSending")));
    try {
      if (!await save()) {
        $("demo-result").replaceChildren();
        return;
      }
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
    $("subscription-form").addEventListener("submit", (event) => {
      event.preventDefault();
      save();
    });
    $("unsubscribe").addEventListener("click", () => {
      if (confirm(t("stopConfirm"))) save(true);
    });
    $("subscription-logout").addEventListener("click", () => {
      Polit.account.logout("subscription-message", () => $("subscription-dialog").close());
    });
    $("delete-account").addEventListener("click", deleteAccount);
    $("watch-add").addEventListener("click", addWatch);
    $("demo-send").addEventListener("click", sendDemoNotification);
  }

  Polit.subscriptions = { bindEvents, open, capture, render, isOpen: () => $("subscription-dialog").open };
})();

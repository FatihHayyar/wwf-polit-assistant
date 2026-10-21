"use strict";
// Shared state, translations and DOM helpers used by all frontend modules.
// Modules attach themselves to window.Polit and look each other up at call
// time, so the load order in index.html only matters for core.js itself.
window.Polit = (() => {
  const ui = window.PolitUI;

  const state = {
    language: ui.readLanguage(),
    names: {},
    dataset: "affairs",
    filterDrafts: {},
    controller: null,
    page: 1,
    pages: 0,
    categories: [],
    cantons: [],
    account: null,
    // Context filters set when browsing records related to another record.
    affairId: null,
    groupId: null,
    personId: null,
    agendaId: null,
    meetingId: null,
    request: 0,
    detailRequest: 0,
    detail: null,
    subscriptions: null,
    result: null,
    saving: false,
    demo: { enabled: false, mailboxUrl: null },
  };
  state.names = ui.datasets(state.language);

  const t = (key, values) => ui.t(state.language, key, values);
  const $ = (id) => document.getElementById(id);

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function button(text, onClick, className) {
    const node = el("button", text, className);
    node.type = "button";
    node.addEventListener("click", onClick);
    return node;
  }

  class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.status = status;
    }
  }

  async function api(path, options = {}) {
    const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers };
    const response = await fetch(path, { credentials: "same-origin", ...options, headers });
    if (!response.ok) {
      let detail;
      try {
        detail = (await response.json()).detail;
      } catch {
        detail = response.statusText;
      }
      throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), response.status);
    }
    return response.status === 204 ? null : response.json();
  }

  /** Message for an API error; rate limits get a translated hint. */
  function errorText(error) {
    return error.status === 429 ? t("tooManyRequests") : error.message;
  }

  function showStatus(id, text, error = false) {
    const node = $(id);
    node.textContent = text;
    node.classList.toggle("error", error);
    node.hidden = !text;
  }

  function addOption(select, value, label) {
    const node = el("option", label);
    node.value = value;
    select.append(node);
  }

  function checkbox(container, name, value, label, checked = false) {
    const wrapper = el("label");
    const input = el("input");
    input.type = "checkbox";
    input.name = name;
    input.value = value;
    input.checked = checked;
    wrapper.append(input, document.createTextNode(label));
    container.append(wrapper);
  }

  /** Only http(s) links from source data are rendered. */
  function safeLink(url) {
    try {
      const parsed = new URL(url, location.origin);
      return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : null;
    } catch {
      return null;
    }
  }

  function externalLink(url, text, className) {
    const href = safeLink(url);
    if (!href) return null;
    const link = el("a", text, className);
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  }

  function formatDate(value) {
    if (!value) return t("noDate");
    return new Intl.DateTimeFormat(`${state.language}-CH`, { dateStyle: "medium", timeZone: "Europe/Zurich" })
      .format(new Date(value));
  }

  function categoryName(item) {
    const code = item.code || item.category_code;
    const category = state.categories
      .flatMap((parent) => [parent, ...parent.subcategories])
      .find((row) => row.code === code);
    return ui.localized(category || item, "name", state.language) || item.category_name_de || item.name || code;
  }

  /** "Main topic / subtopic"; the global fallback has no parent. */
  function categoryPath(item) {
    const code = item.code || item.category_code;
    const parent = state.categories.find((row) => row.subcategories.some((child) => child.code === code));
    const parentName = parent ? categoryName(parent) : item.parent_category_name_de;
    return parentName ? `${parentName} / ${categoryName(item)}` : categoryName(item);
  }

  function sourceTitle(dataset, record) {
    return ui.localized(record, "title", state.language)
      || ui.localized(record, "name", state.language)
      || record.item_title
      || record.name
      || state.names[dataset];
  }

  /** Records without own titles show the title of their context, e.g. the affair. */
  function recordTitle(dataset, item) {
    const title = item.title || state.names[dataset];
    const usesContext = ["events", "votings", "texts", "documents"].includes(dataset);
    return usesContext && item.context_title && item.context_title !== title ? `${title} · ${item.context_title}` : title;
  }

  let toastTimer;
  function toast(message, error = false) {
    clearTimeout(toastTimer);
    showStatus("toast", message, error);
    const dialog = $("subscription-dialog");
    const toolbar = dialog.querySelector(".subscription-toolbar");
    $("toast").style.bottom = dialog.open
      ? `${window.innerHeight - toolbar.getBoundingClientRect().top + 12}px`
      : "90px";
    $("toast").showPopover?.();
    toastTimer = setTimeout(() => {
      $("toast").hidePopover?.();
      showStatus("toast", "");
    }, 6000);
  }

  return {
    ui, state, t, $, el, button, api, ApiError, errorText, showStatus, addOption, checkbox,
    safeLink, externalLink, formatDate, categoryName, categoryPath, sourceTitle, recordTitle, toast,
  };
})();

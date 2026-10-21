"use strict";
// Dataset navigation, search filters, result list and pagination.
(() => {
  const Polit = window.Polit;
  const { state, t, $, el, button, api, showStatus, addOption, formatDate, categoryName, categoryPath,
    recordTitle, externalLink } = Polit;

  const CONTEXT_FILTERS = {
    affairId: "affair_id",
    groupId: "group_id",
    personId: "person_id",
    agendaId: "agenda_id",
    meetingId: "meeting_id",
  };

  function updateSubcategories(preserve = false) {
    const select = $("subcategory");
    const previous = preserve ? select.value : "";
    const parent = state.categories.find((item) => item.code === $("category").value);
    select.replaceChildren();
    addOption(select, "", t("allSubtopics"));
    for (const child of parent?.subcategories || []) addOption(select, child.code, categoryName(child));
    if (previous) select.value = previous;
  }

  function renderDatasetNavigation() {
    $("datasets").replaceChildren();
    for (const [dataset, name] of Object.entries(state.names)) {
      const node = button(name, () => chooseDataset(dataset));
      node.dataset.value = dataset;
      $("datasets").append(node);
    }
    markActiveDataset();
  }

  function markActiveDataset() {
    for (const node of $("datasets").children) {
      const active = node.dataset.value === state.dataset;
      node.classList.toggle("active", active);
      node.setAttribute("aria-pressed", String(active));
    }
  }

  /** Rebuild the filter selects in the current language, keeping selections. */
  function renderFilterOptions() {
    const category = $("category").value;
    $("category").replaceChildren();
    addOption($("category"), "", t("allTopics"));
    for (const item of state.categories) addOption($("category"), item.code, categoryName(item));
    $("category").value = category;
    updateSubcategories(true);

    const canton = $("canton").value;
    $("canton").replaceChildren();
    addOption($("canton"), "", t("allCantons"));
    for (const row of state.cantons) addOption($("canton"), row.code, row.name);
    $("canton").value = canton;

    const affairType = $("affair-type").value;
    $("affair-type").replaceChildren();
    addOption($("affair-type"), "", t("allAffairTypes"));
    for (const value of state.affairTypes) addOption($("affair-type"), value, value);
    $("affair-type").value = affairType;
    updateAffairTypeFilter();
  }

  /** Affair types only exist for affairs; a disabled select is not submitted. */
  function updateAffairTypeFilter() {
    const visible = state.dataset === "affairs";
    $("affair-type-filter").hidden = !visible;
    $("affair-type").disabled = !visible;
  }

  function hasContextFilter() {
    return Object.keys(CONTEXT_FILTERS).some((key) => state[key]);
  }

  function clearContextFilters() {
    for (const key of Object.keys(CONTEXT_FILTERS)) state[key] = null;
  }

  function renderContextNavigation() {
    const container = $("context-navigation");
    container.replaceChildren();
    container.hidden = !hasContextFilter();
    if (!container.hidden) container.append(button(t("backToAffairs"), () => chooseDataset(state.dataset)));
  }

  /** Switch dataset; each dataset keeps its own filter draft. */
  function chooseDataset(dataset, filters = {}) {
    state.filterDrafts[state.dataset] = Object.fromEntries(new FormData($("search-form")));
    showDataset(dataset, filters);
  }

  /** Show a dataset with the given filter values, e.g. from a question. */
  function applyFilters(dataset, values) {
    state.filterDrafts[state.dataset] = Object.fromEntries(new FormData($("search-form")));
    state.filterDrafts[dataset] = { ...values };
    showDataset(dataset);
  }

  function showDataset(dataset, filters = {}) {
    state.result = null;
    state.dataset = dataset;
    state.page = 1;

    const draft = state.filterDrafts[dataset] || {};
    for (const node of $("search-form").elements) {
      if (node.name) node.value = draft[node.name] || "";
    }
    updateSubcategories();
    $("subcategory").value = draft.subcategory || "";
    for (const key of Object.keys(CONTEXT_FILTERS)) state[key] = filters[key] || null;

    $("heading").textContent = state.names[dataset];
    markActiveDataset();
    updateAffairTypeFilter();
    loadResults();
    renderContextNavigation();
  }

  /** Leave the detail dialog and list all records related to it. */
  function browseRelated(dataset, filters) {
    $("detail-dialog").close();
    $("search-form").reset();
    setTimeout(() => chooseDataset(dataset, filters), 1);
  }

  function searchParams() {
    const params = new URLSearchParams(new FormData($("search-form")));
    for (const [key, value] of [...params]) {
      if (!value) params.delete(key);
    }
    params.set("page", state.page);
    for (const [key, param] of Object.entries(CONTEXT_FILTERS)) {
      if (state[key]) params.set(param, state[key]);
    }
    return params;
  }

  async function loadResults() {
    const request = ++state.request;
    const dataset = state.dataset;
    state.controller?.abort();
    state.controller = new AbortController();

    $("results").setAttribute("aria-busy", "true");
    showStatus("message", "");
    $("previous").disabled = true;
    $("next").disabled = true;
    $("result-count").textContent = t("loading");
    try {
      const result = await api(`/api/v1/entities/${dataset}?${searchParams()}`, { signal: state.controller.signal });
      if (request !== state.request) return;
      state.result = result;
      renderResults(result);
    } catch (error) {
      if (request === state.request) {
        showStatus("message", error.message, true);
        $("result-count").textContent = t("loadError");
        $("results").replaceChildren();
      }
    } finally {
      if (request === state.request) $("results").setAttribute("aria-busy", "false");
    }
  }

  function resultCard(item) {
    const dataset = item.dataset || state.dataset;
    const showDetail = Polit.detail.show;
    const card = el("article", undefined, "result-card");
    card.append(
      el("span", state.names[dataset], "tag type-tag"),
      el("div", `${item.canton || t("noCanton")} · ${formatDate(item.date)}`, "card-meta"),
    );
    if (dataset === "agendas") {
      const kind = t(item.title_origin === "meeting" ? "meetingAgenda" : "agendaItem");
      card.append(el("p", kind + (item.item_number ? ` · ${item.item_number}` : ""), "card-meta"));
    }

    const heading = el("h2");
    heading.append(button(recordTitle(dataset, item), () => showDetail(dataset, item.id)));
    card.append(heading);

    const context = [item.body?.name, item.kind, item.state, item.person?.fullname, item.role, item.group?.title,
      item.location, item.decision].filter(Boolean);
    if (context.length) card.append(el("p", context.join(" · "), "card-context"));

    const tags = el("div", undefined, "tags");
    for (const category of item.categories) tags.append(el("span", categoryPath(category), "tag"));
    if (!item.categories.length && dataset !== "agendas") tags.append(el("span", t("noClassification"), "tag"));
    card.append(tags);

    // Grouped results: same title, body and day share one card.
    if (item.record_variants?.length) {
      const variants = el("div", undefined, "agenda-links");
      for (const variant of item.record_variants) {
        const label = [variant.kind, variant.number].filter(Boolean).join(" · ") || variant.title;
        variants.append(button(label, () => showDetail(dataset, variant.id)));
      }
      card.append(variants);
    }

    const links = el("div", undefined, "agenda-links");
    if (item.meeting) {
      const label = item.title_origin === "meeting" ? t("openMeeting") : item.meeting.title || t("meetings");
      links.append(button(label, () => showDetail("meetings", item.meeting.id)));
    }
    if (item.affair) links.append(button(item.affair.number || t("openAffair"), () => showDetail("affairs", item.affair.id)));
    const source = item.source_url ? externalLink(item.source_url, t("officialSource")) : null;
    if (source) links.append(source);
    card.append(links);
    return card;
  }

  function renderResults(result) {
    state.pages = result.pagination.total_pages;
    $("results").replaceChildren();
    const total = result.pagination.total_items.toLocaleString(`${state.language}-CH`);
    $("result-count").textContent = t("resultCount", { count: total });
    for (const item of result.items) $("results").append(resultCard(item));
    if (!result.items.length) $("results").append(el("div", t("empty"), "empty"));

    $("page-label").textContent = state.pages ? t("page", { page: state.page, pages: state.pages }) : t("noResults");
    $("previous").disabled = state.page <= 1;
    $("next").disabled = state.page >= state.pages;
  }

  function bindEvents() {
    $("category").addEventListener("change", () => updateSubcategories());
    $("search-form").addEventListener("submit", (event) => {
      event.preventDefault();
      state.page = 1;
      loadResults();
    });
    $("search-form").addEventListener("reset", () => {
      delete state.filterDrafts[state.dataset];
      clearContextFilters();
      setTimeout(() => {
        state.page = 1;
        updateSubcategories();
        loadResults();
      }, 0);
    });
    $("previous").addEventListener("click", () => {
      if (state.page > 1) {
        state.page--;
        loadResults();
      }
    });
    $("next").addEventListener("click", () => {
      if (state.page < state.pages) {
        state.page++;
        loadResults();
      }
    });
  }

  Polit.search = {
    bindEvents, chooseDataset, applyFilters, browseRelated, renderDatasetNavigation, renderFilterOptions,
    renderContextNavigation, renderResults,
  };
})();

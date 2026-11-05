"use strict";
// Dialogue-oriented query: questions become search filters, and the recognised
// filters can be kept as a subscription. Earlier questions stay visible as a conversation.
(() => {
  const Polit = window.Polit;
  const { state, t, $, el, button, api, errorText, formatDate, categoryName, toast } = Polit;

  const KIND_LABELS = {
    dataset: "kindDataset", category: "kindCategory", subcategory: "kindSubcategory", canton: "kindCanton",
    affair_type: "kindAffairType", period: "kindPeriod", keyword: "kindKeyword",
  };

  function cantonName(code) {
    return state.cantons.find((row) => row.code === code)?.name || code;
  }

  function periodLabel(filters) {
    const parts = [];
    if (filters.date_from) parts.push(t("periodSince", { date: formatDate(filters.date_from) }));
    if (filters.date_to) parts.push(t("periodUntil", { date: formatDate(filters.date_to) }));
    return parts.join(" ");
  }

  function chipText(item, answer) {
    switch (item.kind) {
      case "dataset": return state.names[item.value];
      case "category":
      case "subcategory": return categoryName({ code: item.value });
      case "canton": return cantonName(item.value);
      case "period": return periodLabel(answer.filters);
      default: return item.value;
    }
  }

  function categoryId(code) {
    for (const parent of state.categories) {
      if (parent.code === code) return parent.id;
      const child = parent.subcategories.find((row) => row.code === code);
      if (child) return child.id;
    }
    return null;
  }

  /** A subscription needs at least one topic, canton or affair type; a
   * recognised keyword alone is not saved. */
  function profileFrom(answer) {
    const { filters } = answer;
    const topic = categoryId(filters.subcategory || filters.category);
    const profile = {
      active: true,
      category_ids: topic ? [topic] : [],
      canton_keys: filters.canton ? [filters.canton] : [],
      affair_types: filters.affair_type ? [filters.affair_type] : [],
      datasets: [answer.dataset],
    };
    return profile.category_ids.length || profile.canton_keys.length || profile.affair_types.length ? profile : null;
  }

  async function saveProfile(answer, trigger) {
    await Polit.account.refresh();
    if (!state.account) {
      toast(t("askSignIn"));
      $("account-dialog").showModal();
      return;
    }
    trigger.disabled = true;
    try {
      const saved = await api("/api/v1/subscriptions/profiles", { method: "POST", body: JSON.stringify(profileFrom(answer)) });
      state.subscriptions = null;
      toast(t("askSaved", { name: saved.name }));
    } catch (error) {
      toast(errorText(error), true);
      trigger.disabled = false;
    }
  }

  function renderAnswer(answer) {
    const entry = el("article", undefined, "ask-entry");
    entry.append(el("p", answer.question, "ask-question"));
    const reply = el("div", undefined, "ask-answer");
    const recognised = answer.recognised.filter((item) => KIND_LABELS[item.kind]);
    if (recognised.length) {
      const chips = el("div", undefined, "tags");
      chips.append(el("span", t("askUnderstood"), "ask-understood"));
      for (const item of recognised) chips.append(el("span", `${t(KIND_LABELS[item.kind])}: ${chipText(item, answer)}`, "tag"));
      reply.append(chips);
    } else {
      reply.append(el("p", t("askNothing")));
    }
    const count = answer.results.pagination.total_items;
    reply.append(el("p", count
      ? t("askAnswer", { count: count.toLocaleString(`${state.language}-CH`), dataset: state.names[answer.dataset] })
      : t("askNone")));
    if (profileFrom(answer)) reply.append(button(t("askSave"), (event) => saveProfile(answer, event.currentTarget)));
    entry.append(reply);
    $("ask-log").prepend(entry);
  }

  async function ask(event) {
    event.preventDefault();
    const question = $("ask-input").value.trim();
    if (question.length < 3) return;
    const submit = $("ask-form").querySelector("button");
    submit.disabled = true;
    try {
      const answer = await api("/api/v1/ask", { method: "POST", body: JSON.stringify({ question }) });
      renderAnswer(answer);
      const { filters } = answer;
      Polit.search.applyFilters(answer.dataset, {
        q: filters.q || "", category: filters.category || "", subcategory: filters.subcategory || "",
        canton: filters.canton || "", affair_type: filters.affair_type || "",
        date_from: filters.date_from || "", date_to: filters.date_to || "",
      });
      $("ask-input").value = "";
    } catch (error) {
      toast(errorText(error), true);
    } finally {
      submit.disabled = false;
    }
  }

  function bindEvents() {
    $("ask-form").addEventListener("submit", ask);
  }

  Polit.ask = { bindEvents };
})();

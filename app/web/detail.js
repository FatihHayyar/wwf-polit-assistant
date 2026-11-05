"use strict";
// Detail dialog of a single record with its linked records and change history.
(() => {
  const Polit = window.Polit;
  const { ui, state, t, $, el, button, api, formatDate, categoryPath, sourceTitle, recordTitle, externalLink } = Polit;

  async function show(dataset, id) {
    const request = ++state.detailRequest;
    state.detail = null;
    $("detail-title").textContent = state.names[dataset];
    $("detail-content").replaceChildren(el("p", t("detailLoading")));
    if (!$("detail-dialog").open) $("detail-dialog").showModal();
    try {
      const data = await api(`/api/v1/entities/${dataset}/${id}`);
      if (request !== state.detailRequest || !$("detail-dialog").open) return;
      state.detail = { dataset, id, data };
      render();
    } catch (error) {
      if (request === state.detailRequest) $("detail-content").replaceChildren(el("p", error.message, "error"));
    }
  }

  function relatedButton(label, dataset, id) {
    return button(label, () => show(dataset, id), "related-item");
  }

  function section(title) {
    const node = el("section", undefined, "related-section");
    node.append(el("h3", title));
    return node;
  }

  /** Preview of related records with a link to the full filtered list. */
  function renderRelated(container, dataset, result, filters, moreLabel = "all") {
    if (!result?.pagination.total_items) return;
    const node = section(`${state.names[dataset]} (${result.pagination.total_items})`);
    for (const item of result.items) {
      const label = `${formatDate(item.date)} · ${recordTitle(dataset, item)}${item.decision ? ` · ${item.decision}` : ""}`;
      node.append(relatedButton(label, dataset, item.id));
    }
    if (result.pagination.total_items > result.items.length) {
      node.append(button(t(moreLabel), () => Polit.search.browseRelated(dataset, filters)));
    }
    container.append(node);
  }

  function renderFields(container, dataset, data, record) {
    const context = data.detail || (data.body ? { canton: data.body.canton, body_name_de: data.body.name } : null);
    const fields = el("dl", undefined, "detail-fields");
    for (const [key, value, kind] of ui.detailFields(dataset, record, context, state.language)) {
      fields.append(el("dt", t(key)), el("dd", kind === "date" ? formatDate(value) : String(value)));
    }
    container.append(fields);
    return fields;
  }

  function renderAgendaContext(container, fields, data, id) {
    if (data.item_number) fields.append(el("dt", t("agendaItem")), el("dd", data.item_number));
    if (data.title_origin === "meeting") container.append(el("p", t("meetingAgendaHelp")));
    if (data.meeting) {
      const node = section(t("meetings"));
      node.append(relatedButton(`${formatDate(data.meeting.date)} · ${data.meeting.title || t("openMeeting")}`,
        "meetings", data.meeting.id));
      container.append(node);
    }
    if (data.group) container.append(button(data.group.title || t("groups"), () => show("groups", data.group.id)));
    if (data.documents) renderRelated(container, "documents", data.documents, { agendaId: id });
  }

  function renderVoteResult(container, record) {
    const node = section(t("voteResult"));
    const results = el("dl", undefined, "detail-fields");
    const counts = [["yes", "results_yes"], ["no", "results_no"], ["abstention", "results_abstention"], ["absent", "results_absent"]];
    for (const [key, field] of counts) {
      if (record[field] !== null && record[field] !== undefined) results.append(el("dt", t(key)), el("dd", String(record[field])));
    }
    if (results.children.length) {
      node.append(results);
      container.append(node);
    }
  }

  function renderOriginalText(container, dataset, record) {
    const lang = state.language;
    const content = ui.localized(record, "title_long", lang)
      || ui.localized(record, "description", lang)
      || ui.localized(record, "text", lang)
      || record.item_description
      || record.text
      || record.details_text;
    if (content && content !== sourceTitle(dataset, record)) {
      const disclosure = el("details", undefined, "original-text");
      disclosure.append(el("summary", t("fullText")), el("p", content));
      container.append(disclosure);
    }
  }

  function renderSourceLinks(container, record, data) {
    const urls = new Set([ui.localized(record, "url_external", state.language), record.item_url, record.url,
      record.details_url, record.declaration_doc_url, data.detail?.original_url].filter(Boolean));
    for (const url of urls) {
      const link = externalLink(url, t("officialSource"), "source-link");
      if (link) container.append(link);
    }
    container.append(el("p", t("sourceLanguage"), "source-language"));
  }

  /** Affair details: classification, related datasets and change history. */
  function renderAffairDetail(container, detail, id) {
    if (detail.classifications.length) {
      const node = section(t("classification"));
      const tags = el("div", undefined, "tags");
      for (const item of detail.classifications) tags.append(el("span", categoryPath(item), "tag"));
      node.append(tags);
      container.append(node);
    }
    for (const [relatedDataset, result] of Object.entries(detail.related)) {
      renderRelated(container, relatedDataset, result, { affairId: id });
    }
    if (!detail.changes.length) return;
    const node = section(t("changes"));
    for (const change of detail.changes) {
      const row = el(change.available ? "button" : "p", undefined, change.available ? "related-item change-item" : "change");
      const datasetName = state.names[change.dataset] || change.dataset;
      row.append(
        el("span", change.title || datasetName, "change-title"),
        el("span", `${formatDate(change.detected_at)} · ${datasetName} · ${t(change.change_type)}`, "card-meta"),
      );
      if (change.available) {
        row.type = "button";
        row.addEventListener("click", () => show(change.dataset, change.source_id));
      }
      node.append(row);
    }
    container.append(node);
  }

  function render() {
    if (!state.detail) return;
    const { dataset, id, data } = state.detail;
    const record = data.record;
    const container = $("detail-content");
    $("detail-title").textContent = state.names[dataset];
    const title = recordTitle(dataset, { ...data, title: data.title || sourceTitle(dataset, record) });
    container.replaceChildren(el("h3", title, "record-title"), Polit.subscriptions.followButton(dataset, id, title));

    const fields = renderFields(container, dataset, data, record);
    if (dataset === "agendas") renderAgendaContext(container, fields, data, id);
    if (data.agendas) renderRelated(container, "agendas", data.agendas, { meetingId: id });
    if (data.related) {
      for (const [key, result] of Object.entries(data.related)) renderRelated(container, key, result, { meetingId: id });
    }
    if (data.agenda) {
      container.append(relatedButton(`${state.names.agendas} · ${data.agenda.title || data.agenda.id}`, "agendas", data.agenda.id));
    }
    if (dataset !== "agendas" && data.meeting) {
      container.append(relatedButton(data.meeting.title || t("openMeeting"), "meetings", data.meeting.id));
    }
    if (dataset !== "agendas" && data.group) {
      container.append(button(data.group.title || t("groups"), () => show("groups", data.group.id)));
    }
    if (dataset === "votings") renderVoteResult(container, record);
    const actor = dataset === "events" ? ui.localized(record, "actor", state.language) : null;
    if (actor) fields.append(el("dt", t("actor")), el("dd", actor));

    renderOriginalText(container, dataset, record);
    renderSourceLinks(container, record, data);

    if (dataset !== "affairs") {
      for (const affair of data.linked_affairs || data.affair_ids.map((affairId) => ({ id: affairId }))) {
        const label = `${t("linkedAffair", { id: affair.id })}${affair.title ? ` · ${affair.title}` : ""}`;
        container.append(relatedButton(label, "affairs", affair.id));
      }
    }
    if (data.person) {
      const party = data.person.party ? ` · ${data.person.party}` : "";
      container.append(el("h3", t("person")), el("p", `${data.person.fullname || t("person")}${party}`));
      container.append(button(t("personInterests"), () => Polit.search.browseRelated("interests", { personId: data.person.id })));
    }
    if (data.meetings) renderRelated(container, "meetings", data.meetings, { groupId: id }, "groupMeetings");
    if (data.detail) renderAffairDetail(container, data.detail, id);
  }

  Polit.detail = { show, render };
})();

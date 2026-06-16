const { $, escapeHtml } = window.Postovaya.utils;
const { STORAGE, DEFAULT_POST_STYLES, state, save, audiencesForVenue } = window.Postovaya.store;
const api = window.Postovaya.api;

const els = {
  venue: $("#venueSelect"), audience: $("#audienceSelect"), context: $("#contextPreview"),
  topic: $("#topicInput"), materials: $("#materialsInput"), materialsCount: $("#materialsCount"),
  postStyle: $("#postStyleSelect"), form: $("#composerForm"),
  generate: $("#generateButton"), error: $("#formError"), empty: $("#emptyState"),
  generateLabel: $("#generateButtonLabel"),
  loading: $("#loadingState"), editorState: $("#editorState"), result: $("#resultEditor"),
  resultCount: $("#resultCount"), demo: $("#demoBanner"), saveState: $("#saveState"),
  imageInput: $("#imageInput"), imageChip: $("#imageChip"), imageThumb: $("#imageThumb"),
  imageName: $("#imageName"), resultImage: $("#resultImage"), attached: $("#attachedPreview"),
  drafts: $("#draftList"), aiStatus: $("#aiStatus"), draftSearch: $("#draftSearch"),
  profilesView: $("#profilesView"), venueDetailView: $("#venueDetailView"), editorView: $("#editorView"), draftsView: $("#draftsView"),
  sidebarToggle: $("#sidebarToggle"), venueTree: $("#venueTree"), profileName: $("#profileName"),
  venueDialog: $("#venueDialog"), venueForm: $("#venueForm"), venueFormError: $("#venueFormError"), audienceDialog: $("#audienceDialog"),
  audienceForm: $("#audienceForm"), audienceFormError: $("#audienceFormError"), audienceName: $("#audienceName"), audiencePortrait: $("#audiencePortrait"), audienceNeeds: $("#audienceNeeds"),
  readinessBanner: $("#readinessBanner"), venueDetailForm: $("#venueDetailForm"), venueDetailTitle: $("#venueDetailTitle"),
  venueDetailStatus: $("#venueDetailStatus"), venueDetailName: $("#venueDetailName"), venueDetailDescription: $("#venueDetailDescription"),
  venueDetailVoice: $("#venueDetailVoice"), venueDetailError: $("#venueDetailError"), venueAudienceList: $("#venueAudienceList"), venueDraftList: $("#venueDraftList"),
  toast: $("#toast"), toastMessage: $("#toastMessage"),
};

let toastTimer;
let activeVenueId = "";
const dialogSnapshots = new Map();

function setResultStatus(status) {
  els.saveState.textContent = status;
  els.saveState.dataset.status = status;
}

function showToast(message) {
  clearTimeout(toastTimer);
  els.toastMessage.textContent = message;
  els.toast.classList.add("visible");
  toastTimer = setTimeout(() => els.toast.classList.remove("visible"), 3200);
}

function formSnapshot(form) {
  return JSON.stringify(Array.from(form.elements)
    .filter(element => element.matches("input, textarea, select"))
    .map(element => [element.id, element.value]));
}

function rememberDialog(dialog, form) {
  dialogSnapshots.set(dialog.id, formSnapshot(form));
}

function closeDialog(dialog, form, force = false) {
  const changed = formSnapshot(form) !== dialogSnapshots.get(dialog.id);
  if (!force && changed && !window.confirm("Закрыть без сохранения? Введённые данные будут потеряны.")) return false;
  dialog.close();
  dialogSnapshots.delete(dialog.id);
  return true;
}

function renderSelects() {
  const currentVenue = els.venue.value;
  const currentAudience = els.audience.value;
  els.venue.innerHTML = state.venues.length
    ? state.venues.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("")
    : '<option value="">Сначала добавьте заведение</option>';
  els.venue.disabled = !state.venues.length;
  if (state.venues.some(x => x.id === currentVenue)) els.venue.value = currentVenue;
  renderAudienceSelect(currentAudience);
  renderContext();
}

function renderAudienceSelect(preferredId = "") {
  const audiences = audiencesForVenue(els.venue.value);
  els.audience.innerHTML = audiences.length
    ? audiences.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("")
    : '<option value="">У этого заведения пока нет аудиторий</option>';
  els.audience.disabled = !audiences.length;
  if (audiences.some(item => item.id === preferredId)) els.audience.value = preferredId;
}

function renderPostStyles() {
  const venue = state.venues.find(item => item.id === els.venue.value);
  const styles = venue?.recommendedStyles?.length ? venue.recommendedStyles : DEFAULT_POST_STYLES;
  const current = els.postStyle.value;
  els.postStyle.innerHTML = styles.map(style => `<option value="${escapeHtml(style)}">${escapeHtml(style)}</option>`).join("");
  if (styles.includes(current)) els.postStyle.value = current;
}

function renderContext() {
  const venue = state.venues.find(item => item.id === els.venue.value);
  const audience = state.audiences.find(item => item.id === els.audience.value && item.venueId === venue?.id);
  const chips = [venue?.description, audience?.needs].filter(Boolean);
  els.context.innerHTML = chips.map(value => `<span>${escapeHtml(value.length > 75 ? value.slice(0, 75) + "…" : value)}</span>`).join("");
  renderPostStyles();
}

function renderDrafts(query = "") {
  const normalized = query.trim().toLocaleLowerCase("ru-RU");
  const drafts = state.drafts.filter(draft => {
    const haystack = `${draft.topic} ${draft.venue} ${draft.audience} ${draft.text}`.toLocaleLowerCase("ru-RU");
    return !normalized || haystack.includes(normalized);
  });
  if (!drafts.length) {
    els.drafts.innerHTML = `<p class="muted">${normalized ? "По вашему запросу ничего не найдено." : "Сохранённых черновиков пока нет."}</p>`;
    return;
  }
  els.drafts.innerHTML = drafts.map(draft => {
    const index = state.drafts.indexOf(draft);
    return `
    <article class="draft-item">
      <button class="draft-open" type="button" data-draft="${index}">
        <span><strong>${escapeHtml(draft.topic || "Без темы")}</strong>
        <small>${escapeHtml(draft.venue)} · ${escapeHtml(draft.audience || "Аудитория не указана")}</small></span>
        <span class="draft-item-end"><time>${new Date(draft.createdAt).toLocaleDateString("ru-RU")}</time><span class="draft-item-action">Продолжить редактирование</span><span class="draft-chevron" aria-hidden="true">›</span></span>
      </button>
      <button class="draft-delete" type="button" data-remove-draft="${index}" aria-label="Удалить черновик">Удалить</button>
    </article>`;
  }).join("");
}

function switchView(view) {
  els.profilesView.classList.toggle("hidden", view !== "profiles");
  els.venueDetailView.classList.toggle("hidden", view !== "venue");
  els.editorView.classList.toggle("hidden", view !== "editor");
  els.draftsView.classList.toggle("hidden", view !== "drafts");
  document.querySelectorAll("[data-view]").forEach(button => {
    const active = button.dataset.view === view;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (view === "profiles") renderProfiles();
  if (view === "venue") renderVenueDetail();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setSidebarCollapsed(collapsed) {
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  els.sidebarToggle.textContent = collapsed ? "☰" : "‹";
  els.sidebarToggle.setAttribute("aria-label", collapsed ? "Показать боковую панель" : "Скрыть боковую панель");
  els.sidebarToggle.title = collapsed ? "Показать боковую панель" : "Скрыть боковую панель";
  localStorage.setItem(STORAGE.sidebarCollapsed, collapsed ? "true" : "false");
}

function setView(name) {
  els.empty.classList.toggle("hidden", name !== "empty");
  els.loading.classList.toggle("hidden", name !== "loading");
  els.editorState.classList.toggle("hidden", name !== "editor");
  $(".result-panel").setAttribute("aria-busy", name === "loading" ? "true" : "false");
}

function selectedPayload() {
  return {
    venue: state.venues.find(item => item.id === els.venue.value),
    audience: state.audiences.find(item => item.id === els.audience.value),
    topic: els.topic.value.trim(), materials: els.materials.value.trim(),
    postStyle: els.postStyle.value,
  };
}

async function generate(event) {
  event.preventDefault();
  els.error.classList.add("hidden");
  if (!state.venues.length || !audiencesForVenue(els.venue.value).length) {
    els.error.textContent = "Сначала добавьте заведению хотя бы одну аудиторию.";
    els.error.classList.remove("hidden");
    switchView("profiles");
    return;
  }
  setResultStatus("Генерируем пост…");
  els.generateLabel.textContent = "Генерируем пост…";
  setView("loading");
  els.generate.disabled = true;
  try {
    const data = await api.generatePost(selectedPayload());
    els.result.value = data.text;
    els.demo.classList.toggle("hidden", !data.demo);
    updateResultCount(false);
    setResultStatus("Пост готов");
    syncResultImage();
    setView("editor");
  } catch (error) {
    setView("empty");
    els.error.textContent = error.message;
    els.error.classList.remove("hidden");
  } finally {
    els.generate.disabled = false;
    els.generateLabel.textContent = "Создать публикацию";
  }
}

function updateResultCount(markDirty = true) {
  els.resultCount.textContent = `${els.result.value.length.toLocaleString("ru-RU")} знаков`;
  if (markDirty) setResultStatus("Есть изменения");
}

function syncResultImage() {
  if (state.imageUrl) {
    els.resultImage.src = state.imageUrl;
    els.attached.classList.remove("hidden");
  } else {
    els.attached.classList.add("hidden");
  }
}

function removeImage() {
  if (state.imageUrl) URL.revokeObjectURL(state.imageUrl);
  state.imageUrl = null;
  state.imageName = "";
  els.imageInput.value = "";
  els.imageChip.classList.add("hidden");
  syncResultImage();
}

function saveDraft() {
  if (!els.result.value.trim()) return;
  const payload = selectedPayload();
  state.drafts.unshift({
    topic: payload.topic, venue: payload.venue.name, venueId: payload.venue.id,
    audience: payload.audience.name, audienceId: payload.audience.id,
    text: els.result.value, createdAt: new Date().toISOString(),
  });
  state.drafts = state.drafts.slice(0, 20);
  save(STORAGE.drafts, state.drafts);
  setResultStatus("Сохранён");
  renderDrafts();
}

async function copyPost() {
  await navigator.clipboard.writeText(els.result.value);
  const button = $("#copyPost");
  const original = button.textContent;
  button.textContent = "Скопировано";
  setTimeout(() => { button.textContent = original; }, 1600);
}

function openDraft(index) {
  const draft = state.drafts[index];
  if (!draft) return;
  if (draft.venueId && state.venues.some(item => item.id === draft.venueId)) {
    els.venue.value = draft.venueId;
    renderAudienceSelect(draft.audienceId);
    renderContext();
  }
  els.topic.value = draft.topic;
  els.result.value = draft.text;
  els.demo.classList.add("hidden");
  updateResultCount(false);
  setResultStatus("Сохранён");
  setView("editor");
  switchView("editor");
}

function deleteDraft(index) {
  const draft = state.drafts[index];
  if (!draft) return;
  if (!window.confirm(`Удалить черновик «${draft.topic || "Без темы"}»?`)) return;
  state.drafts.splice(index, 1);
  save(STORAGE.drafts, state.drafts);
  renderDrafts(els.draftSearch.value);
  if (activeVenueId) renderVenueDetail();
  showToast("Черновик удалён");
}

function startNewPost() {
  els.topic.value = "";
  els.materials.value = "";
  els.materialsCount.textContent = "0";
  els.result.value = "";
  els.error.classList.add("hidden");
  setResultStatus("Не сохранён");
  removeImage();
  setView("empty");
  switchView("editor");
  els.topic.focus();
}

function renderProfiles() {
  els.readinessBanner.classList.toggle("hidden", !state.venues.some(isVenueReady));
  els.venueTree.innerHTML = state.venues.map(venue => `
    <article class="venue-node" data-open-venue="${venue.id}" tabindex="0" role="button" aria-label="Открыть ${escapeHtml(venue.name)}">
      <div class="venue-node-header">
        <div class="entity-copy"><strong>${escapeHtml(venue.name)}</strong><span class="readiness-status ${isVenueReady(venue) ? "ready" : "incomplete"}">${isVenueReady(venue) ? "Готово к работе" : "Нужно заполнить"}</span></div>
        <div class="row-actions"><button class="button button--ghost button--xs" type="button" data-open-venue="${venue.id}">Открыть</button><button class="button button--danger button--xs" type="button" data-remove-venue="${venue.id}">Удалить</button></div>
        <span class="venue-chevron" aria-hidden="true">›</span>
      </div>
    </article>`).join("") || '<div class="profile-empty"><strong>Добавьте первое заведение</strong><span>Здесь появятся места, для которых вы готовите публикации.</span><button class="button button--primary button--sm" type="button" data-add-first-venue>Добавить заведение</button></div>';
}

function isVenueReady(venue) {
  return Boolean(venue.name?.trim() && (venue.description?.trim() || venue.format?.trim()) && venue.voice?.trim() && audiencesForVenue(venue.id).length);
}

function openVenueDetail(venueId) {
  if (!state.venues.some(item => item.id === venueId)) return;
  activeVenueId = venueId;
  switchView("venue");
}

function renderVenueDetail() {
  const venue = state.venues.find(item => item.id === activeVenueId);
  if (!venue) {
    switchView("profiles");
    return;
  }
  const ready = isVenueReady(venue);
  els.venueDetailTitle.textContent = venue.name;
  els.venueDetailStatus.textContent = ready ? "Готово к работе" : "Нужно заполнить";
  els.venueDetailStatus.className = `readiness-status ${ready ? "ready" : "incomplete"}`;
  els.venueDetailName.value = venue.name || "";
  els.venueDetailDescription.value = venue.description || venue.format || "";
  els.venueDetailVoice.value = venue.voice || "";
  const audiences = audiencesForVenue(venue.id);
  els.venueAudienceList.innerHTML = audiences.map(audience => `
    <div class="detail-list-item">
      <div><strong>${escapeHtml(audience.name)}</strong><small>${escapeHtml(audience.description || audience.needs)}</small></div>
      <div class="row-actions"><button class="button button--ghost button--xs" type="button" data-edit-audience="${audience.id}">Изменить</button><button class="button button--danger button--xs" type="button" data-remove-audience="${audience.id}">Удалить</button></div>
    </div>`).join("") || '<p class="detail-empty">Добавьте аудиторию, чтобы учитывать её потребности при создании постов.</p>';
  const drafts = state.drafts.filter(draft => draft.venueId === venue.id || (!draft.venueId && draft.venue === venue.name));
  els.venueDraftList.innerHTML = drafts.map(draft => {
    const index = state.drafts.indexOf(draft);
    return `<div class="detail-list-item detail-draft-row"><button class="detail-draft" type="button" data-draft="${index}"><span><strong>${escapeHtml(draft.topic || "Без темы")}</strong><small>${new Date(draft.createdAt).toLocaleDateString("ru-RU")}</small></span><span class="venue-chevron">›</span></button><button class="button button--danger button--xs" type="button" data-remove-draft="${index}">Удалить</button></div>`;
  }).join("") || '<p class="detail-empty">У этого заведения пока нет сохранённых черновиков.</p>';
}

function saveVenue(event) {
  event.preventDefault();
  const name = els.profileName.value.trim();
  if (!els.venueForm.reportValidity() || !name) {
    els.venueFormError.classList.remove("hidden");
    return;
  }
  els.venueFormError.classList.add("hidden");
  const item = { id: crypto.randomUUID(), name, description: "", voice: "", recommendedStyles: DEFAULT_POST_STYLES };
  state.profileVenueId = item.id;
  state.venues.push(item);
  save(STORAGE.venues, state.venues);
  els.profileName.value = "";
  renderProfiles();
  renderSelects();
  closeDialog(els.venueDialog, els.venueForm, true);
  showToast(`Заведение «${name}» добавлено`);
}

function saveVenueDetail(event) {
  event.preventDefault();
  const venue = state.venues.find(item => item.id === activeVenueId);
  const name = els.venueDetailName.value.trim();
  const description = els.venueDetailDescription.value.trim();
  const voice = els.venueDetailVoice.value.trim();
  if (!venue || !els.venueDetailForm.reportValidity() || !name || !description || !voice) {
    els.venueDetailError.classList.remove("hidden");
    return;
  }
  Object.assign(venue, { name, description, format: description, voice });
  save(STORAGE.venues, state.venues);
  els.venueDetailError.classList.add("hidden");
  renderVenueDetail();
  renderProfiles();
  renderSelects();
  showToast(`Профиль «${name}» сохранён`);
}

function saveAudience(event) {
  event.preventDefault();
  const venueId = state.profileVenueId;
  const name = els.audienceName.value.trim();
  const description = els.audiencePortrait.value.trim();
  const needs = els.audienceNeeds.value.trim();
  if (!els.audienceForm.reportValidity() || !venueId || !name || !description || !needs) {
    els.audienceFormError.classList.remove("hidden");
    return;
  }
  els.audienceFormError.classList.add("hidden");
  const existing = state.audiences.find(item => item.id === state.editingAudienceId);
  if (existing) Object.assign(existing, { name, description, needs });
  else state.audiences.push({ id: crypto.randomUUID(), venueId, name, description, needs });
  save(STORAGE.audiences, state.audiences);
  renderProfiles();
  if (activeVenueId === venueId) renderVenueDetail();
  renderSelects();
  closeDialog(els.audienceDialog, els.audienceForm, true);
  showToast(existing ? `Аудитория «${name}» обновлена` : `Аудитория «${name}» добавлена`);
}

function openVenueDialog() {
  els.profileName.value = "";
  els.venueFormError.classList.add("hidden");
  els.venueDialog.showModal();
  rememberDialog(els.venueDialog, els.venueForm);
}

function openAudienceDialog(venue, audience = null) {
  state.profileVenueId = venue.id;
  state.editingAudienceId = audience?.id || "";
  $("#audienceDialogTitle").textContent = audience ? "Изменить аудиторию" : "Добавить аудиторию";
  $("#saveAudience").textContent = audience ? "Сохранить изменения" : "Добавить аудиторию";
  $("#audienceDialogContext").textContent = `Заведение: ${venue.name}`;
  els.audienceName.value = audience?.name || "";
  els.audiencePortrait.value = audience?.description || "";
  els.audienceNeeds.value = audience?.needs || "";
  els.audienceFormError.classList.add("hidden");
  els.audienceDialog.showModal();
  rememberDialog(els.audienceDialog, els.audienceForm);
}

async function checkHealth() {
  try {
    const data = await api.health();
    els.aiStatus.classList.add("ready");
    els.aiStatus.innerHTML = `<span class="status-dot"></span>${data.aiConfigured ? "AI подключён" : "Демо-режим"}`;
  } catch { els.aiStatus.innerHTML = '<span class="status-dot"></span>Сервер недоступен'; }
}

els.form.addEventListener("submit", generate);
els.venue.addEventListener("change", () => {
  renderAudienceSelect();
  renderContext();
});
els.audience.addEventListener("change", renderContext);
els.materials.addEventListener("input", () => { els.materialsCount.textContent = els.materials.value.length.toLocaleString("ru-RU"); });
els.result.addEventListener("input", updateResultCount);
$("#saveDraft").addEventListener("click", saveDraft);
$("#copyPost").addEventListener("click", copyPost);
$("#removeImage").addEventListener("click", removeImage);
els.imageInput.addEventListener("change", () => {
  const file = els.imageInput.files[0];
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    els.error.textContent = "Изображение должно быть не больше 10 МБ.";
    els.error.classList.remove("hidden");
    els.imageInput.value = "";
    return;
  }
  els.error.classList.add("hidden");
  removeImage();
  state.imageUrl = URL.createObjectURL(file);
  state.imageName = file.name;
  els.imageThumb.src = state.imageUrl;
  els.imageName.textContent = file.name;
  els.imageChip.classList.remove("hidden");
  syncResultImage();
});
els.drafts.addEventListener("click", event => {
  const removeButton = event.target.closest("[data-remove-draft]");
  if (removeButton) {
    deleteDraft(Number(removeButton.dataset.removeDraft));
    return;
  }
  const button = event.target.closest("[data-draft]");
  if (button) openDraft(Number(button.dataset.draft));
});
els.draftSearch.addEventListener("input", () => renderDrafts(els.draftSearch.value));
document.querySelectorAll("[data-view]").forEach(button => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});
els.sidebarToggle.addEventListener("click", () => {
  setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed"));
});
$("#openVenueDialog").addEventListener("click", () => openVenueDialog());
$("#backToProfiles").addEventListener("click", () => switchView("profiles"));
$("#addDetailAudience").addEventListener("click", () => {
  const venue = state.venues.find(item => item.id === activeVenueId);
  if (venue) openAudienceDialog(venue);
});
els.venueDetailForm.addEventListener("submit", saveVenueDetail);
els.venueDetailForm.addEventListener("input", () => els.venueDetailError.classList.add("hidden"));
els.venueForm.addEventListener("submit", saveVenue);
els.venueForm.addEventListener("input", () => els.venueFormError.classList.add("hidden"));
els.audienceForm.addEventListener("submit", saveAudience);
els.audienceForm.addEventListener("input", () => els.audienceFormError.classList.add("hidden"));
document.querySelectorAll("[data-close-dialog]").forEach(button => {
  button.addEventListener("click", () => {
    const dialog = $(`#${button.dataset.closeDialog}`);
    const form = dialog === els.venueDialog ? els.venueForm : els.audienceForm;
    closeDialog(dialog, form);
  });
});
[
  [els.venueDialog, els.venueForm],
  [els.audienceDialog, els.audienceForm],
].forEach(([dialog, form]) => {
  dialog.addEventListener("cancel", event => {
    event.preventDefault();
    closeDialog(dialog, form);
  });
});
els.venueTree.addEventListener("click", event => {
  const venueButton = event.target.closest("[data-remove-venue]");
  if (venueButton) {
    const venue = state.venues.find(item => item.id === venueButton.dataset.removeVenue);
    const message = audiencesForVenue(venueButton.dataset.removeVenue).length
      ? `Удалить «${venue?.name}» и все связанные аудитории?`
      : `Удалить «${venue?.name}»?`;
    if (!window.confirm(message)) return;
    state.venues = state.venues.filter(item => item.id !== venueButton.dataset.removeVenue);
    state.audiences = state.audiences.filter(item => item.venueId !== venueButton.dataset.removeVenue);
    save(STORAGE.venues, state.venues);
    save(STORAGE.audiences, state.audiences);
    renderProfiles(); renderSelects();
    return;
  }
  if (event.target.closest("[data-add-first-venue]")) {
    openVenueDialog();
    return;
  }
  const openButton = event.target.closest("[data-open-venue]");
  if (openButton) openVenueDetail(openButton.dataset.openVenue);
});
els.venueTree.addEventListener("keydown", event => {
  if (event.key !== "Enter" && event.key !== " ") return;
  if (!event.target.classList.contains("venue-node")) return;
  const venue = event.target.closest("[data-open-venue]");
  if (venue) {
    event.preventDefault();
    openVenueDetail(venue.dataset.openVenue);
  }
});
els.venueDetailView.addEventListener("click", event => {
  const removeDraftButton = event.target.closest("[data-remove-draft]");
  if (removeDraftButton) {
    deleteDraft(Number(removeDraftButton.dataset.removeDraft));
    return;
  }
  const draftButton = event.target.closest("[data-draft]");
  if (draftButton) {
    openDraft(Number(draftButton.dataset.draft));
    return;
  }
  const editAudienceButton = event.target.closest("[data-edit-audience]");
  if (editAudienceButton) {
    const audience = state.audiences.find(item => item.id === editAudienceButton.dataset.editAudience);
    const venue = state.venues.find(item => item.id === audience?.venueId);
    if (venue && audience) openAudienceDialog(venue, audience);
    return;
  }
  const audienceButton = event.target.closest("[data-remove-audience]");
  if (audienceButton) {
    const audience = state.audiences.find(item => item.id === audienceButton.dataset.removeAudience);
    if (!window.confirm(`Удалить аудиторию «${audience?.name}»?`)) return;
    state.audiences = state.audiences.filter(item => item.id !== audienceButton.dataset.removeAudience);
    save(STORAGE.audiences, state.audiences);
    renderProfiles(); renderVenueDetail(); renderSelects();
  }
});

renderSelects();
renderDrafts();
renderProfiles();
setSidebarCollapsed(localStorage.getItem(STORAGE.sidebarCollapsed) === "true");
switchView("profiles");
checkHealth();

/**
 * Reverse ATS Studio - Frontend Controller
 * Communicates with the modular FastAPI backend (`/api/*`) and renders
 * interactive, directly editable A4 CV & Cover Letter templates.
 */

let appConfig = {
  providers: [],
  settings: {},
};

let currentProfile = {
  full_name: "",
  title: "",
  email: "",
  phone: "",
  location: "",
  links: [],
  master_bio: "",
  uploaded_cvs: [],
};

let currentResult = null;
let activeDocView = "cv"; // 'cv' | 'letter'

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadConfig(), loadProfile(), loadHistory()]);
});

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const colors = {
    info: "bg-indigo-600 border-indigo-400",
    success: "bg-emerald-600 border-emerald-400",
    error: "bg-rose-600 border-rose-400",
  };
  const toast = document.createElement("div");
  toast.className = `px-4 py-3 rounded-xl border text-white text-xs font-semibold shadow-xl transition-all ${colors[type] || colors.info}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

function switchTab(tabName) {
  ["profile", "job", "result"].forEach((t) => {
    const sec = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tabName) {
      sec.classList.remove("hidden");
      btn.className = "tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-all bg-indigo-600 text-white shadow";
    } else {
      sec.classList.add("hidden");
      btn.className = "tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white";
    }
  });
}

// ============================================================================
// CONFIG & PROVIDERS
// ============================================================================

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    appConfig = await res.json();
    populateProvidersDropdown();
    updateApiStatusIndicator();
  } catch (err) {
    console.error("Erreur chargement config:", err);
  }
}

function populateProvidersDropdown() {
  const providerSelect = document.getElementById("select-provider");
  providerSelect.innerHTML = "";
  appConfig.providers.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    providerSelect.appendChild(opt);
  });

  const defaultProv = appConfig.settings.default_provider || "gemini";
  providerSelect.value = defaultProv;
  onProviderChange();
}

function onProviderChange() {
  const providerId = document.getElementById("select-provider").value;
  const providerObj = appConfig.providers.find((p) => p.id === providerId);
  const modelSelect = document.getElementById("select-model");
  modelSelect.innerHTML = "";

  if (providerObj && providerObj.models) {
    providerObj.models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.label;
      modelSelect.appendChild(opt);
    });
  }
}

function updateApiStatusIndicator() {
  const dot = document.getElementById("api-status-dot");
  const label = document.getElementById("api-status-label");
  const geminiBadge = document.getElementById("gemini-saved-badge");
  const groqBadge = document.getElementById("groq-saved-badge");

  if (appConfig.settings.has_gemini_key) {
    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
    label.textContent = `Gemini configuré (${appConfig.settings.gemini_key_preview})`;
    if (geminiBadge) geminiBadge.textContent = `✓ Active (${appConfig.settings.gemini_key_preview})`;
  } else if (appConfig.settings.has_groq_key) {
    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
    label.textContent = `Groq configuré (${appConfig.settings.groq_key_preview})`;
  } else {
    dot.className = "w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse";
    label.textContent = "Configurer Clé IA Gratuite";
    if (geminiBadge) geminiBadge.textContent = "";
  }

  if (groqBadge) {
    groqBadge.textContent = appConfig.settings.has_groq_key
      ? `✓ Active (${appConfig.settings.groq_key_preview})`
      : "";
  }
}

function openSettingsModal() {
  document.getElementById("settings-modal").classList.remove("hidden");
}

function closeSettingsModal() {
  document.getElementById("settings-modal").classList.add("hidden");
}

async function saveApiSettings() {
  const geminiKey = document.getElementById("input-gemini-key").value.trim();
  const groqKey = document.getElementById("input-groq-key").value.trim();
  const ollamaUrl = document.getElementById("input-ollama-url").value.trim();

  const payload = { ollama_base_url: ollamaUrl };
  if (geminiKey) payload.gemini_api_key = geminiKey;
  if (groqKey) payload.groq_api_key = groqKey;

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    appConfig = await res.json();
    document.getElementById("input-gemini-key").value = "";
    document.getElementById("input-groq-key").value = "";
    updateApiStatusIndicator();
    closeSettingsModal();
    showToast("Clés API sauvegardées avec succès !", "success");
  } catch (err) {
    showToast("Erreur lors de la sauvegarde des paramètres.", "error");
  }
}

// ============================================================================
// PROFILE & CV MANAGEMENT
// ============================================================================

async function loadProfile() {
  try {
    const res = await fetch("/api/profile");
    currentProfile = await res.json();
    renderProfileForm();
  } catch (err) {
    console.error("Erreur chargement profil:", err);
  }
}

function renderProfileForm() {
  document.getElementById("prof-name").value = currentProfile.full_name || "";
  document.getElementById("prof-title").value = currentProfile.title || "";
  document.getElementById("prof-email").value = currentProfile.email || "";
  document.getElementById("prof-phone").value = currentProfile.phone || "";
  document.getElementById("prof-location").value = currentProfile.location || "";
  document.getElementById("prof-links").value = (currentProfile.links || []).join(", ");
  document.getElementById("prof-bio").value = currentProfile.master_bio || "";

  const list = document.getElementById("uploaded-cvs-list");
  list.innerHTML = "";

  if (!currentProfile.uploaded_cvs || currentProfile.uploaded_cvs.length === 0) {
    list.innerHTML = `
      <div class="text-xs text-slate-500 text-center py-3 border border-slate-800 rounded-xl">
        Aucun CV importé pour le moment.
      </div>
    `;
    return;
  }

  currentProfile.uploaded_cvs.forEach((cv) => {
    const charCount = (cv.extracted_text || "").length;
    const item = document.createElement("div");
    item.className = "p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-between gap-3";
    item.innerHTML = `
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-white truncate">${escapeHtml(cv.filename)}</span>
          <span class="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">${charCount} car. extraits</span>
        </div>
        <p class="text-[11px] text-slate-400 truncate mt-0.5">${escapeHtml((cv.extracted_text || "").slice(0, 110))}...</p>
      </div>
      <button onclick="deleteCV('${cv.id}')" class="px-2.5 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 text-xs font-semibold transition">
        Supprimer
      </button>
    `;
    list.appendChild(item);
  });
}

async function saveProfile() {
  const linksRaw = document.getElementById("prof-links").value;
  const links = linksRaw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const updated = {
    ...currentProfile,
    full_name: document.getElementById("prof-name").value.trim(),
    title: document.getElementById("prof-title").value.trim(),
    email: document.getElementById("prof-email").value.trim(),
    phone: document.getElementById("prof-phone").value.trim(),
    location: document.getElementById("prof-location").value.trim(),
    links: links,
    master_bio: document.getElementById("prof-bio").value,
  };

  try {
    const res = await fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });
    currentProfile = await res.json();
    showToast("Profil et Master Bio sauvegardés !", "success");
  } catch (err) {
    showToast("Erreur lors de la sauvegarde du profil.", "error");
  }
}

async function saveProfileAndNext() {
  await saveProfile();
  switchTab("job");
}

async function handleCVUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Save current text fields first so nothing is lost
  await saveProfile();

  const formData = new FormData();
  formData.append("file", file);

  showToast(`Extraction du texte de ${file.name} en cours...`, "info");
  try {
    const res = await fetch("/api/profile/cv", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Erreur d'extraction");
    }
    currentProfile = await res.json();
    renderProfileForm();
    showToast(`CV "${file.name}" importé et analysé avec succès !`, "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    event.target.value = "";
  }
}

async function deleteCV(cvId) {
  try {
    const res = await fetch(`/api/profile/cv/${cvId}`, { method: "DELETE" });
    currentProfile = await res.json();
    renderProfileForm();
    showToast("CV supprimé.", "info");
  } catch (err) {
    showToast("Erreur lors de la suppression.", "error");
  }
}

// ============================================================================
// JOB OFFER SCRAPING & GENERATION
// ============================================================================

async function scrapeJobUrl() {
  const url = document.getElementById("job-url-input").value.trim();
  if (!url) {
    showToast("Veuillez coller une URL valide.", "error");
    return;
  }

  const btn = document.getElementById("btn-scrape-url");
  const originalText = btn.textContent;
  btn.textContent = "⏳ Extraction...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/scrape-job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Erreur lors de l'extraction");

    document.getElementById("job-text-input").value = data.extracted_text;
    showToast("Texte de l'offre extrait avec succès !", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

async function generateApplication() {
  await saveProfile();

  const rawText = document.getElementById("job-text-input").value.trim();
  const sourceUrl = document.getElementById("job-url-input").value.trim();
  const providerId = document.getElementById("select-provider").value;
  const modelName = document.getElementById("select-model").value;
  const language = document.getElementById("select-language").value;
  const tone = document.getElementById("select-tone").value;
  const customInstructions = document.getElementById("job-custom-instructions").value.trim();

  if (!rawText && !sourceUrl) {
    showToast("Veuillez fournir le texte de l'offre ou son lien URL.", "error");
    return;
  }

  const btn = document.getElementById("btn-generate");
  const origHtml = btn.innerHTML;
  btn.innerHTML = `<span>⏳</span> Analyse ATS & Rédaction IA en cours...`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_text: rawText,
        source_url: sourceUrl || null,
        provider_id: providerId,
        model_name: modelName,
        language: language,
        tone: tone,
        custom_instructions: customInstructions,
      }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "Erreur lors de la génération");
    }

    currentResult = payload.data;
    renderResultDashboard();
    renderDocuments();
    await loadHistory();
    switchTab("result");
    showToast("CV & Lettre de motivation générés sur-mesure !", "success");
  } catch (err) {
    showToast(err.message, "error");
    if (err.message.includes("Clé API")) {
      openSettingsModal();
    }
  } finally {
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

// ============================================================================
// HISTORY & MANUAL JSON IMPORT
// ============================================================================

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const items = await res.json();
    const container = document.getElementById("history-list");
    container.innerHTML = "";

    if (!items.length) {
      container.innerHTML = `<div class="text-slate-500">Aucune génération enregistrée.</div>`;
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "p-2 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 cursor-pointer flex items-center justify-between transition";
      row.onclick = () => loadHistoryItem(item.id);
      row.innerHTML = `
        <div class="truncate pr-2">
          <div class="font-semibold text-slate-200 truncate">${escapeHtml(item.job_title || "Candidature")}</div>
          <div class="text-[10px] text-slate-400">${escapeHtml(item.company || "")}</div>
        </div>
        <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-[10px]">${item.match_score}%</span>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    console.error(err);
  }
}

async function loadHistoryItem(genId) {
  try {
    const res = await fetch(`/api/history/${genId}`);
    const record = await res.json();
    currentResult = record.result;
    renderResultDashboard();
    renderDocuments();
    switchTab("result");
  } catch (err) {
    showToast("Impossible de charger cette candidature.", "error");
  }
}

function copyFallbackPrompt() {
  const txt = document.getElementById("fallback-prompt-textarea").value;
  navigator.clipboard.writeText(txt);
  showToast("Prompt copié dans le presse-papier !", "success");
}

async function importManualJson() {
  const rawJson = document.getElementById("manual-json-input").value.trim();
  if (!rawJson) {
    showToast("Collez d'abord le JSON généré.", "error");
    return;
  }
  try {
    const res = await fetch("/api/import-json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_json: rawJson }),
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || "JSON invalide");

    currentResult = payload.data;
    renderResultDashboard();
    renderDocuments();
    showToast("CV et Lettre mis à jour depuis votre JSON !", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ============================================================================
// RENDER ATS DASHBOARD & A4 DOCUMENTS (CV + COVER LETTER)
// ============================================================================

function switchDocView(view) {
  activeDocView = view;
  const cvSheet = document.getElementById("a4-cv-sheet");
  const letterSheet = document.getElementById("a4-letter-sheet");
  const btnCv = document.getElementById("doc-btn-cv");
  const btnLetter = document.getElementById("doc-btn-letter");
  const tplBar = document.getElementById("template-selector-bar");

  if (view === "cv") {
    cvSheet.classList.remove("hidden");
    letterSheet.classList.add("hidden");
    tplBar.classList.remove("hidden");
    btnCv.className = "px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white transition";
    btnLetter.className = "px-4 py-2 rounded-lg text-xs font-bold text-slate-300 hover:text-white transition";
  } else {
    cvSheet.classList.add("hidden");
    letterSheet.classList.remove("hidden");
    tplBar.classList.add("hidden");
    btnLetter.className = "px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white transition";
    btnCv.className = "px-4 py-2 rounded-lg text-xs font-bold text-slate-300 hover:text-white transition";
  }
}

function renderResultDashboard() {
  if (!currentResult) return;

  const ats = currentResult.ats_analysis || {};
  document.getElementById("ats-score-val").textContent = `${ats.match_score ?? 85}%`;
  document.getElementById("ats-provider-badge").textContent =
    `Moteur : ${currentResult.provider_used || "IA"} (${currentResult.model_used || ""})`;

  const kwContainer = document.getElementById("ats-matched-keywords");
  kwContainer.innerHTML = (ats.matched_keywords || [])
    .map(
      (kw) =>
        `<span class="px-2 py-0.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[11px] font-medium">${escapeHtml(kw)}</span>`
    )
    .join("");

  const stratList = document.getElementById("ats-strategy-list");
  stratList.innerHTML = (ats.tailoring_strategy || [])
    .map((s) => `<li>${escapeHtml(s)}</li>`)
    .join("");

  const fallbackBox = document.getElementById("fallback-prompt-box");
  if (currentResult.fallback_prompt) {
    fallbackBox.classList.remove("hidden");
    document.getElementById("fallback-prompt-textarea").value = currentResult.fallback_prompt;
  } else {
    fallbackBox.classList.add("hidden");
  }
}

function renderDocuments() {
  if (!currentResult) return;
  const tpl = document.getElementById("cv-template-select").value;
  const cvSheet = document.getElementById("a4-cv-sheet");
  const letterSheet = document.getElementById("a4-letter-sheet");

  if (tpl === "modern_sidebar") {
    cvSheet.innerHTML = renderModernSidebarCV(currentResult.cv);
  } else {
    cvSheet.innerHTML = renderExecutiveATSCV(currentResult.cv);
  }

  letterSheet.innerHTML = renderCoverLetter(currentResult.cover_letter, currentResult.cv);
}

// --- TEMPLATE 1: MODERN 2-COLUMN SIDEBAR A4 CV ---

function renderModernSidebarCV(cv) {
  const skillsHtml = (cv.skill_categories || [])
    .map(
      (cat) => `
      <div class="mb-3.5">
        <div contenteditable="true" class="text-[11px] font-bold uppercase tracking-wider text-indigo-200 mb-1.5">${escapeHtml(cat.category)}</div>
        <div class="flex flex-wrap gap-1">
          ${(cat.skills || [])
            .map(
              (s) =>
                `<span contenteditable="true" class="px-2 py-0.5 rounded bg-slate-800/90 text-slate-100 text-[10.5px] font-medium">${escapeHtml(s)}</span>`
            )
            .join("")}
        </div>
      </div>
    `
    )
    .join("");

  const eduHtml = (cv.education || [])
    .map(
      (ed) => `
      <div class="mb-3">
        <div contenteditable="true" class="text-xs font-bold text-white leading-snug">${escapeHtml(ed.degree)}</div>
        <div contenteditable="true" class="text-[11px] text-indigo-200">${escapeHtml(ed.institution)}</div>
        <div contenteditable="true" class="text-[10px] text-slate-400">${escapeHtml(ed.period)}</div>
        ${ed.details ? `<div contenteditable="true" class="text-[10px] text-slate-300 mt-0.5">${escapeHtml(ed.details)}</div>` : ""}
      </div>
    `
    )
    .join("");

  const expHtml = (cv.experiences || [])
    .map(
      (exp) => `
      <div class="mb-4">
        <div class="flex items-baseline justify-between gap-2">
          <div>
            <span contenteditable="true" class="text-[13px] font-bold text-slate-900">${escapeHtml(exp.role)}</span>
            <span class="text-slate-400 mx-1">•</span>
            <span contenteditable="true" class="text-[12.5px] font-semibold text-indigo-700">${escapeHtml(exp.company)}</span>
          </div>
          <span contenteditable="true" class="text-[11px] font-medium text-slate-500 whitespace-nowrap">${escapeHtml(exp.period)}</span>
        </div>
        <ul class="mt-1.5 space-y-1 list-disc list-outside ml-4 text-[11.5px] text-slate-700 leading-snug">
          ${(exp.highlights || [])
            .map((h) => `<li contenteditable="true">${escapeHtml(h)}</li>`)
            .join("")}
        </ul>
      </div>
    `
    )
    .join("");

  const projHtml = (cv.projects || [])
    .map(
      (p) => `
      <div class="mb-3">
        <div class="flex items-baseline justify-between">
          <div>
            <span contenteditable="true" class="text-[12.5px] font-bold text-slate-900">${escapeHtml(p.name)}</span>
            ${p.tech_stack ? `<span contenteditable="true" class="ml-2 text-[10.5px] font-semibold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">${escapeHtml(p.tech_stack)}</span>` : ""}
          </div>
          ${p.period ? `<span contenteditable="true" class="text-[10.5px] text-slate-500">${escapeHtml(p.period)}</span>` : ""}
        </div>
        <p contenteditable="true" class="text-[11.5px] text-slate-700 mt-0.5 leading-snug">${escapeHtml(p.description)}</p>
      </div>
    `
    )
    .join("");

  return `
    <div class="grid grid-cols-12 min-h-[297mm]">
      <!-- LEFT SIDEBAR -->
      <aside class="col-span-4 bg-slate-900 text-white p-7 flex flex-col justify-between">
        <div class="space-y-5">
          <!-- Name & Target Title -->
          <div class="border-b border-slate-700 pb-4">
            <h1 contenteditable="true" class="text-xl font-extrabold tracking-tight text-white leading-tight">${escapeHtml(cv.full_name)}</h1>
            <div contenteditable="true" class="text-xs font-semibold text-indigo-400 mt-1.5 uppercase tracking-wider">${escapeHtml(cv.target_title)}</div>
          </div>

          <!-- Contact -->
          <div class="space-y-1.5 text-[11px] text-slate-300">
            ${cv.email ? `<div contenteditable="true">✉️ ${escapeHtml(cv.email)}</div>` : ""}
            ${cv.phone ? `<div contenteditable="true">📱 ${escapeHtml(cv.phone)}</div>` : ""}
            ${cv.location ? `<div contenteditable="true">📍 ${escapeHtml(cv.location)}</div>` : ""}
            ${(cv.links || []).map((l) => `<div contenteditable="true" class="truncate text-indigo-300">🔗 ${escapeHtml(l)}</div>`).join("")}
          </div>

          <!-- Skills -->
          <div>
            <h2 class="text-xs font-extrabold uppercase tracking-wider text-white border-b border-slate-700 pb-1 mb-2.5">Compétences</h2>
            ${skillsHtml}
          </div>

          <!-- Education -->
          <div>
            <h2 class="text-xs font-extrabold uppercase tracking-wider text-white border-b border-slate-700 pb-1 mb-2.5">Formation</h2>
            ${eduHtml}
          </div>

          <!-- Languages -->
          ${
            cv.languages && cv.languages.length
              ? `
            <div>
              <h2 class="text-xs font-extrabold uppercase tracking-wider text-white border-b border-slate-700 pb-1 mb-2">Langues</h2>
              <ul class="space-y-1 text-[11px] text-slate-300">
                ${cv.languages.map((lang) => `<li contenteditable="true">${escapeHtml(lang)}</li>`).join("")}
              </ul>
            </div>`
              : ""
          }
        </div>
      </aside>

      <!-- RIGHT MAIN CONTENT -->
      <div class="col-span-8 p-8 bg-white text-slate-900 space-y-5">
        <!-- Executive Summary -->
        <div class="bg-slate-50 border-l-4 border-indigo-600 p-3.5 rounded-r-lg">
          <p contenteditable="true" class="text-[12px] text-slate-700 leading-relaxed">${escapeHtml(cv.executive_summary)}</p>
        </div>

        <!-- Experiences -->
        <div>
          <h2 class="text-xs font-extrabold uppercase tracking-wider text-indigo-700 border-b-2 border-indigo-100 pb-1 mb-3">
            Expériences Professionnelles
          </h2>
          ${expHtml}
        </div>

        <!-- Projects -->
        ${
          projHtml
            ? `
          <div>
            <h2 class="text-xs font-extrabold uppercase tracking-wider text-indigo-700 border-b-2 border-indigo-100 pb-1 mb-3">
              Projets Clés & Réalisations Techniques
            </h2>
            ${projHtml}
          </div>`
            : ""
        }

        <!-- Extras / Certifications -->
        ${
          cv.certifications_or_extras && cv.certifications_or_extras.length
            ? `
          <div>
            <h2 class="text-xs font-extrabold uppercase tracking-wider text-indigo-700 border-b-2 border-indigo-100 pb-1 mb-2">
              Certifications & Informations Complémentaires
            </h2>
            <ul class="list-disc list-inside text-[11.5px] text-slate-700 space-y-0.5">
              ${cv.certifications_or_extras.map((c) => `<li contenteditable="true">${escapeHtml(c)}</li>`).join("")}
            </ul>
          </div>`
            : ""
        }
      </div>
    </div>
  `;
}

// --- TEMPLATE 2: SINGLE-COLUMN EXECUTIVE ATS CV ---

function renderExecutiveATSCV(cv) {
  const contactLine = [cv.email, cv.phone, cv.location, ...(cv.links || [])]
    .filter(Boolean)
    .map((item) => `<span contenteditable="true">${escapeHtml(item)}</span>`)
    .join(` <span class="text-slate-400">•</span> `);

  const skillsHtml = (cv.skill_categories || [])
    .map(
      (cat) => `
      <div class="text-[11.5px] leading-snug">
        <span contenteditable="true" class="font-bold text-slate-900">${escapeHtml(cat.category)} :</span>
        <span contenteditable="true" class="text-slate-700"> ${(cat.skills || []).map(escapeHtml).join(", ")}</span>
      </div>
    `
    )
    .join("");

  const expHtml = (cv.experiences || [])
    .map(
      (exp) => `
      <div class="mb-3.5">
        <div class="flex justify-between items-baseline">
          <div>
            <span contenteditable="true" class="font-bold text-[13px] text-slate-900">${escapeHtml(exp.role)}</span>
            <span class="text-slate-500"> — </span>
            <span contenteditable="true" class="font-semibold text-[12.5px] text-slate-800">${escapeHtml(exp.company)}</span>
          </div>
          <span contenteditable="true" class="text-[11px] font-medium text-slate-600">${escapeHtml(exp.period)}</span>
        </div>
        <ul class="list-disc list-outside ml-4 mt-1 space-y-0.5 text-[11.5px] text-slate-700">
          ${(exp.highlights || []).map((h) => `<li contenteditable="true">${escapeHtml(h)}</li>`).join("")}
        </ul>
      </div>
    `
    )
    .join("");

  const projHtml = (cv.projects || [])
    .map(
      (p) => `
      <div class="mb-2.5">
        <div class="flex justify-between items-baseline">
          <div>
            <span contenteditable="true" class="font-bold text-[12px] text-slate-900">${escapeHtml(p.name)}</span>
            ${p.tech_stack ? `<span contenteditable="true" class="text-[11px] text-slate-600"> (${escapeHtml(p.tech_stack)})</span>` : ""}
          </div>
          <span contenteditable="true" class="text-[11px] text-slate-600">${escapeHtml(p.period)}</span>
        </div>
        <p contenteditable="true" class="text-[11.5px] text-slate-700">${escapeHtml(p.description)}</p>
      </div>
    `
    )
    .join("");

  const eduHtml = (cv.education || [])
    .map(
      (ed) => `
      <div class="flex justify-between items-baseline mb-1.5 text-[11.5px]">
        <div>
          <span contenteditable="true" class="font-bold text-slate-900">${escapeHtml(ed.degree)}</span> —
          <span contenteditable="true" class="text-slate-700">${escapeHtml(ed.institution)}</span>
        </div>
        <span contenteditable="true" class="text-slate-600 text-[11px]">${escapeHtml(ed.period)}</span>
      </div>
    `
    )
    .join("");

  return `
    <div class="p-[16mm] text-slate-900 space-y-4">
      <header class="text-center border-b-2 border-slate-900 pb-3">
        <h1 contenteditable="true" class="text-2xl font-extrabold uppercase tracking-tight">${escapeHtml(cv.full_name)}</h1>
        <div contenteditable="true" class="text-sm font-bold text-indigo-700 mt-0.5">${escapeHtml(cv.target_title)}</div>
        <div class="text-[11px] text-slate-600 mt-1.5 flex flex-wrap justify-center gap-2">${contactLine}</div>
      </header>

      <section>
        <p contenteditable="true" class="text-[11.5px] text-slate-700 leading-relaxed">${escapeHtml(cv.executive_summary)}</p>
      </section>

      <section>
        <h2 class="text-xs font-extrabold uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-0.5 mb-2">Compétences Techniques & Clés</h2>
        <div class="space-y-1">${skillsHtml}</div>
      </section>

      <section>
        <h2 class="text-xs font-extrabold uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-0.5 mb-2">Expériences Professionnelles</h2>
        ${expHtml}
      </section>

      ${
        projHtml
          ? `<section>
              <h2 class="text-xs font-extrabold uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-0.5 mb-2">Projets Réalisés</h2>
              ${projHtml}
            </section>`
          : ""
      }

      <section>
        <h2 class="text-xs font-extrabold uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-0.5 mb-2">Formation</h2>
        ${eduHtml}
      </section>
    </div>
  `;
}

// --- COVER LETTER A4 RENDERER ---

function renderCoverLetter(cl, cv) {
  const bodyHtml = (cl.body_paragraphs || [])
    .map(
      (p) =>
        `<p contenteditable="true" class="text-[13px] text-slate-800 leading-relaxed mb-4 text-justify">${escapeHtml(p)}</p>`
    )
    .join("");

  return `
    <div class="flex flex-col justify-between h-full text-slate-900">
      <div class="space-y-8">
        <!-- Sender & Recipient Header -->
        <div class="flex justify-between items-start border-b border-slate-200 pb-6">
          <div class="space-y-0.5 text-xs">
            <div contenteditable="true" class="text-base font-extrabold text-slate-900">${escapeHtml(cv.full_name || cl.signature_name)}</div>
            <div contenteditable="true" class="text-indigo-700 font-semibold">${escapeHtml(cv.target_title)}</div>
            ${cv.email ? `<div contenteditable="true" class="text-slate-600">${escapeHtml(cv.email)}</div>` : ""}
            ${cv.phone ? `<div contenteditable="true" class="text-slate-600">${escapeHtml(cv.phone)}</div>` : ""}
            ${cv.location ? `<div contenteditable="true" class="text-slate-600">${escapeHtml(cv.location)}</div>` : ""}
          </div>

          <div class="text-right space-y-1 text-xs">
            <div contenteditable="true" class="font-bold text-slate-900">À l'attention du Recrutement — ${escapeHtml(cl.recipient_company)}</div>
            <div contenteditable="true" class="text-slate-600">${escapeHtml(cl.recipient_role)}</div>
            <div contenteditable="true" class="text-slate-500 pt-2">${escapeHtml(cl.date_location || "")}</div>
          </div>
        </div>

        <!-- Subject -->
        <div class="bg-slate-50 border-l-4 border-indigo-600 px-4 py-2.5">
          <span class="text-xs font-bold uppercase text-indigo-700">Objet : </span>
          <span contenteditable="true" class="text-sm font-bold text-slate-900">${escapeHtml(cl.subject)}</span>
        </div>

        <!-- Letter Content -->
        <div class="space-y-4">
          <div contenteditable="true" class="text-[13px] font-semibold text-slate-900">${escapeHtml(cl.salutation)}</div>
          <p contenteditable="true" class="text-[13px] text-slate-800 leading-relaxed text-justify">${escapeHtml(cl.opening_paragraph)}</p>
          ${bodyHtml}
          <p contenteditable="true" class="text-[13px] text-slate-800 leading-relaxed text-justify">${escapeHtml(cl.closing_paragraph)}</p>
          <p contenteditable="true" class="text-[13px] text-slate-800 pt-2">${escapeHtml(cl.sign_off)}</p>
        </div>

        <!-- Signature -->
        <div class="pt-6 text-right">
          <div contenteditable="true" class="text-sm font-bold text-slate-900">${escapeHtml(cl.signature_name)}</div>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

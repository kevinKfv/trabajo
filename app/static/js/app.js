document.addEventListener("DOMContentLoaded", () => {
    // --- Utilidades ---
    function showToast(msg, type="success") {
        const toast = document.getElementById("toast");
        const toastMsg = document.getElementById("toast-message");
        if(toast && toastMsg) {
            toastMsg.textContent = msg;
            toast.className = `toast ${type}`;
            toast.classList.remove("hidden");
            setTimeout(() => toast.classList.add("hidden"), 3000);
        } else {
            console.log("Toast fallback:", msg);
            alert(msg);
        }
    }

    const deviceId = sessionStorage.getItem("jhAI_deviceId") || (() => {
        const id = "dev_" + Math.random().toString(36).slice(2, 10);
        sessionStorage.setItem("jhAI_deviceId", id);
        return id;
    })();

    // Interceptar fetch para agregar Device-ID en todas las llamadas al API
    const originalFetch = window.fetch;
    window.fetch = async function(resource, config) {
        if (typeof resource === 'string' && resource.startsWith('/api/v1/')) {
            config = config || {};
            config.headers = config.headers || {};
            if (config.headers instanceof Headers) {
                config.headers.append('X-Device-ID', deviceId);
            } else {
                config.headers['X-Device-ID'] = deviceId;
            }
        }
        return originalFetch(resource, config);
    };

    // ═══════════════════════════════════════════════════════════
    // AISLAMIENTO POR DISPOSITIVO (sessionStorage)
    // Cada sesión de navegador es independiente: los empleos
    // guardados/descartados y el CV cargado sólo persisten
    // durante la sesión actual. Al cerrar el navegador o abrir
    // desde otro dispositivo, empieza limpio.
    // ═══════════════════════════════════════════════════════════
    const SESSION_KEY = "jhAI_session_" + deviceId;

    // Cache de vista local (no persiste entre sesiones/dispositivos)
    let sessionViewedJobs = JSON.parse(sessionStorage.getItem(SESSION_KEY + "_viewed") || "[]");
    let sessionHiddenJobs = JSON.parse(sessionStorage.getItem(SESSION_KEY + "_hidden") || "[]");

    function markJobViewed(jobId) {
        if (!sessionViewedJobs.includes(jobId)) {
            sessionViewedJobs.push(jobId);
            sessionStorage.setItem(SESSION_KEY + "_viewed", JSON.stringify(sessionViewedJobs));
        }
    }

    function hideJobLocally(jobId) {
        if (!sessionHiddenJobs.includes(jobId)) {
            sessionHiddenJobs.push(jobId);
            sessionStorage.setItem(SESSION_KEY + "_hidden", JSON.stringify(sessionHiddenJobs));
        }
    }

    // ═══════════════════════════════════════════════════════════
    // HAMBURGER MENU & SIDEBAR DRAWER (móvil)
    // ═══════════════════════════════════════════════════════════
    const hamburgerBtn = document.getElementById("btn-hamburger");
    const sidebarEl = document.querySelector(".sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");

    function openSidebar() {
        sidebarEl.classList.add("open");
        sidebarOverlay.classList.add("active");
        hamburgerBtn.textContent = "✕";
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        sidebarEl.classList.remove("open");
        sidebarOverlay.classList.remove("active");
        hamburgerBtn.textContent = "☰";
        document.body.style.overflow = "";
    }

    if (hamburgerBtn) {
        hamburgerBtn.addEventListener("click", () => {
            sidebarEl.classList.contains("open") ? closeSidebar() : openSidebar();
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeSidebar);
    }

    // ═══════════════════════════════════════════════════════════
    // BOTTOM NAV — sincronizado con el sidebar nav
    // ═══════════════════════════════════════════════════════════
    const bottomNavItems = document.querySelectorAll(".bottom-nav-item[data-tab]");

    function switchTab(targetTab) {
        // Actualizar sidebar nav
        document.querySelectorAll(".nav-item[data-tab]").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        const sidebarBtn = document.querySelector(`.nav-item[data-tab="${targetTab}"]`);
        if (sidebarBtn) sidebarBtn.classList.add("active");
        const tabEl = document.getElementById(targetTab);
        if (tabEl) tabEl.classList.add("active");

        // Actualizar bottom nav
        bottomNavItems.forEach(b => b.classList.remove("active"));
        const bnBtn = document.querySelector(`.bottom-nav-item[data-tab="${targetTab}"]`);
        if (bnBtn) bnBtn.classList.add("active");

        // Actualizar topbar
        if (TAB_META[targetTab] && topbarTitle && topbarSub) {
            topbarTitle.innerHTML = TAB_META[targetTab].title;
            topbarSub.textContent = TAB_META[targetTab].sub;
        }

        // Cerrar sidebar si estamos en móvil
        if (window.innerWidth <= 768) closeSidebar();

        // Cargar datos de la pestaña
        if (targetTab === "search-configs-tab") loadSearchConfigs();
        if (targetTab === "profile-tab") loadUserProfile();
        if (targetTab === "auto-apply-tab") loadApplyLogs();
        if (targetTab === "crm-tab") loadKanbanBoard();
        if (targetTab === "analytics-tab") loadAnalyticsTab();
    }

    bottomNavItems.forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
    });


    let currentPage = 1;
    let currentLimit = 12;
    let currentJobs = [];
    let searchTimeout = null;
    let selectedJobForApply = null;


    // Referencias DOM principales
    const grid = document.getElementById("jobs-grid");
    const jobsCount = document.getElementById("jobs-count");
    const pageIndicator = document.getElementById("page-indicator");
    const paginationInfo = document.getElementById("pagination-info");
    const btnPrev = document.getElementById("btn-prev-page");
    const btnNext = document.getElementById("btn-next-page");

    // Filtros
    const inputSearch = document.getElementById("input-search");
    const selectSeniority = document.getElementById("select-seniority");
    const selectSource = document.getElementById("select-source");
    const selectDateFeed = document.getElementById("filter-date-feed");
    const checkRemote = document.getElementById("check-remote");
    const rangeScore = document.getElementById("range-score");
    const scoreVal = document.getElementById("score-val");

    // Stats (topbar + sidebar)
    const statTotal = document.getElementById("stat-total-jobs");
    const statRemote = document.getElementById("stat-remote-jobs");
    const statHighMatch = document.getElementById("stat-high-match");

    // KPI cards en jobs-tab
    const kpiTotalJobs = document.getElementById("kpi-total-jobs");
    const kpiRemoteJobs = document.getElementById("kpi-remote-jobs");
    const kpiHighMatch = document.getElementById("kpi-high-match");

    // Topbar contextual
    const topbarTitle = document.getElementById("topbar-current-title");
    const topbarSub   = document.getElementById("topbar-current-sub");

    const TAB_META = {
        "jobs-tab":          { title: "Empleos &amp; Feed",        sub: "// scraping activo en 3 portales" },
        "search-configs-tab":{ title: "Búsquedas Configuradas",  sub: "// pasantías · jóvenes profesionales · roles" },
        "profile-tab":       { title: "Mi CV &amp; Perfil",         sub: "// datos usados para matching con IA" },
        "auto-apply-tab":    { title: "Auto-Apply",               sub: "// postulación automática por score IA" },
        "crm-tab":           { title: "CRM / Pipeline Kanban",    sub: "// seguimiento de candidaturas" },
        "chat-tab":          { title: "Chat IA Conversacional",   sub: "// asistente de carrera inteligente" },
        "analytics-tab":     { title: "Dashboard &amp; Admin",       sub: "// métricas del mercado tech" }
    };

    // Modal
    const modal = document.getElementById("job-modal");
    const modalClose = document.getElementById("modal-close");
    const modalAutoApplyBtn = document.getElementById("modal-auto-apply-btn");

    // Botones de Acción Global
    const btnScrape = document.getElementById("btn-trigger-scrape");
    const btnAI = document.getElementById("btn-trigger-ai");
    const btnNotify = document.getElementById("btn-trigger-notify");

    // --- Navegación entre Pestañas (sidebar) ---
    const tabButtons = document.querySelectorAll(".nav-item[data-tab]");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            switchTab(btn.getAttribute("data-tab"));
        });
    });


    // --- Exponer función del chat para sugerencias rápidas ---
    window.askChatQuestion = function(question) {
        const chatInput = document.getElementById("chat-input");
        switchTab("chat-tab");
        setTimeout(() => {
            if (chatInput) {
                chatInput.value = question;
                document.getElementById("chat-form").dispatchEvent(new Event("submit"));
            }
        }, 200);
    };


    // --- Cargar Estadísticas ---
    async function loadStats() {
        try {
            const res = await fetch("/api/v1/jobs/stats");
            if (res.ok) {
                const stats = await res.json();
                const total = stats.total_jobs || 0;
                const remote = stats.remote_jobs_count || 0;
                const highMatch = stats.high_match_jobs_count || 0;

                // Topbar inline stats
                if (statTotal) statTotal.textContent = total;
                if (statRemote) statRemote.textContent = remote;
                if (statHighMatch) statHighMatch.textContent = highMatch;

                // KPI cards del feed
                if (kpiTotalJobs) kpiTotalJobs.textContent = total;
                if (kpiRemoteJobs) kpiRemoteJobs.textContent = remote;
                if (kpiHighMatch) kpiHighMatch.textContent = highMatch;

                // Badge sidebar + bottom nav
                const navBadge = document.getElementById("nav-badge-jobs");
                if (navBadge) navBadge.textContent = total;
                const bnBadge = document.getElementById("bn-badge-jobs");
                if (bnBadge) bnBadge.textContent = total > 0 ? total : "";
            }
        } catch (e) {
            console.error("Error al cargar estadísticas:", e);
        }
    }

    // --- Cargar Lista de Empleos ---
    async function loadJobs() {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px;">⏳ Cargando ofertas laborales...</div>`;

        const queryParams = new URLSearchParams({
            page: currentPage,
            limit: currentLimit
        });

        if (inputSearch.value.trim()) queryParams.append("search_query", inputSearch.value.trim());
        if (selectSeniority.value) queryParams.append("seniority", selectSeniority.value);
        if (selectSource.value) queryParams.append("source", selectSource.value);
        if (selectDateFeed && selectDateFeed.value !== 'all') queryParams.append("date_filter", selectDateFeed.value);
        if (checkRemote.checked) queryParams.append("remote", "true");
        if (parseInt(rangeScore.value) > 0) queryParams.append("min_ai_score", rangeScore.value);

        try {
            const res = await fetch(`/api/v1/jobs?${queryParams.toString()}`);
            if (!res.ok) throw new Error("Error al obtener ofertas");

            const data = await res.json();
            currentJobs = data.items || [];

            jobsCount.textContent = data.total || 0;
            pageIndicator.textContent = `Página ${data.page} de ${data.pages || 1}`;
            paginationInfo.textContent = `Mostrando ${currentJobs.length} de ${data.total} ofertas`;

            btnPrev.disabled = data.page <= 1;
            btnNext.disabled = data.page >= (data.pages || 1);

            renderJobs(currentJobs);
        } catch (e) {
            console.error("Error al cargar empleos:", e);
            grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #ef4444;">❌ Error al conectar con el servidor API.</div>`;
        }
    }

    function renderJobs(jobs) {
        if (!jobs || jobs.length === 0) {
            grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--text-3); font-family:'JetBrains Mono',monospace; font-size:0.88rem;">// sin resultados con los filtros actuales</div>`;
            return;
        }

        grid.innerHTML = jobs.map(job => {
            const score = job.ai_score !== null && job.ai_score !== undefined ? Math.round(job.ai_score) : null;
            let matchClass = "match-none";
            let matchLabel = "Sin analizar";
            if (score !== null) {
                if (score >= 80) { matchClass = "match-high"; matchLabel = `★ ${score}%`; }
                else if (score >= 50) { matchClass = "match-mid"; matchLabel = `★ ${score}%`; }
                else { matchClass = "match-low"; matchLabel = `★ ${score}%`; }
            }

            const remoteBadge   = job.remote ? `<span class="badge badge-remote">🏠 remoto</span>` : ``;
            const seniorBadge   = job.seniority ? `<span class="badge badge-seniority">${job.seniority}</span>` : ``;
            const sourceBadge   = `<span class="badge badge-source">${job.source.toUpperCase()}</span>`;
            const appliedBadge  = job.status === "APPLIED" ? `<span class="badge badge-applied">✓ postulado</span>` : ``;
            const techTags      = (job.technologies || []).slice(0, 4).map(t => `<span class="tech-tag">${t}</span>`).join("");

            return `
                <div class="job-card">
                    <div class="job-card-top">
                        <div class="job-badges">
                            ${sourceBadge}${remoteBadge}${seniorBadge}${appliedBadge}
                        </div>
                        <span class="match-pill ${matchClass}">${matchLabel}</span>
                    </div>

                    <div>
                        <div class="job-title">${job.title}</div>
                        <div class="job-meta">
                            <div class="job-company">🏢 ${job.company}</div>
                            <div class="job-location">📍 ${job.location || "Ubicación no especificada"}</div>
                        </div>
                        <div class="tech-tags" style="margin-top:10px;">${techTags}</div>
                    </div>

                    <div class="job-card-footer">
                        <button class="btn btn-secondary btn-sm" onclick="openJobDetail(${job.id})">🔍 Detalle</button>
                        <button class="btn btn-secondary btn-sm" onclick="sendJobFeedback(${job.id}, 'SAVED')">⭐ Guardar</button>
                        <button class="btn btn-coral btn-sm" onclick="sendJobFeedback(${job.id}, 'DISMISSED')">✕ Descartar</button>
                        <button class="btn btn-primary btn-sm" onclick="window.open('${job.url}', '_blank')">⚡ Postular</button>
                    </div>
                </div>
            `;
        }).join("");
    }

    // --- Enviar Feedback del Usuario ---
    window.sendJobFeedback = async function(jobId, action) {
        try {
            const res = await fetch(`/api/v1/recommendations/feedback/${jobId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
            if (res.ok) {
                const msg = action === "SAVED" ? "⭐ Oferta guardada." : "👎 Oferta descartada del feed.";
                showToast(msg);
                loadJobs();
            }
        } catch (e) {
            showToast("❌ Error al registrar feedback.");
        }
    };

    // --- Abrir Modal de Detalle y Auto-Apply ---
    window.openJobDetail = async function(jobId) {
        try {
            const res = await fetch(`/api/v1/jobs/${jobId}`);
            if (!res.ok) return;

            const job = await res.json();
            selectedJobForApply = job;

            document.getElementById("modal-title").textContent = job.title;
            document.getElementById("modal-company").textContent = `${job.company} — ${job.location || 'N/A'}`;
            document.getElementById("modal-source").textContent = job.source.toUpperCase();
            document.getElementById("modal-remote").textContent = job.remote ? "Remoto 🏠" : "Presencial 🏢";
            document.getElementById("modal-seniority").textContent = job.seniority || "Seniority N/A";

            const score = job.ai_score !== null ? Math.round(job.ai_score) : "N/A";
            document.getElementById("modal-score-val").textContent = `${score}%`;
            document.getElementById("modal-score-reasoning").textContent = job.ai_analysis?.reasoning || "Pendiente de análisis con IA.";
            document.getElementById("modal-summary").textContent = job.ai_summary || "Haga clic en 'Analizar con IA' para generar un resumen técnico.";

            const advantages = job.ai_analysis?.advantages || [];
            const missing = job.ai_analysis?.missing_skills || [];
            document.getElementById("modal-advantages").innerHTML = advantages.length > 0
                ? advantages.map(a => `<span class="tech-tag" style="background:rgba(16,185,129,0.2); color:#34d399;">✔ ${a}</span>`).join("")
                : `<span class="tech-tag" style="background:rgba(16,185,129,0.2); color:#34d399;">✔ Coincidencias detectadas</span>`;

            document.getElementById("modal-missing").innerHTML = missing.length > 0
                ? missing.map(m => `<span class="tech-tag" style="background:rgba(239,68,68,0.2); color:#f87171;">• ${m}</span>`).join("")
                : `<span class="tech-tag" style="background:rgba(100,116,139,0.2); color:#94a3b8;">Sin faltantes críticos</span>`;

            document.getElementById("modal-interview-prob").textContent = job.ai_analysis?.interview_probability || (score >= 80 ? "Alta" : "Media");
            document.getElementById("modal-recommendation").textContent = job.ai_analysis?.recommendation || (score >= 80 ? "Aplicar inmediatamente" : "Revisar requisitos");

            const techContainer = document.getElementById("modal-techs");
            techContainer.innerHTML = (job.technologies || []).map(t => `<span class="tech-tag">${t}</span>`).join("");

            document.getElementById("modal-description").textContent = job.description;
            document.getElementById("modal-url-btn").href = job.url;

            modal.classList.remove("hidden");
        } catch (e) {
            console.error("Error al abrir detalle de oferta:", e);
        }
    };

    modalClose.addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.add("hidden"); });

    modalAutoApplyBtn.addEventListener("click", () => {
        if (selectedJobForApply) {
            window.open(selectedJobForApply.url, '_blank');
            modal.classList.add("hidden");
        }
    });

    // Referencias a Modal de Documentos
    const docModal = document.getElementById("doc-modal");
    const docModalTitle = document.getElementById("doc-modal-title");
    const docModalText = document.getElementById("doc-modal-text");
    const docModalClose = document.getElementById("doc-modal-close");
    const docModalCopyBtn = document.getElementById("doc-modal-copy-btn");

    document.getElementById("modal-gen-cv-btn").addEventListener("click", async () => {
        if (!selectedJobForApply) return;
        showToast("⏳ Generando CV Adaptado por IA...");
        try {
            const res = await fetch(`/api/v1/jobs/${selectedJobForApply.id}/generate-cv`, { method: "POST" });
            if (!res.ok) throw new Error();
            const data = await res.json();
            docModalTitle.textContent = `📄 CV Adaptado para ${data.company}`;
            docModalText.value = data.tailored_cv_markdown;
            docModal.classList.remove("hidden");
        } catch (e) {
            showToast("❌ Error al generar CV adaptado.");
        }
    });

    document.getElementById("modal-gen-cover-btn").addEventListener("click", async () => {
        if (!selectedJobForApply) return;
        showToast("⏳ Generando Carta de Presentación...");
        try {
            const res = await fetch(`/api/v1/jobs/${selectedJobForApply.id}/generate-cover-letter`, { method: "POST" });
            if (!res.ok) throw new Error();
            const data = await res.json();
            docModalTitle.textContent = `✉️ Carta de Presentación - ${data.company}`;
            docModalText.value = data.cover_letter_text;
            docModal.classList.remove("hidden");
        } catch (e) {
            showToast("❌ Error al generar Carta de Presentación.");
        }
    });

    docModalClose.addEventListener("click", () => docModal.classList.add("hidden"));
    docModal.addEventListener("click", (e) => { if (e.target === docModal) docModal.classList.add("hidden"); });

    docModalCopyBtn.addEventListener("click", () => {
        docModalText.select();
        navigator.clipboard.writeText(docModalText.value);
        showToast("📋 Documento copiado al portapapeles.");
    });

    // --- Postulación 1-Click Auto-Apply ---
    window.triggerSingleAutoApply = async function(jobId) {
        showToast("⚡ Iniciando postulación automática...");
        try {
            const res = await fetch(`/api/v1/auto-apply/jobs/${jobId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ dry_run: false })
            });
            const data = await res.json();
            showToast(data.message || "Postulación registrada.");
            loadJobs();
        } catch (e) {
            showToast("❌ Error al ejecutar postulación automática.");
        }
    };

    // --- Búsquedas Personalizadas (Search Configs) ---
    async function loadSearchConfigs() {
        const container = document.getElementById("search-configs-list");
        container.innerHTML = `<div style="color:var(--text-3); font-size:0.84rem; grid-column:1/-1;">Cargando configuraciones...</div>`;
        try {
            const res = await fetch("/api/v1/search-configs");
            if (!res.ok) return;
            const configs = await res.json();

            if (configs.length === 0) {
                container.innerHTML = `<div style="grid-column:1/-1; color:var(--text-3); font-size:0.84rem; font-family:'JetBrains Mono',monospace;">// sin búsquedas configuradas aún</div>`;
                return;
            }

            container.innerHTML = configs.map(c => `
                <div class="config-card">
                    <button class="config-card-delete" onclick="deleteSearchConfig(${c.id})">✕</button>
                    <div class="config-card-name">${c.name}</div>
                    <div class="config-card-meta">📍 ${c.location || 'Cualquier ubicación'} · 🏠 ${c.remote_only ? 'Solo remoto' : 'Presencial o remoto'}</div>
                    <div class="tech-tags" style="margin-top:6px;">
                        ${(c.keywords || []).map(k => `<span class="tech-tag">${k}</span>`).join("")}
                    </div>
                </div>
            `).join("");
        } catch (e) {
            console.error("Error al cargar búsquedas configuradas:", e);
        }
    }

    document.getElementById("form-search-config").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("config-name").value.trim();
        const location = document.getElementById("config-location").value.trim();
        const keywords = document.getElementById("config-keywords").value.split(",").map(k => k.trim()).filter(Boolean);
        const remoteOnly = document.getElementById("config-remote-only").checked;
        const dateFilter = document.getElementById("config-date-filter").value;
        const sources = Array.from(document.querySelectorAll("input[name='source-opt']:checked")).map(cb => cb.value);

        try {
            const res = await fetch("/api/v1/search-configs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    keywords,
                    sources,
                    location,
                    remote_only: remoteOnly,
                    date_filter: dateFilter,
                    is_active: true
                })
            });

            if (res.ok) {
                showToast("✅ Búsqueda configurada correctamente.");
                document.getElementById("form-search-config").reset();
                loadSearchConfigs();
            }
        } catch (e) {
            showToast("❌ Error al guardar la búsqueda.");
        }
    });

    window.deleteSearchConfig = async function(id) {
        if (!confirm("¿Deseas eliminar esta configuración de búsqueda?")) return;
        try {
            const res = await fetch(`/api/v1/search-configs/${id}`, { method: "DELETE" });
            if (res.ok) {
                showToast("🗑️ Búsqueda eliminada.");
                loadSearchConfigs();
            }
        } catch (e) {
            showToast("❌ Error al eliminar.");
        }
    };

    window.resetAllSearches = async function() {
        if (!confirm("¿Deseas eliminar TODAS las configuraciones de búsqueda? Esta acción no se puede deshacer.")) return;
        try {
            const res = await fetch("/api/v1/search-configs");
            if (!res.ok) return;
            const configs = await res.json();
            
            let count = 0;
            for (const c of configs) {
                await fetch(`/api/v1/search-configs/${c.id}`, { method: "DELETE" });
                count++;
            }
            showToast(`🗑️ ${count} búsquedas eliminadas.`);
            loadSearchConfigs();
        } catch (e) {
            showToast("❌ Error al eliminar todas las búsquedas.");
            console.error(e);
        }
    };

    window.clearFeed = async function() {
        if (!confirm("¿Deseas eliminar TODAS las ofertas de empleo? Esta acción no se puede deshacer.")) return;
        try {
            const res = await fetch("/api/v1/jobs/all", { method: "DELETE" });
            if (res.ok) {
                showToast("🗑️ Empleos borrados correctamente.");
                currentPage = 1;
                loadJobs();
                loadStats();
            } else {
                showToast("❌ Error al vaciar el feed.");
            }
        } catch (e) {
            showToast("❌ Error de conexión al vaciar el feed.");
            console.error(e);
        }
    };

    // --- Cargar Perfil y Subida de CV ---
    async function loadUserProfile() {
        try {
            const res = await fetch("/api/v1/profile");
            if (!res.ok) return;

            const profile = await res.json();
            document.getElementById("prof-name").value    = profile.full_name || "";
            document.getElementById("prof-email").value   = profile.email || "";
            document.getElementById("prof-phone").value   = profile.phone || "";
            document.getElementById("prof-linkedin").value = profile.linkedin_url || "";
            document.getElementById("prof-cv-text").value = profile.cv_text || "";

            const statusEl = document.getElementById("cv-file-status");
            if (profile.cv_filename && statusEl) {
                statusEl.innerHTML = `✅ ${profile.cv_filename}`;
                statusEl.classList.add("loaded");
            }

            const skillsContainer = document.getElementById("cv-skills-tags");
            if (profile.cv_skills && profile.cv_skills.length > 0) {
                skillsContainer.innerHTML = profile.cv_skills.map(s => `<span class="skill-tag">${s}</span>`).join("");
            }
        } catch (e) {
            console.error("Error al cargar perfil:", e);
        }
    }

    const cvFileInput = document.getElementById("cv-file-input");
    cvFileInput.addEventListener("change", async () => {
        if (!cvFileInput.files || cvFileInput.files.length === 0) return;

        const file = cvFileInput.files[0];
        document.getElementById("cv-file-status").textContent = `⏳ Subiendo y procesando ${file.name}...`;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/v1/profile/cv", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                showToast("🎉 CV subido y analizado con éxito.");
                loadUserProfile();
            } else {
                const err = await res.json();
                showToast(`❌ Error: ${err.detail || 'No se pudo procesar el CV'}`);
            }
        } catch (e) {
            showToast("❌ Error de conexión al subir el CV.");
        }
    });

    document.getElementById("form-user-profile").addEventListener("submit", async (e) => {
        e.preventDefault();
        const profileData = {
            full_name: document.getElementById("prof-name").value,
            email: document.getElementById("prof-email").value,
            phone: document.getElementById("prof-phone").value,
            linkedin_url: document.getElementById("prof-linkedin").value,
            summary: document.getElementById("prof-cv-text").value,
            cv_text: document.getElementById("prof-cv-text").value
        };

        try {
            const res = await fetch("/api/v1/profile", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profileData)
            });
            if (res.ok) {
                showToast("💾 Perfil guardado correctamente.");
            }
        } catch (e) {
            showToast("❌ Error al guardar perfil.");
        }
    });

    // --- Historial de Postulaciones (Auto-Apply Logs) ---
    async function loadApplyLogs() {
        const tbody = document.getElementById("apply-logs-body");
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px;">Cargando...</td></tr>`;

        try {
            const res = await fetch("/api/v1/auto-apply/logs");
            if (!res.ok) return;
            const logs = await res.json();

            if (logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--text-muted);">No se registran postulaciones aún.</td></tr>`;
                return;
            }

            tbody.innerHTML = logs.map(l => {
                const dateStr = new Date(l.applied_at).toLocaleString();
                return `
                    <tr>
                        <td>${dateStr}</td>
                        <td><strong>${l.job_title}</strong></td>
                        <td>${l.company}</td>
                        <td><span class="badge badge-source">${l.source.toUpperCase()}</span></td>
                        <td><span class="status-badge ${l.status}">${l.status}</span></td>
                        <td>${l.notes || l.error_message || 'N/A'}</td>
                    </tr>
                `;
            }).join("");
        } catch (e) {
            console.error("Error al cargar logs:", e);
        }
    }

    const batchMinScoreInput = document.getElementById("batch-min-score");
    const batchScoreVal = document.getElementById("batch-score-val");
    batchMinScoreInput.addEventListener("input", () => {
        batchScoreVal.textContent = `${batchMinScoreInput.value}%`;
    });

    document.getElementById("btn-run-batch-apply").addEventListener("click", async () => {
        const btn = document.getElementById("btn-run-batch-apply");
        const minScore = parseFloat(batchMinScoreInput.value);
        const dryRun = document.getElementById("batch-dry-run").checked;

        btn.disabled = true;
        btn.innerHTML = "⏳ Postulando...";

        try {
            const res = await fetch("/api/v1/auto-apply/batch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ min_ai_score: minScore, dry_run: dryRun, max_applications: 10 })
            });
            const data = await res.json();
            showToast(data.message || "Postulaciones completadas.");
            loadApplyLogs();
        } catch (e) {
            showToast("❌ Error en postulación masiva.");
        } finally {
            btn.disabled = false;
            btn.innerHTML = "⚡ Ejecutar Postulación Masiva";
        }
    });

    // --- Toast Notifications ---
    function showToast(message) {
        const toast = document.getElementById("toast");
        document.getElementById("toast-message").textContent = message;
        toast.classList.remove("hidden");
        setTimeout(() => toast.classList.add("hidden"), 4000);
    }

    // --- Listeners Filtros Dashboard ---
    inputSearch.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => { currentPage = 1; loadJobs(); }, 400);
    });

    selectSeniority.addEventListener("change", () => { currentPage = 1; loadJobs(); });
    selectSource.addEventListener("change", () => { currentPage = 1; loadJobs(); });
    if (selectDateFeed) selectDateFeed.addEventListener("change", () => { currentPage = 1; loadJobs(); });
    checkRemote.addEventListener("change", () => { currentPage = 1; loadJobs(); });
    rangeScore.addEventListener("input", () => {
        scoreVal.textContent = `${rangeScore.value}%`;
        currentPage = 1;
        loadJobs();
    });

    btnPrev.addEventListener("click", () => { if (currentPage > 1) { currentPage--; loadJobs(); } });
    btnNext.addEventListener("click", () => { currentPage++; loadJobs(); });

    // --- Acciones de Header ---
    btnScrape.addEventListener("click", async () => {
        btnScrape.disabled = true;
        btnScrape.innerHTML = "⏳ Scraping...";
        try {
            const res = await fetch("/api/v1/scrape", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ use_saved_configs: true })
            });
            const data = await res.json();
            showToast(`Scraping finalizado: ${data.total_added_to_db || data.total_added || 0} nuevas ofertas agregadas.`);
            loadStats();
            loadJobs();
        } catch (e) {
            showToast("❌ Error al ejecutar el scraping.");
        } finally {
            btnScrape.disabled = false;
            btnScrape.innerHTML = '<span class="icon">🔄</span> Scrapear Ofertas';
        }
    });

    btnAI.addEventListener("click", async () => {
        btnAI.disabled = true;
        btnAI.innerHTML = "⏳ Analizando...";
        try {
            const res = await fetch("/api/v1/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ limit: 10 })
            });
            const data = await res.json();
            showToast(data.message || "Análisis de IA completado.");
            loadStats();
            loadJobs();
        } catch (e) {
            showToast("❌ Error al ejecutar análisis con IA.");
        } finally {
            btnAI.disabled = false;
            btnAI.innerHTML = '<span class="icon">🧠</span> Analizar con IA';
        }
    });

    btnNotify.addEventListener("click", async () => {
        btnNotify.disabled = true;
        btnNotify.innerHTML = "⏳ Notificando...";
        try {
            const res = await fetch("/api/v1/notify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ min_score: 70.0 })
            });
            const data = await res.json();
            showToast(`Alertas procesadas: ${data.total_notified || 0} enviadas.`);
            loadStats();
        } catch (e) {
            showToast("❌ Error al enviar notificaciones.");
        } finally {
            btnNotify.disabled = false;
            btnNotify.innerHTML = '<span class="icon">🔔</span> Enviar Alertas';
        }
    });

    // --- CRM Kanban & Calendario ---
    async function loadKanbanBoard() {
        const container = document.getElementById("kanban-board");
        if (!container) return;
        container.innerHTML = `<div style="padding: 20px;">Cargando tablero CRM...</div>`;

        try {
            const res = await fetch("/api/v1/crm/kanban");
            if (!res.ok) {
                container.innerHTML = `<div style="padding: 20px; color:#ef4444;">❌ Error al cargar tablero CRM (${res.status}).</div>`;
                return;
            }
            const board = await res.json();

            const stagesOrder = [
                { key: "POSTULADO", label: "Postulado 📩" },
                { key: "CONTACTO_RRHH", label: "Contacto RRHH 📞" },
                { key: "ENTREVISTA_TECNICA", label: "Entrevista Técnica 💻" },
                { key: "DESAFIO_CODIGO", label: "Desafío / Challenge 🛠️" },
                { key: "OFERTA_RECIBIDA", label: "Oferta Recibida 🎉" },
                { key: "ACEPTADO", label: "Aceptado ✅" },
                { key: "RECHAZADO", label: "Descartado / Rechazado ❌" }
            ];

            // Actualizar pills de estadísticas del CRM
            const countPostulado = document.getElementById("crm-count-postulado");
            const countEntrevista = document.getElementById("crm-count-entrevista");
            const countOferta = document.getElementById("crm-count-oferta");
            const countAceptado = document.getElementById("crm-count-aceptado");
            if (countPostulado) countPostulado.textContent = (board["POSTULADO"] || []).length;
            if (countEntrevista) countEntrevista.textContent = (board["ENTREVISTA_TECNICA"] || []).length;
            if (countOferta) countOferta.textContent = (board["OFERTA_RECIBIDA"] || []).length;
            if (countAceptado) countAceptado.textContent = (board["ACEPTADO"] || []).length;

            container.innerHTML = stagesOrder.map(s => {
                const items = board[s.key] || [];
                const cardsHtml = items.map(item => `
                    <div class="kanban-card">
                        <div class="kanban-card-title">${item.title}</div>
                        <div class="kanban-card-company">🏢 ${item.company}</div>
                        <div>📍 ${item.location || 'Remoto'}</div>
                        <div class="kanban-card-actions">
                            <select class="kanban-stage-select" onchange="updateKanbanStage(${item.id}, this.value)">
                                ${stagesOrder.map(st => `<option value="${st.key}" ${st.key === s.key ? 'selected' : ''}>${st.label}</option>`).join("")}
                            </select>
                            <button class="btn btn-secondary btn-sm" onclick="exportCalendarEvent(${item.id})">📅 GCal</button>
                        </div>
                    </div>
                `).join("");

                return `
                    <div class="kanban-column">
                        <div class="kanban-column-header">
                            <span>${s.label}</span>
                            <span>(${items.length})</span>
                        </div>
                        ${cardsHtml || '<div style="font-size:0.8rem; color:var(--text-muted); padding:10px 0;">Sin postulaciones</div>'}
                    </div>
                `;
            }).join("");

        } catch (e) {
            console.error("Error al cargar tablero Kanban:", e);
        }
    }

    window.updateKanbanStage = async function(jobId, newStage) {
        try {
            const res = await fetch(`/api/v1/crm/jobs/${jobId}/stage`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ stage: newStage })
            });
            if (res.ok) {
                showToast("📋 Etapa actualizada en el CRM.");
                loadKanbanBoard();
            }
        } catch (e) {
            showToast("❌ Error al actualizar etapa.");
        }
    };

    window.exportCalendarEvent = async function(jobId) {
        try {
            const res = await fetch(`/api/v1/crm/jobs/${jobId}/export-calendar`);
            if (!res.ok) return;
            const data = await res.json();
            window.open(data.google_calendar_url, "_blank");
        } catch (e) {
            showToast("❌ Error al exportar a Google Calendar.");
        }
    };

    // --- Chat IA Conversacional ---
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");

    function formatMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Convertir enlaces markdown [Texto](url)
        html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; text-decoration:underline; font-weight:600;">$1 🔗</a>');

        // Convertir URLs directas que no estén ya dentro de un href
        html = html.replace(/(^|[\s\n])(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; text-decoration:underline;">$2 🔗</a>');

        return html
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
    }

    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text) return;

            // Agregar mensaje del usuario
            chatMessages.innerHTML += `<div class="chat-msg user">👤 ${text}</div>`;
            chatInput.value = "";
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Loader bot
            const loaderId = "loader-" + Date.now();
            chatMessages.innerHTML += `<div id="${loaderId}" class="chat-msg bot">🤖 Pensando respuesta...</div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const res = await fetch("/api/v1/chat/query", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: text })
                });
                const data = await res.json();
                
                let answerHtml = formatMarkdown(data.answer || 'Sin respuesta.');

                document.getElementById(loaderId).outerHTML = `<div class="chat-msg bot">🤖 ${answerHtml}</div>`;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } catch (e) {
                document.getElementById(loaderId).outerHTML = `<div class="chat-msg bot">❌ Error al consultar asistente de IA.</div>`;
            }
        });
    }

    // --- Dashboard Analítico & Salud de Scrapers ---
    window.loadAnalyticsTab = async function loadAnalyticsTab() {
        // 1. Cargar estadísticas analíticas
        try {
            const res = await fetch("/api/v1/analytics/dashboard");
            if (res.ok) {
                const data = await res.json();

                // KPIs
                const avgMatch = document.getElementById("kpi-avg-match");
                const remotePct = document.getElementById("kpi-remote-pct");
                const highMatchCount = document.getElementById("kpi-high-match-count");
                const sourcesCount = document.getElementById("kpi-sources-count");
                if (avgMatch) avgMatch.textContent = data.avg_ai_score ? `${Math.round(data.avg_ai_score)}%` : "—";
                if (remotePct) remotePct.textContent = data.remote_percentage ? `${Math.round(data.remote_percentage)}%` : "—";
                if (highMatchCount) highMatchCount.textContent = data.high_match_jobs_count ?? "—";
                if (sourcesCount) sourcesCount.textContent = Object.keys(data.sources_distribution || {}).length || "—";

                // Tech bars
                const techList = document.getElementById("analytics-tech-list");
                if (techList) {
                    const techEntries = Object.entries(data.top_technologies || {});
                    if (techEntries.length === 0) {
                        techList.innerHTML = `<span style="color:var(--text-muted); font-size:0.9rem;">Sin datos de tecnologías aún. Ejecuta el análisis con IA primero.</span>`;
                    } else {
                        const maxVal = Math.max(...techEntries.map(([, v]) => v), 1);
                        techList.innerHTML = techEntries.slice(0, 10).map(([t, count]) => `
                            <div class="tech-bar-item">
                                <div class="tech-bar-label"><span>${t}</span><span>${count}</span></div>
                                <div class="tech-bar-track"><div class="tech-bar-fill" style="width: ${Math.round((count / maxVal) * 100)}%"></div></div>
                            </div>
                        `).join("");
                    }
                }

                // Sources bars
                const sourcesList = document.getElementById("analytics-sources-list");
                if (sourcesList) {
                    const srcEntries = Object.entries(data.sources_distribution || {});
                    if (srcEntries.length === 0) {
                        sourcesList.innerHTML = `<span style="color:var(--text-muted); font-size:0.9rem;">Sin datos de fuentes aún. Ejecuta el scraping primero.</span>`;
                    } else {
                        const maxSrc = Math.max(...srcEntries.map(([, v]) => v), 1);
                        sourcesList.innerHTML = srcEntries.map(([s, count]) => `
                            <div class="source-bar-item">
                                <span style="min-width:100px; font-weight:600;">🌐 ${s}</span>
                                <div class="source-bar-fill" style="width: ${Math.round((count / maxSrc) * 100)}%; max-width: 100%;"></div>
                                <span style="color:var(--text-muted); font-size:0.85rem;">${count}</span>
                            </div>
                        `).join("");
                    }
                }
            } else {
                const techList = document.getElementById("analytics-tech-list");
                if (techList) techList.innerHTML = `<span style="color:#ef4444;">❌ Error al conectar con analíticas (${res.status})</span>`;
            }
        } catch (e) {
            console.error("Error al cargar analíticas:", e);
        }

        // 2. Cargar estado de scrapers
        try {
            const resAdmin = await fetch("/api/v1/admin/scrapers-status");
            const body = document.getElementById("scrapers-status-body");
            if (resAdmin.ok && body) {
                const scrapers = await resAdmin.json();
                body.innerHTML = scrapers.map(sc => `
                    <tr>
                        <td><strong>${sc.name.toUpperCase()}</strong></td>
                        <td><span class="status-badge SUCCESS">${sc.status}</span></td>
                        <td>${sc.last_run ? new Date(sc.last_run).toLocaleString() : 'N/A'}</td>
                        <td>${sc.recent_found}</td>
                        <td>${sc.recent_added}</td>
                    </tr>
                `).join("") || `<tr><td colspan="5" style="text-align:center;">Sin registros de scrapers</td></tr>`;
            } else if (body) {
                body.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#ef4444;">❌ Error al cargar estado de scrapers (${resAdmin.status})</td></tr>`;
            }
        } catch (e) {
            console.error("Error al cargar estado de scrapers:", e);
        }
    }

    // --- Lógica de Configuración de Sistema ---
    const btnOpenConfig = document.getElementById("btn-open-config");
    const sysConfigModal = document.getElementById("sys-config-modal");
    const sysConfigClose = document.getElementById("sys-config-close");
    const sysConfigCancel = document.getElementById("sys-config-cancel");
    const formSysConfig = document.getElementById("form-sys-config");

    if (btnOpenConfig && sysConfigModal) {
        btnOpenConfig.addEventListener("click", async () => {
            try {
                const response = await fetch("/api/v1/config/");
                if (response.ok) {
                    const config = await response.json();
                    document.getElementById("config-ai-provider").value = config.AI_PROVIDER || "openai";
                    document.getElementById("config-openai-key").value = config.OPENAI_API_KEY || "";
                    document.getElementById("config-groq-key").value = config.GROQ_API_KEY || "";
                    document.getElementById("config-anthropic-key").value = config.ANTHROPIC_API_KEY || "";
                    document.getElementById("config-telegram-token").value = config.TELEGRAM_BOT_TOKEN || "";
                    document.getElementById("config-telegram-chat").value = config.TELEGRAM_CHAT_ID || "";
                    sysConfigModal.classList.remove("hidden");
                } else {
                    showToast("❌ Error al cargar configuración", "error");
                }
            } catch (error) {
                console.error("Error fetching config:", error);
                showToast("❌ Error al conectar con el servidor", "error");
            }
        });

        sysConfigClose.addEventListener("click", () => sysConfigModal.classList.add("hidden"));
        sysConfigCancel.addEventListener("click", () => sysConfigModal.classList.add("hidden"));

        formSysConfig.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                AI_PROVIDER: document.getElementById("config-ai-provider").value,
                OPENAI_API_KEY: document.getElementById("config-openai-key").value,
                GROQ_API_KEY: document.getElementById("config-groq-key").value,
                ANTHROPIC_API_KEY: document.getElementById("config-anthropic-key").value,
                TELEGRAM_BOT_TOKEN: document.getElementById("config-telegram-token").value,
                TELEGRAM_CHAT_ID: document.getElementById("config-telegram-chat").value
            };

            try {
                const response = await fetch("/api/v1/config/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    showToast("✅ Configuración guardada correctamente");
                    sysConfigModal.classList.add("hidden");
                } else {
                    const err = await response.json();
                    showToast(`❌ Error al guardar: ${err.detail || 'Desconocido'}`, "error");
                }
            } catch (error) {
                console.error("Error saving config:", error);
                showToast("❌ Error de red al guardar configuración", "error");
            }
        });
    }

    // Carga inicial
    loadStats();
    loadJobs();
});

/**
 * ScamShield AI — Frontend Application Logic
 * 
 * Provides interactive preset scenarios, real-time character counting, keyboard
 * shortcuts (Ctrl+Enter), safe DOM rendering (XSS prevention), and benchmark modal.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const form = document.getElementById("analyze-form");
  const messageInput = document.getElementById("message-text");
  const urlInput = document.getElementById("url-input");
  const messageCounter = document.getElementById("message-char-count");
  const urlCounter = document.getElementById("url-char-count");
  const btnAnalyze = document.getElementById("btn-analyze");
  const btnClear = document.getElementById("btn-clear");
  const alertBanner = document.getElementById("alert-banner");
  const alertText = document.getElementById("alert-text");

  // State Containers
  const emptyState = document.getElementById("empty-state");
  const loadingState = document.getElementById("loading-state");
  const verdictContainer = document.getElementById("verdict-container");

  // Result Elements
  const verdictBanner = document.getElementById("verdict-banner");
  const verdictIcon = document.getElementById("verdict-icon");
  const verdictLabel = document.getElementById("verdict-label");
  const scoreValue = document.getElementById("score-value");
  const confidenceBadge = document.getElementById("confidence-badge");
  const gaugeFill = document.getElementById("gauge-fill");
  const summaryText = document.getElementById("summary-text");
  const evidenceList = document.getElementById("evidence-list");
  const textSignalsSection = document.getElementById("text-signals-section");
  const textSignalsList = document.getElementById("text-signals-list");
  const textTokensCloud = document.getElementById("text-tokens-cloud");
  const urlSignalsSection = document.getElementById("url-signals-section");
  const urlSignalsList = document.getElementById("url-signals-list");
  const actionText = document.getElementById("action-text");

  // Evaluation Modal Elements
  const btnEvaluation = document.getElementById("btn-view-evaluation");
  const modalEvaluation = document.getElementById("modal-evaluation");
  const btnModalClose = document.getElementById("btn-modal-close");
  const metricAcc = document.getElementById("metric-accuracy");
  const metricPrec = document.getElementById("metric-precision");
  const metricRec = document.getElementById("metric-recall");
  const metricF1 = document.getElementById("metric-f1");
  const cmTn = document.getElementById("cm-tn-val");
  const cmFp = document.getElementById("cm-fp-val");
  const cmFn = document.getElementById("cm-fn-val");
  const cmTp = document.getElementById("cm-tp-val");
  const evalMetaTime = document.getElementById("eval-meta-time");

  // Preset Scenarios Data
  const PRESETS = {
    bank: {
      text: "URGENT: Your SBI account has been locked due to incomplete KYC verification. Verify your identity immediately at http://sbi-kyc-verify.xyz/login to prevent permanent account suspension and fee.",
      url: "http://sbi-kyc-verify.xyz/login"
    },
    job: {
      text: "Exciting Part-Time Opportunity! Earn Rs. 2,000 to Rs. 5,000 daily working from home just by liking YouTube videos and writing short reviews. Instant daily payout to your UPI. Reply now to get started!",
      url: ""
    },
    shortlink: {
      text: "",
      url: "http://192.168.1.1/free-gift-card/claim-reward"
    },
    safe: {
      text: "Your Amazon package with tracking #IN-84920 has been dispatched and is scheduled for delivery today before 6 PM.",
      url: "https://www.amazon.in/orders/track"
    }
  };

  // ---------------------------------------------------------------------------
  // Real-Time Character Counters
  // ---------------------------------------------------------------------------
  function updateCharCounters() {
    messageCounter.textContent = `${messageInput.value.length} / 10,000`;
    urlCounter.textContent = `${urlInput.value.length} / 2,048`;
  }

  messageInput.addEventListener("input", updateCharCounters);
  urlInput.addEventListener("input", updateCharCounters);

  // ---------------------------------------------------------------------------
  // Preset Chips Listener
  // ---------------------------------------------------------------------------
  document.querySelectorAll(".preset-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const presetKey = chip.getAttribute("data-preset");
      if (PRESETS[presetKey]) {
        messageInput.value = PRESETS[presetKey].text;
        urlInput.value = PRESETS[presetKey].url;
        updateCharCounters();
        hideAlert();
        handleAnalyze();
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Alert Helper
  // ---------------------------------------------------------------------------
  function showAlert(msg) {
    alertText.textContent = msg;
    alertBanner.classList.add("visible");
  }

  function hideAlert() {
    alertBanner.classList.remove("visible");
    alertText.textContent = "";
  }

  // ---------------------------------------------------------------------------
  // Keyboard Shortcut: Ctrl + Enter / Cmd + Enter
  // ---------------------------------------------------------------------------
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleAnalyze();
    }
  });

  // ---------------------------------------------------------------------------
  // Reset Form
  // ---------------------------------------------------------------------------
  btnClear.addEventListener("click", () => {
    messageInput.value = "";
    urlInput.value = "";
    updateCharCounters();
    hideAlert();
    verdictContainer.classList.remove("visible");
    loadingState.classList.remove("visible");
    emptyState.style.display = "flex";
  });

  // ---------------------------------------------------------------------------
  // Core Analysis Action
  // ---------------------------------------------------------------------------
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    handleAnalyze();
  });

  async function handleAnalyze() {
    const text = messageInput.value.trim();
    const url = urlInput.value.trim();

    if (!text && !url) {
      showAlert("Please provide at least a message text or a valid URL to analyze.");
      messageInput.focus();
      return;
    }

    hideAlert();

    // Set UI to loading state
    emptyState.style.display = "none";
    verdictContainer.classList.remove("visible");
    loadingState.classList.add("visible");
    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = `
      <svg class="pulse-dot" viewBox="0 0 24 24" style="width:16px;height:16px;border-radius:50%;background:none;box-shadow:none;">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" stroke-dasharray="32" stroke-linecap="round">
          <animateTransform attributeName="transform" type="rotate" dur="1s" from="0 12 12" to="360 12 12" repeatCount="indefinite"/>
        </circle>
      </svg>
      Analyzing...
    `;

    try {
      const response = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text.length > 0 ? text : null,
          url: url.length > 0 ? url : null,
        }),
      });

      if (!response.ok) {
        if (response.status === 429) {
          const retryAfter = response.headers.get("Retry-After") || 60;
          throw new Error(`Rate limit reached (Protection Policy). Please wait ${retryAfter}s before scanning again.`);
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Analysis request failed.");
      }

      const result = await response.json();
      renderVerdict(result);
      fetchTelemetry();
    } catch (err) {
      showAlert(`Notice: ${err.message}`);
      loadingState.classList.remove("visible");
      emptyState.style.display = "flex";
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        Inspect &amp; Analyze
      `;
    }
  }

  // ---------------------------------------------------------------------------
  // Safe DOM Rendering (Zero XSS)
  // ---------------------------------------------------------------------------
  let latestVerdictData = null;

  function renderVerdict(data) {
    latestVerdictData = data;
    loadingState.classList.remove("visible");

    // 1. Reset theme classes
    verdictBanner.classList.remove("verdict-safe", "verdict-review", "verdict-scam");

    // 2. Map verdict to visual state
    let themeClass = "verdict-safe";
    let iconSvg = `
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <polyline points="9 12 11 14 15 10"/>
      </svg>
    `;

    if (data.verdict === "likely scam") {
      themeClass = "verdict-scam";
      iconSvg = `
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      `;
    } else if (data.verdict === "needs review") {
      themeClass = "verdict-review";
      iconSvg = `
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      `;
    }

    verdictBanner.classList.add(themeClass);
    verdictIcon.innerHTML = iconSvg;
    verdictLabel.textContent = data.verdict.toUpperCase();
    scoreValue.textContent = data.risk_score;
    confidenceBadge.textContent = `${Math.round(data.confidence * 100)}% Risk Index`;

    // 3. Smooth animated progress gauge
    gaugeFill.style.width = `${data.risk_score}%`;
    gaugeFill.className = `gauge-fill gauge-${themeClass.replace("verdict-", "")}`;

    // 4. Diagnostic Summary
    summaryText.textContent = data.summary;

    // 5. Plain-English Evidence List
    evidenceList.innerHTML = "";
    if (data.evidence && data.evidence.length > 0) {
      data.evidence.forEach(point => {
        const li = document.createElement("li");
        li.className = "evidence-item";

        const bullet = document.createElement("span");
        bullet.className = "evidence-bullet";
        bullet.textContent = "•";

        const textSpan = document.createElement("span");
        textSpan.textContent = point;

        li.appendChild(bullet);
        li.appendChild(textSpan);
        evidenceList.appendChild(li);
      });
    }

    // 6. Text Signals Breakdown
    if (data.text_analysis && data.text_analysis.provided) {
      textSignalsSection.style.display = "block";
      textSignalsList.innerHTML = "";
      textTokensCloud.innerHTML = "";

      if (data.text_analysis.detected_patterns) {
        data.text_analysis.detected_patterns.forEach(pat => {
          const li = document.createElement("li");
          li.className = "evidence-item";
          li.textContent = pat;
          textSignalsList.appendChild(li);
        });
      }

      if (data.text_analysis.key_tokens) {
        data.text_analysis.key_tokens.forEach(tok => {
          const chip = document.createElement("span");
          chip.className = `chip-token ${data.risk_score < 35 ? "safe-token" : ""}`;
          chip.textContent = tok;
          textTokensCloud.appendChild(chip);
        });
      }
    } else {
      textSignalsSection.style.display = "none";
    }

    // 7. URL Signals Breakdown
    if (data.url_analysis && data.url_analysis.provided) {
      urlSignalsSection.style.display = "block";
      urlSignalsList.innerHTML = "";

      if (data.url_analysis.flagged_indicators && data.url_analysis.flagged_indicators.length > 0) {
        data.url_analysis.flagged_indicators.forEach(ind => {
          const li = document.createElement("li");
          li.className = "evidence-item";
          li.textContent = ind;
          urlSignalsList.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.className = "evidence-item";
        li.textContent = "No suspicious lexical patterns or spoofing keywords detected in URL.";
        urlSignalsList.appendChild(li);
      }
    } else {
      urlSignalsSection.style.display = "none";
    }

    // 8. Recommended Action
    actionText.textContent = data.recommended_action;

    // Show result container
    verdictContainer.classList.add("visible");
  }

  // ---------------------------------------------------------------------------
  // Evaluation Modal Handlers
  // ---------------------------------------------------------------------------
  btnEvaluation.addEventListener("click", async () => {
    modalEvaluation.classList.add("active");
    try {
      const response = await fetch("/api/v1/evaluation");
      if (response.ok) {
        const evalData = await response.json();
        metricAcc.textContent = `${(evalData.metrics.accuracy * 100).toFixed(1)}%`;
        metricPrec.textContent = `${(evalData.metrics.precision * 100).toFixed(1)}%`;
        metricRec.textContent = `${(evalData.metrics.recall * 100).toFixed(1)}%`;
        metricF1.textContent = `${(evalData.metrics.f1_score * 100).toFixed(1)}%`;

        cmTn.textContent = evalData.confusion_matrix.true_negatives;
        cmFp.textContent = evalData.confusion_matrix.false_positives;
        cmFn.textContent = evalData.confusion_matrix.false_negatives;
        cmTp.textContent = evalData.confusion_matrix.true_positives;

        evalMetaTime.textContent = `Evaluation Verified: ${evalData.verified_at} | Test Samples: ${evalData.dataset.test_samples}`;
      }
    } catch (err) {
      console.error("Failed to load evaluation metrics:", err);
    }
  });

  btnModalClose.addEventListener("click", () => {
    modalEvaluation.classList.remove("active");
  });

  modalEvaluation.addEventListener("click", (e) => {
    if (e.target === modalEvaluation) {
      modalEvaluation.classList.remove("active");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalEvaluation.classList.contains("active")) {
      modalEvaluation.classList.remove("active");
    }
  });

  // ---------------------------------------------------------------------------
  // Real-Time Telemetry HUD Polling & Fetching (Item 14)
  // ---------------------------------------------------------------------------
  const hudTotal = document.getElementById("hud-total-scans");
  const hudThreats = document.getElementById("hud-threats-intercepted");
  const hudSafe = document.getElementById("hud-safe-verified");
  const hudLatency = document.getElementById("hud-avg-latency");

  async function fetchTelemetry() {
    try {
      const res = await fetch("/api/v1/analytics");
      if (res.ok) {
        const data = await res.json();
        if (hudTotal) hudTotal.textContent = Number(data.total_scans).toLocaleString();
        if (hudThreats) hudThreats.textContent = Number(data.scams_intercepted + data.suspicious_flagged).toLocaleString();
        if (hudSafe) hudSafe.textContent = Number(data.safe_verified).toLocaleString();
        if (hudLatency) hudLatency.textContent = `${data.avg_latency_ms}ms`;
      }
    } catch {
      // Gracefully silent on connection hiccup
    }
  }

  // Trigger telemetry on load and periodically
  fetchTelemetry();
  setInterval(fetchTelemetry, 15000);

  // ---------------------------------------------------------------------------
  // Dynamic Engine Runtime Health Polling (Stage B/C)
  // ---------------------------------------------------------------------------
  const runtimeBadge = document.getElementById("runtime-badge");
  const runtimeDot = document.getElementById("runtime-dot");
  const runtimeText = document.getElementById("runtime-text");

  async function checkEngineHealth() {
    try {
      const res = await fetch("/api/v1/health");
      if (res.ok) {
        const data = await res.json();
        if (data.status === "healthy") {
          if (runtimeDot) runtimeDot.style.background = "var(--safe-text)";
          if (runtimeText) runtimeText.textContent = "Engine Online";
          if (runtimeBadge) runtimeBadge.title = "ML Model & Database operational";
        } else {
          if (runtimeDot) runtimeDot.style.background = "var(--review-text)";
          if (runtimeText) runtimeText.textContent = "Subsystem Degraded";
          if (runtimeBadge) runtimeBadge.title = "Core subsystem degraded";
        }
      } else {
        if (runtimeDot) runtimeDot.style.background = "var(--danger)";
        if (runtimeText) runtimeText.textContent = "Engine Offline";
      }
    } catch {
      if (runtimeDot) runtimeDot.style.background = "var(--danger)";
      if (runtimeText) runtimeText.textContent = "Engine Offline";
    }
  }

  checkEngineHealth();
  setInterval(checkEngineHealth, 30000);

  // ---------------------------------------------------------------------------
  // Copy Threat Assessment Report to Clipboard
  // ---------------------------------------------------------------------------
  const btnCopyReport = document.getElementById("btn-copy-report");
  const btnCopyReportText = document.getElementById("btn-copy-report-text");

  if (btnCopyReport) {
    btnCopyReport.addEventListener("click", () => {
      if (!latestVerdictData) return;
      const d = latestVerdictData;
      const confidencePct = Math.round((d.confidence || 0) * 100);
      const evidenceLines = (d.evidence && d.evidence.length > 0)
        ? d.evidence.map(e => `  - ${e}`).join("\n")
        : "  - No critical threat anomalies detected.";

      const report = [
        "==================================================",
        "  SCAMSHIELD AI — THREAT ASSESSMENT REPORT",
        "==================================================",
        `Verdict:         ${(d.verdict || "UNKNOWN").toUpperCase()}`,
        `Risk Score:      ${d.risk_score} / 100`,
        `Risk Band:       ${(d.risk_band || "").toUpperCase()}`,
        `Risk Index:      ${confidencePct}% (Score Normalized)`,
        "",
        `Diagnostic Summary:`,
        `  ${d.summary || "No diagnostic summary available."}`,
        "",
        `Observed Evidence:`,
        evidenceLines,
        "",
        `Recommended Protective Action:`,
        `  ${d.action || "Verify independently with official institution."}`,
        "==================================================",
        "Verified by ScamShield AI (Zero-Network Passive Heuristics)",
      ].join("\n");

      navigator.clipboard.writeText(report).then(() => {
        if (btnCopyReportText) {
          const original = btnCopyReportText.textContent;
          btnCopyReportText.textContent = "Copied!";
          setTimeout(() => {
            btnCopyReportText.textContent = original;
          }, 2000);
        }
      }).catch(() => {
        showAlert("Unable to access clipboard. Please copy manually.");
      });
    });
  }


  // ---------------------------------------------------------------------------
  // Interactive Onboarding Tour Controller (Item 19)
  // ---------------------------------------------------------------------------
  const modalTour = document.getElementById("modal-tour");
  const btnOpenTour = document.getElementById("btn-open-tour");
  const btnStartTour = document.getElementById("btn-start-tour");
  const btnTourClose = document.getElementById("btn-tour-close");
  const btnTourPrev = document.getElementById("btn-tour-prev");
  const btnTourNext = document.getElementById("btn-tour-next");
  const tourStepBadge = document.getElementById("tour-step-badge");
  const tourSlides = document.querySelectorAll(".tour-slide");
  const tourDots = document.querySelectorAll(".tour-dot");

  let currentTourStep = 1;
  const totalTourSteps = 4;

  function showTourStep(step) {
    currentTourStep = step;
    tourSlides.forEach((slide) => {
      slide.classList.toggle("active", parseInt(slide.dataset.step, 10) === step);
    });
    tourDots.forEach((dot) => {
      dot.classList.toggle("active", parseInt(dot.dataset.dot, 10) === step);
    });

    if (tourStepBadge) {
      tourStepBadge.textContent = `Step ${step} of ${totalTourSteps}`;
    }

    if (btnTourPrev) {
      btnTourPrev.style.display = step > 1 ? "inline-flex" : "none";
    }

    if (btnTourNext) {
      btnTourNext.textContent = step === totalTourSteps ? "Finish Tour" : "Next Step";
    }
  }

  function openTour() {
    showTourStep(1);
    if (modalTour) modalTour.classList.add("active");
  }

  function closeTour() {
    if (modalTour) modalTour.classList.remove("active");
    try {
      localStorage.setItem("scamshield_tour_seen", "true");
    } catch {
      // Storage unavailable fallback
    }
  }

  if (btnOpenTour) btnOpenTour.addEventListener("click", openTour);
  if (btnStartTour) btnStartTour.addEventListener("click", openTour);
  if (btnTourClose) btnTourClose.addEventListener("click", closeTour);

  if (btnTourPrev) {
    btnTourPrev.addEventListener("click", () => {
      if (currentTourStep > 1) {
        showTourStep(currentTourStep - 1);
      }
    });
  }

  if (btnTourNext) {
    btnTourNext.addEventListener("click", () => {
      if (currentTourStep < totalTourSteps) {
        showTourStep(currentTourStep + 1);
      } else {
        closeTour();
      }
    });
  }

  if (modalTour) {
    modalTour.addEventListener("click", (e) => {
      if (e.target === modalTour) closeTour();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalTour && modalTour.classList.contains("active")) {
      closeTour();
    }
  });

  // Automatically offer tour on first visit
  try {
    if (!localStorage.getItem("scamshield_tour_seen")) {
      setTimeout(openTour, 1000);
    }
  } catch {
    // Ignored
  }

  // ---------------------------------------------------------------------------
  // Authentication & Account Lifecycle Controller (Items 1, 2, 3, 10, 18)
  // ---------------------------------------------------------------------------
  const modalAuth = document.getElementById("modal-auth");
  const modalHistory = document.getElementById("modal-history");
  const authGuestSection = document.getElementById("auth-guest-section");
  const authUserSection = document.getElementById("auth-user-section");
  const btnOpenAuth = document.getElementById("btn-open-auth");
  const btnAuthClose = document.getElementById("btn-auth-close");
  const btnOpenHistory = document.getElementById("btn-open-history");
  const btnHistoryClose = document.getElementById("btn-history-close");
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const btnLogout = document.getElementById("btn-logout");
  const userDisplayEmail = document.getElementById("user-display-email");
  const settingsDisplayEmail = document.getElementById("settings-display-email");
  const settingsVerifiedBadge = document.getElementById("settings-verified-badge");
  const authMsgBanner = document.getElementById("auth-msg-banner");
  const tabSettingsBtn = document.getElementById("tab-settings-btn");
  const historyItemsList = document.getElementById("history-items-list");
  const historyEmpty = document.getElementById("history-empty");

  // Auth Tabs
  const authTabs = document.querySelectorAll(".auth-tab");
  const authPanes = document.querySelectorAll(".auth-tab-pane");

  function switchAuthTab(tabName) {
    authTabs.forEach(t => t.classList.toggle("active", t.dataset.tab === tabName));
    authPanes.forEach(p => p.classList.toggle("active", p.id === `pane-${tabName}`));
    clearAuthMsg();
  }

  authTabs.forEach(tab => {
    tab.addEventListener("click", () => switchAuthTab(tab.dataset.tab));
  });

  function showAuthMsg(msg, isSuccess = false) {
    if (!authMsgBanner) return;
    authMsgBanner.textContent = msg;
    authMsgBanner.className = `auth-msg-banner ${isSuccess ? 'auth-msg-success' : 'auth-msg-error'}`;
    authMsgBanner.style.display = "block";
  }

  function clearAuthMsg() {
    if (!authMsgBanner) return;
    authMsgBanner.style.display = "none";
    authMsgBanner.textContent = "";
  }

  function openAuthModal(defaultTab = "login") {
    switchAuthTab(defaultTab);
    if (modalAuth) modalAuth.classList.add("active");
  }

  function closeAuthModal() {
    if (modalAuth) modalAuth.classList.remove("active");
    clearAuthMsg();
  }

  if (btnOpenAuth) btnOpenAuth.addEventListener("click", () => openAuthModal("login"));
  if (btnAuthClose) btnAuthClose.addEventListener("click", closeAuthModal);
  if (btnOpenSettings) btnOpenSettings.addEventListener("click", () => openAuthModal("settings"));

  // Check Current Session Status
  let currentUser = null;

  async function checkAuthStatus() {
    try {
      const res = await fetch("/api/v1/auth/me");
      if (res.ok) {
        const data = await res.json();
        currentUser = data.user;
        renderLoggedInState(currentUser);
      } else {
        currentUser = null;
        renderLoggedOutState();
      }
    } catch {
      currentUser = null;
      renderLoggedOutState();
    }
  }

  function renderLoggedInState(user) {
    if (authGuestSection) authGuestSection.style.display = "none";
    if (authUserSection) authUserSection.style.display = "flex";
    if (userDisplayEmail) {
      const name = user.email.split("@")[0];
      userDisplayEmail.textContent = name.length > 12 ? name.substring(0, 10) + ".." : name;
    }
    if (settingsDisplayEmail) settingsDisplayEmail.textContent = user.email;
    if (settingsVerifiedBadge) {
      settingsVerifiedBadge.textContent = user.is_verified ? "Verified User" : "Unverified (Check Code)";
      settingsVerifiedBadge.style.color = user.is_verified ? "var(--safe-text)" : "var(--review-text)";
    }
    if (tabSettingsBtn) tabSettingsBtn.style.display = "inline-block";
  }

  function renderLoggedOutState() {
    if (authGuestSection) authGuestSection.style.display = "flex";
    if (authUserSection) authUserSection.style.display = "none";
    if (tabSettingsBtn) tabSettingsBtn.style.display = "none";
  }

  // Handle Login Form
  const formLogin = document.getElementById("form-login");
  if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("login-email").value.trim();
      const password = document.getElementById("login-password").value;
      try {
        const res = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Login failed");
        showAuthMsg("Login successful! Welcome back.", true);
        setTimeout(() => {
          closeAuthModal();
          checkAuthStatus();
        }, 600);
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle Register Form (Item 1 & 3)
  const formRegister = document.getElementById("form-register");
  const sectionVerify = document.getElementById("section-verify-email");
  let pendingVerifyEmail = "";

  if (formRegister) {
    formRegister.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("reg-email").value.trim();
      const password = document.getElementById("reg-password").value;
      try {
        const res = await fetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Registration failed");

        pendingVerifyEmail = email;
        showAuthMsg(`Account created! Simulated verification code: ${data.verification_code}`, true);
        if (sectionVerify) {
          sectionVerify.style.display = "block";
          const codeInput = document.getElementById("verify-code-input");
          if (codeInput) codeInput.value = data.verification_code;
        }
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle Verify Email Code
  const btnSubmitVerify = document.getElementById("btn-submit-verify");
  if (btnSubmitVerify) {
    btnSubmitVerify.addEventListener("click", async () => {
      const code = document.getElementById("verify-code-input").value.trim();
      if (!code || !pendingVerifyEmail) {
        showAuthMsg("Please enter the verification code.", false);
        return;
      }
      try {
        const res = await fetch("/api/v1/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: pendingVerifyEmail, code }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Verification failed");
        showAuthMsg("Email verified successfully! You are now logged in.", true);
        setTimeout(() => {
          closeAuthModal();
          checkAuthStatus();
        }, 800);
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle Forgot Password (Item 2)
  const formForgot = document.getElementById("form-forgot");
  const sectionReset = document.getElementById("section-reset-pwd");
  if (formForgot) {
    formForgot.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("forgot-email").value.trim();
      try {
        const res = await fetch("/api/v1/auth/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await res.json();
        showAuthMsg(data.message, true);
        if (sectionReset) {
          sectionReset.style.display = "block";
        }
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle Reset Password Submit
  const btnSubmitReset = document.getElementById("btn-submit-reset");
  if (btnSubmitReset) {
    btnSubmitReset.addEventListener("click", async () => {
      const token = document.getElementById("reset-token-input").value.trim();
      const new_password = document.getElementById("reset-new-password").value;
      if (!token || !new_password) {
        showAuthMsg("Please provide both the reset token and new password.", false);
        return;
      }
      try {
        const res = await fetch("/api/v1/auth/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, new_password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Password reset failed");
        showAuthMsg("Password updated! You can now sign in.", true);
        setTimeout(() => switchAuthTab("login"), 1000);
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle Logout
  if (btnLogout) {
    btnLogout.addEventListener("click", async () => {
      await fetch("/api/v1/auth/logout", { method: "POST" });
      currentUser = null;
      renderLoggedOutState();
    });
  }

  // Handle Delete Account (Item 18)
  const btnDeleteAccount = document.getElementById("btn-delete-account");
  if (btnDeleteAccount) {
    btnDeleteAccount.addEventListener("click", async () => {
      const confirmPurge = confirm("WARNING: This will permanently delete your account and all associated scan history from the database in compliance with GDPR Right to Erasure. Proceed?");
      if (!confirmPurge) return;

      try {
        const res = await fetch("/api/v1/auth/account", { method: "DELETE" });
        if (res.ok) {
          closeAuthModal();
          currentUser = null;
          renderLoggedOutState();
          showAlert("Account and private scan records permanently purged (GDPR Art. 17).");
        }
      } catch (err) {
        showAuthMsg(err.message, false);
      }
    });
  }

  // Handle User Scan History Modal (Item 10)
  if (btnOpenHistory) {
    btnOpenHistory.addEventListener("click", async () => {
      if (modalHistory) modalHistory.classList.add("active");
      if (historyItemsList) historyItemsList.innerHTML = "<div style='color:var(--text-tertiary); text-align:center; padding:1.5rem;'>Loading scans...</div>";

      try {
        const res = await fetch("/api/v1/auth/history");
        if (!res.ok) throw new Error("Failed to load history");
        const data = await res.json();
        const scans = data.scans || [];

        if (scans.length === 0) {
          if (historyEmpty) historyEmpty.style.display = "block";
          if (historyItemsList) historyItemsList.innerHTML = "";
        } else {
          if (historyEmpty) historyEmpty.style.display = "none";
          if (historyItemsList) {
            historyItemsList.innerHTML = scans.map(s => {
              const dateStr = new Date(s.timestamp * 1000).toLocaleString();
              let pillClass = "pill-safe";
              if (s.verdict === "needs review") pillClass = "pill-review";
              if (s.verdict === "likely scam") pillClass = "pill-scam";

              const preview = s.preview_text || s.preview_url || "Empty scan";
              // Escape HTML for XSS prevention
              const safePreview = preview.replace(/[&<>"']/g, m => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
              })[m]);

              return `
                <div class="history-card">
                  <div class="history-info">
                    <span class="history-preview">${safePreview}</span>
                    <span class="history-date">${dateStr} &middot; Risk Score: ${s.risk_score}</span>
                  </div>
                  <span class="tour-pill ${pillClass}">${s.verdict.toUpperCase()}</span>
                </div>
              `;
            }).join("");
          }
        }
      } catch {
        if (historyItemsList) historyItemsList.innerHTML = "<div style='color:var(--danger); text-align:center;'>Unable to load scan history.</div>";
      }
    });
  }

  if (btnHistoryClose) {
    btnHistoryClose.addEventListener("click", () => {
      if (modalHistory) modalHistory.classList.remove("active");
    });
  }

  // Close modals on escape or backdrop
  [modalAuth, modalHistory].forEach(m => {
    if (!m) return;
    m.addEventListener("click", (e) => {
      if (e.target === m) m.classList.remove("active");
    });
  });

  // Check auth session on startup
  checkAuthStatus();
});



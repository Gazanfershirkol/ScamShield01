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
  function renderVerdict(data) {
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
});


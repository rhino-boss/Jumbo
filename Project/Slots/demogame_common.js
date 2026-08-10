(() => {
  "use strict";

  document.body.classList.add("slot-simulator");

  const betModePanel = document.getElementById("bet-mode-panel");
  const helpDialog = document.getElementById("helpDialog");
  const helpButton = document.getElementById("helpBtn");

  function syncBetModeAccessibility() {
    if (!betModePanel) return;
    for (const button of betModePanel.querySelectorAll("button")) {
      const active = button.classList.contains("active") || button.classList.contains("is-active");
      button.setAttribute("aria-pressed", String(active));
    }
  }

  syncBetModeAccessibility();
  if (betModePanel) {
    new MutationObserver(syncBetModeAccessibility).observe(betModePanel, {
      attributes: true,
      attributeFilter: ["class"],
      subtree: true
    });
  }

  if (helpDialog) {
    const title = helpDialog.querySelector("h2");
    if (title && !title.id) title.id = "helpDialogTitle";
    if (title) helpDialog.setAttribute("aria-labelledby", title.id);
    helpButton?.setAttribute("aria-haspopup", "dialog");
    helpButton?.setAttribute("aria-controls", helpDialog.id);
  }

  function getMathConfig() {
    const candidates = [];
    try {
      if (typeof data !== "undefined" && data && typeof data === "object") candidates.push(data);
    } catch (_) {}
    for (const key of Object.keys(window)) {
      if (!/(?:_BOX_DATA|_CONFIG)$/.test(key)) continue;
      const value = window[key];
      if (value && typeof value === "object") candidates.push(value);
    }
    return candidates.find((value) => value.card_system)
      || candidates.find((value) => value.excel_version || value.game_version)
      || candidates[0]
      || null;
  }

  function normalizeConfigName(option) {
    const source = `${option?.value || ""} ${option?.textContent || ""}`;
    const configMatch = source.match(/config[_-]?([0-9]+[A-Za-z]?)/i);
    if (configMatch) return configMatch[1].toUpperCase();
    const compact = source.match(/(?:^|[^0-9])((?:9[0-9])(?:[A-Za-z])?)(?:[^0-9]|$)/);
    if (compact) return compact[1].toUpperCase();
    const mathConfig = getMathConfig();
    const parsheetMatch = String(mathConfig?.parsheet_id || mathConfig?.source_game_id || "").match(/(9[0-9][A-Za-z]?)$/);
    return String(mathConfig?.rtp_label || parsheetMatch?.[1] || option?.textContent?.trim() || "Current").toUpperCase();
  }

  function normalizeProfileName(value) {
    const raw = String(value || "").toLowerCase();
    if (/new|weight[_-]?1/.test(raw)) return "Newbie";
    return "Oldhand";
  }

  function syncNativeCardControl(enabled) {
    const select = document.getElementById("cardRangeSelect");
    if (!select || ![...select.options].some((option) => option.value === "off")) return;
    let savedProfile = "oldhand";
    try { savedProfile = localStorage.getItem("slotDemoCardProfile") === "newbie" ? "newbie" : "oldhand"; } catch (_) {}
    const combinedProfile = document.getElementById("demogameConfigSelect")?.selectedOptions?.[0]?.textContent;
    const profile = combinedProfile ? normalizeProfileName(combinedProfile).toLowerCase() : savedProfile;
    const next = enabled && [...select.options].some((option) => option.value === profile) ? profile : "off";
    if (select.value === next) return;
    select.value = next;
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function ensureCombinedConfigAndVersion() {
    const body = document.querySelector("#settings-wrap > .setting-body");
    if (!body || document.getElementById("demogameConfigSelect")) return;

    const configSelect = document.getElementById("configSelect");
    const profileSelect = document.getElementById("cardProfileSelect");
    const rangeSelect = document.getElementById("cardRangeSelect");
    const configOptions = configSelect ? [...configSelect.options] : [new Option("Current", "")];
    const profileOptions = profileSelect
      ? [...profileSelect.options].map((option) => ({ value: option.value, name: normalizeProfileName(option.value || option.textContent) }))
      : [
          { value: "newbie", name: "Newbie" },
          { value: "oldhand", name: "Oldhand" }
        ];

    configSelect?.closest("label")?.classList.add("demogame-source-control");
    profileSelect?.closest("label")?.classList.add("demogame-source-control");

    const combinedLabel = document.createElement("label");
    combinedLabel.className = "config-control demogame-combined-control";
    combinedLabel.append("Config ");
    const combined = document.createElement("select");
    combined.id = "demogameConfigSelect";
    for (const configOption of configOptions) {
      for (const profile of profileOptions) {
        const option = document.createElement("option");
        option.value = JSON.stringify([configOption.value, profile.value]);
        option.textContent = `${normalizeConfigName(configOption)}-${profile.name}`;
        if ((!configSelect || configOption.selected) && profile.name === normalizeProfileName(profileSelect?.value || "oldhand")) {
          option.selected = true;
        }
        combined.appendChild(option);
      }
    }
    combinedLabel.appendChild(combined);

    const versionLabel = document.createElement("label");
    versionLabel.className = "config-control demogame-version-control";
    versionLabel.append("Version ");
    const versionSelect = document.createElement("select");
    versionSelect.id = "versionSelect";
    const mathConfig = getMathConfig();
    const version = mathConfig?.excel_version || mathConfig?.game_version || mathConfig?.version || "Current";
    versionSelect.appendChild(new Option(String(version), String(version), true, true));
    versionLabel.appendChild(versionSelect);

    const anchor = configSelect?.closest("label") || profileSelect?.closest("label") || body.firstChild;
    body.insertBefore(versionLabel, anchor);
    versionLabel.insertAdjacentElement("afterend", combinedLabel);

    combined.addEventListener("change", () => {
      const [configValue, profileValue] = JSON.parse(combined.value);
      try { localStorage.setItem("slotDemoCardProfile", normalizeProfileName(profileValue).toLowerCase()); } catch (_) {}
      if (profileSelect && profileSelect.value !== profileValue) {
        profileSelect.value = profileValue;
        profileSelect.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (rangeSelect) {
        const target = [...rangeSelect.options].find((option) => normalizeProfileName(option.value || option.textContent) === normalizeProfileName(profileValue));
        if (target && rangeSelect.value !== target.value) {
          rangeSelect.value = target.value;
          rangeSelect.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
      syncNativeCardControl(document.getElementById("cardSystemInput")?.checked);
      if (configSelect && configSelect.value !== configValue) {
        configSelect.value = configValue;
        configSelect.dispatchEvent(new Event("change", { bubbles: true }));
      }
      updateSharedSimulationContext();
    });
  }

  function normalizeStatsTitle() {
    const title = document.querySelector("#simulation-stats h3");
    if (!title) return;
    title.removeAttribute("data-i18n");
    title.textContent = "Stats";
  }

  function ensureCardSystemToggle() {
    const settingsBody = document.querySelector("#settings-wrap > .setting-body");
    if (!settingsBody) return;

    let input = document.getElementById("cardSystemInput");
    const nativeInput = Boolean(input);
    let label = input?.closest("label");
    if (!input) {
      label = document.createElement("label");
      label.className = "setting-toggle";
      label.htmlFor = "cardSystemInput";
      label.innerHTML = '<input id="cardSystemInput" type="checkbox"><span>Card System</span>';
      input = label.querySelector("input");
      const firstControl = settingsBody.querySelector(".config-control");
      settingsBody.insertBefore(label, firstControl);

      let saved = null;
      try { saved = localStorage.getItem("slotDemoCardSystem"); } catch (_) {}
      input.checked = saved !== "off";
    }

    if (!nativeInput) {
      const supported = getMathConfig()?.card_system?.enabled === true;
      input.disabled = !supported;
      if (!supported) input.checked = false;
      label.classList.toggle("is-unavailable", !supported);
      label.title = supported ? "" : "This math config has no Card System model.";
    }

    const text = label.querySelector("span") || label.appendChild(document.createElement("span"));
    text.removeAttribute("data-i18n");
    text.textContent = "Card System";

    window.DEMOGAME_CARD_SYSTEM_ENABLED = input.checked;
    syncNativeCardControl(input.checked);
    input.addEventListener("change", () => {
      window.DEMOGAME_CARD_SYSTEM_ENABLED = input.checked;
      syncNativeCardControl(input.checked);
      try { localStorage.setItem("slotDemoCardSystem", input.checked ? "on" : "off"); } catch (_) {}
      document.dispatchEvent(new CustomEvent("demogame:card-system-change", {
        detail: { enabled: input.checked }
      }));
      updateSharedSimulationContext();
    });
  }

  ensureCardSystemToggle();
  ensureCombinedConfigAndVersion();
  syncNativeCardControl(document.getElementById("cardSystemInput")?.checked);
  normalizeStatsTitle();

  function normalizeSettings() {
    const settings = document.getElementById("settings-wrap");
    const body = settings?.querySelector(":scope > .setting-body");
    if (!settings || !body || body.dataset.demogameNormalized === "true") return;

    settings.classList.add("demogame-settings");
    settings.querySelector(":scope > .setting-header, :scope > .diagnostic-header")
      ?.classList.add("diagnostic-header");

    const left = document.createElement("div");
    const right = document.createElement("div");
    left.className = "setting-toggle-group";
    right.className = "setting-control-group";

    for (const child of [...body.children]) {
      const checkbox = child.matches("label") && child.querySelector('input[type="checkbox"]');
      const select = child.matches("label") && child.querySelector("select");
      if (checkbox) child.classList.add("setting-toggle");
      if (select) child.classList.add("config-control");
      (checkbox ? left : right).appendChild(child);
    }

    body.replaceChildren(left, right);
    body.dataset.demogameNormalized = "true";
  }

  normalizeSettings();

  function fallbackSimulationMarkup() {
    return `
      <span class="zone-label">Simulation</span>
      <div id="batchSimulationNote" class="batch-simulation-note">Independent math simulation · Current Bet</div>
      <div class="batch-simulation-controls">
        <input id="batchSimulationRounds" type="number" min="1" max="1000000" step="1" value="10000" inputmode="numeric" aria-label="Simulation rounds">
        <button id="batchSimulationStartBtn" type="button">Start</button>
      </div>
      <div class="simulation-row"><span class="s-label">Total Rounds</span><span class="s-value" id="batchSimulationRoundCount">0</span></div>
      <div class="simulation-row"><span class="s-label">RTP</span><span class="s-value" id="batchSimulationRtp">0.00%</span></div>
      <div class="simulation-row"><span class="s-label">Hit Rate</span><span class="s-value" id="batchSimulationHitRate">0.00%</span></div>
      <div class="simulation-row"><span class="s-label">FG Trigger</span><span class="s-value hi" id="batchSimulationFgTrigger">0.00% (-- rounds)</span></div>
      <div class="simulation-row"><span class="s-label">Max Multiplier</span><span class="s-value hi" id="batchSimulationMaxMultiplier">x0</span></div>
      <div class="simulation-row"><span class="s-label">Retry Limit Exceeded</span><span class="s-value" id="batchSimulationRetryLimitExceeded">0 (0.00%)</span></div>
      <table class="batch-cascade-table" aria-label="Cascade distribution">
        <thead><tr><th>Scene</th><th>0</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5+</th></tr></thead>
        <tbody>
          <tr><th>BG</th><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td></tr>
          <tr><th>FG</th><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td></tr>
        </tbody>
      </table>`;
  }

  function ensureSimulationPanel() {
    if (document.getElementById("batch-simulation")) return;
    const settings = document.getElementById("settings-wrap");
    if (!settings) return;
    const panel = document.createElement("section");
    panel.id = "batch-simulation";
    panel.className = "control-zone debug-only debug-hidden demogame-fallback-simulation";
    panel.innerHTML = fallbackSimulationMarkup();
    settings.before(panel);

    const debugInput = document.querySelector('#debugModeInput, #debugInput');
    const syncVisibility = () => panel.classList.toggle("debug-hidden", !debugInput?.checked);
    debugInput?.addEventListener("change", syncVisibility);
    syncVisibility();
  }

  ensureSimulationPanel();

  function updateSharedSimulationContext() {
    const note = document.getElementById("batchSimulationNote");
    if (!note) return;
    const config = document.getElementById("demogameConfigSelect")?.selectedOptions?.[0]?.textContent?.trim()
      || document.getElementById("configSelect")?.selectedOptions?.[0]?.textContent?.trim()
      || "Current";
    const version = document.getElementById("versionSelect")?.value || "Current";
    const bet = document.getElementById("betValue")?.textContent?.trim() || "--";
    const cardSystem = document.getElementById("cardSystemInput")?.checked ? "On" : "Off";
    if (document.querySelector(".demogame-fallback-simulation")) {
      note.textContent = `Config ${config} · Version ${version} · Card System ${cardSystem} · Actual Demo Game logic · Bet ${bet}`;
    }
  }

  function writeFallbackStats(stats) {
    const write = (id, value) => { const node = document.getElementById(id); if (node && value != null) node.textContent = value; };
    const rounds = stats.rounds || 0;
    const pct = (value) => `${(value * 100).toFixed(2)}%`;
    write("batchSimulationRoundCount", rounds.toLocaleString("en-US"));
    write("batchSimulationRtp", pct(rounds ? stats.totalMultiplier / rounds : 0));
    write("batchSimulationHitRate", pct(rounds ? stats.hits / rounds : 0));
    write("batchSimulationFgTrigger", `${pct(rounds ? stats.fgTriggers / rounds : 0)} (${stats.fgTriggers ? `1 / ${Math.round(rounds / stats.fgTriggers).toLocaleString("en-US")}` : "-- rounds"})`);
    write("batchSimulationMaxMultiplier", `x${Number(stats.maxMultiplier.toFixed(2))}`);
    const retries = stats.retryLimitExceeded || 0;
    write("batchSimulationRetryLimitExceeded", `${retries.toLocaleString("en-US")} (${pct(rounds ? retries / rounds : 0)})`);
    const renderCascades = (rowIndex, counts) => {
      const cells = document.querySelectorAll(`.demogame-fallback-simulation .batch-cascade-table tbody tr:nth-child(${rowIndex}) td`);
      const total = (counts || []).reduce((sum, value) => sum + Number(value || 0), 0);
      cells.forEach((cell, index) => { cell.textContent = pct(total ? Number(counts[index] || 0) / total : 0); });
    };
    renderCascades(1, stats.bgCascades);
    renderCascades(2, stats.fgCascades);
  }

  function setupFallbackSimulation() {
    const panel = document.querySelector(".demogame-fallback-simulation");
    const start = panel?.querySelector("#batchSimulationStartBtn");
    const roundsInput = panel?.querySelector("#batchSimulationRounds");
    if (!panel || !start || !roundsInput) return;

    start.addEventListener("click", async () => {
      const requested = Math.min(1000000, Math.max(1, Math.trunc(Number(roundsInput.value) || 0)));
      roundsInput.value = String(requested);
      start.disabled = true;
      roundsInput.disabled = true;
      const original = start.textContent;
      const simulateRound = typeof window.demogameSimulateRound === "function"
        ? window.demogameSimulateRound
        : null;
      if (!simulateRound) {
        const note = document.getElementById("batchSimulationNote");
        if (note) note.textContent = "Simulation adapter unavailable: this page cannot run the actual Demo Game logic yet.";
        start.textContent = original;
        start.disabled = false;
        roundsInput.disabled = false;
        return;
      }
      const stats = {
        rounds: 0,
        totalMultiplier: 0,
        hits: 0,
        fgTriggers: 0,
        maxMultiplier: 0,
        retryLimitExceeded: 0,
        bgCascades: Array(6).fill(0),
        fgCascades: Array(6).fill(0)
      };
      try {
        while (stats.rounds < requested) {
          const sliceStarted = performance.now();
          let sliceRounds = 0;
          while (stats.rounds < requested && sliceRounds < 2000 && performance.now() - sliceStarted < 40) {
            const pending = simulateRound();
            const result = pending && typeof pending.then === "function" ? await pending : (pending || {});
            const multiplier = Math.max(0, Number(result.multiplier) || 0);
            if (result.fgTriggered) stats.fgTriggers += 1;
            stats.retryLimitExceeded += Number(result.retryLimitExceeded) || 0;
            if (Number.isFinite(Number(result.bgCascade))) {
              stats.bgCascades[Math.min(5, Math.max(0, Math.trunc(Number(result.bgCascade))))] += 1;
            }
            for (const cascade of result.fgCascades || []) {
              stats.fgCascades[Math.min(5, Math.max(0, Math.trunc(Number(cascade))))] += 1;
            }
            stats.rounds += 1;
            sliceRounds += 1;
            stats.totalMultiplier += multiplier;
            if (multiplier > 0) stats.hits += 1;
            stats.maxMultiplier = Math.max(stats.maxMultiplier, Number(result.maxMultiplier) || multiplier);
          }
          writeFallbackStats(stats);
          start.textContent = `${stats.rounds.toLocaleString("en-US")} / ${requested.toLocaleString("en-US")}`;
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
      } finally {
        start.textContent = original;
        start.disabled = false;
        roundsInput.disabled = false;
      }
    });
    updateSharedSimulationContext();
  }

  setupFallbackSimulation();

  function placeSimulationAfterChangeLog() {
    const simulation = document.getElementById("batch-simulation");
    const changeLog = document.getElementById("change-log-wrap");
    const settings = document.getElementById("settings-wrap");
    if (!simulation) return;
    if (changeLog) {
      changeLog.insertAdjacentElement("afterend", simulation);
      simulation.dataset.demogamePlacement = "after-change-log";
    } else if (settings) {
      settings.insertAdjacentElement("beforebegin", simulation);
      simulation.dataset.demogamePlacement = "before-settings";
    }
  }

  placeSimulationAfterChangeLog();

  const root = document.getElementById("helpContent");
  if (!root) return;

  const style = document.createElement("style");
  style.textContent = `
    @keyframes slot-symbol-clear {
      0% { opacity: 1; transform: scale(1); filter: brightness(1.35); }
      55% { opacity: .35; transform: scale(.72); filter: brightness(1.8); }
      100% { opacity: 0; transform: scale(.18); filter: brightness(2); }
    }
    @keyframes slot-symbol-drop {
      0% { transform: translateY(var(--drop-start, -105%)); }
      100% { transform: translateY(0); }
    }
    @keyframes slot-symbol-refill {
      0% { opacity: 0; transform: scale(.2); filter: brightness(1.8); }
      72% { opacity: 1; transform: scale(1.08); filter: brightness(1.2); }
      100% { opacity: 1; transform: scale(1); filter: brightness(1); }
    }
    @keyframes slot-symbol-settle {
      0% { transform: translateY(var(--drop-start, -105%)); }
      100% { transform: translateY(0); }
    }
    .cell.symbol-cleared {
      pointer-events: none;
    }
    .cell.symbol-cleared > .symbol-wrap,
    .cell.symbol-cleared > .icon,
    .cell.symbol-cleared > .code,
    .cell.symbol-cleared > .symbol-code,
    .cell.symbol-cleared > .multi-badge,
    .cell.symbol-cleared > .m1-multiplier {
      animation: slot-symbol-clear 180ms ease-in forwards;
    }
    .cell.symbol-drop {
      z-index: 4;
      opacity: 1;
      filter: none;
      overflow: visible;
      will-change: transform;
      animation: slot-symbol-drop var(--drop-duration, 280ms) linear var(--drop-delay, 0ms) both;
    }
    .cell.symbol-settle {
      z-index: 3;
      opacity: 1;
      filter: none;
      overflow: visible;
      will-change: transform;
      animation: slot-symbol-settle var(--drop-duration, 280ms) linear var(--drop-delay, 0ms) both;
    }
    .cell.symbol-refill > .symbol-wrap,
    .cell.symbol-refill > .icon,
    .cell.symbol-refill > .code,
    .cell.symbol-refill > .symbol-code,
    .cell.symbol-refill > .multi-badge,
    .cell.symbol-refill > .m1-multiplier {
      animation: slot-symbol-refill var(--refill-duration, 420ms) cubic-bezier(.2, .75, .25, 1) both;
    }
    @media (prefers-reduced-motion: reduce) {
      .cell.symbol-cleared > * {
        animation-duration: 1ms !important;
      }
    }
    #grid-panel {
      transition: background-color 220ms ease, box-shadow 220ms ease;
    }
    #board {
      overflow: hidden;
    }
    body.fg-mode #grid-panel {
      background: #174a70;
      box-shadow: inset 0 0 0 1px rgba(119, 199, 255, 0.38);
    }
    #helpDialog {
      box-sizing: border-box;
      width: min(960px, calc(100vw - 32px));
      height: min(780px, calc(100vh - 32px));
      max-width: 960px;
      max-height: calc(100vh - 32px);
      padding: 0;
      border: 1px solid #1d4668;
      border-radius: 10px;
      background: #06111f;
      color: #dceeff;
      overflow: hidden;
    }
    #helpDialog::backdrop {
      background: rgba(0, 7, 16, 0.78);
    }
    #helpDialog .help-dialog-shell {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      width: 100%;
      height: 100%;
      background: #06111f;
    }
    #helpDialog .help-dialog-header,
    #helpDialog .help-head {
      box-sizing: border-box;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 52px;
      padding: 10px 14px;
      border-bottom: 1px solid #1d4668;
      background: #091c33;
    }
    #helpDialog .help-dialog-header h2,
    #helpDialog .help-head h2 {
      margin: 0;
      color: #ffffff;
      font: 700 17px/1.35 "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
      text-transform: none;
    }
    #helpDialog #closeHelpBtn {
      box-sizing: border-box;
      height: 30px;
      padding: 0 12px;
      border: 1px solid #1d4668;
      border-radius: 6px;
      background: #102b49;
      color: #dceeff;
      font: 700 11px/1 "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
      text-transform: none;
      cursor: pointer;
    }
    #helpContent {
      box-sizing: border-box;
      width: 100%;
      height: 100%;
      min-height: 0;
      padding: 16px;
      overflow-y: auto;
      background: #06111f;
      color: #dceeff;
      font: 13px/1.55 "Segoe UI", Arial, sans-serif;
    }
    #helpContent * {
      box-sizing: border-box;
    }
    #helpContent .help-section,
    #helpContent .help-card,
    #helpContent .help-standard-card {
      display: block;
      box-sizing: border-box;
      margin: 0 0 14px;
      padding: 14px;
      border: 1px solid #1d4668;
      border-radius: 8px;
      background: #071a2d;
      overflow: visible;
    }
    #helpContent .help-section-title,
    #helpContent .help-group-title,
    #helpContent .help-card > h3 {
      display: block;
      margin: 0 0 10px;
      padding: 0;
      border: 0;
      background: transparent;
      color: #00ddc0;
      font: 600 16px/1.35 "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
      text-align: left;
      text-transform: none;
    }
    #helpContent .help-group-title {
      margin: 14px 0 10px;
      color: #00ddc0;
      font-size: 14px;
    }
    #helpContent .help-section-title .help-en,
    #helpContent .help-group-title .help-en {
      color: inherit;
      font: inherit;
      text-align: inherit;
    }
    #helpContent .help-rule {
      display: block;
      box-sizing: border-box;
      margin: 6px 0;
      padding: 10px;
      border: 0;
      border-radius: 6px;
      background: rgba(31, 91, 151, 0.28);
      color: #dceeff;
      font: 13px/1.55 "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
      text-align: left;
      text-transform: none;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    #helpContent .help-rule > *,
    #helpContent .help-rule-zh,
    #helpContent .help-rule-en {
      margin: 0;
      color: inherit;
      font: inherit;
      letter-spacing: inherit;
      text-align: inherit;
      text-transform: inherit;
    }
    #helpContent .help-lang-label {
      display: none;
    }
    #helpContent .help-paytable-wrap,
    #helpContent .help-payout-table {
      box-sizing: border-box;
      width: 100%;
      margin: 10px 0 0;
      padding: 10px;
      border-radius: 6px;
      background: rgba(31, 91, 151, 0.28);
      overflow-x: auto;
    }
    #helpContent .help-paytable,
    #helpContent table.paytable {
      width: 100%;
      min-width: 560px;
      border-collapse: collapse;
      border-spacing: 0;
      background: transparent;
      color: #dceeff;
      font: 12px/1.45 Consolas, "Segoe UI", monospace;
    }
    #helpContent .help-paytable th,
    #helpContent .help-paytable td,
    #helpContent table.paytable th,
    #helpContent table.paytable td {
      padding: 7px 6px;
      border: 0;
      border-bottom: 1px solid #1d4668;
      background: transparent;
      color: #dceeff;
      font: inherit;
      text-align: right;
      white-space: nowrap;
    }
    #helpContent .help-paytable th:first-child,
    #helpContent .help-paytable td:first-child,
    #helpContent table.paytable th:first-child,
    #helpContent table.paytable td:first-child {
      text-align: left;
    }
    #helpContent .help-paytable th,
    #helpContent table.paytable th {
      color: #77c7ff;
      font-weight: 800;
    }
    #helpContent .help-paytable td:first-child,
    #helpContent table.paytable td:first-child {
      color: #00ddc0;
    }
    #helpContent .help-payout-table {
      display: table;
      min-width: 560px;
      border-collapse: collapse;
    }
    #helpContent .help-payout-row {
      display: table-row;
    }
    #helpContent .help-payout-cell {
      display: table-cell;
      padding: 7px 6px;
      border: 0;
      border-bottom: 1px solid #1d4668;
      border-radius: 0;
      background: transparent;
      text-align: right;
      white-space: nowrap;
    }
    #helpContent .help-payout-row:first-child .help-payout-cell {
      color: #77c7ff;
      font-weight: 800;
    }
    #helpContent .help-payout-cell:first-child {
      color: #00ddc0;
      text-align: left;
    }
    #helpContent .help-loading,
    #helpContent .help-load-error {
      display: grid;
      min-height: 180px;
      padding: 20px;
      place-items: center;
      color: #89a9c4;
      font: 12px/1.55 "Segoe UI", Arial, sans-serif;
      text-align: center;
    }
    @media (max-width: 640px) {
      #helpDialog {
        width: calc(100vw - 16px);
        height: calc(100vh - 16px);
        max-height: calc(100vh - 16px);
      }
      #helpContent {
        padding: 10px;
      }
      #helpContent .help-section,
      #helpContent .help-card,
      #helpContent .help-standard-card {
        padding: 12px;
      }
    }
  `;
  document.head.appendChild(style);

  window.slotBuildDropMotion = (rowCountOrList, columnCount, clearedPositions = []) => {
    const rowCounts = Array.isArray(rowCountOrList)
      ? rowCountOrList
      : Array(columnCount).fill(Number(rowCountOrList) || 0);
    const cleared = new Set(clearedPositions.map(([row, col]) => `${row}-${col}`));
    const motion = {};
    for (let col = 0; col < columnCount; col += 1) {
      const rowCount = rowCounts[col] || 0;
      const survivors = [];
      for (let row = 0; row < rowCount; row += 1) {
        if (!cleared.has(`${row}-${col}`)) survivors.push(row);
      }
      const firstSurvivorRow = rowCount - survivors.length;
      for (let row = 0; row < firstSurvivorRow; row += 1) {
        motion[`${row}-${col}`] = {
          type: "new",
          rows: firstSurvivorRow,
          groupSize: firstSurvivorRow
        };
      }
      survivors.forEach((oldRow, index) => {
        const newRow = firstSurvivorRow + index;
        if (newRow > oldRow) motion[`${newRow}-${col}`] = { type: "settle", rows: newRow - oldRow };
      });
    }
    return motion;
  };

  const acronyms = new Map([
    ["bg", "BG"], ["fg", "FG"], ["op", "OP"], ["rng", "RNG"],
    ["rtp", "RTP"], ["ww", "WW"], ["c1", "C1"], ["c2", "C2"]
  ]);

  function titleCase(value) {
    const text = String(value || "").trim();
    if (!text || /[\u3400-\u9fff]/.test(text)) return text;
    return text.toLowerCase().replace(/[a-z0-9]+/g, (word) => {
      if (acronyms.has(word)) return acronyms.get(word);
      return word.charAt(0).toUpperCase() + word.slice(1);
    });
  }

  function currentBet() {
    const text = document.getElementById("betValue")?.textContent?.trim();
    const value = Number(String(text || "1").replace(/,/g, ""));
    return Number.isFinite(value)
      ? value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "1.00";
  }

  function isPaytableTitle(value) {
    return /pay\s*table|paytable|賠率表|赔率表/i.test(String(value || ""));
  }

  function parseFlatPayout(text) {
    const clean = String(text || "").replace(/[\[\]{}]/g, "").trim();
    const match = clean.match(/^([A-Za-z]+\d*)\s+(.+?)\s*[-–]\s*([\d,.]+(?:\s*[xX])?)$/);
    if (!match) return null;
    return { symbol: match[1], count: match[2].trim(), value: match[3].replace(/\s+/g, "") };
  }

  function countOrder(value) {
    const match = String(value).match(/\d+/);
    return match ? Number(match[0]) : Number.MAX_SAFE_INTEGER;
  }

  function buildPivotTable(items) {
    const entries = items.map((item) => parseFlatPayout(item.textContent)).filter(Boolean);
    if (entries.length < 2) return null;

    const counts = [...new Set(entries.map((entry) => entry.count))].sort((a, b) => countOrder(a) - countOrder(b));
    const symbols = [...new Set(entries.map((entry) => entry.symbol))];
    const values = new Map(entries.map((entry) => [`${entry.symbol}\u0000${entry.count}`, entry.value]));
    const table = document.createElement("table");
    table.className = "help-paytable";
    table.innerHTML = `<thead><tr><th>Symbol</th>${counts.map((count) => `<th>${count}</th>`).join("")}</tr></thead>`;
    const body = document.createElement("tbody");
    for (const symbol of symbols) {
      const row = document.createElement("tr");
      row.innerHTML = `<td>${symbol}</td>${counts.map((count) => `<td>${values.get(`${symbol}\u0000${count}`) || "—"}</td>`).join("")}`;
      body.appendChild(row);
    }
    table.appendChild(body);
    return table;
  }

  function buildMatrixTable(items) {
    const rows = items.map((item) => item.textContent.split(/\s+·\s+/).map((cell) => cell.replace(/[\[\]{}]/g, "").trim()));
    if (rows.length < 2 || rows.some((row) => row.length < 3)) return null;
    const width = rows[0].length;
    if (rows.some((row) => row.length !== width)) return null;
    const bet = Number(currentBet().replace(/,/g, ""));

    const table = document.createElement("table");
    table.className = "help-paytable";
    table.innerHTML = `<thead><tr><th>Symbol</th>${Array.from({ length: width - 1 }, (_, index) => `<th>${index + 3}</th>`).join("")}</tr></thead>`;
    const body = document.createElement("tbody");
    for (const cells of rows) {
      const row = document.createElement("tr");
      row.innerHTML = cells.map((cell, index) => {
        const value = index > 0 && Number.isFinite(Number(cell)) ? Number(cell) * bet : cell;
        return `<td>${typeof value === "number" ? Number(value.toFixed(6)) : value}</td>`;
      }).join("");
      body.appendChild(row);
    }
    table.appendChild(body);
    return table;
  }

  function replacePayoutGrids(card) {
    for (const grid of card.querySelectorAll(".help-payout-grid")) {
      const items = [...grid.querySelectorAll(".help-payout-item")];
      const table = buildPivotTable(items) || buildMatrixTable(items);
      if (!table) continue;
      const wrap = document.createElement("div");
      wrap.className = "help-paytable-wrap";
      wrap.appendChild(table);
      grid.replaceWith(wrap);
    }
  }

  function replacePayoutDivTables(card) {
    for (const source of card.querySelectorAll(".help-payout-table")) {
      const rows = [...source.querySelectorAll(":scope > .help-payout-row")]
        .map((row) => [...row.querySelectorAll(":scope > .help-payout-cell")].map((cell) => cell.textContent.trim()))
        .filter((row) => row.length);
      if (rows.length < 2) continue;

      const table = document.createElement("table");
      table.className = "help-paytable";
      const head = document.createElement("thead");
      const headRow = document.createElement("tr");
      for (const value of rows[0]) {
        const cell = document.createElement("th");
        cell.textContent = value;
        headRow.appendChild(cell);
      }
      head.appendChild(headRow);
      table.appendChild(head);

      const body = document.createElement("tbody");
      for (const values of rows.slice(1)) {
        const row = document.createElement("tr");
        for (const value of values) {
          const cell = document.createElement("td");
          cell.textContent = value;
          row.appendChild(cell);
        }
        body.appendChild(row);
      }
      table.appendChild(body);

      const wrap = document.createElement("div");
      wrap.className = "help-paytable-wrap";
      wrap.appendChild(table);
      source.replaceWith(wrap);
    }
  }

  function normalizeCardStructure(card) {
    card.classList.add("help-standard-card");
    const title = card.querySelector(":scope > .help-section-title, :scope > h3");
    if (title) title.classList.add("help-section-title");
    for (const paragraph of card.querySelectorAll(":scope > p")) {
      paragraph.classList.add("help-rule");
    }
    for (const list of card.querySelectorAll(":scope > ul, :scope > ol")) {
      list.classList.add("help-rule");
    }
  }

  function wrapBarePaytables(card) {
    for (const table of card.querySelectorAll("table.paytable")) {
      if (table.closest(".help-paytable-wrap")) continue;
      const wrap = document.createElement("div");
      wrap.className = "help-paytable-wrap";
      table.before(wrap);
      wrap.appendChild(table);
    }
  }

  function normalizeLooseRuleGrids(card) {
    const titleTexts = [...card.querySelectorAll(".help-section-title, .help-group-title, :scope > h3")]
      .map((heading) => titleCase(heading.textContent));
    for (const grid of card.querySelectorAll(".help-payout-grid")) {
      const items = [...grid.querySelectorAll(".help-payout-item")];
      if (!items.length) continue;
      const fragment = document.createDocumentFragment();
      for (const item of items) {
        const text = item.textContent.trim();
        const normalized = titleCase(text);
        const duplicateTitle = titleTexts.includes(normalized)
          || /^(symbol payout values?|符號賠付值|符号赔付值)$/i.test(text);
        if (duplicateTitle || !text) continue;
        const rule = document.createElement("div");
        rule.className = "help-rule";
        rule.textContent = text;
        fragment.appendChild(rule);
      }
      grid.replaceWith(fragment);
    }
  }

  function readHtmlPaytable(table) {
    const headers = [...table.querySelectorAll("thead th")].map((cell) => cell.textContent.trim());
    const rows = [...table.querySelectorAll("tbody tr")].map((row) => [...row.children].map((cell) => cell.textContent.trim()));
    return headers.length > 1 && rows.length ? { headers, rows } : null;
  }

  function mergePaytables(card) {
    const wraps = [...card.querySelectorAll(".help-paytable-wrap")];
    const sources = wraps
      .map((wrap) => ({ wrap, data: readHtmlPaytable(wrap.querySelector("table.help-paytable, table.paytable")) }))
      .filter((source) => source.data);
    if (sources.length < 2) return;

    const columns = [...new Set(sources.flatMap((source) => source.data.headers.slice(1)))].sort((a, b) => countOrder(a) - countOrder(b));
    const symbolRows = new Map();
    for (const source of sources) {
      for (const row of source.data.rows) {
        const symbol = row[0];
        if (!symbolRows.has(symbol)) symbolRows.set(symbol, new Map());
        source.data.headers.slice(1).forEach((header, index) => symbolRows.get(symbol).set(header, row[index + 1]));
      }
    }

    const table = document.createElement("table");
    table.className = "help-paytable";
    table.innerHTML = `<thead><tr><th>Symbol</th>${columns.map((column) => `<th>${column}</th>`).join("")}</tr></thead>`;
    const body = document.createElement("tbody");
    for (const [symbol, values] of symbolRows) {
      const row = document.createElement("tr");
      row.innerHTML = `<td>${symbol}</td>${columns.map((column) => `<td>${values.get(column) || "—"}</td>`).join("")}`;
      body.appendChild(row);
    }
    table.appendChild(body);

    for (const source of sources) source.wrap.remove();
    const mergedWrap = document.createElement("div");
    mergedWrap.className = "help-paytable-wrap";
    mergedWrap.appendChild(table);
    card.appendChild(mergedWrap);
  }

  function buildConfigFallback() {
    if (!root.querySelector(".help-load-error") || !window.data?.pay_table) return;
    const box = window.data;
    const scale = Number(box.default_coin_in || 100);
    const entries = box.pay_table
      .map((pays, index) => ({ symbol: box.symbol_str?.[String(index)] || box.symbol_str?.[index] || `S${index}`, pays }));
    const normalRows = entries.filter((entry) => !["WW", "C1", "C2"].includes(entry.symbol) && entry.pays?.slice(-3).some(Number));
    const scatterRow = entries.find((entry) => entry.symbol === "C1" && entry.pays?.slice(0, 3).some(Number));
    if (!normalRows.length) return;

    const card = document.createElement("section");
    card.className = "help-section";
    card.innerHTML = `<h3 class="help-section-title">Paytable (Current Bet: ${currentBet()})</h3>`;
    const wrap = document.createElement("div");
    wrap.className = "help-paytable-wrap";
    const table = document.createElement("table");
    table.className = "help-paytable";
    const hasScatterPay = Boolean(scatterRow);
    table.innerHTML = `<thead><tr><th>Symbol</th>${hasScatterPay ? "<th>4</th><th>5</th><th>6</th>" : ""}<th>8–9</th><th>10–11</th><th>12+</th></tr></thead>`;
    const body = document.createElement("tbody");
    for (const entry of normalRows) {
      const row = document.createElement("tr");
      const values = entry.pays.slice(-3).map((value) => Number(value) / scale * Number(currentBet().replace(/,/g, "")));
      row.innerHTML = `<td>${entry.symbol}</td>${hasScatterPay ? "<td>—</td><td>—</td><td>—</td>" : ""}${values.map((value) => `<td>${Number(value.toFixed(6))}</td>`).join("")}`;
      body.appendChild(row);
    }
    if (scatterRow) {
      const row = document.createElement("tr");
      const values = scatterRow.pays.slice(0, 3).map((value) => Number(value) / scale * Number(currentBet().replace(/,/g, "")));
      row.innerHTML = `<td>C1</td>${values.map((value) => `<td>${Number(value.toFixed(6))}</td>`).join("")}<td>—</td><td>—</td><td>—</td>`;
      body.appendChild(row);
    }
    table.appendChild(body);
    wrap.appendChild(table);
    card.appendChild(wrap);
    root.replaceChildren(card);
  }

  let applying = false;
  function standardize() {
    if (applying) return;
    applying = true;
    try {
      buildConfigFallback();
      const cards = root.querySelectorAll(".help-section, .help-card");
      for (const card of cards) {
        normalizeCardStructure(card);
        const sectionTitle = card.querySelector(":scope > .help-section-title, :scope > h3");
        if (!sectionTitle) continue;
        const groupTitles = [...card.querySelectorAll(".help-group-title")];
        const paytable = isPaytableTitle(sectionTitle.textContent)
          || groupTitles.some((heading) => isPaytableTitle(heading.textContent) || /symbol payouts?/i.test(heading.textContent))
          || Boolean(card.querySelector("table.paytable"));
        if (paytable) {
          const expected = `Paytable (Current Bet: ${currentBet()})`;
          if (sectionTitle.textContent !== expected) sectionTitle.textContent = expected;
          for (const note of card.querySelectorAll(":scope > .help-rule")) {
            if (/current.*bet|目前.*(?:押注|投注)/i.test(note.textContent)) note.remove();
          }
          for (const heading of card.querySelectorAll(".help-group-title")) {
            if (isPaytableTitle(heading.textContent) || /symbol payout/i.test(heading.textContent)) heading.remove();
          }
          replacePayoutGrids(card);
          replacePayoutDivTables(card);
          wrapBarePaytables(card);
          mergePaytables(card);
          const table = card.querySelector("table.paytable");
          if (table) {
            const firstHeader = table.querySelector("th");
            if (firstHeader && firstHeader.textContent !== "Symbol") firstHeader.textContent = "Symbol";
          }
          const firstGridCell = card.querySelector(".help-payout-row:first-child .help-payout-cell:first-child");
          if (firstGridCell && firstGridCell.textContent !== "Symbol") firstGridCell.textContent = "Symbol";
        }
        normalizeLooseRuleGrids(card);
      }

      for (const heading of root.querySelectorAll(".help-section-title, .help-group-title, .help-card > h3")) {
        if (isPaytableTitle(heading.textContent)) continue;
        if (heading.children.length) {
          for (const child of heading.querySelectorAll(".help-en")) child.textContent = titleCase(child.textContent);
        } else {
          const normalized = titleCase(heading.textContent);
          if (normalized !== heading.textContent) heading.textContent = normalized;
        }
      }
    } finally {
      applying = false;
    }
  }

  new MutationObserver(() => standardize()).observe(root, { childList: true, subtree: true, characterData: true });
  const betValue = document.getElementById("betValue");
  if (betValue) new MutationObserver(() => standardize()).observe(betValue, { childList: true, subtree: true, characterData: true });
  document.getElementById("helpBtn")?.addEventListener("click", () => setTimeout(standardize));
  standardize();
})();

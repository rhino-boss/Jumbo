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
    // 完整模型代號（如 H016192A）優先：取出其中的 RTP＋Variant
    const modelMatch = source.match(/H\d{3}1([89][0-9][A-Za-z]?(?:_bet\d+)?)(?![0-9A-Za-z])/i);
    if (modelMatch) return modelMatch[1].toUpperCase();
    // RTP 家族＋Variant，保留 _Bet100 這類後綴，避免 92A 與 92A_Bet100 顯示成同一個
    const compact = source.match(/(?:^|[^0-9])([89][0-9][A-Za-z]?(?:_bet\d+)?)(?=[^0-9A-Za-z_]|$)/i);
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

  function parseFourPartVersion(value) {
    const match = String(value || "").trim().match(/^(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?$/);
    if (!match) return null;
    return [Number(match[1]), Number(match[2]), Number(match[3] || 0), Number(match[4] || 0)];
  }

  function compareVersionParts(left, right) {
    for (let index = 0; index < 4; index += 1) {
      if (left[index] !== right[index]) return left[index] - right[index];
    }
    return 0;
  }

  function filterVersionOptions() {
    const select = document.getElementById("versionSelect");
    if (!select) return;

    const versionOptions = [...select.options]
      .map((option) => ({ option, parts: parseFourPartVersion(option.value || option.textContent) }))
      .filter((entry) => entry.parts);
    const latestByModel = new Map();

    for (const entry of versionOptions) {
      entry.option.textContent = entry.parts.join(".");
      const modelKey = `${entry.parts[0]}.${entry.parts[1]}`;
      const current = latestByModel.get(modelKey);
      if (!current || compareVersionParts(entry.parts, current.parts) > 0) latestByModel.set(modelKey, entry);
    }

    for (const entry of versionOptions) {
      const modelKey = `${entry.parts[0]}.${entry.parts[1]}`;
      if (latestByModel.get(modelKey) !== entry) entry.option.remove();
    }
  }

  function hasUsableCardEntries(value) {
    if (Array.isArray(value)) {
      return value.some((entry) => entry && typeof entry === "object" && Number(entry.weight) > 0
        && (entry.type != null || entry.min != null || entry.max != null));
    }
    if (!value || typeof value !== "object") return false;
    return Object.values(value).some(hasUsableCardEntries);
  }

  function cardSystemSupported() {
    if (window.DEMOGAME_CARD_SYSTEM_SUPPORTED === false) return false;
    const cardSystem = getMathConfig()?.card_system;
    return cardSystem?.enabled === true && hasUsableCardEntries(cardSystem);
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
    const supportsCardSystem = cardSystemSupported();
    // Config 選單同時決定卡片系統開關：「92A」＝自然機率（卡片關），「92A-Oldhand」「92A-Newbie」＝卡片開＋該 Profile
    const offOption = { value: "off", name: "Off" };
    const profileOptions = !supportsCardSystem
      ? [offOption]
      : [offOption, ...(profileSelect
        ? [...profileSelect.options].map((option) => ({ value: option.value, name: normalizeProfileName(option.value || option.textContent) }))
        : [
            { value: "oldhand", name: "Oldhand" },
            { value: "newbie", name: "Newbie" }
          ])];
    const cardOnAtStart = supportsCardSystem && document.getElementById("cardSystemInput")?.checked !== false;
    // 不再提供 Newbie：頁面原生 Profile 選單若停在 newbie（舊的記憶值），改回 oldhand
    if (profileSelect && [...profileSelect.options].some((option) => option.value === "oldhand") && profileSelect.value !== "oldhand") {
      profileSelect.value = "oldhand";
      profileSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
    try { localStorage.setItem("slotDemoCardProfile", "oldhand"); } catch (_) {}

    configSelect?.closest("label")?.classList.add("demogame-source-control");
    profileSelect?.closest("label")?.classList.add("demogame-source-control");

    const combinedLabel = document.createElement("label");
    combinedLabel.className = "config-control demogame-combined-control";
    combinedLabel.append("Config ");
    const combined = document.createElement("select");
    combined.id = "demogameConfigSelect";
    // 自然機率與 RTP 家族（92／94）無關，只依基礎數學 Variant 分：
    // 只有一套 → 「Base」；有 A／B 兩套 → 「BaseA」「BaseB」。卡片開的選項仍是 <Config>-<Profile>。
    let savedProfile = "oldhand";
    try { savedProfile = localStorage.getItem("slotDemoCardProfile") === "newbie" ? "newbie" : "oldhand"; } catch (_) {}
    const selectedProfile = cardOnAtStart ? normalizeProfileName(profileSelect?.value || savedProfile) : "Off";
    const variantOf = (configOption) => (normalizeConfigName(configOption).match(/^\d+([A-Z])/) || ["", ""])[1];
    const variants = [...new Set(configOptions.map(variantOf))].sort();
    const currentConfig = configOptions.find((option) => option.selected) || configOptions[0];
    const addOption = (configOption, profile, text, selected) => {
      const option = document.createElement("option");
      option.value = JSON.stringify([configOption.value, profile.value]);
      option.textContent = text;
      option.selected = selected;
      combined.appendChild(option);
    };
    for (const variant of variants) {
      const sameVariant = configOptions.filter((option) => variantOf(option) === variant);
      const target = sameVariant.includes(currentConfig) ? currentConfig : sameVariant[0];
      const text = variants.length > 1 ? `Base${variant}` : "Base";
      addOption(target, offOption, text, selectedProfile === "Off" && target === currentConfig);
    }
    // 卡片開只用 Oldhand，不列 Newbie；選項只寫 Config 代號（例：92A、94A、92A_BET100）
    const oldhand = profileOptions.find((profile) => profile.name === "Oldhand") || profileOptions.find((profile) => profile.value !== "off");
    if (oldhand) {
      for (const configOption of configOptions) {
        addOption(configOption, oldhand, normalizeConfigName(configOption),
          configOption === currentConfig && selectedProfile !== "Off");
      }
    }
    combinedLabel.appendChild(combined);

    let versionSelect = document.getElementById("versionSelect");
    let versionLabel = versionSelect?.closest("label");
    if (versionSelect && versionLabel) {
      versionLabel.classList.add("config-control", "demogame-version-control");
    } else {
      versionLabel = document.createElement("label");
      versionLabel.className = "config-control demogame-version-control";
      versionLabel.append("Version ");
      versionSelect = document.createElement("select");
      versionSelect.id = "versionSelect";
      const mathConfig = getMathConfig();
      const version = window.DEMOGAME_VERSION_OVERRIDE
        || mathConfig?.excel_version
        || mathConfig?.game_version
        || mathConfig?.version
        || "Current";
      versionSelect.appendChild(new Option(String(version), String(version), true, true));
      versionLabel.appendChild(versionSelect);
    }

    const anchor = configSelect?.closest("label") || profileSelect?.closest("label") || body.firstChild;
    if (versionLabel !== anchor) body.insertBefore(versionLabel, anchor);
    versionLabel.insertAdjacentElement("afterend", combinedLabel);

    combined.addEventListener("change", () => {
      const [configValue, profileValue] = JSON.parse(combined.value);
      if (profileValue !== "off") {
        try { localStorage.setItem("slotDemoCardProfile", normalizeProfileName(profileValue).toLowerCase()); } catch (_) {}
      }
      if (profileValue !== "off" && profileSelect && profileSelect.value !== profileValue) {
        profileSelect.value = profileValue;
        profileSelect.dispatchEvent(new Event("change", { bubbles: true }));
      }
      // 卡片系統開關跟著 Config：選「92A」（Off）就關，選 Oldhand／Newbie 就開
      const cardToggle = document.getElementById("cardSystemInput");
      const cardOn = profileValue !== "off";
      if (cardToggle && !cardToggle.disabled && cardToggle.checked !== cardOn) {
        cardToggle.checked = cardOn;
        cardToggle.dispatchEvent(new Event("change", { bubbles: true }));
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

    const supported = cardSystemSupported();
    input.disabled = !supported;
    if (!supported) input.checked = false;
    label.classList.toggle("is-unavailable", !supported);
    // 勾選框不顯示：卡片系統開關改由 Config 選單決定（見 ensureCombinedConfigAndVersion）
    label.hidden = true;
    label.style.display = "none";
    label.title = "";

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

  function getImageToggleAdapter() {
    const adapter = window.DEMOGAME_IMAGE_TOGGLE;
    if (!adapter || adapter.supported === false || typeof adapter.setEnabled !== "function") return null;
    return adapter;
  }

  // ===== 符號圖片預載（Demogame規範：有圖片時，開局前必須預載並解碼完成）=====
  // 各遊戲在 window.DEMOGAME_IMAGE_TOGGLE.images 提供本遊戲會用到的所有圖片網址（陣列或回傳陣列的函式）。
  // 預載期間顯示進度遮罩並擋住點擊與鍵盤；Image 物件留在 window.__demogameImageCache，避免瀏覽器丟掉解碼結果。
  // 任一張載入失敗：關閉圖片模式改用文字顯示，並提示失敗張數（不會卡在載入畫面）。
  const imageLoadCache = new Map();
  window.__demogameImageCache = window.__demogameImageCache || [];

  function loadImageOnce(url) {
    if (imageLoadCache.has(url)) return imageLoadCache.get(url);
    const img = new Image();
    img.decoding = "async";
    const promise = new Promise((resolve) => {
      img.onload = () => {
        // decode() 在背景分頁（document.hidden）會一直等到分頁回到前景才完成：
        // 背景時略過解碼，前景時最多等 1.5 秒，避免載入遮罩卡住。
        if (typeof img.decode !== "function" || document.hidden) {
          resolve(true);
          return;
        }
        Promise.race([
          img.decode().catch(() => {}),
          new Promise((done) => setTimeout(done, 1500))
        ]).then(() => resolve(true));
      };
      img.onerror = () => resolve(false);
    });
    img.src = url;
    window.__demogameImageCache.push(img);
    imageLoadCache.set(url, promise);
    return promise;
  }

  let preloadOverlay = null;
  let preloadOverlayTimer = 0;
  let preloadActive = 0;

  function blockInputWhileLoading(event) {
    if (!preloadActive) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function setPreloadOverlay(done, total) {
    if (!preloadOverlay) return;
    const text = preloadOverlay.querySelector(".demogame-preload-text");
    const bar = preloadOverlay.querySelector(".demogame-preload-bar > span");
    if (text) text.textContent = `載入圖片 Loading images ${done} / ${total}`;
    if (bar) bar.style.width = `${total ? Math.round((done / total) * 100) : 100}%`;
  }

  function openPreloadOverlay(total) {
    if (preloadOverlay) return;
    preloadOverlay = document.createElement("div");
    preloadOverlay.className = "demogame-preload";
    preloadOverlay.setAttribute("role", "status");
    preloadOverlay.setAttribute("aria-live", "polite");
    preloadOverlay.style.cssText = "position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(8,10,16,.72);color:#fff;font:600 15px/1.4 system-ui,'Microsoft JhengHei',sans-serif;";
    preloadOverlay.innerHTML = '<div style="min-width:240px;text-align:center"><div class="demogame-preload-text"></div>'
      + '<div class="demogame-preload-bar" style="margin-top:10px;height:6px;border-radius:3px;background:rgba(255,255,255,.2);overflow:hidden">'
      + '<span style="display:block;height:100%;width:0;background:#f5c542;transition:width .15s"></span></div></div>';
    document.body.appendChild(preloadOverlay);
    setPreloadOverlay(0, total);
  }

  function closePreloadOverlay() {
    clearTimeout(preloadOverlayTimer);
    preloadOverlay?.remove();
    preloadOverlay = null;
  }

  function showPreloadNotice(message) {
    const notice = document.createElement("div");
    notice.className = "demogame-preload-notice";
    notice.style.cssText = "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:2147483000;padding:8px 14px;border-radius:6px;background:rgba(160,40,40,.92);color:#fff;font:600 13px/1.4 system-ui,'Microsoft JhengHei',sans-serif;";
    notice.textContent = message;
    document.body.appendChild(notice);
    setTimeout(() => notice.remove(), 4000);
  }

  function getAdapterImages(adapter) {
    const source = typeof adapter?.images === "function" ? adapter.images() : adapter?.images;
    return [...new Set((Array.isArray(source) ? source : []).filter(Boolean))];
  }

  async function preloadImages(urls) {
    const list = [...new Set((urls || []).filter(Boolean))];
    if (!list.length) return { failed: [] };
    let done = 0;
    const failed = [];
    // 圖片已在快取時通常 100ms 內完成：延遲顯示遮罩避免畫面閃一下，但從一開始就擋住輸入。
    preloadActive += 1;
    if (preloadActive === 1) {
      window.addEventListener("keydown", blockInputWhileLoading, true);
      window.addEventListener("pointerdown", blockInputWhileLoading, true);
      window.addEventListener("click", blockInputWhileLoading, true);
    }
    clearTimeout(preloadOverlayTimer);
    preloadOverlayTimer = setTimeout(() => {
      if (preloadActive) {
        openPreloadOverlay(list.length);
        setPreloadOverlay(done, list.length);
      }
    }, 120);
    await Promise.all(list.map((url) => loadImageOnce(url).then((ok) => {
      done += 1;
      if (!ok) failed.push(url);
      setPreloadOverlay(done, list.length);
    })));
    preloadActive -= 1;
    if (!preloadActive) {
      closePreloadOverlay();
      window.removeEventListener("keydown", blockInputWhileLoading, true);
      window.removeEventListener("pointerdown", blockInputWhileLoading, true);
      window.removeEventListener("click", blockInputWhileLoading, true);
    }
    return { failed };
  }

  window.DemogameImagePreload = { preload: preloadImages };

  async function preloadAdapterImages(adapter, onFailed) {
    const result = await preloadImages(getAdapterImages(adapter));
    if (result.failed.length) {
      console.warn("[demogame] 圖片載入失敗，改用文字顯示：", result.failed);
      showPreloadNotice(`有 ${result.failed.length} 張圖片載入失敗，已改用文字顯示`);
      onFailed?.();
    }
    return result;
  }

  function ensureImageToggle() {
    const adapter = getImageToggleAdapter();
    const settingsBody = document.querySelector("#settings-wrap > .setting-body");
    if (adapter && !settingsBody && adapter.defaultEnabled !== false) {
      preloadAdapterImages(adapter, () => adapter.setEnabled(false, { initial: false }));
      return;
    }
    if (!adapter || !settingsBody) return;

    let input = document.getElementById("symbolImageInput");
    let label = input?.closest("label");
    if (!input) {
      label = document.createElement("label");
      label.className = "setting-toggle";
      label.htmlFor = "symbolImageInput";
      label.innerHTML = '<input id="symbolImageInput" type="checkbox"><span>Image</span>';
      input = label.querySelector("input");
      const cardLabel = document.getElementById("cardSystemInput")?.closest("label");
      if (cardLabel?.parentElement === settingsBody) cardLabel.insertAdjacentElement("afterend", label);
      else settingsBody.insertBefore(label, settingsBody.querySelector(".config-control"));
    }

    let saved = null;
    try { saved = localStorage.getItem("slotDemoSymbolImages"); } catch (_) {}
    input.checked = saved == null ? adapter.defaultEnabled !== false : saved !== "off";

    const apply = (initial = false) => {
      adapter.setEnabled(input.checked, { initial });
      window.DEMOGAME_SYMBOL_IMAGES_ENABLED = input.checked;
      document.dispatchEvent(new CustomEvent("demogame:image-change", {
        detail: { enabled: input.checked, initial }
      }));
      if (input.checked) {
        preloadAdapterImages(adapter, () => {
          input.checked = false;
          apply(false);
        });
      }
    };

    input.addEventListener("change", () => {
      try { localStorage.setItem("slotDemoSymbolImages", input.checked ? "on" : "off"); } catch (_) {}
      apply(false);
    });
    apply(true);
  }

  ensureCardSystemToggle();
  ensureImageToggle();
  ensureCombinedConfigAndVersion();
  filterVersionOptions();
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
      ${cascadeListMarkup()}`;
  }

  // 消除分布：轉置成「Cascade 次數 × BG／FG」，與 Simulation 其他列相同的列樣式。
  function cascadeListMarkup() {
    const rows = ["0", "1", "2", "3", "4", "5+"].map((label, i) =>
      `<div class="simulation-row batch-cascade-row"><span class="s-label">${label}</span><span class="s-value" id="batchCascadeBg${i}">0.00%</span><span class="s-value" id="batchCascadeFg${i}">0.00%</span></div>`).join("");
    return `<div class="batch-cascade-list" aria-label="Cascade distribution">
        <div class="batch-cascade-title">Cascade Distribution</div>
        <div class="simulation-row batch-cascade-row batch-cascade-head"><span class="s-label">Cascades</span><span class="s-label">BG</span><span class="s-label">FG</span></div>
        ${rows}
      </div>`;
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
    const version = document.getElementById("versionSelect")?.selectedOptions?.[0]?.textContent?.trim() || "Current";
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
    const roundUnit = /^zh/i.test(document.getElementById("languageSelect")?.value || "") ? "場" : "rounds";
    write("batchSimulationFgTrigger", `${pct(rounds ? stats.fgTriggers / rounds : 0)} (${stats.fgTriggers ? Math.round(rounds / stats.fgTriggers).toLocaleString("en-US") : "--"} ${roundUnit})`);
    write("batchSimulationMaxMultiplier", `x${Number(stats.maxMultiplier.toFixed(2))}`);
    const retries = stats.retryLimitExceeded || 0;
    write("batchSimulationRetryLimitExceeded", `${retries.toLocaleString("en-US")} (${pct(rounds ? retries / rounds : 0)})`);
    const renderCascades = (prefix, counts) => {
      const total = (counts || []).reduce((sum, value) => sum + Number(value || 0), 0);
      for (let i = 0; i < 6; i++) write(`${prefix}${i}`, pct(total ? Number(counts[i] || 0) / total : 0));
    };
    renderCascades("batchCascadeBg", stats.bgCascades);
    renderCascades("batchCascadeFg", stats.fgCascades);
    // 沒有消除機制的遊戲（adapter 不回傳 bgCascade／fgCascades）不顯示消除分布
    const cascadeTotal = [...(stats.bgCascades || []), ...(stats.fgCascades || [])].reduce((a, b) => a + Number(b || 0), 0);
    document.querySelector(".demogame-fallback-simulation .batch-cascade-list")?.classList.toggle("demogame-removed", rounds > 0 && cascadeTotal === 0);
  }

  // 押注模式選單：遊戲宣告 window.demogameSimulationModes = [{ value, label }] 時才顯示，
  // 選定值以 demogameSimulateRound({ mode }) 傳給遊戲；未宣告則沿用目前押注模式。
  // 倍率線型：模擬時每局 multiplier（總得分 ÷ 押注，含 FG）計入面板內的線型圖。
  function ensureSimulationExtras(panel) {
    const controls = panel.querySelector(".batch-simulation-controls");
    let modeSelect = panel.querySelector("#batchSimulationMode");
    if (!modeSelect && controls) {
      modeSelect = document.createElement("select");
      modeSelect.id = "batchSimulationMode";
      modeSelect.setAttribute("aria-label", "Simulation bet mode");
      controls.prepend(modeSelect);
    }
    const modes = Array.isArray(window.demogameSimulationModes) ? window.demogameSimulationModes : [];
    if (modeSelect) {
      modeSelect.innerHTML = modes.map((m) => `<option value="${m.value}">${m.label}</option>`).join("");
      modeSelect.hidden = !modes.length;
      controls?.classList.toggle("has-mode", modes.length > 0);
    }
    const oldTable = panel.querySelector(".batch-cascade-table");
    if (oldTable && !panel.querySelector(".batch-cascade-list")) oldTable.outerHTML = cascadeListMarkup();
    let chart = panel.querySelector(".batch-line-chart");
    if (!chart) {
      chart = document.createElement("div");
      chart.className = "batch-line-chart";
      panel.appendChild(chart);
    }
    if (!document.getElementById("batch-simulation-extras-style")) {
      const style = document.createElement("style");
      style.id = "batch-simulation-extras-style";
      style.textContent = `
        body.slot-simulator .batch-simulation-controls.has-mode{grid-template-columns:auto minmax(0,1fr) auto}
        body.slot-simulator #batchSimulationMode{min-height:34px;padding:7px 8px;border:0;border-radius:6px;color:var(--sim-text);background:var(--sim-surface);font:700 12px/1 "Segoe UI",system-ui,sans-serif}
        body.slot-simulator #batchSimulationMode[hidden]{display:none}
        .batch-line-chart{margin-top:8px;border:1px solid rgba(38,92,137,.35);border-radius:8px;padding:6px 8px 2px;background:rgba(6,13,26,.6)}
        .batch-line-chart .dlc-title{text-align:center;font-size:12.5px;color:var(--sim-sub,#7f9bb8);margin-bottom:2px}
        body.slot-simulator .batch-cascade-list{margin-top:8px;border:1px solid rgba(38,92,137,.35);border-radius:8px;padding:2px 10px 4px;background:rgba(6,13,26,.6)}
        body.slot-simulator .batch-cascade-title{padding:5px 0;color:var(--sim-sub);font-size:12px;font-weight:700;text-align:center;border-bottom:1px solid var(--sim-surface)}
        body.slot-simulator .batch-cascade-row{display:grid;grid-template-columns:minmax(0,1fr) 90px 90px;text-align:right}
        body.slot-simulator .batch-cascade-row > :first-child{text-align:left}
        body.slot-simulator .batch-cascade-list .simulation-row:last-child{border-bottom:0}
        .batch-line-chart svg{display:block;width:100%;height:auto}`;
      document.head.appendChild(style);
    }
    return { modeSelect, chart, modes };
  }

  // 模擬線型區間固定為 H026 標準 64 區間 (下限, 上限]，X 軸逐一標出區間文字。
  // 縱軸：Buy Feature 20%，其餘 1%；超過上限或為 0 的區間不畫點。
  const STANDARD_UPPERS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200,
    250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 2000, 3000, 4000, 5000, 6000,
    7000, 8000, 9000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999];
  const SIMULATION_BUCKETS = {
    labels: STANDARD_UPPERS.map((u, i) => `(${i ? STANDARD_UPPERS[i - 1] : -1}, ${u}]`),
    index(x) { for (let i = 0; i < STANDARD_UPPERS.length; i++) if (x <= STANDARD_UPPERS[i]) return i; return STANDARD_UPPERS.length - 1; }
  };

  function simulationChartSvg(counts, buckets, ymax) {
    const W = 900, H = 340, L = 44, R = 12, T = 10, B = 112, n = buckets.labels.length;
    const total = counts.reduce((a, b) => a + b, 0);
    const shares = counts.map((c) => (total ? c / total * 100 : 0));
    const px = (i) => L + (W - L - R) * (n > 1 ? i / (n - 1) : 0.5);
    const py = (v) => T + (H - T - B) * (1 - Math.min(v, ymax) / ymax);
    let out = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="倍率線型">`;
    for (let k = 0; k <= 4; k++) {
      const v = ymax * k / 4, y = py(v);
      out += `<line x1="${L}" y1="${y.toFixed(1)}" x2="${W - R}" y2="${y.toFixed(1)}" stroke="rgba(120,160,200,.18)"/><text x="${L - 6}" y="${(y + 4).toFixed(1)}" font-size="12" text-anchor="end" fill="#7f9bb8">${Number(v.toFixed(2))}%</text>`;
    }
    buckets.labels.forEach((label, i) => {
      const x = px(i).toFixed(1), y = H - B + 8;
      out += `<line x1="${x}" y1="${T}" x2="${x}" y2="${H - B}" stroke="rgba(120,160,200,.08)"/><text x="${x}" y="${y}" font-size="10" text-anchor="end" dominant-baseline="middle" fill="#7f9bb8" transform="rotate(-90 ${x} ${y})">${label}</text>`;
    });
    // 只畫 0 < 值 ≤ 縱軸上限的點；超出上限或為 0 的區間不畫點、線在該處斷開。
    const visible = (v) => v > 0 && v <= ymax;
    let d = "", pen = false;
    shares.forEach((v, i) => {
      if (!visible(v)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${px(i).toFixed(1)},${py(v).toFixed(1)}`;
      pen = true;
    });
    out += `<path d="${d}" fill="none" stroke="#4aa8ff" stroke-width="2"/>`;
    shares.forEach((v, i) => { if (visible(v)) out += `<circle cx="${px(i).toFixed(1)}" cy="${py(v).toFixed(1)}" r="3" fill="#4aa8ff"><title>${buckets.labels[i]} ${v.toFixed(3)}%（${counts[i]}）</title></circle>`; });
    return out + "</svg>";
  }

  function setupFallbackSimulation() {
    const panel = document.querySelector(".demogame-fallback-simulation");
    const start = panel?.querySelector("#batchSimulationStartBtn");
    const roundsInput = panel?.querySelector("#batchSimulationRounds");
    if (!panel || !start || !roundsInput) return;
    const { modeSelect, chart, modes } = ensureSimulationExtras(panel);
    const modeLabel = () => modes.find((m) => String(m.value) === modeSelect?.value)?.label || "Current Bet";
    const selectedMode = () => (modes.length ? modes.find((m) => String(m.value) === modeSelect.value)?.value : undefined);
    const yMaxFor = () => {
      const entry = modes.find((m) => String(m.value) === modeSelect?.value);
      if (Number(entry?.yMax) > 0) return Number(entry.yMax);
      return /buy|^bf$/i.test(entry?.label || "") ? 20 : 1;
    };
    let lastCounts = null;
    const renderChart = (counts, buckets) => {
      lastCounts = counts;
      const c = counts || new Array(buckets.labels.length).fill(0);
      const label = window.demogameSharedText ? window.demogameSharedText(modeLabel()) : modeLabel();
      chart.innerHTML = `<div class="dlc-title">${isZhText() ? "倍率線型" : "Multiplier Distribution"} · ${label}</div>${simulationChartSvg(c, buckets, yMaxFor())}`;
    };
    const renderEmpty = () => renderChart(null, SIMULATION_BUCKETS);
    modeSelect?.addEventListener("change", renderEmpty);
    document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(() => {
      renderChart(lastCounts, SIMULATION_BUCKETS);
      if (start.disabled && window.demogameSharedText) start.textContent = window.demogameSharedText("Running");
    }, 0));
    setTimeout(renderEmpty, 0);   // 等共用語言字典就緒
    // 沒有消除機制的遊戲：試跑一局，adapter 沒回傳 bgCascade 就一開始就隱藏消除分布
    setTimeout(async () => {
      if (typeof window.demogameSimulateRound !== "function") return;
      try {
        const pending = window.demogameSimulateRound({ mode: selectedMode() });
        const probe = pending && typeof pending.then === "function" ? await pending : (pending || {});
        const hasCascade = Number.isFinite(Number(probe.bgCascade)) || (Array.isArray(probe.fgCascades) && probe.fgCascades.length > 0);
        panel.querySelector(".batch-cascade-list")?.classList.toggle("demogame-removed", !hasCascade);
      } catch (error) { /* 試跑失敗就維持顯示 */ }
    }, 0);

    start.addEventListener("click", async () => {
      const requested = Math.min(1000000, Math.max(1, Math.trunc(Number(roundsInput.value) || 0)));
      roundsInput.value = String(requested);
      start.disabled = true;
      roundsInput.disabled = true;
      if (modeSelect) modeSelect.disabled = true;
      const mode = selectedMode();
      const buckets = SIMULATION_BUCKETS;
      const lineCounts = new Array(buckets.labels.length).fill(0);
      const simulateRound = typeof window.demogameSimulateRound === "function"
        ? window.demogameSimulateRound
        : null;
      if (!simulateRound) {
        const note = document.getElementById("batchSimulationNote");
        if (note) note.textContent = "Simulation adapter unavailable: this page cannot run the actual Demo Game logic yet.";
        start.textContent = window.demogameSharedText ? window.demogameSharedText("Start") : "Start";
        start.disabled = false;
        roundsInput.disabled = false;
        if (modeSelect) modeSelect.disabled = false;
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
      start.textContent = window.demogameSharedText ? window.demogameSharedText("Running") : "Running";   // 中文顯示「進行中」
      try {
        while (stats.rounds < requested) {
          const sliceStarted = performance.now();
          let sliceRounds = 0;
          while (stats.rounds < requested && sliceRounds < 2000 && performance.now() - sliceStarted < 40) {
            const pending = simulateRound({ mode });
            const result = pending && typeof pending.then === "function" ? await pending : (pending || {});
            const multiplier = Math.max(0, Number(result.multiplier) || 0);
            const lineValue = Number.isFinite(Number(result.lineMultiplier)) ? Number(result.lineMultiplier) : multiplier;
            lineCounts[buckets.index(lineValue)] += 1;
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
            stats.maxMultiplier = Math.max(stats.maxMultiplier, lineValue);   // 最高倍數＝單局總得分倍數（BF ÷ 底注）
          }
          writeFallbackStats(stats);
          renderChart(lineCounts, buckets);
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
      } finally {
        start.textContent = window.demogameSharedText ? window.demogameSharedText("Start") : "Start";
        start.disabled = false;
        roundsInput.disabled = false;
        if (modeSelect) modeSelect.disabled = false;
      }
    });
    updateSharedSimulationContext();
  }

  setupFallbackSimulation();

  // Spin Result 面板已停用（共用）：各遊戲仍可寫入 #lineList 等節點，不會報錯，只是不顯示。
  function hideSpinResult() {
    document.querySelectorAll("#log-wrap, .diagnostic-region").forEach((region) => {
      const head = region.querySelector(".diagnostic-header, h3, #log-header")?.textContent?.trim() || "";
      if (region.id === "log-wrap" || /^spin result$|^spin 結果$|^旋轉結果$/i.test(head)) region.classList.add("demogame-removed");
    });
    if (!document.getElementById("demogame-removed-style")) {
      const style = document.createElement("style");
      style.id = "demogame-removed-style";
      style.textContent = ".demogame-removed{display:none!important}";
      document.head.appendChild(style);
    }
  }

  hideSpinResult();

  // Force FG 已停用（共用）：隱藏勾選框並固定不勾，遊戲讀到的 checked 永遠是 false。
  function removeForceFg() {
    const input = document.getElementById("forceFgInput");
    if (!input) return;
    input.checked = false;
    input.disabled = true;
    (input.closest("label") || input).classList.add("demogame-removed");
  }

  removeForceFg();

  // ===== 可重現 RNG（共用）=====
  // 每局用一組 32-bit 種子（mulberry32）驅動所有數學抽樣；Log 印一行「RNG <碼>」，點一下複製並填入 Set RNG 的 #rngInput，
  // 下一局 Spin 照碼重跑出同一局（BG、消除、FG 全部相同）。
  // RNG 碼：<Config-Profile>/<NB|EB|BF|SF>/<Card on|off>/<遊戲選項|->/<種子 8 碼 hex>，例 92A-Oldhand/NB/on/-/8f3a21b0。
  // 遊戲用法：
  //   const code = demogameRng.takeInput();            // 讀 #rngInput（不清空，按重置才清），格式錯誤會丟 Error；沒填回 null
  //   const seed = code ? code.seed : demogameRng.newSeed();
  //   const result = demogameRng.run(seed, () => 算出整局結果（BG＋FG，同步）);   // 期間 Math.random 換成種子序列
  //   appendLog(`RNG ${demogameRng.format({ config, mode, card, opts, seed })}`);
  // 表演用的亂數不要放進 run()；整局結果必須在 run() 內一次算完。
  function seededRandom(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  window.demogameRng = {
    newSeed: () => (crypto.getRandomValues(new Uint32Array(1))[0] >>> 0),
    seeded: seededRandom,
    run(seed, fn) {
      const original = Math.random;
      Math.random = seededRandom(seed);
      try { return fn(); } finally { Math.random = original; }
    },
    format({ config = "", mode = "NB", card = false, opts = "", seed = 0 } = {}) {
      return [String(config).replace(/\s+/g, "") || "-", mode, card ? "on" : "off", opts || "-", (seed >>> 0).toString(16).padStart(8, "0")].join("/");
    },
    parse(text) {
      const parts = String(text || "").trim().replace(/^RNG\s+/i, "").split("/");
      if (parts.length !== 5 || !/^(NB|EB|BF|SF)$/.test(parts[1]) || !/^(on|off)$/.test(parts[2]) || !/^[0-9a-f]{8}$/i.test(parts[4])) return null;
      return { config: parts[0], mode: parts[1], card: parts[2] === "on", opts: parts[3] === "-" ? "" : parts[3], seed: parseInt(parts[4], 16) >>> 0 };
    },
    takeInput() {
      const input = document.getElementById("rngInput");
      const text = input?.value.trim() || "";
      if (!text) return null;   // 填了就一直沿用，按重置才清空
      const code = this.parse(text);
      if (!code) throw new Error(isZhText() ? "RNG 格式錯誤：Config-Profile/NB|EB|BF|SF/on|off/選項|-/8 碼種子" : "Invalid RNG code: Config-Profile/NB|EB|BF|SF/on|off/opts|-/8-hex seed");
      return code;
    }
  };
  function isZhText() { return /^zh/i.test(document.getElementById("languageSelect")?.value || ""); }

  // ===== 算分後停頓（共用）=====
  // 每一轉（BG 局與每一轉 FG）分數加完後停 DEMOGAME_ROUND_PAUSE_MS 再放行下一轉／Auto；固定毫秒，不受 Speed 影響。
  const DEMOGAME_ROUND_PAUSE_MS = 500;
  window.demogameRoundPause = () => new Promise((resolve) => setTimeout(resolve, DEMOGAME_ROUND_PAUSE_MS));

  // ===== Log（共用）=====
  // window.demogameLog(text, type)：寫一行「[HH:MM:SS] text」到 #liveLogBody，最多 500 行。
  // type：info（一般）／mode（局號、模式、FG 觸發）／rng／result（得分、載入、FG 結束）／cascade（有消除的 FG 轉）／error。
  // 統一的行格式（照 H045）：
  //   Config <名稱> loaded | Version <版本> | Card System On|Off
  //   #<局號> Normal Bet|Extra Bet|Buy Feature|Super Feature | Bet <押注>[ | Card Range set][ | Replay]
  //   RNG <碼>
  //   BG|BF Entry | <盤面表> | Cascade <n> | C1 <n> | Win <得分> (<倍數>x)
  //   Free Game triggered|Buy Feature | <n> spins[ (Retrigger ×k)]
  //   FG <i>/<n> | <盤面表> | Cascade <n> | C1 <n> | Win <得分>
  //   FG complete | Total <得分> (<倍數>x)
  //   Error | <訊息>
  // 不記演出過程（轉輪中、逐步消除等）。
  window.demogameLog = (text, type = "info") => {
    const body = document.getElementById("liveLogBody");
    if (!body) return;
    const line = document.createElement("div");
    line.className = `live-log-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString("en-GB", { hour12: false })}] ${text}`;
    body.appendChild(line);
    while (body.children.length > 500) body.firstElementChild.remove();
    body.scrollTop = body.scrollHeight;
  };

  // Log 裡的「RNG <碼>」行：點一下複製並填入 #rngInput
  function decorateRngLines(root) {
    root?.querySelectorAll?.(".live-log-line, div").forEach((line) => {
      if (line.dataset.rngReady || line.children.length) return;
      const match = /RNG\s+(\S+\/(?:NB|EB|BF|SF)\/(?:on|off)\/\S+\/[0-9a-f]{8})\s*$/i.exec(line.textContent);
      if (!match) return;
      line.dataset.rngReady = "1";
      line.classList.add("demogame-rng-line");
      line.title = "Click: copy + fill RNG";
      line.addEventListener("click", () => {
        navigator.clipboard?.writeText(match[1]).catch(() => {});
        const input = document.getElementById("rngInput");
        if (input) { input.value = match[1]; input.dispatchEvent(new Event("input", { bubbles: true })); }
      });
    });
  }
  const liveLog = document.getElementById("liveLogBody");
  if (liveLog) {
    new MutationObserver(() => decorateRngLines(liveLog)).observe(liveLog, { childList: true });
    const style = document.createElement("style");
    style.textContent = ".demogame-rng-line{cursor:pointer;color:#f0c060!important}.demogame-rng-line:hover{text-decoration:underline}";
    document.head.appendChild(style);
  }

  // 共用區語言切換：Language 選繁中時，把共用區（Player／Play／Bet Mode／Stats／Simulation／Set RNG／
  // Reel RNG／Log／Setting）仍是英文的固定標籤換成中文；切回 English 時還原。
  // 只比對「整段文字完全相同」的標籤，不碰盤面、Help、Log 內容與修改紀錄內文（By Game 由各遊戲自行翻譯）。
  const SHARED_ZH = {
    "credit": "餘額", "bet": "押注", "win": "得分", "play": "遊戲", "auto": "自動", "speed": "速度",
    "bet mode": "押注模式", "normal bet": "一般押注", "extra bet": "額外押注", "buy feature": "購買特色", "super feature": "超級特色", "buy super feature": "購買超級特色",
    "stats": "統計", "simulation stats": "模擬統計", "total rounds": "總局數", "hit rate": "中獎率",
    "fg trigger": "FG 觸發", "fg trigger (observed)": "FG 觸發（實測）", "max multiplier": "最高倍數",
    "set rng": "指定 RNG", "card bg range": "卡片 BG 區間", "card bf range": "卡片 BF 區間", "reel rng": "輪帶 RNG",
    "reset": "重置", "force fg": "強制 FG", "log": "紀錄", "clear": "清除", "simulation": "模擬", "start": "開始",
    "running": "進行中", "retry limit exceeded": "Retry 超限", "scene": "場景", "setting": "設定",
    "debug mode": "除錯模式", "card system": "卡片系統", "image": "圖片", "version": "版本", "language": "語言",
    "help": "說明", "change log": "修改紀錄", "previous": "上一步", "next": "下一步",
    "cascade distribution": "消除分布", "cascades": "消除次數", "history": "歷史紀錄", "report": "數值報告", "bg max multiplier": "BG 最大倍數", "fg max multiplier": "FG 最大倍數", "double-click to play offline. no server needed.": "雙擊即可離線遊玩，不需伺服器。"
  };
  const SHARED_SKIP = "#helpContent, #helpDialog .help-body, #changeLogBody, #liveLogBody, #rngList, #lineList, #spinResultList, script, style, svg";
  const sharedOriginal = new WeakMap();
  const isZh = () => /^zh/i.test(document.getElementById("languageSelect")?.value || document.documentElement.lang || "");
  let sharedApplying = false;
  function applySharedLanguage() {
    if (sharedApplying) return;
    sharedApplying = true;
    const zh = isZh();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => n.nodeType === 1
        ? (n.matches(SHARED_SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_SKIP)
        : NodeFilter.FILTER_ACCEPT
    });
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const raw = node.nodeValue;
      const text = raw.trim();
      if (!text) continue;
      if (zh) {
        const zhText = SHARED_ZH[text.toLowerCase()];
        if (zhText) { sharedOriginal.set(node, text); node.nodeValue = raw.replace(text, zhText); }
      } else if (sharedOriginal.has(node)) {
        const original = sharedOriginal.get(node);
        if (SHARED_ZH[original.toLowerCase()] === text) node.nodeValue = raw.replace(text, original);
        sharedOriginal.delete(node);
      }
    }
    sharedApplying = false;
  }
  window.demogameSharedText = (english) => (isZh() && SHARED_ZH[String(english).toLowerCase()]) || english;
  document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(applySharedLanguage, 0));
  let sharedQueued = false;
  new MutationObserver(() => {
    if (sharedApplying || sharedQueued || !isZh()) return;
    sharedQueued = true;
    requestAnimationFrame(() => { sharedQueued = false; applySharedLanguage(); });
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
  setTimeout(applySharedLanguage, 0);

  // FG 觸發的單位隨語言切換：(N 場)／(N rounds)
  const syncFgUnit = () => {
    const node = document.getElementById("batchSimulationFgTrigger");
    if (node) node.textContent = node.textContent.replace(/ (場|rounds)\)$/, isZh() ? " 場)" : " rounds)");
  };
  document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(syncFgUnit, 0));
  setTimeout(syncFgUnit, 0);

  // ===== 歷史紀錄（共用，Debug Mode 顯示）=====
  // 頁面在載入本檔前設 window.DEMOGAME_HISTORY = true 才建立面板；
  // 每局結束時呼叫 window.demogameHistory.record({ bg: BG 得分 ÷ 底注, fg: 該局 FG 總得分 ÷ 底注 })，沒有 FG 時 fg 給 0 或省略。
  function setupHistoryPanel() {
    if (!window.DEMOGAME_HISTORY || document.getElementById("demogame-history")) return;
    const panel = document.createElement("section");
    panel.id = "demogame-history";
    panel.className = "control-zone debug-only debug-hidden demogame-history";
    panel.innerHTML = `
      <div class="demogame-history-header"><span class="zone-label">History</span><button id="clearHistoryBtn" type="button">Clear</button></div>
      <div class="demogame-history-body">
        <div class="simulation-row"><span class="s-label">BG Max Multiplier</span><span class="s-value hi" id="historyBgMax">x0</span></div>
        <div class="simulation-row"><span class="s-label">FG Max Multiplier</span><span class="s-value hi" id="historyFgMax">x0</span></div>
      </div>`;
    const anchor = document.getElementById("live-log-wrap") || document.getElementById("rng-wrap");
    if (anchor) anchor.insertAdjacentElement("afterend", panel);
    else document.getElementById("settings-wrap")?.insertAdjacentElement("beforebegin", panel);
    if (!document.getElementById("demogame-history-style")) {
      const style = document.createElement("style");
      style.id = "demogame-history-style";
      style.textContent = `
        body.slot-simulator #demogame-history{display:block;width:100%;margin-top:10px;padding:12px 14px;border:1px solid var(--sim-border)!important;border-radius:10px;background:var(--sim-panel);box-shadow:0 4px 14px rgba(0,0,0,.13)!important}
        .demogame-history-header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:4px}
        #demogame-history #clearHistoryBtn{padding:5px 10px;border:0;border-radius:5px;color:var(--sim-sub);background:var(--sim-surface);font:700 11px/1 inherit;cursor:pointer}
        #demogame-history.debug-hidden{display:none!important}`;
      document.head.appendChild(style);
    }
    const debugInput = document.querySelector("#debugModeInput, #debugInput");
    const sync = () => panel.classList.toggle("debug-hidden", !debugInput?.checked);
    debugInput?.addEventListener("change", sync);
    sync();
    let bgMax = 0, fgMax = 0;
    const fmt = (v) => `x${Number(v.toFixed(2))}`;
    const render = () => {
      document.getElementById("historyBgMax").textContent = fmt(bgMax);
      document.getElementById("historyFgMax").textContent = fmt(fgMax);
    };
    window.demogameHistory = {
      record({ bg = 0, fg = 0 } = {}) {
        if (Number.isFinite(Number(bg))) bgMax = Math.max(bgMax, Number(bg));
        if (Number.isFinite(Number(fg))) fgMax = Math.max(fgMax, Number(fg));
        render();
      },
      reset() { bgMax = 0; fgMax = 0; render(); }
    };
    panel.querySelector("#clearHistoryBtn").addEventListener("click", () => window.demogameHistory.reset());
    document.getElementById("resetBtn")?.addEventListener("click", () => window.demogameHistory.reset());
  }

  setupHistoryPanel();

  // 最後調性更新日期（共用，頁尾 .footer-note）：頁面在載入本檔前設 window.DEMOGAME_LAST_TUNING = "YYYY-MM-DD HH:MM"。
  // 只看調性：數學模型或倍率（卡片）權重有改才更新；介面、文件修改不算。
  // 另可設 window.DEMOGAME_LAST_CODE（程式最後調整：index／Simulator／共用程式）與
  // window.DEMOGAME_LAST_UPDATE（任何東西最後調整），有設才多顯示一行。
  function syncLastTuning() {
    const date = window.DEMOGAME_LAST_TUNING;
    const note = document.querySelector(".footer-note");
    if (!date || !note) return;
    const zh = isZhText();
    const lines = [zh ? `最後調性更新：${date}` : `Last tuning update: ${date}`];
    if (window.DEMOGAME_LAST_CODE) lines.push(zh ? `程式最後調整：${window.DEMOGAME_LAST_CODE}` : `Last code update: ${window.DEMOGAME_LAST_CODE}`);
    if (window.DEMOGAME_LAST_UPDATE) lines.push(zh ? `最後更新：${window.DEMOGAME_LAST_UPDATE}` : `Last update: ${window.DEMOGAME_LAST_UPDATE}`);
    note.textContent = "";
    lines.forEach((text, index) => {
      if (index) note.appendChild(document.createElement("br"));
      note.appendChild(document.createTextNode(text));
    });
  }
  syncLastTuning();
  document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(syncLastTuning, 0));

  // 標題列右側按鈕（共用）：數值報告、說明、重置排在一起。
  // 數值報告：頁面在載入本檔前設 window.DEMOGAME_REPORT_URL（相對路徑）才出現；在同一分頁開啟，
  // 可用瀏覽器「上一頁」回到 Demo（報告頁另有「← 返回 Demo」）。說明／重置由設定列搬來，事件監聽沿用。
  function setupTitleActions() {
    const title = document.getElementById("game-title");
    const bar = title?.parentElement;
    if (!bar || document.getElementById("demogameTitleActions")) return;
    const group = document.createElement("div");
    group.id = "demogameTitleActions";
    const url = window.DEMOGAME_REPORT_URL;
    if (url) {
      const link = document.createElement("a");
      link.id = "demogameReportBtn";
      link.href = url;
      link.textContent = "Report";
      group.appendChild(link);
    }
    for (const id of ["helpBtn", "resetBtn"]) {
      const button = document.getElementById(id);
      if (button) group.appendChild(button);
    }
    if (!group.children.length) return;
    if (getComputedStyle(bar).position === "static") bar.style.position = "relative";
    bar.appendChild(group);
    const style = document.createElement("style");
    style.textContent = `#demogameTitleActions{position:absolute;right:12px;top:50%;transform:translateY(-50%);display:flex;gap:2px;align-items:center}
      #demogameTitleActions > a, #demogameTitleActions > button{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;
        height:30px;min-height:0;min-width:0;width:auto;margin:0;padding:0 8px;border-radius:7px;border:none;
        color:#6f8fae;background:transparent;font-family:inherit;font-size:var(--demogame-title-size,13px);font-weight:var(--demogame-title-weight,700);line-height:1;
        letter-spacing:0;white-space:nowrap;text-decoration:none;cursor:pointer}
      #demogameTitleActions > a:hover, #demogameTitleActions > button:hover{color:#dceeff;background:rgba(127,160,200,.14)}
      #demogameTitleActions > a:focus-visible, #demogameTitleActions > button:focus-visible{outline:2px solid rgba(127,160,200,.6);outline-offset:1px}`;
    const titleStyle = getComputedStyle(document.getElementById("gameName") || title);
    group.style.setProperty("--demogame-title-size", titleStyle.fontSize);
    group.style.setProperty("--demogame-title-weight", titleStyle.fontWeight);
    group.style.fontFamily = titleStyle.fontFamily;
    document.head.appendChild(style);
    // 標題列右側若原本有其他文字，留出按鈕群寬度避免重疊
    const pad = parseFloat(getComputedStyle(bar).paddingRight) || 0;
    bar.style.paddingRight = `${pad + group.offsetWidth + 14}px`;
  }

  setupTitleActions();

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

// Shared control binding for games that opt in. Existing games keep their
// current listeners until they migrate to this API.
(() => {
  "use strict";

  window.slotBindCommonControls = (actions = {}) => {
    const byId = (id) => document.getElementById(id);
    const bind = (id, eventName, handler) => {
      const element = byId(id);
      if (element && typeof handler === "function") element.addEventListener(eventName, handler);
      return element;
    };

    bind("spinBtn", "click", actions.spin);
    bind("autoBtn", "click", actions.toggleAuto);
    bind("normalBetBtn", "click", actions.normalMode);
    bind("extraBetBtn", "click", actions.extraMode);
    bind("buyFeatureBtn", "click", actions.buyFeatureMode);
    bind("betMinusBtn", "click", actions.betMinus);
    bind("betPlusBtn", "click", actions.betPlus);
    bind("betBtn", "click", actions.toggleBetMenu);
    bind("speedRange", "input", actions.speedChange);
    bind("previousStepBtn", "click", actions.previousStep);
    bind("nextStepBtn", "click", actions.nextStep);
    bind("debugModeInput", "change", actions.debugChange);
    bind("setRngResetBtn", "click", actions.resetRng);
    bind("clearLogBtn", "click", actions.clearLog);
    bind("resetBtn", "click", actions.reset);
    bind("configSelect", "change", actions.configChange);
    bind("languageSelect", "change", actions.languageChange);
    bind("helpBtn", "click", actions.openHelp);
    bind("closeHelpBtn", "click", actions.closeHelp);

    const rngInput = byId("rngInput");
    const cardRange = byId("cardRangeSelect");
    rngInput?.addEventListener("input", () => {
      if (rngInput.value.trim() && cardRange) cardRange.value = "";
      actions.rngChanged?.();
    });
    cardRange?.addEventListener("change", () => {
      if (cardRange.value && rngInput) rngInput.value = "";
      actions.rngChanged?.();
    });

    document.addEventListener("click", (event) => actions.documentClick?.(event));
    document.addEventListener("keydown", (event) => {
      if (event.code !== "Space" || ["INPUT", "SELECT", "BUTTON"].includes(event.target?.tagName)) return;
      event.preventDefault();
      actions.spin?.(event);
    });

    const helpDialog = byId("helpDialog");
    helpDialog?.addEventListener("click", (event) => {
      if (event.target === helpDialog) actions.closeHelp?.(event);
    });
    byId("helpFrame")?.addEventListener("load", actions.helpFrameLoad);

    return { rngInput, cardRange, helpDialog };
  };
})();

// Shared cascade/win FX layer (opt-in). A game activates it by calling
// window.slotFx.* helpers with its own cell elements; pages that never call
// slotFx are completely unaffected. First use injects the fx styles once.
(() => {
  "use strict";

  let stylesInjected = false;

  function injectStyles() {
    if (stylesInjected) return;
    stylesInjected = true;
    const style = document.createElement("style");
    style.id = "slot-fx-styles";
    style.textContent = `
      .slot-fx-layer {
        position: absolute;
        inset: 0;
        z-index: 40;
        pointer-events: none;
        overflow: visible;
      }
      .cell.fx-dim { filter: brightness(0.32) saturate(0.55); }
      .cell.fx-win {
        border-color: #ffe27a !important;
        animation: slot-fx-win-glow 460ms ease-in-out infinite alternate;
        z-index: 5;
      }
      @keyframes slot-fx-win-glow {
        from { box-shadow: 0 0 10px rgba(255, 214, 90, 0.55), inset 0 0 8px rgba(255, 232, 150, 0.35); transform: scale(1.02); filter: brightness(1.12); }
        to   { box-shadow: 0 0 26px rgba(255, 214, 90, 0.95), inset 0 0 16px rgba(255, 240, 180, 0.6); transform: scale(1.08); filter: brightness(1.5); }
      }
      .cell.fx-pop > .symbol-wrap,
      .cell.fx-pop > .icon,
      .cell.fx-pop > .code,
      .cell.fx-pop > .symbol-code { animation: slot-fx-pop 300ms ease-in forwards; }
      @keyframes slot-fx-pop {
        0%   { transform: scale(1); filter: brightness(1.6); }
        55%  { transform: scale(1.28); filter: brightness(2.2); }
        100% { transform: scale(0); filter: brightness(2.6); opacity: 0; }
      }
      .fx-coin {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: radial-gradient(circle at 34% 30%, #fff6c8, #ffd85e 45%, #b97a12 90%);
        box-shadow: 0 0 8px rgba(255, 214, 90, 0.9);
        animation: slot-fx-coin var(--dur, 700ms) cubic-bezier(0.2, 0.6, 0.6, 1) forwards;
      }
      @keyframes slot-fx-coin {
        0%   { transform: translate(0, 0) scale(1); opacity: 1; }
        100% { transform: translate(var(--dx), var(--dy)) scale(0.35) rotate(300deg); opacity: 0; }
      }
      .cell.fx-wild-pop { z-index: 6; animation: slot-fx-wild-pop 520ms cubic-bezier(0.2, 1.4, 0.4, 1); }
      @keyframes slot-fx-wild-pop {
        0%   { transform: scale(0.2); filter: brightness(3); }
        60%  { transform: scale(1.28); }
        100% { transform: scale(1); filter: brightness(1); }
      }
      .cell.fx-wild-stay { animation: slot-fx-wild-stay 1.4s ease-in-out infinite; border-color: #ffb054 !important; }
      @keyframes slot-fx-wild-stay {
        0%, 100% { box-shadow: 0 0 8px rgba(255, 150, 60, 0.5); }
        50%      { box-shadow: 0 0 22px rgba(255, 170, 70, 0.95), 0 0 40px rgba(255, 120, 40, 0.35); }
      }
      .cell.fx-scatter { animation: slot-fx-scatter 900ms ease-in-out infinite alternate; z-index: 5; }
      @keyframes slot-fx-scatter {
        from { box-shadow: 0 0 8px rgba(115, 239, 255, 0.5); filter: brightness(1.05); transform: scale(1); }
        to   { box-shadow: 0 0 26px rgba(255, 230, 130, 0.95); filter: brightness(1.4); transform: scale(1.07); }
      }
      .fx-multi-pop {
        position: absolute;
        left: 50%;
        top: 42%;
        z-index: 60;
        transform: translate(-50%, -50%);
        font: 900 64px "Franklin Gothic Medium", "Arial Black", sans-serif;
        color: #ffd75e;
        -webkit-text-stroke: 2px #7a3c00;
        text-shadow: 0 0 22px rgba(255, 190, 60, 0.95), 0 4px 0 #5c2e00, 0 0 60px rgba(255, 150, 30, 0.5);
        animation: slot-fx-multi-pop 950ms cubic-bezier(0.18, 1.3, 0.4, 1) forwards;
        pointer-events: none;
        white-space: nowrap;
        text-align: center;
      }
      .fx-multi-pop.jump {
        color: #7dffc8;
        -webkit-text-stroke: 2px #044d33;
        text-shadow: 0 0 26px rgba(90, 255, 190, 0.95), 0 4px 0 #033524, 0 0 70px rgba(60, 255, 170, 0.5);
      }
      .fx-multi-pop .fx-jump-tag {
        display: block;
        font-size: 20px;
        letter-spacing: 3px;
        text-align: center;
        -webkit-text-stroke: 1px #044d33;
      }
      @keyframes slot-fx-multi-pop {
        0%   { transform: translate(-50%, -50%) scale(0.15); opacity: 0; }
        18%  { transform: translate(-50%, -50%) scale(1.35); opacity: 1; }
        32%  { transform: translate(-50%, -50%) scale(1); }
        72%  { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        100% { transform: translate(-50%, -56%) scale(0.9); opacity: 0; }
      }
      .fx-win-float {
        position: absolute;
        left: 50%;
        top: 62%;
        z-index: 55;
        transform: translateX(-50%);
        font: 900 30px Consolas, "Courier New", monospace;
        color: #fff2ba;
        text-shadow: 0 0 14px rgba(255, 214, 90, 0.9), 0 2px 0 #5c2e00;
        animation: slot-fx-win-float 1000ms ease-out forwards;
        pointer-events: none;
        white-space: nowrap;
      }
      @keyframes slot-fx-win-float {
        0%   { transform: translate(-50%, 14px) scale(0.7); opacity: 0; }
        20%  { transform: translate(-50%, 0) scale(1.08); opacity: 1; }
        100% { transform: translate(-50%, -46px) scale(1); opacity: 0; }
      }
      .fx-total-win {
        position: absolute;
        left: 0;
        right: 0;
        top: 46%;
        z-index: 70;
        padding: 14px 0;
        text-align: center;
        background: linear-gradient(90deg, transparent, rgba(255, 245, 210, 0.16) 18%, rgba(255, 250, 230, 0.34) 50%, rgba(255, 245, 210, 0.16) 82%, transparent);
        animation: slot-fx-total-in 1600ms ease forwards;
        pointer-events: none;
      }
      .fx-total-win .fx-total-label {
        display: block;
        font: 900 15px "Franklin Gothic Medium", sans-serif;
        letter-spacing: 4px;
        color: #ffe9b0;
        text-shadow: 0 0 10px rgba(255, 200, 80, 0.8);
      }
      .fx-total-win .fx-total-value {
        display: block;
        font: 900 44px "Franklin Gothic Medium", "Arial Black", sans-serif;
        color: #ffd75e;
        -webkit-text-stroke: 1.5px #7a3c00;
        text-shadow: 0 0 24px rgba(255, 200, 70, 0.95), 0 3px 0 #5c2e00;
      }
      @keyframes slot-fx-total-in {
        0%   { transform: scaleX(0.1); opacity: 0; filter: brightness(3); }
        14%  { transform: scaleX(1); opacity: 1; filter: brightness(1.8); }
        26%  { filter: brightness(1); }
        82%  { opacity: 1; }
        100% { opacity: 0; }
      }
      .cell.fx-reel-roll > .symbol-wrap,
      .cell.fx-reel-roll > .icon,
      .cell.fx-reel-roll > .code { animation: slot-fx-reel-roll 90ms linear infinite; filter: blur(1.2px) brightness(0.92); }
      @keyframes slot-fx-reel-roll {
        from { transform: translateY(-46%); }
        to   { transform: translateY(46%); }
      }
      @media (prefers-reduced-motion: reduce) {
        .fx-coin, .fx-multi-pop, .fx-win-float, .fx-total-win { animation-duration: 1ms !important; }
      }
    `;
    document.head.appendChild(style);
  }

  const addClass = (elements, className) => {
    (elements || []).forEach((element) => element?.classList.add(className));
  };

  window.slotFx = {
    // container：board 的外框（例如 .board-shell）。回傳可放置粒子／浮字的 fx layer。
    ensureLayer(container) {
      injectStyles();
      if (!container) return null;
      let layer = container.querySelector(":scope > .slot-fx-layer");
      if (!layer) {
        if (getComputedStyle(container).position === "static") container.style.position = "relative";
        layer = document.createElement("div");
        layer.className = "slot-fx-layer";
        container.appendChild(layer);
      }
      return layer;
    },
    mark(element, className) { injectStyles(); element?.classList.add(className); },
    // 中獎強調：winCells 金光爆閃、dimCells 壓暗
    winGlow(winCells, dimCells) { injectStyles(); addClass(winCells, "fx-win"); addClass(dimCells, "fx-dim"); },
    // 滾動中的輪帶格
    reelRoll(cells) { injectStyles(); addClass(cells, "fx-reel-roll"); },
    // 消除縮爆
    popCells(cells) { injectStyles(); addClass(cells, "fx-pop"); },
    // 金框轉 Wild 彈出（在補牌後對新 Wild 格呼叫）
    wildPop(cells) { injectStyles(); addClass(cells, "fx-wild-pop"); },
    // 金幣粒子：items = [{el, count}]，以每格中心為原點噴散
    spawnCoins(layer, items, maxTotal = 48) {
      injectStyles();
      if (!layer) return;
      const layerRect = layer.getBoundingClientRect();
      let spawned = 0;
      for (const item of items || []) {
        if (!item?.el || spawned >= maxTotal) continue;
        const rect = item.el.getBoundingClientRect();
        const cx = rect.left - layerRect.left + rect.width / 2;
        const cy = rect.top - layerRect.top + rect.height / 2;
        const count = Number(item.count) || 5;
        for (let i = 0; i < count && spawned < maxTotal; i += 1) {
          const coin = document.createElement("span");
          coin.className = "fx-coin";
          const angle = Math.random() * Math.PI * 2;
          const dist = 40 + Math.random() * 90;
          coin.style.left = `${cx - 6}px`;
          coin.style.top = `${cy - 6}px`;
          coin.style.setProperty("--dx", `${Math.cos(angle) * dist}px`);
          coin.style.setProperty("--dy", `${Math.sin(angle) * dist - 40}px`);
          coin.style.setProperty("--dur", `${520 + Math.random() * 380}ms`);
          layer.appendChild(coin);
          setTimeout(() => coin.remove(), 1000);
          spawned += 1;
        }
      }
    },
    // 盤面中央大字（倍數等）。options.jump = 綠金跳階配色、options.tag = 上方小標籤
    multiPop(layer, text, options = {}) {
      injectStyles();
      if (!layer) return;
      const node = document.createElement("div");
      node.className = `fx-multi-pop${options.jump ? " jump" : ""}`;
      node.innerHTML = `${options.tag ? `<span class="fx-jump-tag">${options.tag}</span>` : ""}${text}`;
      layer.appendChild(node);
      setTimeout(() => node.remove(), 1100);
    },
    // 每段贏分浮字
    winFloat(layer, text) {
      injectStyles();
      if (!layer) return;
      const node = document.createElement("div");
      node.className = "fx-win-float";
      node.textContent = text;
      layer.appendChild(node);
      setTimeout(() => node.remove(), 1100);
    },
    // 回合結束總贏分閃光橫幅
    totalWin(layer, label, value) {
      injectStyles();
      if (!layer) return;
      const node = document.createElement("div");
      node.className = "fx-total-win";
      node.innerHTML = `<span class="fx-total-label">${label}</span><span class="fx-total-value">${value}</span>`;
      layer.appendChild(node);
      setTimeout(() => node.remove(), 1700);
    }
  };
})();

// ===== 倍率線型（共用；Debug 模式才顯示）=====
// 有共用 Simulation 面板（.demogame-fallback-simulation）且遊戲有 demogameSimulateRound 時，
// 線型併入 Simulation 面板（setupFallbackSimulation 內繪製，標準 64 區間），不再另外顯示即時面板。
// 否則維持即時面板（Set RNG 上方）：各遊戲在 NB 一局（含 FG）結束時呼叫
//   window.demogameLineChart?.record(該局總得分 ÷ 底注)
// 區間為 H026 標準 64 區間 (Lower, Upper]；Reset 按鈕會清空；縱軸固定 0～20%，超過貼頂。
(() => {
  const THRESH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200,
    250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 2000, 3000, 4000, 5000, 6000,
    7000, 8000, 9000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999];
  const LABELS = THRESH.map((upper, i) => `(${i ? THRESH[i - 1] : -1}, ${upper}]`);
  const YMAX = 20;
  let counts = new Array(THRESH.length).fill(0);
  let chart = null, panel = null;

  function bucket(x) {
    for (let i = 0; i < THRESH.length; i++) if (x <= THRESH[i]) return i;
    return THRESH.length - 1;
  }

  function svg(counts) {
    const W = 900, H = 280, L = 44, R = 12, T = 10, B = 40, n = THRESH.length;
    const total = counts.reduce((a, b) => a + b, 0);
    const shares = counts.map(c => total ? c / total * 100 : 0);
    const px = i => L + (W - L - R) * i / (n - 1), py = v => T + (H - T - B) * (1 - Math.min(v, YMAX) / YMAX);
    let out = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="倍率線型">`;
    for (let k = 0; k <= 4; k++) {
      const v = YMAX * k / 4, y = py(v);
      out += `<line x1="${L}" y1="${y.toFixed(1)}" x2="${W - R}" y2="${y.toFixed(1)}" stroke="rgba(120,160,200,.18)"/><text x="${L - 6}" y="${(y + 4).toFixed(1)}" font-size="12" text-anchor="end" fill="#7f9bb8">${v}%</text>`;
    }
    for (const i of [0, 5, 10, 14, 18, 23, 28, 32, 36, 44, 49, 54, 59, 63]) {
      out += `<line x1="${px(i).toFixed(1)}" y1="${T}" x2="${px(i).toFixed(1)}" y2="${H - B}" stroke="rgba(120,160,200,.08)"/><text x="${px(i).toFixed(1)}" y="${H - B + 18}" font-size="11" text-anchor="middle" fill="#7f9bb8">${i === 0 ? "0" : THRESH[i - 1]}</text>`;
    }
    let d = "", pen = false;
    shares.forEach((v, i) => { if (v <= 0) { pen = false; return; } d += `${pen ? "L" : "M"}${px(i).toFixed(1)},${py(v).toFixed(1)}`; pen = true; });
    out += `<path d="${d}" fill="none" stroke="#4aa8ff" stroke-width="2"/>`;
    shares.forEach((v, i) => { if (v > 0) out += `<circle cx="${px(i).toFixed(1)}" cy="${py(v).toFixed(1)}" r="3" fill="#4aa8ff"><title>${LABELS[i]} ${v.toFixed(3)}%（${counts[i]}）</title></circle>`; });
    return out + "</svg>";
  }

  function render() {
    if (!chart) return;
    const total = counts.reduce((a, b) => a + b, 0);
    const nz = counts.map((c, i) => c ? i : -1).filter(i => i >= 0);
    const range = nz.length ? `${LABELS[nz[0]]} ～ ${LABELS[nz[nz.length - 1]]}` : "—";
    chart.innerHTML = `<div class="dlc-title"><span>NB（每局總得分 ÷ 底注，含 FG）</span><span>n=${total.toLocaleString("en-US")} · ${range}</span></div>${svg(counts)}`;
  }

  function mount() {
    if (document.querySelector(".demogame-fallback-simulation") && typeof window.demogameSimulateRound === "function") return;   // 已併入 Simulation 面板
    const anchor = document.getElementById("set-rng-panel");
    if (!anchor || document.getElementById("demogame-line-chart")) return;
    const style = document.createElement("style");
    style.textContent = `
      #demogame-line-chart .dlc-body{display:block;width:100%}
      #demogame-line-chart .dlc-chart{width:100%;min-width:0;border:1px solid rgba(38,92,137,.35);border-radius:8px;padding:6px 8px 2px;background:rgba(6,13,26,.6)}
      #demogame-line-chart .dlc-title{display:flex;justify-content:space-between;gap:8px;font-size:12.5px;color:var(--sub,#7f9bb8);margin-bottom:2px}
      #demogame-line-chart svg{display:block;width:100%;height:auto}
      #demogame-line-chart.debug-hidden{display:none!important}`;
    document.head.appendChild(style);
    panel = document.createElement("div");
    panel.id = "demogame-line-chart";
    panel.className = "control-zone line-shape-zone debug-hidden";
    panel.innerHTML = `<span class="zone-label">倍率線型（即時，64 區間）</span><div class="dlc-body"><div class="dlc-chart"></div></div>`;
    anchor.insertAdjacentElement("beforebegin", panel);
    chart = panel.querySelector(".dlc-chart");
    // 跟 Set RNG 同步顯示／隱藏（各遊戲 Debug Mode 都會切 #set-rng-panel 的 debug-hidden）
    const sync = () => panel.classList.toggle("debug-hidden", anchor.classList.contains("debug-hidden") || anchor.hidden);
    new MutationObserver(sync).observe(anchor, { attributes: true, attributeFilter: ["class", "hidden"] });
    sync();
    document.getElementById("resetBtn")?.addEventListener("click", () => window.demogameLineChart.reset());
    render();
  }

  window.demogameLineChart = {
    record(multiplier) {
      const x = Number(multiplier);
      if (!Number.isFinite(x)) return;
      counts[bucket(Math.max(0, x))] += 1;
      render();
    },
    reset() { counts = new Array(THRESH.length).fill(0); render(); },
    counts: () => counts.slice()
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();

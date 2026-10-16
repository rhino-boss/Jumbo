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
    title.textContent = "Basic Metrics";
    // 有些遊戲切換語言時會把標題寫回「Simulation Stats／模擬統計」，一律改回基本指標（再由共用字典翻譯）
    new MutationObserver(() => {
      const textNode = [...title.childNodes].find((n) => n.nodeType === 3 && n.nodeValue.trim());
      const text = textNode ? textNode.nodeValue.trim() : "";
      if (text === "Basic Metrics" || text === "基本指標") return;
      const btn = title.querySelector(".demogame-zoom-btn");
      title.textContent = "Basic Metrics";
      if (btn) title.appendChild(btn);   // 保留放大按鈕
    }).observe(title, { childList: true, characterData: true, subtree: true });
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

  // 統計 (By Game)（共用）：統計區只留共用五項（總局數、RTP、中獎率、FG 觸發、最高倍數）；
  // 其他遊戲自訂的特殊指標列（或標了 data-by-game 的列）搬到下方獨立的「統計 (By Game)」區，沒有就不建立。
  function setupByGameStats() {
    const stats = document.getElementById("simulation-stats");
    if (!stats || document.getElementById("by-game-stats")) return;
    const SHARED = new Set(["roundCountValue", "rtpValue", "hitRateValue", "fgTriggerValue", "maxMultiplierValue"]);
    const rows = [...stats.querySelectorAll(".simulation-row")].filter((row) =>
      row.hasAttribute("data-by-game") || !SHARED.has(row.querySelector(".s-value")?.id || ""));
    if (!rows.length) return;
    const panel = document.createElement("section");
    panel.id = "by-game-stats";
    panel.className = stats.className;
    const head = stats.querySelector("h3");
    const title = document.createElement(head ? head.tagName : "h3");
    if (head) title.className = head.className;
    title.textContent = "Special Metrics";
    panel.appendChild(title);
    rows.forEach((row) => panel.appendChild(row));   // 搬移節點，id 不變，遊戲照原本方式更新數值
    stats.insertAdjacentElement("afterend", panel);
    const style = document.createElement("style");
    style.textContent = "body.slot-simulator #by-game-stats{margin-top:0;padding:10px 14px;border:1px solid var(--sim-border);border-radius:10px;background:var(--sim-panel)}"
      + "body.slot-simulator #by-game-stats h3{margin:0 0 7px;color:var(--sim-sub);font-size:12px!important;font-weight:700;letter-spacing:.5px;text-transform:none}";
    document.head.appendChild(style);
  }

  setupByGameStats();

  // 版面（共用）：餘額／遊戲／押注模式三區一律放在盤面下方（左欄），右欄只留統計。只搬節點，id 與事件不變。
  function setupPlayerUnderBoard() {
    const shell = document.getElementById("app-shell");
    const board = document.getElementById("grid-panel");
    const right = document.getElementById("right-panel");
    if (!shell || !board || !right) return;
    const ids = ["credit-bar", "play-panel", "bet-mode-panel"];
    const nodes = ids.map((id) => document.getElementById(id)).filter((node) => node && right.contains(node));
    if (!nodes.length) return;
    const under = document.createElement("div");
    under.id = "demogame-under-board";
    shell.appendChild(under);
    const style = document.createElement("style");
    style.textContent = `body.slot-simulator #app-shell.player-under-board{grid-template-rows:auto 1fr;align-items:start}
      body.slot-simulator #app-shell.player-under-board #grid-panel{grid-column:1;grid-row:1}
      body.slot-simulator #app-shell.player-under-board #right-panel{grid-column:2;grid-row:1 / span 2}
      body.slot-simulator #demogame-under-board{grid-column:1;grid-row:2;align-self:start;display:flex;flex-direction:column;gap:10px;min-width:0}
      body.slot-simulator #app-shell:not(.player-under-board) #demogame-under-board{display:none}
      @media (max-width: 760px){body.slot-simulator #app-shell.player-under-board #grid-panel{grid-column:1;grid-row:1}body.slot-simulator #demogame-under-board{grid-column:1;grid-row:2}body.slot-simulator #app-shell.player-under-board #right-panel{grid-column:1;grid-row:3}}`;
    document.head.appendChild(style);
    shell.classList.add("player-under-board");
    nodes.forEach((node) => under.appendChild(node));
  }

  setupPlayerUnderBoard();

  // 狀態列（#strip-bar，共用）：拿掉前面的模式標題（#modeText，基礎遊戲／免費遊戲）；
  // 剩下沒有任何要顯示的特色（連消、倍數、FG 剩餘等都沒顯示）時，整個狀態列隱藏。
  function setupStripBar() {
    const strip = document.getElementById("strip-bar");
    if (!strip) return;
    document.getElementById("modeText")?.classList.add("demogame-removed");
    // 原模式標題的位置（沒有就放最前面）固定顯示 Base Game／Free Game 標籤（依 body.fg-mode，語言跟著 Language 切換）
    const phase = document.createElement("span");
    phase.id = "demogame-phase";
    // 狀態列：場景標籤（Base Game／Free Game）用深藍底淺藍字膠囊，其他資訊一律黃色膠囊（同 H045 Table 標籤）
    if (!document.getElementById("demogame-strip-pill-style")) {
      const pillStyle = document.createElement("style");
      pillStyle.id = "demogame-strip-pill-style";
      pillStyle.textContent = `body #strip-bar .feature-pill:not(.hidden),body #strip-bar #demogame-phase,body #strip-bar #featureStatus:not(:empty){display:inline-flex!important;align-items:center;gap:6px;padding:4px 12px!important;border:0!important;border-radius:20px!important;background:rgba(255,196,61,.18)!important;box-shadow:none!important;color:#ffd36b!important;font:600 12px/1.3 "Segoe UI",system-ui,sans-serif!important;letter-spacing:0!important;text-transform:none!important;white-space:nowrap}
        body #strip-bar .feature-pill .k,body #strip-bar .feature-pill .v{color:#ffd36b!important;font:inherit!important;text-shadow:none!important}
        body #strip-bar #featureStatus:empty{display:none!important}
        body #strip-bar #demogame-phase,body #strip-bar #featureStatus.demogame-scene:not(:empty){background:#0c2240!important;color:#77c7ff!important}`;
      document.head.appendChild(pillStyle);
    }
    const modeText = document.getElementById("modeText");
    if (modeText && strip.contains(modeText)) modeText.before(phase);
    else strip.prepend(phase);
    const updatePhase = () => {
      const zh = /^zh/i.test(document.getElementById("languageSelect")?.value || document.documentElement.lang || "");
      const fg = document.body.classList.contains("fg-mode");
      const text = fg ? (zh ? "免費遊戲" : "Free Game") : (zh ? "基礎遊戲" : "Base Game");
      if (phase.textContent !== text) phase.textContent = text;
    };
    updatePhase();
    new MutationObserver(updatePhase).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    // 特色狀態若是場景名稱（FG、BF、Super Feature 等）也用藍色場景標籤
    const status = document.getElementById("featureStatus");
    const SCENE = /^(base game|free games?|buy feature|super feature|feature buy|bonus|基礎遊戲|主遊戲|免費遊戲|购买特色|購買特色|超級特色|超级特色|免费游戏)(\s*\d+\s*\/\s*\d+)?$/i;
    const updateScene = () => { if (status) status.classList.toggle("demogame-scene", SCENE.test(status.textContent.trim())); };
    if (status) { updateScene(); new MutationObserver(updateScene).observe(status, { childList: true, characterData: true, subtree: true }); }
    document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(updatePhase));
    let busy = false;
    const check = () => {
      if (busy) return;
      busy = true;
      strip.classList.remove("demogame-removed");
      const shown = [...strip.querySelectorAll("*")].some((el) => {
        if (el.closest("#modeText, .demogame-removed") || el.children.length) return false;
        const rects = el.getClientRects();
        if (!rects.length || !rects[0].width) return false;
        return Boolean(el.textContent.trim()) || /^(CANVAS|SVG|IMG)$/i.test(el.tagName);
      });
      strip.classList.toggle("demogame-removed", !shown);
      requestAnimationFrame(() => { busy = false; });
    };
    check();
    new MutationObserver(check).observe(strip, { attributes: true, subtree: true, childList: true, characterData: true, attributeFilter: ["class", "hidden", "style"] });
    setTimeout(check, 0);
  }

  setupStripBar();

  // #controls（Set RNG 等的外層容器）裡沒有可見內容時（例如關閉除錯模式），不佔上下間距
  function setupEmptyZoneSpacing() {
    const zone = document.getElementById("controls");
    if (!zone) return;
    const check = () => {
      const visible = [...zone.children].some((k) => getComputedStyle(k).display !== "none" && !k.hidden);
      zone.classList.toggle("demogame-empty-zone", !visible);
    };
    check();
    new MutationObserver(check).observe(zone, { attributes: true, subtree: true, childList: true, attributeFilter: ["class", "hidden", "style"] });
  }

  setTimeout(setupEmptyZoneSpacing, 0);

  // 押注模式按鈕樣式（共用）：NB／EB 為切換鈕（選取中用「自動」鈕的深綠底白字）；BF／SF 為購買鈕，改用 SPIN 的藍底白字；
  // 所有按鈕字體、大小、字重一致。依按鈕文字判斷是否為購買鈕（含 Buy／Super／購買／超級／BF／SF）。
  function setupBetModeButtonStyle() {
    const panel = document.getElementById("bet-mode-panel");
    if (!panel) return;
    const classify = () => panel.querySelectorAll("button").forEach((btn) => {
      const text = `${btn.textContent || ""}`.trim();
      btn.classList.toggle("demogame-buy-btn", /buy|super|購買|超級|^(BF|SF)(?![A-Za-z])/i.test(text));
    });
    const style = document.createElement("style");
    style.textContent = "body.slot-simulator #app-shell #bet-mode-panel button{font:700 12px/1 \"Segoe UI\",system-ui,sans-serif!important;text-transform:uppercase;letter-spacing:0;color:#fff!important}"
      + "body.slot-simulator #app-shell #bet-mode-panel button.is-active:not(.demogame-buy-btn),body.slot-simulator #app-shell #bet-mode-panel button.active:not(.demogame-buy-btn){background:#007755!important;color:#fff!important;border:0!important;box-shadow:none!important}"
      + "body.slot-simulator #app-shell #bet-mode-panel button.demogame-buy-btn{background:#0077cc!important;color:#fff!important;border:0!important}"
      + "body.slot-simulator #app-shell #bet-mode-panel button.demogame-buy-btn:disabled{opacity:.45}";
    document.head.appendChild(style);
    classify();
    new MutationObserver(classify).observe(panel, { childList: true, subtree: true, characterData: true });
  }

  setupBetModeButtonStyle();

  // 區域標題（共用）：有標題的區域，標題下用一條線隔開（同紀錄區），標題列滿版；遊戲區不顯示標題。
  function setupRegionTitleRule() {
    const play = document.querySelector("#play-panel > .zone-label");
    if (play) play.classList.add("demogame-removed");
    const apply = () => document.querySelectorAll(".control-zone > .zone-label, #simulation-stats > h3, #by-game-stats > h3, #demogame-cumulative-chart > h3").forEach((title) => {
      if (title.classList.contains("demogame-removed")) return;
      const box = getComputedStyle(title.parentElement);
      if (box.display === "none") return;
      const flexGap = /flex|grid/.test(box.display) ? parseFloat(box.rowGap) || 0 : 0;
      Object.assign(title.style, {
        display: "flex", alignItems: "center", boxSizing: "border-box", minHeight: "36px",
        margin: `-${box.paddingTop} -${box.paddingRight} ${Math.max(0, 8 - flexGap)}px -${box.paddingLeft}`,
        padding: `0 ${box.paddingRight} 0 ${box.paddingLeft}`, borderBottom: "1px solid var(--sim-surface)"
      });
      title.dataset.ruled = "1";
    });
    apply();
    const debugInput = document.querySelector("#debugModeInput, #debugInput");
    debugInput?.addEventListener("change", () => setTimeout(apply, 0));
    setTimeout(apply, 0);
  }

  setTimeout(setupRegionTitleRule, 0);

  // 捲軸（共用）：所有區塊不顯示捲軸，但仍可用滑鼠滾輪／觸控上下捲動
  (() => {
    const style = document.createElement("style");
    style.textContent = "*{scrollbar-width:none!important;-ms-overflow-style:none!important}*::-webkit-scrollbar{width:0!important;height:0!important;display:none!important}";
    document.head.appendChild(style);
  })();

  // 放大檢視（共用）：倍率線型（累積、模擬）、紀錄、修改紀錄的標題後加「+」，點下去用彈窗顯示完整內容（倍率線型為大圖）。
  // 彈窗是把原區塊的內容暫時搬進來（數值、按鈕照常即時更新），關閉後搬回原位。
  function setupZoomButtons() {
    const overlay = document.createElement("div");
    overlay.id = "demogame-zoom";
    overlay.innerHTML = `<div class="dz-box" role="dialog" aria-modal="true"><div class="dz-head"><span class="dz-title"></span><span class="dz-actions"><button type="button" class="dz-rotate" aria-label="Rotate" title="旋轉 90°">⟳</button><button type="button" class="dz-close" aria-label="Close">✕</button></span></div><div class="dz-body"></div></div>`;
    document.body.appendChild(overlay);
    const style = document.createElement("style");
    style.textContent = `#demogame-zoom{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.6);padding:24px}
      #demogame-zoom.open{display:flex}
      #demogame-zoom .dz-box{width:min(1200px,96vw);height:92vh;max-height:92vh;display:flex;flex-direction:column;border:1px solid var(--sim-border,#1d4668);border-radius:12px;background:var(--sim-panel,#071528);box-shadow:0 12px 40px rgba(0,0,0,.5)}
      #demogame-zoom .dz-head{display:flex;align-items:center;justify-content:space-between;min-height:40px;padding:0 14px;border-bottom:1px solid var(--sim-surface,#0c2240);color:var(--sim-sub,#5a88aa);font:700 13px/1 "Segoe UI",system-ui,sans-serif;letter-spacing:.5px}
      #demogame-zoom .dz-close{border:0;background:transparent;color:var(--sim-sub,#5a88aa);font:700 16px/1 "Segoe UI",system-ui,sans-serif;cursor:pointer;padding:6px}
      #demogame-zoom .dz-close:hover,#demogame-zoom .dz-rotate:hover{color:#fff}
      #demogame-zoom .dz-actions{display:flex;align-items:center;gap:6px}
      #demogame-zoom .dz-rotate{border:0;background:transparent;color:var(--sim-sub,#5a88aa);font:700 16px/1 "Segoe UI",system-ui,sans-serif;cursor:pointer;padding:6px}
      #demogame-zoom{overflow:hidden}
      #demogame-zoom .dz-box{transition:transform .35s ease;transform-origin:center center}
      #demogame-zoom .dz-body{padding:14px;overflow:auto;flex:1;min-height:0}
      /* 彈窗一開就是最大；紀錄／版本紀錄撐滿剩餘高度，沒資料處維持深色底 */
      #demogame-zoom .dz-body{display:flex;flex-direction:column}
      /* 彈窗內捲到底不帶動背景頁面 */
      #demogame-zoom,#demogame-zoom .dz-body,#demogame-zoom .dz-body *{overscroll-behavior:contain}
      html.demogame-zoom-open,html.demogame-zoom-open body{overflow:hidden!important}
      #demogame-zoom .dz-body > *{flex:0 0 auto}
      #demogame-zoom .dz-body > #liveLogBody,#demogame-zoom .dz-body > #changeLogBody{flex:1 1 auto;min-height:0;overflow:auto}
      #demogame-zoom .dz-body .batch-line-chart svg,#demogame-zoom .dz-body svg{width:100%;height:auto}
      #demogame-zoom .dz-body #liveLogBody,#demogame-zoom .dz-body #changeLogBody{max-height:none!important;height:auto!important;box-sizing:border-box}
      .demogame-zoom-btn{margin-left:auto;flex:0 0 auto;width:22px;height:22px;min-height:0!important;padding:0!important;border:0!important;border-radius:5px;background:var(--sim-surface,#0c2240)!important;color:var(--sim-sub,#5a88aa)!important;font:700 14px/22px "Segoe UI",system-ui,sans-serif!important;text-align:center;cursor:pointer}
      .demogame-zoom-btn:hover{color:#fff!important}
      .demogame-zoom-btn + *{margin-left:0}
      .diagnostic-header:has(> .demogame-zoom-btn){column-gap:6px!important;gap:6px!important}
      .diagnostic-header .demogame-zoom-btn{margin-left:0}
      .batch-line-chart > .dlc-title{justify-content:center!important;position:relative;min-height:24px}
      .batch-line-chart > .dlc-title > .demogame-zoom-btn{position:absolute;right:0;top:50%;transform:translateY(-50%);margin:0}
      .diagnostic-header > button:not(.demogame-zoom-btn):first-of-type{margin-left:auto}
      .diagnostic-header:not(:has(> button:not(.demogame-zoom-btn))) .demogame-zoom-btn{margin-left:auto}`;
    document.head.appendChild(style);
    const body = overlay.querySelector(".dz-body");
    const titleEl = overlay.querySelector(".dz-title");
    let moved = null;   // { parent, nodes, markers }
    // 旋轉 90°：整個彈窗區塊轉 90° 並等比放大到填滿畫面（有轉動動畫），再按一次轉回
    const box = overlay.querySelector(".dz-box");
    // 旋轉時把彈窗寬高對調成「螢幕高 × 螢幕寬」再轉 90°，直接滿版，不用縮小
    const fitRotation = () => {
      if (!overlay.classList.contains("rotated")) {
        Object.assign(box.style, { position: "", left: "", top: "", width: "", height: "", maxHeight: "", transform: "" });
        return;
      }
      Object.assign(box.style, {
        position: "fixed", left: "50%", top: "50%",
        width: `${window.innerHeight - 24}px`, height: `${window.innerWidth - 24}px`, maxHeight: "none",
        transform: "translate(-50%, -50%) rotate(90deg)"
      });
    };
    overlay.querySelector(".dz-rotate").addEventListener("click", () => { overlay.classList.toggle("rotated"); fitRotation(); });
    window.addEventListener("resize", () => { if (overlay.classList.contains("rotated")) fitRotation(); });
    const close = () => {
      overlay.classList.remove("rotated");
      fitRotation();
      if (moved) moved.nodes.forEach((node, i) => moved.markers[i].replaceWith(node));
      moved = null;
      overlay.classList.remove("open");
      body.innerHTML = "";
      document.documentElement.classList.remove("demogame-zoom-open");
    };
    const open = (label, nodes) => {
      if (moved) close();
      const markers = nodes.map((node) => { const m = document.createComment("zoom"); node.replaceWith(m); return m; });
      nodes.forEach((node) => body.appendChild(node));
      moved = { nodes, markers };
      titleEl.textContent = label;
      overlay.classList.add("open");
      // 直式手機放大圖表：一開就轉成橫的（紀錄、版本紀錄維持直式）
      const isChart = nodes.some((node) => node.matches?.("svg, canvas") || node.querySelector?.("svg, canvas"))
        && !nodes.some((node) => node.matches?.("#liveLogBody, #changeLogBody") || node.querySelector?.("#liveLogBody, #changeLogBody"));
      if (isChart && window.innerHeight > window.innerWidth && window.innerWidth < 700) {
        overlay.classList.add("rotated");
        box.style.transition = "none";
        fitRotation();
        void box.offsetWidth;
        box.style.transition = "";
      }
      document.documentElement.classList.add("demogame-zoom-open");   // 鎖住背景捲動
    };
    overlay.querySelector(".dz-close").addEventListener("click", close);
    // 滾輪落在遮罩（彈窗外）或內容已捲到頭時，不讓背景跟著捲
    overlay.addEventListener("wheel", (event) => {
      const scroller = event.target.closest?.("#liveLogBody, #changeLogBody, .dz-body");
      if (!scroller || !overlay.contains(scroller)) { event.preventDefault(); return; }
      const atTop = scroller.scrollTop <= 0 && event.deltaY < 0;
      const atBottom = scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 1 && event.deltaY > 0;
      if (atTop || atBottom) event.preventDefault();
    }, { passive: false });
    overlay.addEventListener("click", (event) => { if (event.target === overlay) close(); });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape" && overlay.classList.contains("open")) close(); });
    const titleText = (title) => [...title.childNodes].filter((n) => !(n.classList?.contains("demogame-zoom-btn")) && !(n.tagName === "BUTTON")).map((n) => n.textContent).join(" ").replace(/\s+/g, " ").trim();
    const attach = () => {
      const titles = document.querySelectorAll("#demogame-cumulative-chart > h3, #batch-simulation .batch-line-chart > .dlc-title, #live-log-wrap > .diagnostic-header, #change-log-wrap > .diagnostic-header");
      titles.forEach((title) => {
        if (title.querySelector(".demogame-zoom-btn") || title.classList.contains("demogame-removed") || title.closest("#demogame-zoom")) return;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "demogame-zoom-btn";
        btn.textContent = "+";
        btn.title = "Enlarge";
        btn.addEventListener("click", (event) => {
          event.stopPropagation();
          // 圖表子標題（模擬面板的倍率線型、消除分布）只放大該子區塊；其他標題放大整個區域內容
          const sub = title.closest(".batch-line-chart, .batch-cascade-list");
          const container = sub || title.parentElement;
          const nodes = [...container.children].filter((node) => node !== title);
          open(titleText(title), nodes);
        });
        title.appendChild(btn);
        if (getComputedStyle(title).display === "block") Object.assign(title.style, { display: "flex", alignItems: "center" });
      });
    };
    attach();
    // 模擬面板的圖表標題會重畫，有變動時補上按鈕（每畫格最多一次）
    let queued = false;
    new MutationObserver(() => {
      if (queued) return;
      queued = true;
      setTimeout(() => { queued = false; attach(); }, 30);
    }).observe(document.body, { childList: true, subtree: true });
  }

  setTimeout(setupZoomButtons, 0);

  // 版本紀錄（共用，#change-log-wrap）：標題統一為「版本紀錄」；內容是專案根目錄 修改紀錄.md 的複本
  // （依版本分節、新到舊、只記調性差異），設定區目前選的版本那一節會標示出來。
  function setupVersionLog() {
    const wrap = document.getElementById("change-log-wrap");
    if (!wrap) return;
    const head = wrap.querySelector(".diagnostic-header");
    if (head) {
      const textNode = [...head.childNodes].find((n) => n.nodeType === 3 && n.nodeValue.trim());
      if (textNode) textNode.nodeValue = "Version Log"; else head.prepend(document.createTextNode("Version Log"));
    }
    const style = document.createElement("style");
    style.textContent = "body.slot-simulator #changeLogBody .change-log-entry.demogame-current-version{border:1px solid var(--sim-accent,#00ddc0)!important}"
      + "body.slot-simulator #changeLogBody .change-log-entry.demogame-current-version h4::after{content:'  ← Current';color:var(--sim-sub,#5a88aa);font-weight:400}";
    document.head.appendChild(style);
    const mark = () => {
      const version = (document.getElementById("versionSelect")?.value || "").trim();
      wrap.querySelectorAll("#changeLogBody .change-log-entry").forEach((entry) => {
        const h = entry.querySelector("h4")?.textContent || "";
        entry.classList.toggle("demogame-current-version", Boolean(version) && h.includes(version));
      });
    };
    mark();
    document.getElementById("versionSelect")?.addEventListener("change", () => setTimeout(mark, 0));
    // 沒有任何調性紀錄就整區不顯示（沒有的東西不顯示）
    const syncEmpty = () => wrap.classList.toggle("demogame-removed", !wrap.querySelector("#changeLogBody li"));
    syncEmpty();
    const body = document.getElementById("changeLogBody");
    if (body) new MutationObserver(syncEmpty).observe(body, { childList: true, subtree: true });
  }

  setTimeout(setupVersionLog, 0);

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
    const W = 900, H = 332, L = 44, R = 12, T = 10, B = 104, n = buckets.labels.length;
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

  // ===== 累積倍率線型（共用，統計區下方）=====
  // 畫面實際遊玩的局：NB 記在 NB、EB 記在 EB，BF／SF 不記錄；依目前押注模式顯示對應的累積圖（標準 64 區間，Y 軸 1%）。
  // 遊戲在一局（含該局 FG）結束時呼叫 window.demogameLineChart.record(總得分 ÷ 押注, "NB"|"EB")；不給模式視為 NB。
  // 顯示模式依押注模式按鈕自動判斷（#extraBetBtn／購買類按鈕 is-active），也可由遊戲呼叫 setMode("NB"|"EB"|"BF")。Reset 清空。
  function setupCumulativeLineChart() {
    const right = document.getElementById("right-panel");
    if (!right || document.getElementById("demogame-cumulative-chart")) return;
    const counts = { NB: new Array(SIMULATION_BUCKETS.labels.length).fill(0), EB: new Array(SIMULATION_BUCKETS.labels.length).fill(0) };
    let forcedMode = null;
    const panel = document.createElement("section");
    panel.id = "demogame-cumulative-chart";
    panel.innerHTML = `<h3 class="demogame-region-title">Multiplier Distribution</h3><div class="batch-line-chart"></div>`;
    right.appendChild(panel);
    const chart = panel.querySelector(".batch-line-chart");
    const style = document.createElement("style");
    style.textContent = "body.slot-simulator #demogame-cumulative-chart{padding:10px 14px 3px;border:1px solid var(--sim-border);border-radius:10px;background:var(--sim-panel)}"
      + "body.slot-simulator #demogame-cumulative-chart .batch-line-chart{margin-top:0;border:0;padding:0;background:transparent}"
      + "body.slot-simulator #demogame-cumulative-chart .dlc-empty{padding:18px 0;text-align:center;color:var(--sim-sub);font-size:12px}";
    document.head.appendChild(style);
    const detectMode = () => {
      if (forcedMode) return forcedMode;
      const active = document.querySelector("#bet-mode-panel .is-active, #bet-mode-panel .active");
      const key = `${active?.id || ""} ${active?.textContent || ""}`;
      if (/extra/i.test(key) || /額外/.test(key)) return "EB";
      if (/buy|super|購買|超級/i.test(key)) return "BF";
      return "NB";
    };
    const names = { NB: "Normal Bet", EB: "Extra Bet", BF: "Buy Feature" };
    const render = () => {
      const mode = detectMode();
      const zh = isZhText();
      const modeName = window.demogameSharedText ? window.demogameSharedText(names[mode]) : names[mode];
      // 區域標題：倍率線型 (押注模式)；圖內不再另放標題
      const head = panel.querySelector(".demogame-region-title");
      if (head) {
        const label = `${zh ? "倍率線型" : "Multiplier Distribution"} (${modeName})`;
        const textNode = [...head.childNodes].find((n) => n.nodeType === 3);
        if (textNode) { if (textNode.nodeValue !== label) textNode.nodeValue = label; } else head.prepend(document.createTextNode(label));
      }
      if (mode === "BF") {
        chart.innerHTML = `<div class="dlc-empty">${zh ? "購買特色不記錄" : "Buy Feature is not recorded"}</div>`;
        return;
      }
      chart.innerHTML = simulationChartSvg(counts[mode], SIMULATION_BUCKETS, 1);
    };
    window.demogameLineChart = {
      cumulative: true,
      record(multiplier, mode = "NB") {
        const x = Number(multiplier);
        const key = String(mode).toUpperCase();
        if (!Number.isFinite(x) || !counts[key]) return;   // BF／SF 不記錄
        counts[key][SIMULATION_BUCKETS.index(Math.max(0, x))] += 1;
        render();
      },
      setMode(mode) { forcedMode = mode ? String(mode).toUpperCase() : null; render(); },
      reset() { counts.NB.fill(0); counts.EB.fill(0); render(); },
      counts: (mode = "NB") => (counts[String(mode).toUpperCase()] || []).slice()
    };
    const modePanel = document.getElementById("bet-mode-panel");
    if (modePanel) new MutationObserver(render).observe(modePanel, { attributes: true, subtree: true, attributeFilter: ["class"] });
    document.getElementById("resetBtn")?.addEventListener("click", () => window.demogameLineChart.reset());
    document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(render, 0));
    setTimeout(render, 0);
  }

  setupCumulativeLineChart();

  // Spin Result 面板已停用（共用）：各遊戲仍可寫入 #lineList 等節點，不會報錯，只是不顯示。
  function hideSpinResult() {
    document.querySelectorAll("#log-wrap, .diagnostic-region").forEach((region) => {
      const head = region.querySelector(".diagnostic-header, h3, #log-header")?.textContent?.trim() || "";
      if (region.id === "log-wrap" || /^spin result$|^spin 結果$|^旋轉結果$/i.test(head)) region.classList.add("demogame-removed");
    });
    if (!document.getElementById("demogame-removed-style")) {
      const style = document.createElement("style");
      style.id = "demogame-removed-style";
      style.textContent = ".demogame-removed{display:none!important}"
        // 統計／統計 (By Game)／模擬的數值一律用白色字（不用強調綠）
        + "body.slot-simulator #simulation-stats .s-value,body.slot-simulator #by-game-stats .s-value,body.slot-simulator #batch-simulation .s-value{color:var(--sim-text)!important}"
        // 遊戲區換行時，速度列拉長到與上一列同寬（從左邊到 + 按鈕）
        // 間距統一 10px：盤面左右欄間距、頁尾（置中）與上方區塊、空的區塊不佔間距
        + "body.slot-simulator #app-shell{gap:10px!important}"
        + "body.slot-simulator .footer-note{margin-top:10px!important;text-align:center!important;color:var(--sim-sub)!important}"
        + "body.slot-simulator .demogame-empty-zone{margin:0!important;padding:0!important;border:0!important;height:0!important;overflow:hidden}"
        // 字體統一：所有按鈕 12px 粗體；設定區的文字標籤同「版本」（12px 一般字重、說明色），下拉選項同按鈕；
        // 有寫名稱的區域標題統一 12px 粗體、說明色、不轉大寫
        + "body.slot-simulator main button,body.slot-simulator #demogameTitleActions>a,body.slot-simulator #demogameTitleActions>button{font-family:\"Segoe UI\",system-ui,sans-serif!important;font-size:12px!important;font-weight:700!important}"
        + "body.slot-simulator #settings-wrap label,body.slot-simulator #settings-wrap .setting-toggle,body.slot-simulator #settings-wrap .setting-toggle span{font-family:\"Segoe UI\",system-ui,sans-serif!important;font-size:12px!important;font-weight:400!important;color:var(--sim-sub)!important}"
        + "body.slot-simulator #settings-wrap select{font-family:\"Segoe UI\",system-ui,sans-serif!important;font-size:12px!important;font-weight:700!important}"
        + "body.slot-simulator .zone-label,body.slot-simulator .diagnostic-header,body.slot-simulator #simulation-stats h3,body.slot-simulator #by-game-stats h3,body.slot-simulator .demogame-region-title,body.slot-simulator .dlc-title,body.slot-simulator .batch-cascade-title,body.slot-simulator .setting-header{font-family:\"Segoe UI\",system-ui,sans-serif!important;font-size:12px!important;font-weight:700!important;color:var(--sim-sub)!important;text-transform:none!important;letter-spacing:.5px!important}"
        // 餘額與押注同樣式（淺色字），得分維持強調色
        + "body.slot-simulator #credit-bar #balanceValue{color:var(--sim-text)!important}"
        + "body.slot-simulator #app-shell #play-panel .play-main-controls{display:flex;flex-wrap:wrap}"
        + "body.slot-simulator #app-shell #play-panel .play-main-controls>.bet-stepper{flex:1 1 200px}"
        + "body.slot-simulator #app-shell #play-panel .play-main-controls>.speed-control{flex:1 1 116px;width:auto;grid-template-columns:auto minmax(48px,1fr) auto}"
        + "body.slot-simulator #app-shell #play-panel .speed-control input{width:100%}";
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

  // ===== 卡片區間選單文字（共用）=====
  // #cardRangeSelect 的選項只顯示區間：去掉前面的編號（#11、Card 11:）與後面的子表標記（（A）），
  // 「a < x ≤ b」統一寫成「(a, b]」、「Win = 0」寫成「(-1, 0]」；option 的 value 不變。
  function cardRangeLabel(text) {
    let t = String(text || "").trim()
      .replace(/^#\d+\s*/, "").replace(/^Card\s*\d+\s*[:：]\s*/i, "")
      .replace(/\s*[（(][A-Z]{1,3}[）)]\s*$/, "").trim();
    let m = /^(-?[\d.]+)\s*<\s*x\s*≤\s*(-?[\d.]+)$/.exec(t);
    if (m) t = `(${m[1]}, ${m[2]}]`;
    if (/^Win\s*=\s*0$/i.test(t)) t = "(-1, 0]";
    return t;
  }
  function normalizeCardRangeOptions() {
    const select = document.getElementById("cardRangeSelect");
    if (!select) return;
    for (const option of select.options) {
      if (option.value === "") continue;   // Auto
      const label = cardRangeLabel(option.textContent);
      if (label && label !== option.textContent) option.textContent = label;
    }
  }
  const cardRangeSelectNode = document.getElementById("cardRangeSelect");
  if (cardRangeSelectNode) {
    normalizeCardRangeOptions();
    new MutationObserver(normalizeCardRangeOptions).observe(cardRangeSelectNode, { childList: true, subtree: true, characterData: true });
  }

  // ===== Set RNG 欄位互斥（共用）=====
  // #set-rng-panel 內的設定（卡片區間、遊戲專屬選單、RNG 欄…）同時只會有一個作用：
  // 設定其中一個時，其他欄位清回預設（選單回第一個／空值選項、輸入欄清空）。設定會一直保留，按重置才清。
  function setupSetRngExclusive() {
    const panel = document.getElementById("set-rng-panel");
    if (!panel) return;
    let syncing = false;
    const fields = () => [...panel.querySelectorAll("select, input[type=text], input:not([type])")];
    const isDefault = (el) => el.tagName === "SELECT" ? el.selectedIndex <= 0 : !el.value.trim();
    const toDefault = (el) => {
      if (isDefault(el)) return;
      if (el.tagName === "SELECT") el.selectedIndex = 0; else el.value = "";
      el.dispatchEvent(new Event(el.tagName === "SELECT" ? "change" : "input", { bubbles: true }));
    };
    const onSet = (event) => {
      const target = event.target;
      if (syncing || !fields().includes(target) || isDefault(target)) return;
      syncing = true;
      try { fields().forEach((el) => { if (el !== target) toDefault(el); }); } finally { syncing = false; }
    };
    panel.addEventListener("change", onSet);
    panel.addEventListener("input", onSet);
  }
  setupSetRngExclusive();

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
    "stats": "統計", "basic metrics": "基本指標", "special metrics": "特殊指標", "simulation stats": "模擬統計", "total rounds": "總局數", "hit rate": "中獎率",
    "fg trigger": "FG 觸發", "fg trigger (observed)": "FG 觸發（實測）", "max multiplier": "最高倍數",
    "set rng": "指定 RNG", "card bg range": "卡片 BG 區間", "card bf range": "卡片 BF 區間", "reel rng": "輪帶 RNG",
    "reset": "重置", "force fg": "強制 FG", "log": "紀錄", "clear": "清除", "simulation": "模擬", "start": "開始",
    "running": "進行中", "retry limit exceeded": "Retry 超限", "scene": "場景", "setting": "設定",
    "debug mode": "除錯模式", "card system": "卡片系統", "image": "圖片", "version": "版本", "language": "語言",
    "help": "說明", "change log": "修改紀錄", "version log": "版本紀錄", "previous": "上一步", "next": "下一步",
    "cascade distribution": "消除分布", "cascades": "消除次數", "history": "歷史紀錄", "report": "報告", "multiplier distribution": "倍率線型", "bg max multiplier": "BG 最大倍數", "fg max multiplier": "FG 最大倍數", "double-click to play offline. no server needed.": "雙擊即可離線遊玩，不需伺服器。"
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
  // BG／FG 最大倍數（共用，併在「統計」區，取代原「最高倍數」列；原獨立的歷史紀錄面板已併入）。
  // 頁面在載入本檔前設 window.DEMOGAME_HISTORY = true 才出現；每局呼叫
  // window.demogameHistory.record({ bg: BG 得分 ÷ 底注, fg: 該局 FG 總得分 ÷ 底注 })，沒有 FG 的遊戲不顯示 FG 列；Reset 清空。
  function setupHistoryPanel() {
    if (!window.DEMOGAME_HISTORY || document.getElementById("historyBgMax")) return;
    const stats = document.getElementById("simulation-stats");
    if (!stats) return;
    const hasFg = Boolean(document.getElementById("fgTriggerValue"));
    const makeRow = (label, id) => {
      const row = document.createElement("div");
      row.className = "simulation-row";
      row.innerHTML = `<span class="s-label">${label}</span><span class="s-value hi" id="${id}">x0</span>`;
      return row;
    };
    const anchor = document.getElementById("maxMultiplierValue")?.closest(".simulation-row");
    const rows = [makeRow("BG Max Multiplier", "historyBgMax")];
    if (hasFg) rows.push(makeRow("FG Max Multiplier", "historyFgMax"));
    if (anchor) anchor.after(...rows); else stats.append(...rows);
    anchor?.classList.add("demogame-removed");   // 原「最高倍數」與 BG／FG 最大倍數重複，隱藏（遊戲仍可照常寫入）
    let bgMax = 0, fgMax = 0;
    const fmt = (v) => `x${Number(v.toFixed(2))}`;
    const render = () => {
      const bg = document.getElementById("historyBgMax"), fg = document.getElementById("historyFgMax");
      if (bg) bg.textContent = fmt(bgMax);
      if (fg) fg.textContent = fmt(fgMax);
    };
    window.demogameHistory = {
      record({ bg = 0, fg = 0 } = {}) {
        if (Number.isFinite(Number(bg))) bgMax = Math.max(bgMax, Number(bg));
        if (Number.isFinite(Number(fg))) fgMax = Math.max(fgMax, Number(fg));
        render();
      },
      reset() { bgMax = 0; fgMax = 0; render(); }
    };
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
    style.textContent = `#demogameTitleActions{position:absolute;right:12px;top:50%;transform:translateY(-50%);display:flex;gap:1px;align-items:center}
      #demogameTitleActions > a, #demogameTitleActions > button{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;
        height:30px;min-height:0;min-width:0;width:auto;margin:0;padding:0 4px;border-radius:7px;border:none;
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

    /* Help 版式（2026-10-16）：標題由大到小、區塊以分隔線區隔、規則前方塊符號、賠率表為符號卡片格 */
    body #helpDialog #helpContent .help-section,
    body #helpDialog #helpContent .help-card,
    body #helpDialog #helpContent .help-standard-card {
      margin: 0;
      padding: 18px 8px;
      border: 0;
      border-bottom: 1px solid #1d4668;
      border-radius: 0;
      background: transparent;
    }
    body #helpDialog #helpContent > :last-child { border-bottom: 0; }
    body #helpDialog #helpContent .help-section-title,
    body #helpDialog #helpContent .help-card > h3 {
      margin: 0 0 14px;
      color: #00ddc0;
      font: 700 20px/1.35 "Segoe UI", Arial, sans-serif;
      text-align: center;
    }
    body #helpDialog #helpContent .help-group-title {
      margin: 18px 0 10px;
      color: #77c7ff;
      font: 700 15px/1.35 "Segoe UI", Arial, sans-serif;
      text-align: center;
    }
    body #helpDialog #helpContent .help-rule {
      position: relative;
      margin: 4px 0;
      padding: 0 0 0 18px;
      border-radius: 0;
      background: transparent;
      color: #9fd9ff;
      font-size: 13px;
    }
    body #helpDialog #helpContent .help-rule::before {
      content: "";
      position: absolute;
      left: 4px;
      top: .62em;
      width: 6px;
      height: 6px;
      background: #77c7ff;
    }
    body #helpDialog #helpContent .help-paytable-wrap { background: transparent; padding: 0; }
    body #helpDialog #helpContent .help-sym-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 22px 16px;
      margin: 16px 0 4px;
    }
    body #helpDialog #helpContent .help-sym-card {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      min-width: 0;
    }
    body #helpDialog #helpContent .help-sym-tile {
      flex: 0 0 auto;
      display: grid;
      place-items: center;
      width: 72px;
      height: 72px;
      border: 1px solid #1d3a56;
      border-radius: 8px;
      background: #06101d;
      color: #cfe6ff;
      font: 400 18px/1 Consolas, "Segoe UI", monospace;
    }
    body #helpDialog #helpContent .help-sym-tile.has-art {
      width: 88px;
      height: 88px;
      border: 0;
      background: transparent;
    }
    body #helpDialog #helpContent .help-sym-tile img { width: 100%; height: 100%; object-fit: contain; }
    body #helpDialog #helpContent .help-sym-tile.is-scatter {
      border-color: #7fd8ff;
      background: radial-gradient(circle at 50% 45%, #e8a542 0%, #b8681c 60%, #8a4a12 100%);
      color: #fff3d6;
    }
    body #helpDialog #helpContent .help-sym-tile.is-wild {
      border-color: #00ddc0;
      background: #0b3a3a;
      color: #c8fff4;
    }
    body #helpDialog #helpContent .help-sym-pays {
      min-width: 92px;
      font: 600 14px/1.5 "Segoe UI", Arial, sans-serif;
      white-space: nowrap;
    }
    body #helpDialog #helpContent .help-sym-count { color: #9fd9ff; }
    body #helpDialog #helpContent .help-sym-value { color: #ffd34d; }
    @media (max-width: 640px) {
      body #helpDialog #helpContent .help-sym-grid { gap: 16px 8px; }
      body #helpDialog #helpContent .help-sym-card { gap: 8px; }
      body #helpDialog #helpContent .help-sym-tile { width: 56px; height: 56px; font-size: 16px; }
      body #helpDialog #helpContent .help-sym-tile.has-art { width: 64px; height: 64px; }
      body #helpDialog #helpContent .help-sym-pays { min-width: 0; font-size: 12px; }
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

  function buildMatrixTable(items, headerText = "") {
    const rows = items.map((item) => item.textContent.split(/\s+·\s+/).map((cell) => cell.replace(/[\[\]{}]/g, "").trim()));
    if (rows.length < 2 || rows.some((row) => row.length < 3)) return null;
    const width = rows[0].length;
    if (rows.some((row) => row.length !== width)) return null;
    const bet = Number(currentBet().replace(/,/g, ""));

    const table = document.createElement("table");
    table.className = "help-paytable";
    // 表頭沿用上一列標題（如「符號 · 5 連 · 4 連 · 3 連」）；沒有才預設 3、4、5…
    const named = headerText.split(/\s+·\s+/).slice(1).map((cell) => cell.trim());
    const heads = named.length === width - 1 ? named : Array.from({ length: width - 1 }, (_, index) => String(index + 3));
    table.innerHTML = `<thead><tr><th>Symbol</th>${heads.map((head) => `<th>${head}</th>`).join("")}</tr></thead>`;
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
      const prev = grid.previousElementSibling;
      const headerText = prev?.matches(".help-group-title") && prev.textContent.includes("·") ? prev.textContent : "";
      const table = buildPivotTable(items) || buildMatrixTable(items, headerText);
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

  // 賠率表改成「符號圖 + 由大到小的 N - 派彩」卡片格：有圖用遊戲提供的 window.DEMOGAME_SYMBOL_ART，
  // 沒圖（或 Image 關閉）用盤面同款的代號方格（2026-10-16）
  function symbolTile(code) {
    const tile = document.createElement("div");
    tile.className = "help-sym-tile";
    const src = window.DEMOGAME_SYMBOL_IMAGES_ENABLED !== false ? window.DEMOGAME_SYMBOL_ART?.[code] : "";
    if (src) {
      const img = document.createElement("img");
      img.src = src;
      img.alt = code;
      img.draggable = false;
      img.addEventListener("error", () => { tile.classList.remove("has-art"); img.replaceWith(document.createTextNode(code)); });
      tile.classList.add("has-art");
      tile.appendChild(img);
    } else {
      tile.textContent = code;
      const sym = String(code).toUpperCase().match(/^(M\d+|W\d|WW\d?|WILD|C\d|SC|TE|10|A|K|Q|J)/);
      if (sym) tile.dataset.dgSym = sym[1].replace(/^WILD$/, "WW");   // 配色同盤面無圖符號（見「無圖符號樣式統一」）
      if (/^(C\d|SC)$/i.test(code)) tile.classList.add("is-scatter");
      else if (/^(W\w*|WILD)$/i.test(code)) tile.classList.add("is-wild");
    }
    return tile;
  }

  function buildSymbolGrid(card) {
    for (const table of card.querySelectorAll("table.help-paytable, table.paytable")) {
      const data = readHtmlPaytable(table);
      if (!data) continue;
      const counts = data.headers.slice(1).map((header, index) => ({
        index, label: header.replace(/\s*(連|连|oak|of a kind)\s*/gi, "").trim() || header
      })).sort((a, b) => countOrder(b.label) - countOrder(a.label));
      const grid = document.createElement("div");
      grid.className = "help-sym-grid";
      for (const row of data.rows) {
        const code = row[0].replace(/[\[\]{}]/g, "").trim();
        if (!code) continue;
        const item = document.createElement("div");
        item.className = "help-sym-card";
        item.appendChild(symbolTile(code));
        const list = document.createElement("div");
        list.className = "help-sym-pays";
        for (const count of counts) {
          const value = String(row[count.index + 1] || "").trim();
          if (!value || /^[—–-]$/.test(value)) continue;
          const line = document.createElement("div");
          line.innerHTML = `<span class="help-sym-count"></span> - <span class="help-sym-value"></span>`;
          line.firstElementChild.textContent = count.label;
          line.lastElementChild.textContent = value;
          list.appendChild(line);
        }
        item.appendChild(list);
        grid.appendChild(item);
      }
      const wrap = table.closest(".help-paytable-wrap") || table;
      wrap.replaceWith(grid);
    }
  }

  // 規則列前的 ▪／• 改由 CSS 方塊符號顯示，避免重複
  function stripRuleBullets(card) {
    for (const rule of card.querySelectorAll(".help-rule")) {
      const target = rule.querySelector(".help-rule-zh, .help-rule-en") || rule;
      if (target.children.length) continue;
      const text = target.textContent;
      const clean = text.replace(/^\s*[▪•·]\s*/, "");
      if (clean !== text) target.textContent = clean;
    }
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
          || Boolean(card.querySelector("table.paytable, table.help-paytable"));
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
          buildSymbolGrid(card);
          const table = card.querySelector("table.paytable");
          if (table) {
            const firstHeader = table.querySelector("th");
            if (firstHeader && firstHeader.textContent !== "Symbol") firstHeader.textContent = "Symbol";
          }
          const firstGridCell = card.querySelector(".help-payout-row:first-child .help-payout-cell:first-child");
          if (firstGridCell && firstGridCell.textContent !== "Symbol") firstGridCell.textContent = "Symbol";
        }
        normalizeLooseRuleGrids(card);
        stripRuleBullets(card);
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
  // Image 開關切換時，若 Help 開著就重新開一次讓賠率表換圖／方格
  document.addEventListener("demogame:image-change", () => { const d = document.getElementById("helpDialog"); if (d?.open) { d.close(); document.getElementById("helpBtn")?.click(); } });
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
    // 互斥清除交給「Set RNG 欄位互斥（共用）」：它會對被清的欄位發出 change／input 事件，遊戲才能同步狀態
    rngInput?.addEventListener("input", () => actions.rngChanged?.());
    cardRange?.addEventListener("change", () => actions.rngChanged?.());

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

  if (window.demogameLineChart?.cumulative) return;   // 已由統計區下方的累積倍率線型接手
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

// 連線遊戲得分連線（共用，2026-10-16）：window.demogameWinLines.draw(容器, [[格子元素…], …])
// 在容器上疊一層 SVG，依序連起每條得分線的格子中心；容器重畫（innerHTML）時圖層會跟著消失，每次 render 後重畫即可。
(() => {
  "use strict";
  const COLORS = ["#ffd86a", "#5fe3a1", "#33bbff", "#ff7ad9", "#ff9f43", "#b48cff", "#ff6b6b", "#7ce8ff"];
  const style = document.createElement("style");
  style.textContent = `.demogame-win-lines{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:6;overflow:visible}
    .demogame-win-lines polyline{fill:none;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 0 3px rgba(0,0,0,.85))}`;
  document.head.appendChild(style);
  let last = null;
  const draw = (container, lines) => {
    if (!container) return;
    container.querySelector(":scope > .demogame-win-lines")?.remove();
    last = { container, lines };
    const valid = (lines || []).map((cells) => (cells || []).filter(Boolean)).filter((cells) => cells.length >= 2);
    if (!valid.length) return;
    if (getComputedStyle(container).position === "static") container.style.position = "relative";
    const box = container.getBoundingClientRect();
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "demogame-win-lines");
    svg.setAttribute("viewBox", `0 0 ${container.clientWidth} ${container.clientHeight}`);
    valid.forEach((cells, index) => {
      const points = cells.map((cell) => {
        const r = cell.getBoundingClientRect();
        return `${(r.left + r.width / 2 - box.left - container.clientLeft).toFixed(1)},${(r.top + r.height / 2 - box.top - container.clientTop).toFixed(1)}`;
      }).join(" ");
      const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      line.setAttribute("points", points);
      line.setAttribute("stroke", COLORS[index % COLORS.length]);
      svg.appendChild(line);
    });
    container.appendChild(svg);
  };
  window.addEventListener("resize", () => {
    if (last?.container.querySelector(":scope > .demogame-win-lines")) draw(last.container, last.lines);
  });
  window.demogameWinLines = { draw, clear: (container) => draw(container, []) };
})();

// Previous／Next 樣式統一（共用，2026-10-16）：兩顆同款，覆蓋各遊戲原本一藍一綠的寫法
(() => {
  "use strict";
  const style = document.createElement("style");
  style.textContent = `body #previousStepBtn,body #nextStepBtn{height:34px!important;padding:0 12px!important;border:1px solid #1d4668!important;border-radius:6px!important;background:#102b49!important;color:#dceeff!important;box-shadow:none!important;font:700 12px/1 "Segoe UI",system-ui,sans-serif!important;letter-spacing:0!important;text-transform:none!important;white-space:nowrap;cursor:pointer}
    body #previousStepBtn:hover:not(:disabled),body #nextStepBtn:hover:not(:disabled){border-color:#59ddff!important;color:#fff!important}
    body #previousStepBtn:disabled,body #nextStepBtn:disabled{opacity:.35!important;cursor:default}`;
  document.head.appendChild(style);
})();

// 無圖符號樣式統一（共用，2026-10-16）：沒有符號美術或 Image 關閉時，所有遊戲的代號格同一套——
// M 獎與字獎（A／K／Q／J／10）都有底版，M1～M6 底色各不同、字獎深藍底；C1／C2／SC 金色、Wild 綠色；
// 金框格一律改成亮金漸層並覆蓋原本底色。中獎、轉換等狀態格不覆蓋。
// 依格子顯示的代號自動標 data-dg-sym（不靠各遊戲的 class 命名）。
(() => {
  "use strict";
  const LABEL = ".slot-symbol-label, .symbol-code, .h019-glyph, .sym-code-label";
  const codeOf = (cell) => {
    const label = [...cell.querySelectorAll(LABEL)].find((node) => node.textContent.trim() && !node.hidden && node.style.display !== "none");
    const text = (label || cell).textContent.trim().toUpperCase();
    const match = text.match(/^(M\d+|W\d|WW\d?|WILD|C\d|SC|TE|10|A|K|Q|J)/);
    return match ? match[1].replace(/^WILD$/, "WW") : "";
  };
  const tag = () => {
    for (const cell of document.querySelectorAll("#board .cell")) {
      const code = cell.matches(".has-symbol-art, .sym-digit") ? "" : codeOf(cell);   // H014 數字格不套用
      if ((cell.dataset.dgSym || "") !== code) {
        if (code) cell.dataset.dgSym = code; else delete cell.dataset.dgSym;
      }
    }
  };
  // MutationObserver 回呼在畫面重繪前執行：同步標記，避免 Spin 時先畫成原樣式再換色而閃爍
  let tagging = false;
  const schedule = () => { if (tagging) return; tagging = true; try { tag(); } finally { tagging = false; } };
  const start = () => {
    const board = document.getElementById("board");
    if (!board) return;
    tag();
    new MutationObserver(schedule).observe(board, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();

  const free = ":not(.has-symbol-art):not(.hit):not(.convert):not(.wild-mark):not(.h014-hit):not(.h020-hit):not(.symbol-cleared):not(.empty):not(.symbol-empty):not(:has(> .tile))";
  // Help 賠率表的代號方格（沒圖時）與盤面同一套配色
  const base = `:is(body #board .cell[data-dg-sym]${free}, body #helpDialog #helpContent .help-sym-tile[data-dg-sym]:not(.has-art))`;
  const gold = `body #board .cell:is(.gold,.special-gold)${free}`;
  const label = `:is(${LABEL})`;
  // M 獎：同亮度、不同色相的低彩度漸層，字獎深藍；上緣一條淡高光，整體與金框同一套質感
  const tone = (code, top, bottom, border) => `${base}[data-dg-sym="${code}"]:not(.gold):not(.special-gold){background:linear-gradient(180deg,${top} 0%,${bottom} 100%)!important;border-color:${border}!important}`;
  const style = document.createElement("style");
  style.textContent = `${base}{background:linear-gradient(180deg,#0c1828 0%,#060d1a 100%)!important;border:1.6px solid rgba(70,120,170,.42)!important;border-radius:8px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)!important;color:#d8e8f4!important}
    ${tone("M1", "#5b2733", "#33141c", "#9c5664")}
    ${tone("M2", "#3f2f68", "#221840", "#7c68b8")}
    ${tone("M3", "#1f4d3e", "#112b23", "#4f957d")}
    ${tone("M4", "#24426e", "#132643", "#5a85bf")}
    ${tone("M5", "#1d4c55", "#0f2b31", "#4a959d")}
    ${tone("M6", "#5a2f50", "#321a2d", "#a0628f")}
    ${tone("M7", "#5a4024", "#322312", "#a07a50")}
    ${tone("M8", "#3f4a2a", "#232a16", "#7f8f55")}
    ${base}:is([data-dg-sym^="C"],[data-dg-sym="SC"]):not(.gold):not(.special-gold){background:linear-gradient(180deg,#f0b4ff 0%,#c060e8 45%,#7128a8 100%)!important;border:1.6px solid #e6a2ff!important;box-shadow:inset 0 1px 0 rgba(255,240,255,.55)!important;color:#fff6ff!important}
    ${base}:is([data-dg-sym^="C"],[data-dg-sym="SC"]):not(.gold):not(.special-gold) ${label}{text-shadow:0 1px 2px rgba(50,0,70,.6)!important}
    ${base}:is([data-dg-sym^="W"]):not(.gold):not(.special-gold){background:linear-gradient(180deg,#22706a 0%,#0f3d3a 100%)!important;border-color:#3fd6c4!important;color:#d6fff8!important}
    ${gold}{background:linear-gradient(180deg,#f8dc8c 0%,#e2ac44 45%,#b67a16 100%)!important;border:1.6px solid #f1c35a!important;border-radius:8px!important;box-shadow:inset 0 1px 0 rgba(255,250,220,.55)!important;color:#fff6de!important}
    ${gold} ${label}{color:inherit!important;text-shadow:0 1px 2px rgba(60,30,0,.55)!important}
    :is(${base},${gold}):not(.sym-digit) ${label}{font-family:Consolas,"Courier New",monospace!important;font-weight:400!important;font-size:21px!important;line-height:1!important}
    ${base}:not(.sym-digit) ${label}{color:inherit!important;text-shadow:none!important}`;
  document.head.appendChild(style);
})();

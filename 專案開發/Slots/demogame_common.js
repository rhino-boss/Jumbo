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
    // 2026-11-20：選單只列系列（A／B，小中大 Bet 依押注自動切換）時，直接顯示該字母
    const seriesOnly = String(option?.textContent || "").trim();
    if (/^[A-Za-z]$/.test(seriesOnly)) return seriesOnly.toUpperCase();
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
    // 2026-11-20 使用者：選項名稱帶產線編號（D:\SVN\Math_Release\IGaming\說明書\ID對照表.txt：01 菲律賓主流、01_2 菲律賓 landbase 轉製、02 美國、03 墨西哥）。
    // 遊戲宣告 window.DEMOGAME_PRODUCT_LINE（例 "01"）才啟用；多產線的遊戲在原生 <option> 加 data-line。
    // 啟用後：自然機率＝「{產線}-{A/B}-Base」、卡片開＝「{產線}-{Config}」（例 01-A、01-92A），依產線編號排序，同產線內 Base 在前（2026-11-20 改名：產線編號放前面）。
    // A、B 共用同一份自然機率（只差卡片）時，遊戲宣告 window.DEMOGAME_SHARED_BASE = true，就只列 A 的 Base、不列 B 的 Base。
    // 沒宣告的遊戲維持舊名稱（Base／BaseA／92A…），避免還在讀選項文字的遊戲受影響。
    const lineDefault = String(window.DEMOGAME_PRODUCT_LINE || "").trim();
    const useLine = Boolean(lineDefault);
    const lineOf = (configOption) => String(configOption?.dataset?.line || lineDefault).trim();
    const variantOf = (configOption) => {
      const name = normalizeConfigName(configOption);
      if (/^[A-Z]$/.test(name)) return name;
      const found = (name.match(/^\d+([A-Z])/) || ["", ""])[1];
      return found || (useLine ? "A" : "");
    };
    const currentConfig = configOptions.find((option) => option.selected) || configOptions[0];
    const addOption = (configOption, profile, text, selected) => {
      const option = document.createElement("option");
      option.value = JSON.stringify([configOption.value, profile.value]);
      option.textContent = text;
      option.selected = selected;
      combined.appendChild(option);
    };
    // 卡片開只用 Oldhand，不列 Newbie；選項只寫 Config 代號（例：A、92A、94A、92A_BET100）
    const oldhand = profileOptions.find((profile) => profile.name === "Oldhand") || profileOptions.find((profile) => profile.value !== "off");
    const lines = useLine ? [...new Set(configOptions.map(lineOf))].sort() : [""];
    for (const line of lines) {
      const inLine = useLine ? configOptions.filter((option) => lineOf(option) === line) : configOptions;
      let variants = [...new Set(inLine.map(variantOf))].sort();
      if (useLine && window.DEMOGAME_SHARED_BASE && variants.length > 1) variants = variants.slice(0, 1);
      for (const variant of variants) {
        const sameVariant = inLine.filter((option) => variantOf(option) === variant);
        const target = sameVariant.includes(currentConfig) ? currentConfig : sameVariant[0];
        const text = useLine ? `${line}-${variant}-Base` : (variants.length > 1 ? `Base${variant}` : "Base");
        addOption(target, offOption, text, selectedProfile === "Off" && target === currentConfig);
      }
      if (oldhand) {
        for (const configOption of inLine) {
          const name = normalizeConfigName(configOption);
          // 帶產線時卡片開寫「{產線}-{A/B}」（例 92A 只有一份 → 01-A）；同系列若還列了多份 RTP（92A／94A…）才保留完整代號避免同名
          const variant = variantOf(configOption);
          const isDemo = /demo/i.test(`${configOption.value} ${configOption.textContent}`);   // 例 120A_Demo → 01-A-Demo（2026-11-20 使用者）
          const unique = inLine.filter((option) => variantOf(option) === variant && !/demo/i.test(`${option.value} ${option.textContent}`)).length === 1;
          const lineText = isDemo ? `${line}-${variant || "A"}-Demo` : `${line}-${unique && variant ? variant : name}`;
          addOption(configOption, oldhand, useLine ? lineText : name,
            configOption === currentConfig && selectedProfile !== "Off");
        }
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

  // 符號圖片一律開啟（原「Image」開關已改成「符號ID」，2026-11-20 使用者要求）；圖片載入失敗才退回文字。
  function ensureSymbolImages() {
    const adapter = getImageToggleAdapter();
    if (!adapter) return;
    const enabled = adapter.defaultEnabled !== false;
    adapter.setEnabled(enabled, { initial: true });
    window.DEMOGAME_SYMBOL_IMAGES_ENABLED = enabled;
    if (enabled) preloadAdapterImages(adapter, () => {
      adapter.setEnabled(false, { initial: false });
      window.DEMOGAME_SYMBOL_IMAGES_ENABLED = false;
    });
  }

  // ===== 符號ID（共用，Setting 勾選框）=====
  // 開啟後在盤面每個符號正中間疊一個代號（M1、M2、A、K…），方便對照輪帶與 Log。
  // 代號來源依序：window.DEMOGAME_SYMBOL_ID(cell) → data-symbol-id → .symbol-code 文字 → 符號圖片 alt → .slot-symbol-label／.code 文字 → class symbol-xxx。
  function getCellSymbolId(cell) {
    const custom = window.DEMOGAME_SYMBOL_ID;
    if (typeof custom === "function") {
      const v = custom(cell);
      if (v != null) return String(v);
    }
    const pick = (sel) => [...cell.querySelectorAll(sel)].find((el) => !el.closest(".dg-symbol-id"));
    const tagged = cell.dataset.symbolId || pick("[data-symbol-id]")?.dataset.symbolId;
    if (tagged) return tagged;
    const code = pick(".symbol-code")?.textContent.trim();
    if (code) return code;
    const alt = pick("img[alt]")?.getAttribute("alt").trim();
    if (alt) return alt;
    const label = pick(".slot-symbol-label, .code")?.textContent.trim();
    if (label) return label;
    const cls = [...cell.classList].find((c) => /^symbol-[a-z0-9]+$/i.test(c) && !/^symbol-(art|cleared|low|high)$/i.test(c));
    return cls ? cls.slice(7).toUpperCase() : "";
  }

  function ensureSymbolIdToggle() {
    const board = document.getElementById("board");
    const settingsBody = document.querySelector("#settings-wrap > .setting-body");
    if (!board || !settingsBody || document.getElementById("symbolIdInput")) return;

    const label = document.createElement("label");
    label.className = "setting-toggle";
    label.htmlFor = "symbolIdInput";
    label.innerHTML = '<input id="symbolIdInput" type="checkbox"><span>Show Symbol ID</span>';
    const input = label.querySelector("input");
    const cardLabel = document.getElementById("cardSystemInput")?.closest("label");
    if (cardLabel?.parentElement === settingsBody) cardLabel.insertAdjacentElement("afterend", label);
    else settingsBody.insertBefore(label, settingsBody.querySelector(".config-control"));

    let observer = null;
    let queued = false;
    const paint = () => {
      queued = false;
      board.querySelectorAll(".cell").forEach((cell) => {
        const id = getCellSymbolId(cell);
        let tag = cell.querySelector(":scope > .dg-symbol-id");
        if (!id) { tag?.remove(); return; }
        if (!tag) {
          if (getComputedStyle(cell).position === "static") cell.style.position = "relative";
          tag = document.createElement("span");
          tag.className = "dg-symbol-id";
          // 樣式直接寫在元素上（不依賴 css 版號快取）
          tag.style.cssText = "position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);z-index:50;pointer-events:none;" +
            "padding:1px 6px;border-radius:6px;background:rgba(0,0,0,.72);color:#fff;font:700 14px/1.2 system-ui,sans-serif;" +
            "letter-spacing:.02em;white-space:nowrap;text-shadow:none;margin:0;";
          cell.appendChild(tag);
        }
        if (tag.textContent !== id) tag.textContent = id;
      });
    };
    const schedule = () => { if (!queued) { queued = true; requestAnimationFrame(paint); } };
    const apply = () => {
      document.body.classList.toggle("dg-symbol-id-on", input.checked);
      if (input.checked) {
        paint();
        if (!observer) {
          observer = new MutationObserver((list) => {
            const own = list.every((m) => m.target.closest?.(".dg-symbol-id") ||
              [...m.addedNodes, ...m.removedNodes].every((n) => n.classList?.contains("dg-symbol-id")) && (m.addedNodes.length || m.removedNodes.length));
            if (!own) schedule();
          });
          observer.observe(board, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class", "alt", "src"] });
        }
      } else {
        observer?.disconnect();
        observer = null;
        board.querySelectorAll(".dg-symbol-id").forEach((n) => n.remove());
      }
    };

    try { input.checked = localStorage.getItem("slotDemoSymbolId") === "on"; } catch (_) {}
    input.addEventListener("change", () => {
      try { localStorage.setItem("slotDemoSymbolId", input.checked ? "on" : "off"); } catch (_) {}
      apply();
    });
    apply();
  }

  ensureCardSystemToggle();
  ensureSymbolImages();
  ensureSymbolIdToggle();
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
      + "body.slot-simulator #app-shell #bet-mode-panel button.demogame-buy-btn:disabled{opacity:.45}"
      // 2026-11-12 使用者：所有遊戲的押注模式按鈕統一跟 H032 一樣 —— 一排排開（每顆 88px、間距 6px、高 34px 同 SPIN），兩行字（名稱 11px＋倍數另起一行 9px）
      + "body.slot-simulator #app-shell #bet-mode-panel .zone-body{display:flex!important;flex-wrap:nowrap!important;gap:6px!important}"
      + "body.slot-simulator #app-shell #bet-mode-panel .zone-body button{flex:0 1 88px!important;min-width:0!important;width:88px!important;height:34px!important;min-height:0!important;padding:2px 4px!important;font-size:11px!important;line-height:1.3!important;text-transform:none!important;white-space:normal!important;overflow:hidden}"
      + "body.slot-simulator #app-shell #bet-mode-panel .mode-price{display:block;margin-top:1px;font-size:9px;line-height:1.2;opacity:.85}"
      // 未開放的模式：disabled＋.is-locked，不能按、直接壓黑（2026-11-12 使用者，同 H032）；不半透明、不被購買鈕藍底蓋掉
      + "body.slot-simulator #app-shell #bet-mode-panel button.is-locked,body.slot-simulator #app-shell #bet-mode-panel button.is-locked.demogame-buy-btn{cursor:not-allowed;opacity:1!important;background:#0b111a!important;color:#4a5563!important;box-shadow:none!important}";
    document.head.appendChild(style);
    // 按鈕文字「名稱 (2x)」拆成名稱＋倍數小字（遊戲切語言重寫文字時會再拆一次）；已有 .mode-price 的不動
    const splitPrice = () => panel.querySelectorAll(".zone-body button").forEach((btn) => {
      if (btn.querySelector(".mode-price") || btn.children.length) return;
      const m = (btn.textContent || "").trim().match(/^(.+?)\s*[(（]\s*([\d.,]+\s*[xX×])\s*[)）]$/);
      if (!m) return;
      btn.textContent = m[1];
      const price = document.createElement("span");
      price.className = "mode-price";
      price.textContent = `(${m[2].replace(/\s+/g, "").replace(/X$/, "x")})`;
      btn.appendChild(price);
    });
    classify();
    splitPrice();
    new MutationObserver(() => { classify(); splitPrice(); }).observe(panel, { childList: true, subtree: true, characterData: true });
  }

  setupBetModeButtonStyle();

  // 區域標題（共用）：有標題的區域，標題下用一條線隔開（同紀錄區），標題列滿版；遊戲區不顯示標題。
  function setupRegionTitleRule() {
    const play = document.querySelector("#play-panel > .zone-label");
    if (play) play.classList.add("demogame-removed");
    const apply = () => document.querySelectorAll(".control-zone > .zone-label, #simulation-stats > h3, #by-game-stats > h3, #demogame-overview > h3, #demogame-cumulative-chart > h3").forEach((title) => {
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
      #demogame-zoom:not(.rotated) .dz-box{height:auto}
      /* 紀錄彈窗一打開就固定高度（不隨行數慢慢長高），行數多時在框內捲動 */
      #demogame-zoom:not(.rotated) .dz-box:has(#liveLogBody){height:min(640px,80vh)}
      /* 彈窗高度貼齊內容（最高 92vh）；內容超過時紀錄／版本紀錄在框內捲動 */
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
      .diagnostic-header:not(:has(> button:not(.demogame-zoom-btn))) .demogame-zoom-btn{margin-left:auto}
      /* 消除分布也有「+」（2026-11-27 使用者），按鈕位置同倍率線型 */
      .batch-cascade-list > .batch-cascade-title{position:relative;min-height:24px}
      .batch-cascade-list > .batch-cascade-title > .demogame-zoom-btn{position:absolute;right:0;top:50%;transform:translateY(-50%);margin:0}
      /* 圖表放大彈窗：跟模擬區圖表卡片同一套深色底（2026-11-27 使用者） */
      #demogame-zoom.dz-chart .dz-box{background:#030b17;border:1px solid rgba(120,170,230,.16);border-radius:12px;box-shadow:inset 0 2px 10px rgba(0,0,0,.6),0 12px 40px rgba(0,0,0,.6)}
      #demogame-zoom.dz-chart .dz-head{min-height:52px;padding:8px 14px 0 20px;border-bottom:0;color:var(--sim-text,#b0d4f0);font:700 15px/1.3 "Segoe UI","Microsoft JhengHei",system-ui,sans-serif;letter-spacing:.5px}
      #demogame-zoom.dz-chart .dz-actions{gap:8px}
      #demogame-zoom.dz-chart .dz-rotate,#demogame-zoom.dz-chart .dz-close{width:28px;height:28px;padding:0;border-radius:6px;background:var(--sim-surface,#0c2240);color:var(--sim-sub,#5a88aa);font-size:15px;line-height:28px;text-align:center}
      #demogame-zoom.dz-chart .dz-body{padding:6px 20px 18px}`;
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
      overlay.classList.remove("open", "dz-chart");
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
      // 彈窗高度貼齊內容、最高 92vh，不留大片空白（2026-11-10 使用者，所有放大彈窗）
      overlay.classList.toggle("dz-chart", isChart);
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
      const titles = document.querySelectorAll("#demogame-cumulative-chart > h3, #batch-simulation .batch-line-chart > .dlc-title, #batch-simulation .batch-cascade-list > .batch-cascade-title, #live-log-wrap > .diagnostic-header, #change-log-wrap > .diagnostic-header");
      titles.forEach((title) => {
        if (title.querySelector(".demogame-zoom-btn") || title.classList.contains("demogame-removed") || title.closest("#demogame-zoom")) return;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "demogame-zoom-btn";
        btn.textContent = "+";
        btn.title = "Enlarge";
        btn.addEventListener("click", (event) => {
          event.stopPropagation();
          // 按鈕可能被搬到重畫後的新標題（模擬中圖表重畫會保留同一顆按鈕），以按鈕當下所在的標題為準
          const head = btn.parentElement || title;
          // 圖表子標題（模擬面板的倍率線型、消除分布）只放大該子區塊；其他標題放大整個區域內容
          const sub = head.closest(".batch-line-chart, .batch-cascade-list");
          const container = sub || head.parentElement;
          let nodes = [...container.children].filter((node) => node !== head);
          // 消除分布：只放大下方圖表，不帶上面的數字表（2026-11-27 使用者）
          if (container.classList.contains("batch-cascade-list")) { const chart = container.querySelector(".dg-cascade-chart"); if (chart) nodes = [chart]; }
          open(titleText(head), nodes);
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

  // 除錯模式預設開啟（2026-11-27 使用者「除錯模式預設都開啟」）：載入時沒勾就勾上並觸發各遊戲原本的 change 事件；頁面可設 window.DEMOGAME_DEBUG_DEFAULT = false 關掉
  (() => {
    const turnOn = () => {
      const d = document.querySelector("#debugModeInput, #debugInput");
      if (!d || d.checked || window.DEMOGAME_DEBUG_DEFAULT === false || d.dataset.dgDebugDefault) return;
      d.dataset.dgDebugDefault = "1";
      d.checked = true;
      d.dispatchEvent(new Event("change", { bubbles: true }));
    };
    turnOn();
    setTimeout(turnOn, 0);
  })();

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
    // 2026-11-20 使用者：押注模式右邊多一個「押注大小」選單（樣式同押注模式選單）。
    // 遊戲宣告 window.demogameSimulationBets = [{ value, label }] 時才顯示，選定值以 demogameSimulateRound({ mode, bet }) 傳給遊戲；
    // 預設選 window.demogameSimulationBetDefault()（通常是目前押注）。
    let betSelect = panel.querySelector("#batchSimulationBet");
    if (!betSelect && controls) {
      betSelect = document.createElement("select");
      betSelect.id = "batchSimulationBet";
      betSelect.setAttribute("aria-label", "Simulation bet size");
      if (modeSelect) modeSelect.after(betSelect); else controls.prepend(betSelect);
    }
    const bets = Array.isArray(window.demogameSimulationBets) ? window.demogameSimulationBets : [];
    if (betSelect) {
      betSelect.innerHTML = bets.map((b) => `<option value="${b.value}">${b.label}</option>`).join("");
      betSelect.hidden = !bets.length;
      const def = typeof window.demogameSimulationBetDefault === "function" ? String(window.demogameSimulationBetDefault()) : "";
      if (def && bets.some((b) => String(b.value) === def)) betSelect.value = def;
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
        body.slot-simulator #batchSimulationMode,body.slot-simulator #batchSimulationBet{min-height:34px;padding:7px 8px;border:0;border-radius:6px;color:var(--sim-text);background:var(--sim-surface);font:700 12px/1 "Segoe UI",system-ui,sans-serif}
        body.slot-simulator #batchSimulationMode[hidden],body.slot-simulator #batchSimulationBet[hidden]{display:none}
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
    return { modeSelect, chart, modes, betSelect, bets };
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

  // compact（右欄小圖，2026-11-10 使用者選方案 C）：viewBox 貼近實際寬度讓字維持可讀、X 軸每 8 個區間標一次、
  // 縱軸依 1x 以上區間自動縮放；完整 64 區間標籤看「+」放大圖。
  function simulationChartSvg(counts, buckets, ymax, compact = false) {
    const n = buckets.labels.length;
    const total = counts.reduce((a, b) => a + b, 0);
    const shares = counts.map((c) => (total ? c / total * 100 : 0));
    if (compact) return compactChartSvg(shares, counts, buckets, ymax);
    const W = 900, H = 332, L = 44, R = 12, T = 10, B = 104;
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

  function compactChartSvg(shares, counts, buckets, ymax0) {
    const W = 470, H = 230, L = 44, R = 10, T = 10, B = 62, n = buckets.labels.length, step = 8;
    const nice = (x) => { const p = Math.pow(10, Math.floor(Math.log10(x))), m = x / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p; };
    // 縱軸依 1x 以上區間的最大值縮放（不設上限；還沒有 1x 以上的局就依全部區間）：0x、(0, 1] 占比太大會把尾端壓平，超出就裁掉；
    // 局數少時各區間占比都很大，固定 1% 會整張空白、看起來像沒更新（2026-11-10 使用者回報）
    const tail = shares.slice(2).filter((v) => v > 0);
    const any = shares.filter((v) => v > 0);
    const ymax = Math.min(100, nice(Math.max(...(tail.length ? tail : any.length ? any : [ymax0 / 1.1])) * 1.1));
    const px = (i) => L + (W - L - R) * (n > 1 ? i / (n - 1) : 0.5);
    const py = (v) => T + (H - T - B) * (1 - Math.min(v, ymax) / ymax);
    let out = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="倍率線型">`;
    for (let k = 0; k <= 4; k++) {
      const v = ymax * k / 4, y = py(v);
      out += `<line x1="${L}" y1="${y.toFixed(1)}" x2="${W - R}" y2="${y.toFixed(1)}" stroke="rgba(120,160,200,.18)"/><text x="${L - 6}" y="${(y + 4).toFixed(1)}" font-size="11" text-anchor="end" fill="#7f9bb8">${+v.toPrecision(4)}%</text>`;
    }
    buckets.labels.forEach((label, i) => {
      const x = px(i).toFixed(1);
      out += `<line x1="${x}" y1="${T}" x2="${x}" y2="${H - B}" stroke="rgba(120,160,200,${i % step === 0 ? ".16" : ".05"})"/>`;
      if (i % step === 0 || i === n - 1) {
        const y = H - B + 8;
        out += `<text x="${x}" y="${y}" font-size="10.5" text-anchor="end" dominant-baseline="middle" fill="#7f9bb8" transform="rotate(-40 ${x} ${y})">${label}</text>`;
      }
    });
    const visible = (v) => v > 0 && v <= ymax;
    let d = "", pen = false;
    shares.forEach((v, i) => {
      if (!visible(v)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${px(i).toFixed(1)},${py(v).toFixed(1)}`;
      pen = true;
    });
    out += `<path d="${d}" fill="none" stroke="#4aa8ff" stroke-width="1.8"/>`;
    shares.forEach((v, i) => { if (visible(v)) out += `<circle cx="${px(i).toFixed(1)}" cy="${py(v).toFixed(1)}" r="2.4" fill="#4aa8ff"><title>${buckets.labels[i]} ${v.toFixed(3)}%（${counts[i]}）</title></circle>`; });
    return out + "</svg>";
  }

  function setupFallbackSimulation() {
    const panel = document.querySelector(".demogame-fallback-simulation");
    const start = panel?.querySelector("#batchSimulationStartBtn");
    const roundsInput = panel?.querySelector("#batchSimulationRounds");
    if (!panel || !start || !roundsInput) return;
    const { modeSelect, chart, modes, betSelect, bets } = ensureSimulationExtras(panel);
    // 2026-11-17 使用者：第一次按「開始」，之後按「繼續」接著往後累積；「重置」清空回到第一次
    let resetBtn = panel.querySelector("#batchSimulationResetBtn");
    if (!resetBtn) {
      resetBtn = document.createElement("button");
      resetBtn.type = "button"; resetBtn.id = "batchSimulationResetBtn"; resetBtn.textContent = "Reset";
      start.after(resetBtn);
    }
    if (!document.getElementById("batch-sim-reset-style")) {
      const st = document.createElement("style");
      st.id = "batch-sim-reset-style";
      st.textContent = "html body.slot-simulator .batch-simulation-controls{display:flex!important;align-items:center;gap:8px}"
        + "html body.slot-simulator .batch-simulation-controls>#batchSimulationRounds{flex:1 1 auto;min-width:0;width:auto}"
        + "html body.slot-simulator .batch-simulation-controls>button{flex:0 0 auto}";
      document.head.appendChild(st);
    }
    const tx = (en) => (window.demogameSharedText ? window.demogameSharedText(en) : en);
    const newStats = () => ({ rounds: 0, totalMultiplier: 0, hits: 0, fgTriggers: 0, maxMultiplier: 0, retryLimitExceeded: 0, bgCascades: Array(6).fill(0), fgCascades: Array(6).fill(0) });
    // 2026-11-20 使用者：累積狀態依「押注模式＋押注大小」各自保存；換設定是切到那組的累積（沒跑過就是空的），
    // 只有按重置才全部清空。acc＝目前這組的 { stats, lineCounts }；null＝這組還沒跑過
    const accStore = new Map();
    let acc = null;
    const idleLabel = () => tx(acc && acc.stats.rounds ? "Continue" : "Start");
    const modeLabel = () => modes.find((m) => String(m.value) === modeSelect?.value)?.label || "Current Bet";
    const selectedMode = () => (modes.length ? modes.find((m) => String(m.value) === modeSelect.value)?.value : undefined);
    const selectedBet = () => (bets.length ? bets.find((b) => String(b.value) === betSelect.value)?.value : undefined);
    const accKey = () => `${modeSelect?.value ?? ""}|${bets.length ? betSelect.value : ""}`;
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
      // 模擬中會一直重畫：保留標題上的「+」放大鈕（同一顆搬到新標題），不要每次重畫都消失再補上而一直閃
      const zoomBtn = chart.querySelector(":scope > .dlc-title > .demogame-zoom-btn");
      chart.innerHTML = `<div class="dlc-title">${isZhText() ? "倍率線型" : "Multiplier Distribution"} · ${label}</div>${simulationChartSvg(c, buckets, yMaxFor())}`;
      if (zoomBtn) {
        const t = chart.querySelector(":scope > .dlc-title");
        t.appendChild(zoomBtn);
        Object.assign(t.style, { display: "flex", alignItems: "center" });
      }
    };
    const renderEmpty = () => renderChart(null, SIMULATION_BUCKETS);
    const resetSim = () => {
      accStore.clear();
      acc = null;
      writeFallbackStats(newStats());
      renderEmpty();
      start.textContent = idleLabel();
    };
    // 換押注模式／押注大小：切到那組設定的累積狀態
    const switchSim = () => {
      acc = accStore.get(accKey()) || null;
      writeFallbackStats(acc ? acc.stats : newStats());
      renderChart(acc ? acc.lineCounts : null, SIMULATION_BUCKETS);
      start.textContent = idleLabel();
    };
    resetBtn.addEventListener("click", () => { if (!start.disabled) resetSim(); });
    modeSelect?.addEventListener("change", switchSim);
    betSelect?.addEventListener("change", switchSim);
    document.getElementById("languageSelect")?.addEventListener("change", () => setTimeout(() => {
      renderChart(lastCounts, SIMULATION_BUCKETS);
      start.textContent = start.disabled ? tx("Running") : idleLabel();
    }, 0));
    setTimeout(renderEmpty, 0);   // 等共用語言字典就緒
    // 沒有消除機制的遊戲：試跑一局，adapter 沒回傳 bgCascade 就一開始就隱藏消除分布
    setTimeout(async () => {
      if (typeof window.demogameSimulateRound !== "function") return;
      try {
        const pending = window.demogameSimulateRound({ mode: selectedMode(), bet: selectedBet() });
        const probe = pending && typeof pending.then === "function" ? await pending : (pending || {});
        const hasCascade = Number.isFinite(Number(probe.bgCascade)) || (Array.isArray(probe.fgCascades) && probe.fgCascades.length > 0);
        panel.querySelector(".batch-cascade-list")?.classList.toggle("demogame-removed", !hasCascade);
      } catch (error) { /* 試跑失敗就維持顯示 */ }
    }, 0);

    start.addEventListener("click", async () => {
      const requested = Math.min(1000000, Math.max(1, Math.trunc(Number(roundsInput.value) || 0)));
      roundsInput.value = String(requested);
      start.disabled = true;
      resetBtn.disabled = true;
      roundsInput.disabled = true;
      if (modeSelect) modeSelect.disabled = true;
      if (betSelect) betSelect.disabled = true;
      const mode = selectedMode(), bet = selectedBet();
      const buckets = SIMULATION_BUCKETS;
      acc = accStore.get(accKey()) || null;
      if (!acc) { acc = { stats: newStats(), lineCounts: new Array(buckets.labels.length).fill(0), mode, bet }; accStore.set(accKey(), acc); }
      const lineCounts = acc.lineCounts;
      // 這次要再跑 requested 局，接在前面累積的局數後面
      const target = acc.stats.rounds + requested;
      const simulateRound = typeof window.demogameSimulateRound === "function"
        ? window.demogameSimulateRound
        : null;
      if (!simulateRound) {
        const note = document.getElementById("batchSimulationNote");
        if (note) note.textContent = "Simulation adapter unavailable: this page cannot run the actual Demo Game logic yet.";
        start.textContent = idleLabel();
        start.disabled = false;
        resetBtn.disabled = false;
        roundsInput.disabled = false;
        if (modeSelect) modeSelect.disabled = false;
        if (betSelect) betSelect.disabled = false;
        return;
      }
      const stats = acc.stats;
      start.textContent = window.demogameSharedText ? window.demogameSharedText("Running") : "Running";   // 中文顯示「進行中」
      try {
        while (stats.rounds < target) {
          const sliceStarted = performance.now();
          let sliceRounds = 0;
          while (stats.rounds < target && sliceRounds < 2000 && performance.now() - sliceStarted < 40) {
            const pending = simulateRound({ mode, bet });
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
        start.textContent = idleLabel();
        start.disabled = false;
        resetBtn.disabled = false;
        roundsInput.disabled = false;
        if (modeSelect) modeSelect.disabled = false;
        if (betSelect) betSelect.disabled = false;
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
    // 玩法簡介（共用，倍率線型上方，2026-11-10 使用者）：只寫競品與本作調整；詳細規則放標題列「說明」。
    // 頁面在載入本檔前設 window.DEMOGAME_OVERVIEW = { competitor: "廠商 遊戲名", expect: "一句話期待過程", changes: ["…", …] }；沒設不顯示。
    // changes 只寫規格上的變化（玩法、押注、上限），不寫隱性設計（權重、機率、調性）。
    // 遊戲發想以自家前作為基底時加 label: "base"，標籤顯示「前作」。
    const ov = window.DEMOGAME_OVERVIEW;
    if (ov && (ov.competitor || ov.expect || (ov.changes || []).length)) {
      const esc = (t) => String(t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
      const box = document.createElement("section");
      box.id = "demogame-overview";
      // 2026-11-12：可加 ov.en = { expect, changes } 提供英文版；英文介面顯示 ov.en，沒給就照中文
      const dual = (zhText, enText) => enText ? `<span class="ov-zh">${esc(zhText)}</span><span class="ov-en">${esc(enText)}</span>` : esc(zhText);
      const en = ov.en || {};
      const rows = (ov.changes || []).map((c, i) => `<li>${dual(c, (en.changes || [])[i])}</li>`).join("");
      box.innerHTML = `<h3 class="demogame-region-title">Game Overview</h3>`
        + (ov.competitor ? `<div class="ov-row"><span class="ov-k">${ov.label === "base" ? "Previous Title" : "Competitor"}</span><span class="ov-v">${esc(ov.competitor)}</span></div>` : "")
        + (ov.expect ? `<div class="ov-row"><span class="ov-k">Expectation</span><span class="ov-v">${dual(ov.expect, en.expect)}</span></div>` : "")
        + (rows ? `<div class="ov-row"><span class="ov-k">Gameplay</span><ul class="ov-v">${rows}</ul></div>` : "");
      right.insertBefore(box, panel);
      const st = document.createElement("style");
      st.textContent = "body.slot-simulator #demogame-overview{padding:10px 14px;border:1px solid var(--sim-border);border-radius:10px;background:var(--sim-panel)}"
        + "body.slot-simulator #demogame-overview .ov-row{display:flex;gap:10px;font:13px/1.6 \"Segoe UI\",system-ui,sans-serif;color:var(--sim-text)}"
        + "body.slot-simulator #demogame-overview .ov-row{padding:7px 0}"
        + "body.slot-simulator #demogame-overview .ov-row+.ov-row{border-top:1px solid var(--sim-surface)}"
        + "body.slot-simulator #demogame-overview .ov-row:last-child{padding-bottom:0}"
        + "body.slot-simulator #demogame-overview .ov-k{flex:0 0 auto;min-width:5.5em;color:var(--sim-sub);font-weight:700}"
        + "body.slot-simulator #demogame-overview ul.ov-v{margin:0;padding-left:18px}";
      document.head.appendChild(st);
    }
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
      // 在右欄是小圖（方案 C），搬進「+」放大彈窗後寬度變大就畫完整版
      chart.innerHTML = simulationChartSvg(counts[mode], SIMULATION_BUCKETS, 1, !chart.closest("#demogame-zoom"));
    };
    let lastZoomed = null;
    new ResizeObserver(() => { const z = !!chart.closest("#demogame-zoom"); if (z !== lastZoomed) { lastZoomed = z; render(); } }).observe(chart);
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

  // 右欄區域可摺疊（共用，2026-11-10 使用者）：#right-panel 底下有標題（h3）的區域，點標題收起／展開；
  // 標題內的按鈕（如放大「+」）不觸發摺疊。倍率線型預設收起。
  function setupCollapsibleRegions() {
    const right = document.getElementById("right-panel");
    if (!right) return;
    if (!document.getElementById("dg-collapse-style")) {
      const st = document.createElement("style");
      st.id = "dg-collapse-style";
      st.textContent = "body.slot-simulator .dg-collapsible>h3{cursor:pointer;user-select:none;display:flex;align-items:center}"
        + "body.slot-simulator .dg-collapsible>h3::before{content:\"\";flex:0 0 auto;width:0;height:0;margin-right:7px;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid currentColor;transition:transform .15s}"
        + "body.slot-simulator .dg-collapsed>h3::before{transform:rotate(-90deg)}"
        + "body.slot-simulator .dg-collapsed>:not(h3){display:none!important}"
        + "body.slot-simulator .dg-collapsed>h3{border-bottom:0!important;margin-bottom:0!important;padding-bottom:0!important}"
        + "body.slot-simulator .dg-collapsed{padding-bottom:0!important}";
      document.head.appendChild(st);
    }
    for (const sec of right.children) {
      if (!sec.querySelector(":scope > h3") || sec.classList.contains("dg-collapsible")) continue;
      sec.classList.add("dg-collapsible");
      if (sec.id === "demogame-cumulative-chart") sec.classList.add("dg-collapsed");
    }
    // 用事件委派：有些遊戲會重畫區域內容（含標題），直接綁在標題上會失效
    if (!right.dataset.dgCollapse) {
      right.dataset.dgCollapse = "1";
      right.addEventListener("click", (e) => {
        const head = e.target.closest("h3");
        const sec = head?.parentElement;
        if (!sec || sec.parentElement !== right || !sec.classList.contains("dg-collapsible")) return;
        if (e.target.closest("button, a, input, select")) return;
        sec.classList.toggle("dg-collapsed");
      });
    }
  }
  setupCollapsibleRegions();
  setTimeout(setupCollapsibleRegions, 0);

  // 下方除錯區可摺疊（共用，2026-11-12 使用者）：版本紀錄／模擬／紀錄，點標題列收起／展開，版本紀錄預設折疊、其餘預設展開；
  // 標題列內的按鈕（Clear、放大「+」）不觸發摺疊。標題列是 .diagnostic-header 或 .zone-label。
  const FOLD_IDS = ["change-log-wrap", "batch-simulation", "live-log-wrap"];
  const foldHead = (sec) => sec.querySelector(":scope > .diagnostic-header, :scope > .zone-label");
  function setupFoldRegions() {
    if (!document.getElementById("dg-fold-style")) {
      const st = document.createElement("style");
      st.id = "dg-fold-style";
      st.textContent = "body.slot-simulator .dg-fold>.dg-fold-head{cursor:pointer;user-select:none;display:flex!important;align-items:center}"
        + "body.slot-simulator .dg-fold>.dg-fold-head::before{content:\"\";flex:0 0 auto;width:0;height:0;margin-right:7px;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid currentColor;transition:transform .15s}"
        + "body.slot-simulator .dg-fold.dg-folded>.dg-fold-head::before{transform:rotate(-90deg)}"
        + "body.slot-simulator .dg-fold.dg-folded>:not(.dg-fold-head){display:none!important}"
        + "body.slot-simulator .dg-fold.dg-folded>.dg-fold-head{border-bottom:0!important;margin-bottom:0!important}"
        + "body.slot-simulator .dg-fold.dg-folded{padding-bottom:0!important}";
      document.head.appendChild(st);
    }
    for (const id of FOLD_IDS) {
      const sec = document.getElementById(id);
      const head = sec && foldHead(sec);
      if (!head || sec.classList.contains("dg-fold")) continue;
      sec.classList.add("dg-fold");
      head.classList.add("dg-fold-head");
      // 版本紀錄預設折疊（2026-11-17 使用者），模擬／紀錄維持預設展開
      if (id === "change-log-wrap") sec.classList.add("dg-folded");
    }
    if (!document.body.dataset.dgFold) {
      document.body.dataset.dgFold = "1";
      document.body.addEventListener("click", (e) => {
        const head = e.target.closest(".dg-fold-head");
        const sec = head?.parentElement;
        if (!sec || !sec.classList.contains("dg-fold") || sec.closest("#demogame-zoom")) return;
        if (e.target.closest("button, a, input, select")) return;
        sec.classList.toggle("dg-folded");
      });
    }
  }
  setupFoldRegions();
  setTimeout(setupFoldRegions, 0);
  setTimeout(setupFoldRegions, 1000);

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
  // 2026-11-12 使用者：長按空白鍵連續 Spin 時，局與局之間的停頓減半
  window.demogameRoundPause = () => new Promise((resolve) => setTimeout(resolve, window.demogameSpaceHolding ? DEMOGAME_ROUND_PAUSE_MS / 2 : DEMOGAME_ROUND_PAUSE_MS));

  // ===== Log（共用）=====
  // window.demogameLog(text, type)：寫一行「[HH:MM:SS] text」到 #liveLogBody 最上面（新的在上），最多 500 行。
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
    // 新的一行在最上面、舊的往下擠（2026-11-17）
    body.prepend(line);
    while (body.children.length > 500) body.lastElementChild.remove();
    body.scrollTop = 0;
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
    "game help": "遊戲說明", "close": "關閉",
    "credit": "餘額", "bet": "押注", "win": "得分", "play": "遊戲", "auto": "自動", "speed": "速度",
    "bet mode": "押注模式", "normal bet": "一般押注", "extra bet": "額外押注", "buy feature": "購買特色", "super feature": "超級特色", "buy super feature": "購買超級特色",
    "stats": "統計", "basic metrics": "基本指標", "special metrics": "特殊指標", "simulation stats": "模擬統計", "total rounds": "總局數", "hit rate": "中獎率",
    "fg trigger": "FG 觸發", "fg trigger (observed)": "FG 觸發（實測）", "max multiplier": "最高倍數",
    "set rng": "指定 RNG", "card bg range": "卡片 BG 區間", "card bf range": "卡片 BF 區間", "reel rng": "輪帶 RNG",
    "reset": "重置", "force fg": "強制 FG", "log": "紀錄", "clear": "清除", "simulation": "模擬", "start": "開始", "continue": "繼續",
    "running": "進行中", "retry limit exceeded": "Retry 超限", "scene": "場景", "setting": "設定",
    "debug mode": "除錯模式", "card system": "卡片系統", "image": "圖片", "show symbol id": "顯示符號 ID", "version": "版本", "language": "語言",
    "help": "說明", "guide": "導覽","change log": "修改紀錄", "version log": "版本紀錄", "previous": "上一步", "next": "下一步",
    "cascade distribution": "消除分布", "cascades": "消除次數", "history": "歷史紀錄", "report": "報告", "game overview": "玩法簡介", "competitor": "競品", "previous title": "前作", "gameplay": "玩法", "expectation": "期待", "multiplier distribution": "倍率線型", "bg max multiplier": "BG 最大倍數", "fg max multiplier": "FG 最大倍數", "double-click to play offline. no server needed.": "雙擊即可離線遊玩，不需伺服器。"
  };
  const SHARED_SKIP = "#helpContent, #helpDialog .help-body, #changeLogBody, #liveLogBody, #rngList, #lineList, #spinResultList, script, style, svg";
  const sharedOriginal = new WeakMap();
  const isZh = () => /^zh/i.test(document.getElementById("languageSelect")?.value || document.documentElement.lang || "");
  let sharedApplying = false;
  function applySharedLanguage() {
    if (sharedApplying) return;
    sharedApplying = true;
    const zh = isZh();
    document.body.classList.toggle("demogame-en", !zh);
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

  // 最後調性更新日期（共用，頁尾 .footer-note）：頁面在載入本檔前設 window.DEMOGAME_LAST_TUNING = "YYYY-MM-DD HH:MM"
  // 與 window.DEMOGAME_TUNING_CODE = "6 碼隨機碼"（下一行顯示「唯一碼」）。
  // 只看調性：數學模型或倍率（卡片）權重有改才更新；介面、文件修改不算。
  // 另可設 window.DEMOGAME_LAST_CODE（程式最後調整：index／Simulator／共用程式）與
  // window.DEMOGAME_LAST_UPDATE（任何東西最後調整），有設才多顯示一行。
  function syncLastTuning() {
    const date = window.DEMOGAME_LAST_TUNING;
    const note = document.querySelector(".footer-note");
    if (!date || !note) return;
    const zh = isZhText();
    // 唯一碼：window.DEMOGAME_TUNING_CODE（6 碼隨機碼），每次改調性時與 DEMOGAME_LAST_TUNING 一起換新，用來確認線上是不是最新調性。
    const code = window.DEMOGAME_TUNING_CODE;
    const lines = [zh ? `最後調性更新：${date}` : `Last tuning update: ${date}`];
    if (window.DEMOGAME_LAST_CODE) lines.push(zh ? `程式最後調整：${window.DEMOGAME_LAST_CODE}` : `Last code update: ${window.DEMOGAME_LAST_CODE}`);
    if (window.DEMOGAME_LAST_UPDATE) lines.push(zh ? `最後更新：${window.DEMOGAME_LAST_UPDATE}` : `Last update: ${window.DEMOGAME_LAST_UPDATE}`);
    if (code) lines.push(zh ? `唯一碼：${code}` : `Unique code: ${code}`);   // 唯一碼放最後一行（2026-11-27 使用者）
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
      #demogameTitleActions > a:focus-visible, #demogameTitleActions > button:focus-visible{outline:2px solid rgba(127,160,200,.6);outline-offset:1px}
      /* 按鈕之間加「•」分隔（2026-11-17；用 :is(a,button) 提高權重，否則被上方 margin:0 蓋掉）：點放在按鈕框外（absolute），不吃 hover 底色、點不到 */
      #demogameTitleActions > :is(a,button) + :is(a,button){position:relative;margin-left:14px}
      #demogameTitleActions > :is(a,button) + :is(a,button)::before{content:"•";position:absolute;left:-10px;top:50%;transform:translateY(-50%);color:#6f8fae;opacity:.6;pointer-events:none;background:none}`;
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

  // ===== 餘額「＋」（共用，2026-11-11 使用者）=====
  // 餘額格右側放「＋」，按一下 +1000。各遊戲在自己的作用域設 window.demogameAddCredit(n)（改 state 後重畫）；沒設就不顯示。
  function setupAddCredit() {
    const value = document.getElementById("balanceValue");
    const cell = value?.parentElement;
    if (!cell || typeof window.demogameAddCredit !== "function" || document.getElementById("demogameAddCreditBtn")) return;
    const style = document.createElement("style");
    // 2026-11-11 使用者：「＋」緊貼「餘額」標籤右邊，純文字、不要外框
    style.textContent = `#demogameAddCreditBtn{display:inline;box-sizing:content-box;width:auto;height:auto;min-width:0;min-height:0;margin:0 0 0 4px;padding:0 2px;
        border:0;border-radius:0;background:none;box-shadow:none;color:inherit;font:inherit;font-weight:700;line-height:inherit;cursor:pointer;vertical-align:baseline}
      #demogameAddCreditBtn:hover{color:#f0c060}`;
    document.head.appendChild(style);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = "demogameAddCreditBtn";
    btn.textContent = "+";
    btn.title = "+1000";
    btn.setAttribute("aria-label", "+1000");
    btn.addEventListener("click", (event) => { event.stopPropagation(); window.demogameAddCredit(1000); btn.blur(); });
    const attach = () => {
      if (btn.isConnected) return;
      const label = [...cell.children].find((n) => n !== value && n !== btn && n.textContent.trim());
      if (label) label.appendChild(btn); else value.insertAdjacentElement("beforebegin", btn);
    };
    attach();
    // 遊戲切語言時可能整段改寫標籤文字，把「＋」洗掉 —— 洗掉就補回
    new MutationObserver(attach).observe(cell, { childList: true, subtree: true });
  }

  setTimeout(setupAddCredit, 0);


  // ===== 空白鍵＝Spin（共用，2026-11-11 使用者）=====
  // 空白鍵一律只觸發 Spin，鎖住瀏覽器預設（整頁往下捲、按到焦點所在的按鈕／勾選框）。
  // 在 window 捕獲階段處理並 stopImmediatePropagation，各遊戲自己的空白鍵監聽不會再收到，避免重複 Spin。
  // 例外：焦點在文字輸入欄／下拉選單／可編輯區時照常打字；說明視窗開著時不 Spin；導覽開著時空白鍵關閉導覽。
  (() => {
    const typing = (el) => {
      if (!el || el === document.body) return false;
      if (el.isContentEditable || el.tagName === "TEXTAREA" || el.tagName === "SELECT") return true;
      return el.tagName === "INPUT" && !/^(checkbox|radio|button|submit|reset|range|color|file|image)$/i.test(el.type);
    };
    const isSpace = (e) => e.code === "Space" || e.key === " ";
    // 2026-11-12 使用者：長按空白鍵一直 Spin —— 按住期間，Spin 鈕「變忙碌（disabled）→ 又可按」一輪結束就自動再按一次；放開即停。
    // 只在看到 Spin 鈕先變 disabled 再恢復時才續按，Spin 鈕轉動中仍可按（按了會跳過演出）的遊戲不會被連點。
    let holding = false, sawBusy = false, timer = 0;
    const stopHold = () => { holding = false; sawBusy = false; clearInterval(timer); timer = 0; window.demogameSpaceHolding = false; };
    const blocked = () => document.getElementById("demogame-guide") || document.querySelector("dialog[open]");
    const tick = () => {
      const spin = document.getElementById("spinBtn");
      if (!holding || !spin) return stopHold();
      // 2026-11-19 使用者：FG 結算看板（[data-hold-stop]）出現時終止連續 Spin，看板不被長按關掉；要放開後重新長按才繼續
      if (document.querySelector("[data-hold-stop]")) return stopHold();
      if (spin.disabled) { sawBusy = true; return; }
      if (sawBusy && !blocked()) { sawBusy = false; spin.click(); }
    };
    addEventListener("keydown", (e) => {
      if (!isSpace(e) || e.ctrlKey || e.altKey || e.metaKey || typing(e.target)) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      if (e.repeat) return;   // 按住的重複事件不另外處理，連續 Spin 由 tick 負責
      const guide = document.getElementById("demogame-guide");
      if (guide) { guide.click(); return; }
      if (document.querySelector("dialog[open]")) return;
      const spin = document.getElementById("spinBtn");
      if (spin && !spin.disabled) spin.click();
      stopHold(); holding = true; window.demogameSpaceHolding = true; timer = setInterval(tick, 40);   // 長按中局間停頓減半（demogameRoundPause）
    }, true);
    // 焦點在按鈕上時，瀏覽器會在 keyup 觸發該按鈕 —— 一併擋掉；放開空白鍵停止連續 Spin
    addEventListener("keyup", (e) => {
      if (isSpace(e)) stopHold();
      if (!isSpace(e) || typing(e.target)) return;
      e.preventDefault();
      e.stopImmediatePropagation();
    }, true);
    addEventListener("blur", stopHold);   // 切到別的視窗時放開的 keyup 收不到，一併停止
    addEventListener("keypress", (e) => {
      if (!isSpace(e) || typing(e.target)) return;
      e.preventDefault();
      e.stopImmediatePropagation();
    }, true);

    // 2026-11-12 使用者：長按 SPIN 鍵也一直 Spin（同空白鍵）—— 按住 0.4 秒進入連續 Spin，放開即停；短按照常只 Spin 一次。
    // 進入連續模式時先由這裡按第一下，放開時瀏覽器補的那一下 click 擋掉（不會多轉一局）。
    let pressTimer = 0, pressHold = false, swallowClick = false;
    const endPress = () => { clearTimeout(pressTimer); pressTimer = 0; if (pressHold) { pressHold = false; swallowClick = true; setTimeout(() => { swallowClick = false; }, 400); stopHold(); } };
    addEventListener("pointerdown", (e) => {
      const spin = e.target.closest?.("#spinBtn");
      if (!spin || spin.disabled || e.button !== 0) return;
      clearTimeout(pressTimer);
      pressTimer = setTimeout(() => {
        pressTimer = 0;
        if (blocked()) return;
        pressHold = true;
        const btn = document.getElementById("spinBtn");
        if (btn && !btn.disabled) btn.click();
        stopHold(); holding = true; window.demogameSpaceHolding = true; timer = setInterval(tick, 40);
      }, 400);
    }, true);
    addEventListener("pointerup", endPress, true);
    addEventListener("pointercancel", endPress, true);
    addEventListener("mouseup", endPress, true);
    // 保險：Spin 鈕轉動中是 disabled，部分瀏覽器不把放開事件送到 disabled 按鈕 —— 移動時發現已沒按著就停
    addEventListener("pointermove", (e) => { if ((pressHold || pressTimer) && e.buttons === 0) endPress(); }, true);
    document.addEventListener("mouseleave", endPress);
    addEventListener("blur", endPress);
    addEventListener("click", (e) => {
      if (swallowClick && e.isTrusted && e.target.closest?.("#spinBtn")) { swallowClick = false; e.preventDefault(); e.stopImmediatePropagation(); }
    }, true);
    document.getElementById("spinBtn")?.addEventListener("contextmenu", (e) => e.preventDefault());   // 觸控長按不跳選單
  })();

  // ===== 除錯模式：← ＝ Previous、→ ＝ Next（共用，2026-11-12 使用者）=====
  // 只在除錯模式開啟、按鈕看得到且可按時作用；焦點在輸入欄／下拉選單／滑桿（速度）時不攔，彈窗或導覽開著時不作用。
  (() => {
    const skip = (el) => !!el && (el.isContentEditable || /^(TEXTAREA|SELECT)$/.test(el.tagName)
      || (el.tagName === "INPUT" && !/^(checkbox|radio|button|submit|reset)$/i.test(el.type)));
    addEventListener("keydown", (e) => {
      const id = e.key === "ArrowLeft" ? "previousStepBtn" : e.key === "ArrowRight" ? "nextStepBtn" : "";
      if (!id || e.ctrlKey || e.altKey || e.metaKey || e.shiftKey || skip(e.target)) return;
      if (!document.getElementById("debugModeInput")?.checked) return;
      if (document.querySelector("dialog[open]") || document.getElementById("demogame-guide") || document.querySelector("#demogame-zoom.open")) return;
      const btn = document.getElementById(id);
      if (!btn || btn.disabled || !btn.getClientRects().length) return;
      e.preventDefault();
      if (!e.repeat) btn.click();
    }, true);
  })();

  // ===== 新手導覽（共用，2026-11-11 使用者）=====
  // 每次進 Demo（含重新整理）都自動顯示，標題列「導覽」可再看。
  // 逐步導覽：一次一個區域（盤面、控制、餘額、押注模式、指標、玩法簡介、倍率線型、除錯模式、設定），找不到的略過。
  function setupGuideTour() {
    // 2026-11-11 使用者：手機版不要導覽（不自動播、標題列也不放「導覽」鈕）
    if (window.matchMedia && matchMedia("(max-width: 760px), (hover: none) and (pointer: coarse)").matches) return;
    // 2026-11-12 使用者改版：一次一個區域（逐步導覽），說明框下方有「上一步／n/N／下一步」；
    // 點空白處或「下一步」到下一個，最後一步「完成」關閉；Esc 關閉；← → 也可切換。找不到的區域自動略過。
    const STEPS = [
      { el: () => document.getElementById("grid-panel"),
        zh: "盤面：每一局轉出的符號與中獎結果", en: "Board: the symbols and wins of each round" },
      { el: () => document.getElementById("play-panel") || document.getElementById("spinBtn"),
        zh: "SPIN 開始遊戲（也可以按空白鍵）；自動、押注 −／＋、速度都在這裡", en: "SPIN starts a round (or press Space); Auto, bet −/+ and speed are here" },
      { el: () => document.getElementById("credit-bar") || document.getElementById("balanceValue")?.parentElement?.parentElement,
        zh: "餘額・押注・得分；餘額旁「＋」加 1000", en: "Credit · Bet · Win; \"+\" next to Credit adds 1000" },
      { el: () => document.getElementById("bet-mode-panel"),
        zh: "押注模式：一般押注或購買特色", en: "Bet mode: Normal Bet or Buy Feature" },
      { el: () => [document.getElementById("simulation-stats"), document.getElementById("by-game-stats")],
        zh: "指標：依你玩的局數即時累計；標題可收合", en: "Metrics accumulate live as you play; click a title to collapse" },
      { el: () => document.getElementById("demogame-overview"),
        zh: "玩法簡介：競品與本作的玩法重點", en: "Overview: the competitor and this game's key rules" },
      { el: () => document.getElementById("demogame-cumulative-chart"),
        zh: "倍率線型：你玩過的局依倍數區間的分布；「＋」放大", en: "Multiplier distribution of the rounds you played; \"+\" to enlarge" },
      { el: () => document.querySelector("#debugModeInput, #debugInput")?.closest("label"),
        zh: "除錯模式：用 RNG 碼重現同一局，或選腳本抽指定情境", en: "Debug: replay a round by RNG code, or pick a script scenario" },
      { el: () => document.querySelector("#settings-wrap > .setting-body") || document.getElementById("settings-wrap"),
        zh: "設定：「顯示符號 ID」勾選後盤面每個符號正中間顯示代號（M1、M2…）；版本、Config 切換調性，語言切換中英文",
        en: "Settings: tick \"Show Symbol ID\" to show each symbol's code (M1, M2…) on the board; Version and Config switch the tuning, Language switches Chinese / English" }
    ];
    const style = document.createElement("style");
    style.textContent = `#demogame-guide{position:fixed;inset:0;z-index:99990;cursor:pointer}
      #demogame-guide svg{position:fixed;inset:0;width:100%;height:100%;pointer-events:none}
      #demogame-guide .dgg-box{position:fixed;box-sizing:content-box;border:2px solid #f0c060;pointer-events:none}
      #demogame-guide .dgg-tip{position:fixed;box-sizing:border-box;width:max-content;max-width:min(320px,calc(100vw - 24px));padding:10px 12px 8px;border-radius:9px;
        background:#1b2433;color:#e8eef6;border:2px solid #f0c060;box-shadow:0 6px 20px rgba(0,0,0,.45);cursor:default;
        font:700 13px/1.5 "Segoe UI","Microsoft JhengHei",system-ui,sans-serif;white-space:normal}
      #demogame-guide .dgg-nav{display:flex;align-items:center;gap:8px;margin-top:8px}
      #demogame-guide .dgg-nav button{border:0;border-radius:6px;padding:4px 12px;cursor:pointer;font:700 12px/1.4 "Segoe UI","Microsoft JhengHei",system-ui,sans-serif}
      #demogame-guide .dgg-prev{background:#2a3a55;color:#cfe0f2}
      #demogame-guide .dgg-prev:disabled{opacity:.35;cursor:default}
      #demogame-guide .dgg-next{margin-left:auto;background:#f0c060;color:#1b2433}
      #demogame-guide .dgg-count{color:#8fa6bf;font-size:12px;font-weight:600;font-variant-numeric:tabular-nums}`;
    document.head.appendChild(style);

    let overlay = null, idx = 0, steps = [];
    const zh = () => isZhText();
    const nodesOf = (step) => [].concat(step.el() || []).filter((n) => n && n.getClientRects().length && n.getBoundingClientRect().width > 0);
    function rectOf(nodes) {
      const rs = nodes.map((n) => n.getBoundingClientRect());
      const x = Math.min(...rs.map((r) => r.left)), y = Math.min(...rs.map((r) => r.top));
      return { x, y, w: Math.max(...rs.map((r) => r.right)) - x, h: Math.max(...rs.map((r) => r.bottom)) - y };
    }
    const hit = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
    function layout() {
      if (!overlay) return;
      const step = steps[idx], nodes = step ? nodesOf(step) : [];
      if (!nodes.length) return;
      // 框線緊貼目標外緣：洞＝目標本身，2px 框線畫在洞外，圓角跟目標一致（至少 8px）
      const vw = innerWidth, vh = innerHeight, bw = 2, gap = 10, m = 8;
      const rad = Math.max(8, nodes.length === 1 ? (parseFloat(getComputedStyle(nodes[0]).borderTopLeftRadius) || 0) : 8);
      const t = rectOf(nodes), r = { x: t.x - bw, y: t.y - bw, w: t.w + bw * 2, h: t.h + bw * 2 };
      overlay.querySelector("svg").innerHTML = `<defs><mask id="dgg-mask"><rect width="100%" height="100%" fill="#fff"/>`
        + `<rect x="${t.x}" y="${t.y}" width="${t.w}" height="${t.h}" rx="${rad}" fill="#000"/></mask></defs>`
        + `<rect width="100%" height="100%" fill="rgba(0,0,0,.62)" mask="url(#dgg-mask)"/>`;
      const box = overlay.querySelector(".dgg-box");
      Object.assign(box.style, { left: `${r.x}px`, top: `${r.y}px`, width: `${t.w}px`, height: `${t.h}px`, borderRadius: `${rad + bw}px` });
      const tip = overlay.querySelector(".dgg-tip");
      tip.querySelector(".dgg-text").textContent = zh() ? step.zh : step.en;
      tip.querySelector(".dgg-count").textContent = `${idx + 1} / ${steps.length}`;
      tip.querySelector(".dgg-prev").textContent = zh() ? "上一步" : "Back";
      tip.querySelector(".dgg-prev").disabled = idx === 0;
      tip.querySelector(".dgg-next").textContent = idx === steps.length - 1 ? (zh() ? "完成" : "Done") : (zh() ? "下一步" : "Next");
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      const cx = r.x + r.w / 2 - tw / 2, cy = r.y + r.h / 2 - th / 2;
      const cands = [
        { x: r.x, y: r.y + r.h + gap }, { x: cx, y: r.y + r.h + gap },          // 下
        { x: r.x, y: r.y - gap - th }, { x: cx, y: r.y - gap - th },            // 上
        { x: r.x + r.w + gap, y: r.y }, { x: r.x + r.w + gap, y: cy },          // 右
        { x: r.x - gap - tw, y: r.y }, { x: r.x - gap - tw, y: cy },            // 左
        { x: r.x + gap, y: r.y + gap }, { x: cx, y: cy }                         // 框內（大區塊）
      ].map((p) => ({ x: Math.max(m, Math.min(p.x, vw - tw - m)), y: Math.max(m, Math.min(p.y, vh - th - m)), w: tw, h: th }));
      const pick = cands.find((c, i) => i >= 8 || !hit(c, r)) || cands[0];
      tip.style.left = `${pick.x}px`; tip.style.top = `${pick.y}px`;
    }
    function go(i) {
      if (!overlay) return;
      if (i < 0) return;
      if (i >= steps.length) { close(); return; }
      idx = i;
      const nodes = nodesOf(steps[idx]);
      // 目標不在畫面內就捲過去（捲動會觸發 layout）
      const t = nodes.length ? rectOf(nodes) : null;
      if (t && (t.y < 0 || t.y + Math.min(t.h, innerHeight * 0.6) > innerHeight)) nodes[0].scrollIntoView({ block: t.h > innerHeight * 0.7 ? "start" : "center" });
      layout();
      setTimeout(layout, 60);
    }
    function close() {
      if (!overlay) return;
      overlay.remove(); overlay = null;
      removeEventListener("resize", layout); removeEventListener("scroll", layout, true); removeEventListener("keydown", onKey, true);
    }
    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
      else if (e.key === "ArrowRight" || e.key === "Enter") { e.preventDefault(); e.stopPropagation(); go(idx + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); go(idx - 1); }
    }
    function start() {
      if (overlay) return;
      steps = STEPS.filter((s) => nodesOf(s).length);
      if (!steps.length) return;
      idx = 0;
      overlay = document.createElement("div");
      overlay.id = "demogame-guide";
      overlay.setAttribute("role", "dialog");
      overlay.innerHTML = '<svg aria-hidden="true"></svg><div class="dgg-box"></div>'
        + '<div class="dgg-tip"><div class="dgg-text"></div><div class="dgg-nav">'
        + '<button type="button" class="dgg-prev"></button><span class="dgg-count"></span><button type="button" class="dgg-next"></button></div></div>';
      // 點空白處（含暗底與框選區）＝下一步；點說明框本身不動作，按鈕各自處理
      overlay.addEventListener("click", (e) => {
        e.preventDefault(); e.stopPropagation();
        if (e.target.closest(".dgg-prev")) return go(idx - 1);
        if (e.target.closest(".dgg-next")) return go(idx + 1);
        if (e.target.closest(".dgg-tip")) return;
        go(idx + 1);
      });
      document.body.appendChild(overlay);
      addEventListener("resize", layout); addEventListener("scroll", layout, true); addEventListener("keydown", onKey, true);
      go(0);
      requestAnimationFrame(() => requestAnimationFrame(layout));
    }
    window.demogameGuide = start;
    // 標題列「導覽」鈕（放在「說明」前）
    const group = document.getElementById("demogameTitleActions");
    if (group) {
      const btn = document.createElement("button");
      btn.type = "button"; btn.id = "demogameGuideBtn"; btn.textContent = "Guide";
      btn.addEventListener("click", start);
      group.insertBefore(btn, document.getElementById("helpBtn") || group.firstChild);
    }
    // 2026-11-12 使用者：每台裝置第一次進遊戲才自動播（localStorage 記看過，所有遊戲共用）；之後要看按標題列「導覽」
    {
      // 導覽內容有改時把 GUIDE_REV 加 1，看過舊版的裝置會再自動播一次（2026-11-20 加「設定／符號ID」→ 2）
      const SEEN_KEY = "demogameGuideSeen", GUIDE_REV = "2";
      let seen = false;
      try { seen = localStorage.getItem(SEEN_KEY) === GUIDE_REV; } catch (_) {}
      // 等預載畫面與版面就緒再開始
      const wait = () => (document.querySelector(".demogame-preload:not(.done), #demogame-preload") ? setTimeout(wait, 300) : setTimeout(() => {
        try { localStorage.setItem(SEEN_KEY, GUIDE_REV); } catch (_) {}
        start();
      }, 600));
      if (!seen) {
        if (document.readyState === "complete") wait(); else addEventListener("load", wait, { once: true });
      }
    }
  }

  setupGuideTour();

  // ===== 共通規格（共用，2026-11-12 使用者：以 H032 亡靈派對為準，所有遊戲統一）=====
  // ① 區域拿掉外框，改用更深的背景＋陰影分層；區域內小框也拿掉
  // ② 玩法簡介標題欄 45px；版本紀錄最新版不加綠框
  // ③ 模擬區：消除分布改成 BG／FG 左右兩半直條圖、倍率線型黑底；右欄倍率線型黑底貼齊
  // ④ 控制區：夠寬 SPIN｜自動｜Bet、速度整排；控制區 < 400px 改 2×2
  // ⑤ 盤面下方訊息條：黑色凹槽、13px 淡色置中
  // ⑥ 狀態列整條拿掉；只有倍數（multPill／sumPill）改放盤面上方資訊條（同 H032「倍數總和」條），其他資訊（連消、Respin、SF、Table、FG 剩餘…）不顯示
  //    遊戲可設 window.DEMOGAME_INFO_BAR = false 不用資訊條（H032 有自己的倍數總和條）
  // ⑦ 押注模式：按購買特色／超級特色後該鈕亮起，到那場特色結束再換回原本亮的模式鈕
  // ⑧ 重置：押注回第一檔、紀錄只留載入那一行、指定 RNG（腳本／RNG 碼／強制 FG）清空
  // ⑨ 盤面放不下時整個盤面等比縮小（CSS zoom），不擠出盤面區
  function setupCommonSpec() {
    const $id = (id) => document.getElementById(id);
    const css = `
      html body.slot-simulator, html body.slot-simulator.fg-mode { background: #010409; }
      html body.slot-simulator #feature-bar, html body.slot-simulator #grid-panel, html body.slot-simulator #credit-bar,
      html body.slot-simulator .control-zone, html body.slot-simulator .diagnostic-region, html body.slot-simulator .dg-collapsible,
      html body.slot-simulator #batch-simulation, html body.slot-simulator #set-rng-panel, html body.slot-simulator #play-panel,
      html body.slot-simulator #bet-mode-panel, html body.slot-simulator #settings-wrap, html body.slot-simulator #rng-wrap,
      html body.slot-simulator #log-wrap, html body.slot-simulator #live-log-wrap, html body.slot-simulator #change-log-wrap,
      html body.slot-simulator #demogame-overview, html body.slot-simulator #demogame-cumulative-chart {
        border: 0 !important;
        box-shadow: 0 1px 0 rgba(120, 180, 255, 0.05) inset, 0 6px 20px rgba(0, 0, 0, 0.6) !important;
      }
      html body.slot-simulator .batch-cascade-list, html body.slot-simulator .batch-line-chart, html body.slot-simulator .change-log-entry {
        border: 0 !important; background: rgba(12, 34, 64, 0.55) !important;
      }
      html body.slot-simulator #demogame-overview .ov-row > .ov-k { flex: 0 0 45px !important; width: 45px !important; min-width: 0 !important; }
      html body.slot-simulator.demogame-en #demogame-overview .ov-row > .ov-k { flex: 0 0 84px !important; width: 84px !important; }
      html body.demogame-en #demogame-overview .ov-zh, html body:not(.demogame-en) #demogame-overview .ov-en { display: none; }
      html body.slot-simulator #change-log-wrap #changeLogBody .change-log-entry.demogame-current-version { border: 0 !important; background: #0c2240 !important; }

      html body.slot-simulator #batch-simulation .batch-cascade-list, html body.slot-simulator #batch-simulation .batch-line-chart {
        margin-top: 12px !important; padding: 12px 14px 10px !important; border: 0 !important; border-radius: 10px !important;
        background: #030b17 !important; box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.55) !important;
      }
      html body.slot-simulator #batch-simulation .batch-cascade-title, html body.slot-simulator #batch-simulation .batch-line-chart > .dlc-title {
        display: flex !important; align-items: center; justify-content: flex-start !important; position: relative; min-height: 24px;
        margin: 0 0 8px !important; padding: 0 30px 0 0 !important; border: 0 !important; text-align: left !important;
        color: var(--sim-text, #b0d4f0) !important; font-size: 13px !important; font-weight: 700 !important;
      }
      html body.slot-simulator #batch-simulation .batch-line-chart > .dlc-title > .demogame-zoom-btn {
        position: absolute !important; right: 0; top: 50%; transform: translateY(-50%); margin: 0 !important;
      }
      html body.slot-simulator #batch-simulation .batch-cascade-list.dg-has-chart > .batch-cascade-row { display: none !important; }
      html body.slot-simulator #batch-simulation .dg-cascade-chart svg { display: block; width: 100%; height: auto; }

      html body.slot-simulator #demogame-cumulative-chart { padding: 0 !important; overflow: hidden; }
      html body.slot-simulator #demogame-cumulative-chart > h3 { margin: 0 !important; padding: 0 14px !important; }
      html body.slot-simulator #demogame-cumulative-chart .batch-line-chart {
        margin: 0 !important; padding: 14px 12px 6px 4px !important; border: 0 !important; border-radius: 0 !important;
        background: #030b17 !important; box-shadow: inset 0 6px 10px -6px rgba(0, 0, 0, 0.7) !important;
      }
      html body.slot-simulator #demogame-cumulative-chart .batch-line-chart svg text { font-size: 9px; fill: #5f7d99; }

      html body.slot-simulator #play-panel { container-type: inline-size; }
      html body.slot-simulator #play-panel .play-main-controls {
        display: grid !important; grid-template-columns: auto auto minmax(0, 1fr) !important; gap: 6px !important; align-items: stretch;
      }
      html body.slot-simulator #play-panel .play-main-controls > * { min-width: 0; width: auto !important; }
      html body.slot-simulator #play-panel .play-main-controls > #spinBtn { grid-column: 1 !important; grid-row: 1 !important; min-width: 72px; }
      html body.slot-simulator #play-panel .play-main-controls > #autoBtn { grid-column: 2 !important; grid-row: 1 !important; min-width: 72px; }
      html body.slot-simulator #play-panel .play-main-controls .bet-stepper { grid-column: 3 !important; grid-row: 1 !important; }
      html body.slot-simulator #play-panel .play-main-controls .speed-control { grid-column: 1 / -1 !important; grid-row: 2 !important; }
      @container (max-width: 400px) {
        html body.slot-simulator #play-panel .play-main-controls { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important; }
        html body.slot-simulator #play-panel .play-main-controls .bet-stepper { grid-column: 1 !important; grid-row: 2 !important; }
        html body.slot-simulator #play-panel .play-main-controls .speed-control { grid-column: 2 !important; grid-row: 2 !important; }
      }

      html body.slot-simulator #grid-panel #messageBar {
        min-height: 36px !important; padding: 0 16px !important; display: flex; align-items: center; justify-content: center;
        border: 0 !important; border-radius: 12px !important; background: #030b17 !important;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.7), 0 1px 0 rgba(120, 180, 255, 0.06) !important;
        color: var(--sim-sub, #5a88aa) !important; font: 700 13px/1.3 "Segoe UI", "Microsoft JhengHei", system-ui, sans-serif !important; letter-spacing: 1px;
      }

      html body.slot-simulator #strip-bar { display: none !important; }
      html body.slot-simulator #demogame-info-bar {
        display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 4px 22px;
        width: 100%; align-self: stretch; min-height: 36px; margin: 0 0 10px; padding: 4px 16px; box-sizing: border-box; border-radius: 12px; background: #030b17;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.7), 0 1px 0 rgba(120, 180, 255, 0.06);
      }
      html body.slot-simulator #demogame-info-bar[hidden] { display: none !important; }
      html body.slot-simulator #demogame-info-bar .dib-item { display: inline-flex; align-items: center; gap: 10px; white-space: nowrap; }
      html body.slot-simulator #demogame-info-bar .dib-k { color: var(--sim-sub, #5a88aa); font: 700 13px/1 "Segoe UI", "Microsoft JhengHei", system-ui, sans-serif; letter-spacing: 1px; }
      html body.slot-simulator #demogame-info-bar .dib-v {
        color: #33bbff; text-shadow: 0 0 12px rgba(51, 187, 255, 0.45);
        font: 800 20px/1 "Segoe UI", system-ui, sans-serif; font-variant-numeric: tabular-nums;
      }
      html body.slot-simulator #demogame-info-bar.fx-bar-hit { animation: dgInfoBarHit 420ms ease-out; }
      @keyframes dgInfoBarHit { from { transform: scale(1.08); filter: brightness(2); box-shadow: 0 0 18px rgba(255, 79, 216, .9); } to { transform: scale(1); filter: brightness(1); } }

      /* 2026-11-19 使用者：購買類按鈕（購買特色／超級特色）一律藍色；按下去（買進中，到這場 FG 結束）壓暗，
         壓暗的樣子跟另一顆被停用的購買按鈕完全相同（同藍底、opacity .45），不變綠也不另用深色 */
      html body.slot-simulator #app-shell #bet-mode-panel button.dg-buy-active {
        opacity: .45 !important; color: #fff !important; background: #0077cc !important;
        border: 0 !important; box-shadow: none !important; filter: none !important;
      }
    `;
    const addStyle = () => {
      if ($id("dg-common-spec")) $id("dg-common-spec").remove();
      const st = document.createElement("style");
      st.id = "dg-common-spec"; st.textContent = css;
      document.head.appendChild(st);   // 放在最後，蓋過各遊戲與共用的舊樣式
    };
    addStyle();
    addEventListener("load", () => setTimeout(addStyle, 0), { once: true });

    // ⑥ 盤面上方資訊條：只鏡射狀態列上的倍數膠囊（multPill、sumPill）；2026-11-12 使用者：沒說要留的資訊一律拿掉
    if (window.DEMOGAME_INFO_BAR !== false) {
      const strip = $id("strip-bar"), panel = $id("grid-panel");
      if (strip && panel) {
        const bar = document.createElement("div");
        bar.id = "demogame-info-bar"; bar.hidden = true;
        panel.prepend(bar);
        let lastSig = "", lastVals = "";
        const sync = () => {
          const pills = [...strip.querySelectorAll("#multPill, #sumPill")].filter((p) => !p.classList.contains("hidden") && !p.hidden
            && !p.classList.contains("demogame-removed") && p.textContent.trim());
          const items = pills.map((p) => {
            const k = p.querySelector(".k")?.textContent.trim() ?? "", v = p.querySelector(".v")?.textContent.trim() ?? p.textContent.trim();
            return { k, v, id: p.id };
          });
          const sig = items.map((i) => i.k).join("|"), vals = items.map((i) => i.v).join("|");
          if (sig !== lastSig) {
            bar.innerHTML = items.map(() => '<span class="dib-item"><span class="dib-k"></span><span class="dib-v"></span></span>').join("");
            lastSig = sig;
          }
          bar.querySelectorAll(".dib-item").forEach((el, i) => {
            el.querySelector(".dib-k").textContent = items[i].k;
            el.querySelector(".dib-v").textContent = items[i].v;
            el.dataset.src = items[i].id;
          });
          bar.hidden = !items.length;
          if (lastVals && vals !== lastVals && sig === lastSig) { bar.classList.remove("fx-bar-hit"); void bar.offsetWidth; bar.classList.add("fx-bar-hit"); }
          lastVals = vals;
        };
        sync();
        new MutationObserver(sync).observe(strip, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ["class", "hidden", "style"] });
        // 2026-11-12：狀態列隱藏後，遊戲的飛行／跳動動畫要改對準上方資訊條裡的鏡射膠囊，否則會飛到畫面左上角
        window.demogameFxTarget = (id) => {
          const src = $id(id);
          if (src && src.getClientRects().length) return src;
          return bar.querySelector(`.dib-item[data-src="${id}"]`) || src;
        };
      }
    }

    // ③ 消除分布：BG／FG 左右兩半直條圖（同一張圖，中間分隔線；縱軸固定 0～100%）
    const setupCascadeChart = (n = 0) => {
      const list = document.querySelector("#batch-simulation .batch-cascade-list");
      const rows = list ? [...list.querySelectorAll(".batch-cascade-row:not(.batch-cascade-head)")] : [];
      const ids = rows.map((r) => [...r.querySelectorAll(".s-value")].map((v) => v.id));
      if (!list || !rows.length) { if (n < 30) setTimeout(() => setupCascadeChart(n + 1), 200); return; }   // 模擬區可能稍後才建好
      if (list.classList.contains("dg-has-chart")) return;
      if (ids.every((p) => p.length >= 2 && p[0] && p[1])) {
        list.classList.add("dg-has-chart");
        const labels = rows.map((r) => r.querySelector(".s-label")?.textContent.trim() ?? "");
        const box = document.createElement("div");
        box.className = "dg-cascade-chart";
        list.appendChild(box);
        const val = (id) => Math.max(0, Math.min(100, parseFloat($id(id)?.textContent) || 0));
        const draw = () => {
          const W = 900, H = 226, L = 44, R = 888, T = 34, B = 194, mid = (L + R) / 2, pad = 14, bw = Math.min(34, (mid - L - pad * 2) / labels.length * 0.6);
          const y = (p) => B - (B - T) * p / 100;
          let s = "";
          [0, 25, 50, 75, 100].forEach((p) => {
            s += `<line x1="${L}" y1="${y(p)}" x2="${R}" y2="${y(p)}" stroke="rgba(120,160,200,.18)"/>`
              + `<text x="${L - 6}" y="${y(p) + 4}" font-size="12" text-anchor="end" fill="#7f9bb8">${p}%</text>`;
          });
          s += `<line x1="${mid}" y1="${T - 22}" x2="${mid}" y2="${B + 26}" stroke="rgba(120,160,200,.3)"/>`;
          [[0, "BG", "#33bbff", L + pad, mid - pad], [1, "FG", "#b06aff", mid + pad, R - pad]].forEach(([col, name, color, x0, x1]) => {
            const gw = (x1 - x0) / labels.length;
            s += `<text x="${(x0 + x1) / 2}" y="${T - 14}" font-size="13" font-weight="700" text-anchor="middle" fill="${color}">${name}</text>`;
            labels.forEach((lab, i) => {
              const cx = x0 + gw * i + gw / 2, p = val(ids[i][col]), top = y(p);
              s += `<rect x="${cx - bw / 2}" y="${top}" width="${bw}" height="${B - top}" rx="3" fill="${color}" fill-opacity=".85"/>`
                + `<text x="${cx}" y="${top - 5}" font-size="11" text-anchor="middle" fill="#cfe3f5">${p.toFixed(1)}%</text>`
                + `<text x="${cx}" y="${B + 20}" font-size="12" text-anchor="middle" fill="#7f9bb8">${lab}</text>`;
            });
          });
          box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Cascade distribution">${s}</svg>`;
        };
        draw();
        const mo = new MutationObserver(draw);
        rows.forEach((r) => r.querySelectorAll(".s-value").forEach((el) => mo.observe(el, { childList: true, characterData: true, subtree: true })));
      }
    };
    setupCascadeChart();

    // ⑦ 押注模式：買進中該購買鈕亮起，特色結束換回原本亮的模式鈕
    {
      const modeIds = ["normalBetBtn", "extraBetBtn", "extraBet2Btn"], buyIds = ["buyFeatureBtn", "buySuperFeatureBtn", "superFeatureBtn"];
      let buying = null, prev = [], sawFg = false, idleTimer = 0;
      const modes = () => modeIds.map($id).filter(Boolean);
      const apply = () => {
        if (!buying) return;
        modes().forEach((b) => b.classList.remove("is-active", "active"));
        buying.classList.add("dg-buy-active", "is-active");
      };
      const end = () => {
        if (!buying) return;
        buying.classList.remove("dg-buy-active", "is-active");
        prev.forEach((b) => b.classList.add("is-active"));
        buying = null; prev = []; sawFg = false; clearInterval(idleTimer);
      };
      buyIds.map($id).filter(Boolean).forEach((btn) => btn.addEventListener("click", () => {
        if (btn.disabled) return;
        if (buying) end();
        prev = modes().filter((b) => b.classList.contains("is-active"));
        buying = btn; sawFg = document.body.classList.contains("fg-mode");
        setTimeout(apply, 0);
        clearInterval(idleTimer);
        // 特色結束：進過 FG 又離開；或一直沒進 FG 而 Spin 已可再按（買進的局結束）
        // 「在特色中」：body.fg-mode、FG 剩餘看得到、或 Spin 鈕寫著 FG／免費（有些遊戲買進後停在「Next FG」等玩家按）
        let spinBusySeen = false, quietSince = 0;
        const t0 = Date.now();
        const inFeature = () => document.body.classList.contains("fg-mode")
          || ($id("fgLeftPill") && !$id("fgLeftPill").classList.contains("hidden") && !$id("fgLeftPill").hidden)
          || /\bFG\b|Free|免費/i.test($id("spinBtn")?.textContent || "");
        idleTimer = setInterval(() => {
          const fg = inFeature(), spin = $id("spinBtn");
          if (fg) sawFg = true;
          if (spin?.disabled) spinBusySeen = true;
          // 剛買進先等一下；之後「Spin 可按且不在特色中」要連續 1.5 秒才算結束（特色局與局之間可能短暫看起來像一般局）
          if (Date.now() - t0 < 1500 || !spin || spin.disabled || fg || !(sawFg || spinBusySeen)) { quietSince = 0; return; }
          if (!quietSince) quietSince = Date.now();
          if (Date.now() - quietSince >= 1500) end();
        }, 200);
      }, true));
      const panel = $id("bet-mode-panel");
      if (panel) new MutationObserver(() => { if (buying && (!buying.classList.contains("dg-buy-active") || modes().some((b) => b.classList.contains("is-active")))) apply(); })
        .observe(panel, { attributes: true, subtree: true, attributeFilter: ["class"] });
      $id("resetBtn")?.addEventListener("click", end);
      // 2026-11-20：遊戲在特色結束時發 dg-feature-end，購買鈕立刻恢復（不等上面 1.5 秒的輪詢；連續 Spin 時輪詢等不到空檔）
      document.addEventListener("dg-feature-end", end);
    }

    // ⑧ 重置：押注回第一檔、紀錄只留載入那一行、指定 RNG 清空
    {
      const log = $id("liveLogBody");
      let firstLine = null;
      // 新的在上：最舊的載入行在最下面（lastElementChild）
      const grab = (n = 0) => { if (log?.lastElementChild) firstLine = log.lastElementChild.cloneNode(true); else if (n < 50) setTimeout(() => grab(n + 1), 100); };
      grab();
      $id("resetBtn")?.addEventListener("click", () => setTimeout(() => {
        const sel = $id("scriptSelect");
        if (sel && sel.value !== "") { sel.value = ""; sel.dispatchEvent(new Event("change", { bubbles: true })); }
        const force = $id("forceFgInput");
        if (force?.checked) { force.checked = false; force.dispatchEvent(new Event("change", { bubbles: true })); }
        const rng = $id("rngInput");
        if (rng && rng.value) { rng.value = ""; rng.dispatchEvent(new Event("input", { bubbles: true })); }
        const minus = $id("betMinusBtn");
        for (let i = 0; i < 80 && minus && !minus.disabled; i++) minus.click();
        if (log && firstLine) {
          const line = firstLine.cloneNode(true);
          const now = new Date(), pad = (x) => String(x).padStart(2, "0");
          line.textContent = line.textContent.replace(/^\[\d{2}:\d{2}:\d{2}\]/, `[${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}]`);
          log.innerHTML = ""; log.appendChild(line);
        }
      }, 0));
    }

    // ⑨ 盤面放不下時整個盤面等比縮小
    {
      const panel = $id("grid-panel"), board = $id("board");
      const target = board?.closest(".board-shell") || board;
      if (panel && target && "zoom" in document.body.style) {
        let lastW = -1;
        const fit = () => {
          const w = panel.clientWidth;
          if (w === lastW) return;
          lastW = w;
          target.style.zoom = "";
          const cs = getComputedStyle(panel), avail = w - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
          const need = Math.max(target.scrollWidth, board.scrollWidth);
          const z = need > avail + 1 ? Math.max(0.5, avail / need) : 1;
          if (z < 1) target.style.zoom = String(z);
        };
        new ResizeObserver(fit).observe(panel);
        addEventListener("load", () => { lastW = -1; fit(); }, { once: true });
      }
    }
  }
  setupCommonSpec();

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

    /* Help 參考排版（2026-11-18 使用者）：內容窄欄置中、標題白色置中、圓點條列、派彩兩欄（張數白、派彩金）、
       Wild／Scatter 為「符號圖＋金色名稱」卡片 */
    body #helpDialog #helpContent > * { max-width: 600px; margin-left: auto !important; margin-right: auto !important; }
    body #helpDialog #helpContent .help-section,
    body #helpDialog #helpContent .help-card,
    body #helpDialog #helpContent .help-standard-card { padding: 22px 8px; border-bottom-color: #22344a; }
    body #helpDialog #helpContent .help-section-title,
    body #helpDialog #helpContent .help-card > h3 { margin: 0 0 16px; color: #ffffff; font: 600 20px/1.35 "Segoe UI", Arial, sans-serif; text-align: center; }
    body #helpDialog #helpContent .help-group-title { margin: 20px 0 12px; color: #ffffff; font: 600 16px/1.35 "Segoe UI", Arial, sans-serif; text-align: center; }
    body #helpDialog #helpContent .help-rule { margin: 0 0 12px; padding: 0 0 0 22px; color: #c3cdd8; font: 14px/1.55 "Segoe UI", Arial, sans-serif; }
    body #helpDialog #helpContent .help-rule::before { content: "•"; left: 4px; top: 0; width: auto; height: auto; background: none; color: #8d99a8; font-size: 15px; line-height: 1.45; }
    body #helpDialog #helpContent .help-sym-grid { gap: 26px 12px; margin: 8px 0 18px; }
    body #helpDialog #helpContent .help-sym-card { justify-content: center; gap: 14px; }
    body #helpDialog #helpContent .help-sym-pays { min-width: 70px; font: 600 14px/1.6 "Segoe UI", Arial, sans-serif; }
    body #helpDialog #helpContent .help-sym-pays > div { display: grid; grid-template-columns: 1.4em auto; column-gap: 14px; }
    body #helpDialog #helpContent .help-sym-count { color: #d9e1ea; }
    body #helpDialog #helpContent .help-sym-value { color: #f5c542; }
    body #helpDialog #helpContent .help-sym-specials { display: flex; flex-direction: column; gap: 10px; margin: 14px 0 4px; }
    body #helpDialog #helpContent .help-special-block { display: flex; flex-direction: row; align-items: center; gap: 18px; width: 100%; box-sizing: border-box;
      padding: 14px 18px; border: 1px solid rgba(120, 170, 230, .14); border-radius: 10px; background: rgba(120, 170, 230, .06); }
    body #helpDialog #helpContent .help-special-tile { flex: 0 0 auto; }
    body #helpDialog #helpContent .help-special-tiles { flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; gap: 8px; }
    body #helpDialog #helpContent .help-special-tile.has-art { width: 76px; height: 76px; }
    body #helpDialog #helpContent .help-special-rules { flex: 1 1 auto; min-width: 0; }
    body #helpDialog #helpContent .help-special-name { margin: 0 0 6px; color: #f5c542; font: 600 15px/1.35 "Segoe UI", Arial, sans-serif; }
    body #helpDialog #helpContent .help-special-rules > .help-rule { margin-bottom: 6px; }
    body #helpDialog #helpContent .help-special-rules > .help-rule:last-child { margin-bottom: 0; }
    body #helpDialog #helpContent .help-ways { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); gap: 12px; margin: 6px 0 4px; }
    body #helpDialog #helpContent .help-way { margin: 0; padding: 12px 12px 10px; box-sizing: border-box; border: 1px solid rgba(120, 170, 230, .14); border-radius: 10px; background: rgba(120, 170, 230, .06); text-align: center; }
    body #helpDialog #helpContent .help-way svg { display: block; width: 100%; height: auto; }
    body #helpDialog #helpContent .help-way figcaption { margin-top: 8px; color: #c3cdd8; font: 12px/1.4 "Segoe UI", Arial, sans-serif; }
    @media (max-width: 520px) { body #helpDialog #helpContent .help-ways { grid-template-columns: 1fr; } }
    body #helpDialog #helpContent .help-lines { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px 12px; margin: 8px 0 4px; }
    body #helpDialog #helpContent .help-line { margin: 0; text-align: center; }
    body #helpDialog #helpContent .help-line svg { display: block; width: 100%; height: auto; }
    body #helpDialog #helpContent .help-line figcaption { margin-top: 4px; color: #c3cdd8; font: 600 13px/1.4 "Segoe UI", Arial, sans-serif; font-variant-numeric: tabular-nums; }
    body #helpDialog #helpContent .help-inline-jp { font-weight: 800; letter-spacing: .08em; }   /* [GRAND]／[MAJOR]／[MINOR]／[MINI]：彩金列同色文字 */
    body #helpDialog #helpContent .help-inline-jp.is-grand { color: #ff7a84; }
    body #helpDialog #helpContent .help-inline-jp.is-major { color: #c597ff; }
    body #helpDialog #helpContent .help-inline-jp.is-minor { color: #62b9ff; }
    body #helpDialog #helpContent .help-inline-jp.is-mini { color: #6ce49c; }
    body #helpDialog #helpContent .help-inline-sym { width: 1.5em; height: 1.5em; object-fit: contain; vertical-align: -0.38em; margin: 0 .3em; transform: scale(1.7); }   /* 版面只占 1.5em 不撐高行高；美術圖四周留白多，用 scale 放大；左右只留一點空隙 */
    /* 2026-11-20 使用者：一般符號的賠率卡片也框起來，樣式同特殊符號卡片（淡底色＋細框），卡片之間留 10px */
    body #helpDialog #helpContent .help-sym-grid { gap: 10px; margin: 10px 0 18px; }
    body #helpDialog #helpContent .help-sym-grid > .help-sym-card { box-sizing: border-box; padding: 10px 14px; border: 1px solid rgba(120, 170, 230, .14); border-radius: 10px; background: rgba(120, 170, 230, .06); }
    body #helpDialog #helpContent .help-sym-specials ~ .help-sym-grid { margin-top: 10px; }
    body #helpDialog #helpContent .help-sym-label { color: #f5c542; font: 600 15px/1.35 "Segoe UI", Arial, sans-serif; white-space: normal; max-width: 7em; }
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

  // 賠率表標題依語言：中文「賠率表（目前押注：x）」、英文「Paytable (Current Bet: x)」
  function paytableTitle() {
    const zh = /^zh/i.test(document.getElementById("languageSelect")?.value || document.documentElement.lang || "");
    return zh ? `賠率表（目前押注：${currentBet()}）` : `Paytable (Current Bet: ${currentBet()})`;
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
    // 2026-11-20：遊戲宣告 window.DEMOGAME_HELP_CONFIG（config 物件）時改用 demogameHelp.configPaytable（全盤計數／Ways／Lines）
    if (root.querySelector(".help-load-error") && window.DEMOGAME_HELP_CONFIG && window.demogameHelp?.configPaytable) {
      const table = window.demogameHelp.configPaytable(window.DEMOGAME_HELP_CONFIG, window.DEMOGAME_HELP_CONFIG_OPTIONS || {});
      if (table) {
        const card = document.createElement("section");
        card.className = "help-section";
        card.innerHTML = `<h3 class="help-section-title">${paytableTitle()}</h3>`;
        card.appendChild(table);
        root.replaceChildren(card);
        return;
      }
    }
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
    card.innerHTML = `<h3 class="help-section-title">${paytableTitle()}</h3>`;
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
          line.innerHTML = `<span class="help-sym-count"></span><span class="help-sym-value"></span>`;
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

  // 2026-11-18 使用者：Help 照參考排版——賠率表的 Wild／Scatter 改成「符號圖＋金色名稱」卡片放在符號格最前面
  // （Scatter 獨佔一列置中），原本的說明文字移到符號格下方。
  const SPECIAL_CODES = { scatter: ["C1", "SC", "S1", "C"], wild: ["WW", "W", "WILD", "W1"] };
  // 2026-11-20 使用者：內文符號小圖跟字黏在一起（宙斯 C2／C3 美術幾乎沒透明邊，scale 1.7 後蓋到字）。
  // 依每張圖實際不透明範圍算左右 margin，讓圖的可見邊緣離字固定 GAP；量不到（file:// 跨來源）時當作沒留白，保證不重疊。
  const INLINE_SYM = { box: 1.5, scale: 1.7, gap: 0.25 };   // 與 CSS .help-inline-sym 的 width／scale 一致（em）
  const inlineSymPad = new Map();
  function inlineSymPadding(img) {
    const key = img.currentSrc || img.src;
    if (inlineSymPad.has(key)) return inlineSymPad.get(key);
    let pad = { l: 0, r: 0 };
    try {
      const w = img.naturalWidth, h = img.naturalHeight;
      const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
      const ctx = cv.getContext("2d"); ctx.drawImage(img, 0, 0);
      const data = ctx.getImageData(0, 0, w, h).data;
      let minX = w, maxX = -1;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (data[(y * w + x) * 4 + 3] > 20) { if (x < minX) minX = x; if (x > maxX) maxX = x; }
      if (maxX >= minX) {
        const fit = Math.min(1, w / h);              // object-fit: contain 時圖在方框內的寬度比例
        const off = (1 - fit) / 2;
        pad = { l: off + fit * (minX / w), r: off + fit * ((w - 1 - maxX) / w) };
      }
    } catch (_) { /* 跨來源讀不到像素：維持 0 留白 */ }
    inlineSymPad.set(key, pad);
    return pad;
  }
  function fitInlineSym(img) {
    const { box, scale, gap } = INLINE_SYM;
    const over = (box * scale - box) / 2;             // scale 後單邊多出的寬度
    const pad = inlineSymPadding(img);
    img.style.marginLeft = `${(gap + over - box * scale * pad.l).toFixed(3)}em`;
    img.style.marginRight = `${(gap + over - box * scale * pad.r).toFixed(3)}em`;
  }
  function specialCode(kind) {
    const art = window.DEMOGAME_SYMBOL_ART || {};
    return SPECIAL_CODES[kind].find((code) => { try { return Boolean(art[code]); } catch (_) { return false; } }) || SPECIAL_CODES[kind][0];
  }
  function buildSpecialCards(card) {
    const heads = [...card.querySelectorAll(":scope > .help-group-title")]
      .map((head) => ({ head, kind: /scatter|分散|散佈|散布|夺宝|奪寶/i.test(head.textContent) ? "scatter" : /wild|百搭/i.test(head.textContent) ? "wild"
        : /^\s*(multiplier symbols?|倍數符號|倍数符号)\s*$/i.test(head.textContent) ? "multiplier" : "" }))
      .filter((entry) => entry.kind);
    if (!heads.length) return;
    let grid = card.querySelector(".help-sym-grid");
    if (!grid) { grid = document.createElement("div"); grid.className = "help-sym-grid"; card.appendChild(grid); }
    // 2026-11-20 使用者（方案 A，再改成卡片）：特殊符號（WW／W2／C1／C2…）放在一般符號前，每個特殊符號一張有底色的卡片、「左圖右文」：
    // 左邊符號圖、右邊先是金色名稱（副標題）再是說明條列；說明跟其他區完全同一種排法（靠左、圓點、同字級行高）。卡片滿欄寬。
    // 先 Wild 後 Scatter；屬於賠率表這一區，跟一般符號之間不畫分隔線。
    // 2026-11-20 使用者：倍數符號（H027 [C2]／[C3]）也是特殊符號，做成同樣的卡片；左邊放說明裡提到的所有倍數符號圖（上下排）
    const KIND_CODE = { wild: /^(WW\d?|W\d?|WILD)$/i, scatter: /^(C\d?|SC|S\d)$/i, multiplier: /^(C\d|X\d*)$/i };
    const art = window.DEMOGAME_SYMBOL_ART || {};
    const blocks = [];
    for (const { head, kind } of heads) {
      const rules = [];
      let next = head.nextElementSibling;
      while (next && next.matches(".help-rule")) { rules.push(next); next = next.nextElementSibling; }
      const named = (head.textContent + " " + rules.map((r) => r.textContent).join(" ")).match(/\[([^\]]+)\]/g) || [];
      const codes = named.map((m) => m.slice(1, -1).trim());
      const block = document.createElement("div");
      block.className = `help-special-block is-${kind}`;
      if (kind === "multiplier") {
        const scatter = specialCode("scatter");
        const multi = [...new Set(codes)].filter((c) => KIND_CODE.multiplier.test(c) && c !== scatter && art[c]);
        if (!multi.length) continue;
        const stack = document.createElement("div");
        stack.className = "help-special-tiles";
        for (const c of multi) { const tile = symbolTile(c); tile.classList.add("help-special-tile"); stack.appendChild(tile); }
        block.appendChild(stack);
      } else {
        const code = codes.find((c) => KIND_CODE[kind].test(c)) || specialCode(kind);
        const tile = symbolTile(code);
        tile.classList.add("help-special-tile");
        block.appendChild(tile);
      }
      const body = document.createElement("div");
      body.className = "help-special-rules";
      // 名稱（百搭符號／散佈符號…，正式 Help 的副標題）留在卡片裡當小標
      const label = document.createElement("div");
      label.className = "help-special-name";
      label.textContent = titleCase(head.textContent.trim());
      body.appendChild(label);
      for (const rule of rules) body.appendChild(rule);
      block.appendChild(body);
      blocks.push({ kind, block });
      head.remove();
    }
    blocks.sort((a, b) => (a.kind === "wild" ? 0 : 1) - (b.kind === "wild" ? 0 : 1));
    const zone = document.createElement("div");
    zone.className = "help-sym-specials";
    for (const { block } of blocks) zone.appendChild(block);
    grid.before(zone);
  }

  // 全大寫的英文規則（Help.xlsx 原文）轉成句首大寫；[代號]、{數字}、縮寫（FG、RTP、C1…）維持原樣
  const KEEP_UPPER = new Set(["FG", "BG", "RTP", "WW", "OP", "RNG", "BF", "SF", "NB", "EB", "JP", "GRAND", "MAJOR", "MINOR", "MINI", "MAX", "ID", "OK"]);
  function sentenceCase(text) {
    const bare = text.replace(/\[[^\]]*\]|\{[^}]*\}/g, "");
    if (!/[A-Z]{2}/.test(bare) || /[a-z]/.test(bare)) return text;
    const parts = text.split(/(\[[^\]]*\]|\{[^}]*\})/);
    let out = parts.map((part, i) => (i % 2 ? part : part.replace(/[A-Za-z][A-Za-z0-9']*/g, (word) => {
      if (KEEP_UPPER.has(word)) return word;
      if (/^[A-WYZ]\d+$/.test(word)) return word;   // M1、C1 等符號代號（x2 倍數轉小寫）
      return word.toLowerCase();
    }))).join("");
    out = out.replace(/(^\s*|[.!?]\s+)([a-z])/g, (m, lead, ch) => lead + ch.toUpperCase());
    // 功能名稱維持首字大寫
    out = out.replace(/\b(super free games?|free games?|free spins?|extra bet|buy feature|super feature|op jackpot|wild|scatter)\b/gi, (m) => m.replace(/\b[a-z]/g, (c) => c.toUpperCase()));
    return out;
  }
  function sentenceCaseRules(card) {
    for (const rule of card.querySelectorAll(".help-rule")) {
      for (const target of rule.querySelectorAll(".help-rule-en, .help-rule-zh").length ? rule.querySelectorAll(".help-rule-en, .help-rule-zh") : [rule]) {
        if (target.children.length) continue;
        const next = sentenceCase(target.textContent);
        if (next !== target.textContent) target.textContent = next;
      }
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

  // 2026-11-20 使用者：Help 內文裡的 [代號]（[WW]、[C1]、[M1]…）一律換成內嵌符號小圖；
  // 遊戲沒提供那個代號的圖（DEMOGAME_SYMBOL_ART 沒有，或 Image 關閉）就維持原文字，不硬換。小圖不撐高行高。
  function inlineRuleSymbols(card) {
    const art = window.DEMOGAME_SYMBOL_IMAGES_ENABLED !== false ? (window.DEMOGAME_SYMBOL_ART || {}) : {};
    for (const rule of card.querySelectorAll(".help-rule")) {
      const walker = document.createTreeWalker(rule, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) if (/\[[^\]]+\]/.test(walker.currentNode.nodeValue)) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const parts = node.nodeValue.split(/(\[[^\]]+\])/);
        const JP = /^(GRAND|MAJOR|MINOR|MINI)$/i;
        if (!parts.some((part) => /^\[[^\]]+\]$/.test(part) && (art[part.slice(1, -1).trim()] || JP.test(part.slice(1, -1).trim())))) continue;
        const frag = document.createDocumentFragment();
        const isArt = (part) => /^\[[^\]]+\]$/.test(part || "") && Boolean(art[part.slice(1, -1).trim()]);
        for (let k = 0; k < parts.length; k++) {
          let part = parts[k];
          // 2026-11-20：符號小圖左右不留原文的空白（圖自己有左右間距），不然看起來空一大格
          if (!/^\[[^\]]+\]$/.test(part)) {
            if (isArt(parts[k + 1])) part = part.replace(/\s+$/, "");
            if (isArt(parts[k - 1])) part = part.replace(/^\s+/, "");
          }
          const code = /^\[[^\]]+\]$/.test(part) ? part.slice(1, -1).trim() : "";
          if (code && art[code]) {
            const img = document.createElement("img");
            img.className = "help-inline-sym"; img.alt = code; img.draggable = false;
            img.addEventListener("load", () => fitInlineSym(img), { once: true });
            img.src = art[code];
            frag.appendChild(img);
          } else if (code && JP.test(code)) {
            // 2026-11-20 使用者：彩金名稱用彩金列那種有顏色的字（GRAND 紅、MAJOR 紫、MINOR 藍、MINI 綠），不留中括號
            const tag = document.createElement("span");
            tag.className = `help-inline-jp is-${code.toLowerCase()}`;
            tag.textContent = code.toUpperCase();
            frag.appendChild(tag);
          } else if (part) frag.appendChild(document.createTextNode(part));
        }
        node.replaceWith(frag);
      }
    }
  }

  // 2026-11-20 使用者：走線圖（正式 Help 的 [走線圖-1,024 MAX WAYS]／[走線圖-3 OF A KIND PAYS 2 WAYS]／[走線圖-NO WIN] 佔位列）
  // 畫成盤面小圖：一格一格的盤面、圓點代表符號位置；NO WIN 那張把中斷的那一軸整軸標紅。連續的佔位列排成一橫排，圖下寫說明。
  // 盤面大小取 window.DEMOGAME_WAY_BOARD = [軸數, 列數]，沒宣告就讀 config 的 reel_num／window_size，再沒有用 5×4。
  function wayBoardSize() {
    const set = window.DEMOGAME_WAY_BOARD;
    if (Array.isArray(set) && set[0] > 0 && set[1] > 0) return [Number(set[0]), Number(set[1])];
    const c = getMathConfig() || {};
    const reels = Number(c.reel_num || c.reels || c.reel_count) || 5;
    const rows = Number(c.window_size || c.rows || c.row_num) || 4;
    return [reels, rows];
  }
  function wayDiagramSvg(label) {
    const [reels, rows] = wayBoardSize();
    const dots = new Set();
    let redReel = -1;
    const put = (reel, rowFromBottom) => { if (reel < reels && rowFromBottom < rows) dots.add(`${reel},${rows - 1 - rowFromBottom}`); };
    if (/no\s*win/i.test(label)) {
      // 第 2 軸沒有相同符號 → 連不起來
      redReel = 1;
      put(0, 0); put(2, 1); put(2, 2); put(3, 1);
    } else if (/max\s*ways/i.test(label)) {
      for (let reel = 0; reel < reels; reel++) for (let row = 0; row < rows; row++) dots.add(`${reel},${row}`);
    } else {
      // 3 連、2 路：第 1 軸 1 顆 × 第 2 軸 2 顆 × 第 3 軸 1 顆
      put(0, 0); put(1, 0); put(1, 1); put(2, 1);
    }
    const S = 30, W = reels * S, H = rows * S;
    let out = `<svg viewBox="-1 -1 ${W + 2} ${H + 2}" role="img" aria-label="${label.replace(/"/g, "")}">`;
    out += `<rect x="0" y="0" width="${W}" height="${H}" rx="3" fill="rgba(120,170,230,.06)"/>`;
    if (redReel >= 0) out += `<rect x="${redReel * S}" y="0" width="${S}" height="${H}" fill="rgba(255,110,120,.30)"/>`;
    for (let reel = 0; reel <= reels; reel++) out += `<line x1="${reel * S}" y1="0" x2="${reel * S}" y2="${H}" stroke="rgba(150,190,240,.45)" stroke-width="1"/>`;
    for (let row = 0; row <= rows; row++) out += `<line x1="0" y1="${row * S}" x2="${W}" y2="${row * S}" stroke="rgba(150,190,240,.45)" stroke-width="1"/>`;
    for (const key of dots) {
      const [reel, row] = key.split(",").map(Number);
      out += `<circle cx="${reel * S + S / 2}" cy="${row * S + S / 2}" r="${S * 0.3}" fill="#f5c542"/>`;
    }
    return out + "</svg>";
  }
  // 2026-11-20 使用者：Megaways 走線圖——盤面畫出實際形狀：各軸高度可變、上方額外橫軸畫在盤面上方。
  // 遊戲宣告 window.DEMOGAME_WAY_SHAPE = { reels: 6, rows: 5, top: [2, 5] }（rows＝主盤面每軸最多格數；top＝上方額外橫軸涵蓋的軸，1 起算，沒有就省略）。
  // MAX WAY：每軸最多格數、全部有圓點；另外兩張用高度不一的格子示範（大符號占多格仍算 1 顆）；NO WIN 把第 2 軸整軸標紅。
  function megaWayDiagramSvg(label, shape) {
    const reels = Math.max(3, Number(shape.reels) || 6), rows = Math.max(2, Number(shape.rows) || 5);
    const top = Array.isArray(shape.top) && shape.top.length === 2 ? [Number(shape.top[0]) - 1, Number(shape.top[1]) - 1] : null;
    const isMax = /max\s*ways?/i.test(label), noWin = /no\s*win/i.test(label);
    const S = 30, offY = top ? S : 0, W = reels * S, H = rows * S + offY;
    const line = "rgba(150,190,240,.45)", fill = "rgba(120,170,230,.06)", dot = "#f5c542";
    // 示範用的各軸格數（高度不一）；MAX 用每軸最多格數
    const sample = [rows, Math.max(2, rows - 2), Math.max(2, rows - 1), 2, rows, rows];
    const heights = Array.from({ length: reels }, (_, reel) => (isMax ? rows : Math.min(rows, sample[reel % sample.length])));
    let out = `<svg viewBox="-1 -1 ${W + 2} ${H + 2}" role="img" aria-label="${label.replace(/"/g, "")}">`;
    const cell = (x, y, w, h, red) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${red ? "rgba(255,110,120,.30)" : fill}" stroke="${line}" stroke-width="1"/>`;
    const circle = (cx, cy, r) => `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${dot}"/>`;
    if (top) for (let reel = top[0]; reel <= top[1] && reel < reels; reel++) {
      out += cell(reel * S, 0, S, S, false);
      if (isMax) out += circle(reel * S + S / 2, S / 2, S * 0.3);
    }
    for (let reel = 0; reel < reels; reel++) {
      const n = heights[reel], h = rows * S / n, red = noWin && reel === 1;
      // 圓點位置（由下往上數第幾格）：3 連 2 路＝第 1 軸 1 顆 × 第 2 軸 1 顆 × 第 3 軸 2 顆；NO WIN＝第 2 軸沒有
      let marks = [];
      if (isMax) marks = Array.from({ length: n }, (_, k) => k);
      else if (reel === 0) marks = [0];
      else if (reel === 1) marks = noWin ? [] : [0];
      else if (reel === 2) marks = [0, n - 1];
      for (let k = 0; k < n; k++) {
        const y = offY + rows * S - (k + 1) * h;
        out += cell(reel * S, y, S, h, red);
        if (marks.includes(k)) out += circle(reel * S + S / 2, y + h / 2, Math.min(S, h) * 0.3);
      }
    }
    return out + "</svg>";
  }

  // 2026-11-20 使用者：Line Game 走線圖——每條賠付線一張小盤面圖，線經過的格子標亮（金色）、其餘暗色，圖下寫兩位數線號，一橫排 4 張。
  // 賠付線取自遊戲設定（window.DEMOGAME_PAYLINES，或 config／Box 資料的 paylines：每條線是「各軸在第幾列（0＝最上列）」的陣列），不手寫。
  function findPaylines() {
    const ok = (v) => Array.isArray(v) && v.length && v.every((l) => Array.isArray(l) && l.length && l.every((r) => Number.isInteger(r) && r >= 0));
    if (ok(window.DEMOGAME_PAYLINES)) return window.DEMOGAME_PAYLINES;
    const seen = [];
    try { if (typeof Box !== "undefined" && Box) seen.push(Box); } catch (_) {}
    try { if (typeof data !== "undefined" && data) seen.push(data); } catch (_) {}
    for (const key of Object.keys(window)) {
      if (!/(?:_BOX_DATA|_CONFIG|_CONFIG_RTP)$/.test(key)) continue;
      const value = window[key];
      if (value && typeof value === "object") seen.push(value, value.rtp_config);
    }
    for (const src of seen) if (src && ok(src.paylines)) return src.paylines;
    return null;
  }
  function lineDiagramSvg(payline, rows) {
    const reels = payline.length, S = 20, G = 3, W = reels * S + (reels + 1) * G, H = rows * S + (rows + 1) * G;
    let out = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="payline"><rect x="0" y="0" width="${W}" height="${H}" rx="4" fill="rgba(120,170,230,.10)"/>`;
    for (let reel = 0; reel < reels; reel++) for (let row = 0; row < rows; row++) {
      const on = payline[reel] === row;
      out += `<rect x="${G + reel * (S + G)}" y="${G + row * (S + G)}" width="${S}" height="${S}" rx="2" fill="${on ? "#f5c542" : "rgba(150,190,240,.22)"}"/>`;
    }
    return out + "</svg>";
  }

  const WAY_PLACEHOLDER = /^\s*[▪•·]?\s*\[\s*(?:走[線线]圖|PAYLINE\s+DIAGRAM)\s*[-－–]?\s*([^\]]+)\]\s*$/i;
  function buildWayDiagrams(card) {
    const rules = [...card.querySelectorAll(".help-rule")].filter((rule) => WAY_PLACEHOLDER.test(rule.textContent));
    if (!rules.length) return;
    const shape = window.DEMOGAME_WAY_SHAPE && typeof window.DEMOGAME_WAY_SHAPE === "object" ? window.DEMOGAME_WAY_SHAPE : null;
    let row = null, prev = null;
    for (const rule of rules) {
      const label = rule.textContent.match(WAY_PLACEHOLDER)[1].trim();
      // Line Game：[走線圖 20 LINE]／[PAYLINE DIAGRAM 20 LINE] → 每條線一張小圖
      if (/\d+\s*LINES?\b/i.test(label) && !/ways?/i.test(label)) {
        const paylines = findPaylines();
        if (!paylines) continue;   // 讀不到賠付線就維持原文字，不亂畫
        const rowsCount = Number(window.DEMOGAME_WAY_BOARD?.[1]) || Math.max(...paylines.flat()) + 1;
        const wrap = document.createElement("div");
        wrap.className = "help-lines";
        paylines.forEach((payline, index) => {
          const item = document.createElement("figure");
          item.className = "help-line";
          item.innerHTML = lineDiagramSvg(payline, rowsCount);
          const cap = document.createElement("figcaption");
          cap.textContent = String(index + 1).padStart(2, "0");
          item.appendChild(cap);
          wrap.appendChild(item);
        });
        rule.replaceWith(wrap);
        row = null; prev = null;
        continue;
      }
      if (!row || prev?.nextElementSibling !== rule) {
        row = document.createElement("div");
        row.className = "help-ways";
        rule.before(row);
      }
      const item = document.createElement("figure");
      item.className = "help-way";
      item.innerHTML = shape ? megaWayDiagramSvg(label, shape) : wayDiagramSvg(label);
      const cap = document.createElement("figcaption");
      cap.textContent = label.toUpperCase();
      item.appendChild(cap);
      row.appendChild(item);
      rule.remove();
      prev = row;
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
          const expected = paytableTitle();
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
          buildSpecialCards(card);
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
        sentenceCaseRules(card);
        buildWayDiagrams(card);
        inlineRuleSymbols(card);
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
    if (/^SCATTER/.test(text)) return "C1";   // 代號統一：Scatter 顯示 C1、Wild 顯示 WW
    const match = text.match(/^(M\d+|W\d|WW\d?|WILD|C\d|SC|TE|10|A|K|Q|J)/);
    return match ? match[1].replace(/^WILD$/, "WW") : "";
  };
  const tag = () => {
    // 盤面重畫（例如顯示得分框）時符號圖會重建：同步解碼，避免沒得分的符號空白一格畫面而閃一下
    for (const img of document.querySelectorAll("#board img:not([decoding='sync'])")) img.decoding = "sync";
    for (const cell of document.querySelectorAll("#board .cell")) {
      const code = cell.matches(".has-symbol-art, .sym-digit") ? "" : codeOf(cell);   // H014 數字格不套用
      // 只露出一部分的格子（例如 H026 頂端 peek 列）：標 data-dg-cut，畫成「整顆符號被盤面上緣截斷」
      // 沒圖時顯示的名稱統一成代號：Scatter → C1、Wild → WW（所有遊戲）
      if (code && !cell.matches(".has-symbol-art")) {
        for (const node of cell.querySelectorAll(LABEL)) {
          const t = node.textContent.trim();
          if (/^scatter$/i.test(t)) node.textContent = "C1";
          else if (/^wild$/i.test(t)) node.textContent = "WW";
        }
      }
      const cut = cell.offsetHeight > 0 && cell.offsetHeight < cell.offsetWidth * 0.8;
      if (cut !== ("dgCut" in cell.dataset)) { if (cut) cell.dataset.dgCut = ""; else delete cell.dataset.dgCut; }
      if ((cell.dataset.dgSym || "") !== code) {
        if (code) cell.dataset.dgSym = code; else delete cell.dataset.dgSym;
      }
      // H020 這類格子內另有 .tile 底板：配色畫在 .tile 上
      const tile = cell.querySelector(":scope > .tile");
      if (tile && (tile.dataset.dgSym || "") !== code) {
        if (code) tile.dataset.dgSym = code; else delete tile.dataset.dgSym;
      }
    }
  };
  // MutationObserver 回呼在畫面重繪前執行：同步標記，避免 Spin 時先畫成原樣式再換色而閃爍
  // 盤面重畫時（例如顯示得分框）符號沒變的格子沿用原本的圖片元素：沒得分的符號不重畫、不閃，只有得分格改變
  const reuseImages = (records, board) => {
    const removed = [], added = [];
    for (const record of records || []) {
      if (record.type !== "childList" || record.target !== board) continue;
      record.removedNodes.forEach((node) => { if (node.nodeType === 1 && node.classList.contains("cell")) removed.push(node); });
      record.addedNodes.forEach((node) => { if (node.nodeType === 1 && node.classList.contains("cell") && node.isConnected) added.push(node); });
    }
    if (!removed.length || !added.length) return;
    added.forEach((cell, index) => {
      const old = removed[index];
      if (!old) return;
      const oldImgs = [...old.querySelectorAll("img")], newImgs = [...cell.querySelectorAll("img")];
      if (!oldImgs.length || oldImgs.length !== newImgs.length) return;
      newImgs.forEach((img, k) => {
        const keep = oldImgs[k];
        if (keep.getAttribute("src") !== img.getAttribute("src")) return;
        keep.className = img.className;
        keep.style.cssText = img.style.cssText;
        img.replaceWith(keep);
      });
    });
  };
  let tagging = false;
  const schedule = (records) => {
    if (tagging) return;
    tagging = true;
    try { reuseImages(records, document.getElementById("board")); tag(); } finally { tagging = false; }
  };
  const start = () => {
    const board = document.getElementById("board");
    if (!board) return;
    tag();
    new MutationObserver(schedule).observe(board, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
  window.demogameTagSymbols = () => schedule([]);   // 共用動畫重畫盤面後立即上色（不等觀察者），避免先以原樣式算版面

  // 得分格（hit）照樣套底色，只由「得分框」規則換外框
  const free = ":not(.has-symbol-art):not(.convert):not(.wild-mark):not(.symbol-cleared):not(.empty):not(.symbol-empty):not(:has(> .tile))";
  // Help 賠率表的代號方格（沒圖時）與盤面同一套配色
  const base = `:is(body #board .cell[data-dg-sym]${free}, body #board .cell:not(.has-symbol-art) > .tile[data-dg-sym], body #helpDialog #helpContent .help-sym-tile[data-dg-sym]:not(.has-art))`;
  // 金框格：保留符號原底色，只把外框換成金色（兩個 :not(#…) 只為提高優先權）
  const gold = `body #board .cell:is(.gold,.special-gold)${free}:not(#dg-g1):not(#dg-g2)`;
  const label = `:is(${LABEL})`;
  // M 獎：同亮度、不同色相的低彩度漸層，字獎深藍；上緣一條淡高光，整體與金框同一套質感
  const tone = (code, top, bottom, border) => `${base}[data-dg-sym="${code}"]{background:linear-gradient(180deg,${top} 0%,${bottom} 100%)!important;border-color:${border}!important}`;
  const style = document.createElement("style");
  // 盤面符號不做顏色／框線過渡：重畫時若先以原樣式算出版面再上色，過渡會讓整盤閃一下
  style.textContent = `body #board .cell,body #board .cell > .tile{transition:none!important}
    ${base}{background:linear-gradient(180deg,#0c1828 0%,#060d1a 100%)!important;border:1.6px solid rgba(70,120,170,.42)!important;border-radius:8px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)!important;color:#d8e8f4!important}
    ${tone("M1", "#5b2733", "#33141c", "#9c5664")}
    ${tone("M2", "#3f2f68", "#221840", "#7c68b8")}
    ${tone("M3", "#1f4d3e", "#112b23", "#4f957d")}
    ${tone("M4", "#24426e", "#132643", "#5a85bf")}
    ${tone("M5", "#1d4c55", "#0f2b31", "#4a959d")}
    ${tone("M6", "#5a2f50", "#321a2d", "#a0628f")}
    ${tone("M7", "#5a4024", "#322312", "#a07a50")}
    ${tone("M8", "#3f4a2a", "#232a16", "#7f8f55")}
    ${base}:is([data-dg-sym^="C"],[data-dg-sym="SC"]){background:linear-gradient(180deg,#ffc58a 0%,#f07a28 45%,#a8400c 100%)!important;border:1.6px solid #ffa860!important;box-shadow:inset 0 1px 0 rgba(255,240,220,.55)!important;color:#fff6ee!important}
    ${base}:is([data-dg-sym^="C"],[data-dg-sym="SC"]) ${label}{text-shadow:0 1px 2px rgba(80,25,0,.6)!important}
    ${base}:is([data-dg-sym^="W"]){background:linear-gradient(180deg,#22706a 0%,#0f3d3a 100%)!important;border-color:#3fd6c4!important;color:#d6fff8!important}
    ${gold}{border:1.6px solid #f1c35a!important;box-shadow:inset 0 0 0 1px rgba(241,195,90,.3)!important}
    ${gold}[data-dg-cut]{border-top-width:0!important;border-top-left-radius:0!important;border-top-right-radius:0!important;box-shadow:none!important}
    :is(${base},${gold}):not(.sym-digit) ${label}{font-family:Consolas,"Courier New",monospace!important;font-weight:400!important;font-size:19px!important;line-height:1!important;margin:0!important;padding:0!important;background:transparent!important;box-shadow:none!important;border:0!important;text-align:center!important}
    ${base}:not(.sym-digit):not(:has(> .tile)){display:grid!important;place-items:center!important}
    ${base}:not(.sym-digit):not(:has(> .tile)) > *{grid-area:1/1}
    ${base}:not(.sym-digit) ${label}{position:static!important;left:auto!important;top:auto!important;transform:none!important}
    ${base}[data-dg-cut]{display:block!important;overflow:hidden!important;border-top-width:0!important;border-top-left-radius:0!important;border-top-right-radius:0!important;background-position:bottom!important}
    ${base}[data-dg-cut] > *:not(#dg-cut){position:absolute!important;left:0!important;right:0!important;bottom:0!important;top:auto!important;aspect-ratio:1/1;height:auto!important;width:auto!important;display:grid!important;place-items:center!important;margin:0!important;padding:0!important;background:transparent!important;border:0!important}
    ${base}:not(.sym-digit) > .symbol-wrap{display:grid!important;place-items:center!important}
    ${base}:not(.sym-digit) ${label}{color:inherit!important;text-shadow:none!important}`;
  document.head.appendChild(style);
})();

// 得分符號只換外框顏色（藍框，2026-10-19 由金黃改藍）框起來（共用，2026-10-17）：不放大、不閃、不跳，各遊戲原本的中獎動畫一律停掉；
// 消除（symbol-cleared）與掉落動畫不受影響。
(() => {
  "use strict";
  // 兩個 :not(#…) 只為提高優先權，蓋過無圖符號配色的外框
  // 倍數格（例如 H020 右側 WIN MULTIPLIER 轉輪）連線時不加得分框
  const hit = "body #board .cell:is(.hit,.fx-win,.h014-hit,.h020-hit):not(.symbol-cleared):not(.sym-mult):not(.reel.r4 .cell):not(#dg-x):not(#dg-y)";
  const style = document.createElement("style");
  // 得分格本身不放大；裡面的元素只停動畫，不清除靜態縮放（例如素材留白多而放大的符號圖），得分時符號大小不變
  style.textContent = `${hit}{transform:none!important}
    ${hit},${hit} *{animation:none!important;filter:none!important;transition:none!important}
    ${hit}{border:1.6px solid #4fc3ff!important;outline:0!important;box-shadow:0 0 8px rgba(79,195,255,.45)!important;z-index:5}
    ${hit}[data-dg-cut]{border-top-width:0!important;border-top-left-radius:0!important;border-top-right-radius:0!important}
    ${hit}:is(.gold,.special-gold){border-color:#f1c35a!important;box-shadow:0 0 0 2px #4fc3ff,0 0 8px rgba(79,195,255,.45)!important}
    ${hit}::before,${hit}::after{box-shadow:none!important;border-color:transparent!important}
    body #board :is(.reel.r4 .cell,.cell.sym-mult):is(.hit,.h020-hit)::after{display:none!important}
    body #board :is(.reel.r4 .cell,.cell.sym-mult):is(.hit,.h020-hit) *{animation:none!important;filter:none!important}
    ${hit}:has(> .tile){border:0!important;outline:0!important;box-shadow:none!important;background:transparent!important}
    ${hit} > .tile{border:1.6px solid #4fc3ff!important;box-shadow:0 0 8px rgba(79,195,255,.45)!important}`;
  document.head.appendChild(style);
})();

// 動畫時間統一（共用，2026-10-17）：所有遊戲的轉輪與補牌都讀這裡，跟著 Speed 1～5 走。
// - reelSpinMs：一輪從開始滾動到停下的時間；第一輪滾這麼久，之後每輪再錯開 stopStaggerMs（Speed 5 不錯開、同時停）。
// - dropMs：掉落補牌（既有符號下移＋新符號落入）整段時間＝reelSpinMs。
// - growMs：原地補牌不播掉落，新符號在原位「長出來」（縮放 0→1）的時間＝reelSpinMs。
// - grow(cells)：替原地補牌的新符號套上長出來動畫。
(() => {
  "use strict";
  const SPIN = [700, 520, 380, 260, 180];
  const STAGGER = [120, 100, 80, 60, 0];
  const level = () => Math.min(5, Math.max(1, Math.round(Number(document.getElementById("speedRange")?.value) || 1)));
  const style = document.createElement("style");
  style.textContent = `@keyframes demogame-grow{0%{transform:scale(0);opacity:0}70%{transform:scale(1.06);opacity:1}100%{transform:scale(1);opacity:1}}
    #board .cell.demogame-grow > *{animation:demogame-grow var(--dg-grow-ms,380ms) cubic-bezier(.2,.8,.3,1) both}`;
  document.head.appendChild(style);
  const motion = {
    level,
    reelSpinMs: () => SPIN[level() - 1],
    stopStaggerMs: () => STAGGER[level() - 1],
    dropMs: () => SPIN[level() - 1],
    growMs: () => SPIN[level() - 1],
    grow(cells) {
      const ms = motion.growMs();
      for (const cell of cells || []) {
        if (!cell) continue;
        cell.classList.remove("demogame-grow");
        void cell.offsetWidth;
        cell.style.setProperty("--dg-grow-ms", `${ms}ms`);
        cell.classList.add("demogame-grow");
        setTimeout(() => cell.classList.remove("demogame-grow"), ms + 50);
      }
      return ms;
    }
  };
  window.demogameMotion = motion;
})();

// 掉落類 Spin（共用，2026-10-19）：沒有整條輪帶滾動，舊盤面整欄往下掉出、新符號整欄從上方掉入並輕微回彈；
// 由左到右逐欄錯開（Speed 5 同時），每欄時間＝reelSpinMs。只做畫面，不動結果。
// 用法：await demogameMotion.dropSpin(board, columnsOf, render)
//   columnsOf()：回傳目前盤面每欄由上到下的 .cell 節點；render()：畫出結果盤面（同步）。
(() => {
  "use strict";
  const motion = window.demogameMotion;
  if (!motion) return;
  const offsetIn = (node, host) => {
    let x = 0, y = 0, n = node;
    while (n && n !== host) {
      x += n.offsetLeft; y += n.offsetTop;
      n = n.offsetParent;
      if (n && n !== host) { x += n.clientLeft; y += n.clientTop; }
    }
    return { x, y };
  };
  const strip = ["hit", "symbol-cleared", "symbol-drop", "symbol-settle", "symbol-refill", "reel-spin", "demogame-grow"];
  const clone = (cell, box, left, top) => {
    const copy = cell.cloneNode(true);
    copy.classList.remove(...strip);
    [...copy.classList].forEach((name) => { if (name.startsWith("fx-")) copy.classList.remove(name); });
    copy.removeAttribute("id");
    copy.style.cssText += `;position:absolute;margin:0;left:${box.x - left}px;top:${box.y - top}px;width:${box.w}px;height:${box.h}px;box-sizing:border-box;animation:none;transition:none;visibility:visible`;
    return copy;
  };
  motion.dropSpin = async (board, columnsOf, render) => {
    if (!board) { render?.(); return; }
    const spinMs = motion.reelSpinMs(), gapMs = motion.stopStaggerMs();
    // 舊盤面：先記下位置與複本
    // 位置與尺寸一律用精確小數（getBoundingClientRect），複本與真格逐像素對齊，落定換回真格時不會跳 1px
    const probe = document.createElement("div");
    probe.style.position = "absolute";
    board.appendChild(probe);
    const host = probe.offsetParent || document.body;
    probe.remove();
    const rectIn = (node) => {
      const r = node.getBoundingClientRect(), h = host.getBoundingClientRect();
      return { x: r.left - h.left - host.clientLeft + host.scrollLeft, y: r.top - h.top - host.clientTop + host.scrollTop, w: r.width, h: r.height };
    };
    const oldCols = (columnsOf() || []).map((list) => (list || []).filter(Boolean).map((cell) => { const box = rectIn(cell); return { node: clone(cell, box, 0, 0), ...box }; }));
    render?.();
    window.demogameTagSymbols?.();
    const newCols = (columnsOf() || []).map((list) => (list || []).filter(Boolean));
    const windows = [], hidden = [];
    const jobs = newCols.map((cells, col) => {
      if (!cells.length) return Promise.resolve();
      const win = document.createElement("div");
      win.className = "dg-reel-window";
      win.style.cssText = "position:absolute;overflow:hidden;z-index:6;pointer-events:none;margin:0;padding:0;border:0;background:transparent";
      board.appendChild(win);
      windows.push(win);
      const boxes = cells.map((cell) => ({ cell, ...rectIn(cell) }));
      const left = Math.min(...boxes.map((b) => b.x)) - 3, top = Math.min(...boxes.map((b) => b.y));   // 左右各留 3px，滾動時格子外框／光暈不被遮罩切到
      const right = Math.max(...boxes.map((b) => b.x + b.w)) + 3, bottom = Math.max(...boxes.map((b) => b.y + b.h));
      const height = bottom - top;
      Object.assign(win.style, { left: `${left}px`, top: `${top}px`, width: `${right - left}px`, height: `${height}px` });
      const ms = spinMs + gapMs * col;
      const delay = gapMs * col;
      // 舊符號往下掉出
      const outLayer = document.createElement("div");
      outLayer.style.cssText = "position:absolute;inset:0";
      (oldCols[col] || []).forEach((o) => { o.node.style.left = `${o.x - left}px`; o.node.style.top = `${o.y - top}px`; outLayer.appendChild(o.node); });
      // 新符號從上方掉入
      const inLayer = document.createElement("div");
      inLayer.style.cssText = "position:absolute;inset:0";
      boxes.forEach((b) => inLayer.appendChild(clone(b.cell, b, left, top)));
      win.append(outLayer, inLayer);
      cells.forEach((cell) => { cell.style.visibility = "hidden"; hidden.push(cell); });
      // 舊符號完全掉出後新符號才掉入（不重疊），同一格不會看到符號一直換
      const fall = Math.max(100, (ms - delay) * 0.38);
      const out = outLayer.animate([{ transform: "translateY(0)" }, { transform: `translateY(${height + 20}px)` }], { duration: fall, delay, easing: "cubic-bezier(.5,0,.9,.6)", fill: "both" });
      const inStart = delay + fall, inMs = Math.max(140, ms - inStart);
      const drop = inLayer.animate([
        { transform: `translateY(${-(height + 20)}px)`, easing: "cubic-bezier(.45,0,.85,.55)" },
        { transform: `translateY(${Math.min(14, height * 0.05)}px)`, offset: 0.8, easing: "cubic-bezier(.3,0,.4,1)" },
        { transform: "translateY(0)" }
      ], { duration: inMs, delay: inStart, fill: "both" });
      // 舊符號掉出後立刻移除圖層：不可 cancel 回原位，否則舊符號會在新符號落定後又出現
      out.onfinish = () => outLayer.remove();
      return new Promise((resolve) => { drop.onfinish = resolve; setTimeout(resolve, ms + 80); }).then(() => { outLayer.remove(); });
    });
    await Promise.all(jobs);
    windows.forEach((win) => win.remove());
    hidden.forEach((cell) => { cell.style.visibility = ""; });
  };
})();

// 符號一體（共用，2026-10-19）：符號的字、框、底板是一體，動畫一律整格一起動，不能只有部分變化；
// 顯示得分框時，沒得分的符號完全不變（不變暗、不變框）。
(() => {
  "use strict";
  const style = document.createElement("style");
  style.textContent = `body #board .cell.fx-dim{filter:none!important;opacity:1!important}
    body #board .cell.demogame-grow{animation:demogame-grow var(--dg-grow-ms,380ms) cubic-bezier(.2,.8,.3,1) both!important}
    body #board .cell.demogame-grow > *{animation:none!important}
    body #board .cell.symbol-cleared{animation:slot-symbol-clear 180ms ease-in forwards!important}
    body #board .cell.symbol-cleared > *{animation:none!important}
    body #board .cell.symbol-refill:not(.symbol-drop):not(.symbol-settle):not(.tc-drop-new):not(.tc-settle){animation:slot-symbol-refill var(--refill-duration,420ms) cubic-bezier(.2,.75,.25,1) both!important}
    body #board .cell.symbol-refill > *{animation:none!important}
    body #board .cell.fx-pop{animation:slot-fx-pop 300ms ease-in forwards!important}
    body #board .cell.fx-pop > *{animation:none!important}
    body #board .cell.tc-drop-new > *{animation:none!important}`;
  document.head.appendChild(style);
})();

// 手機連點不放大（共用，2026-10-19）：關掉雙擊縮放（連點 Spin 等按鈕會觸發放大），雙指縮放仍可用
(() => {
  "use strict";
  const style = document.createElement("style");
  style.textContent = "html,body,button,select,input,label,#board,#board *{touch-action:manipulation}";
  document.head.appendChild(style);
  // iPhone 有時不理 touch-action：再鎖縮放比例＝1，並擋掉 300ms 內的第二下點擊（雙擊放大）
  let viewport = document.querySelector('meta[name="viewport"]');
  if (!viewport) { viewport = document.createElement("meta"); viewport.name = "viewport"; document.head.appendChild(viewport); }
  if (!/maximum-scale/.test(viewport.content || "")) viewport.content = `${viewport.content || "width=device-width, initial-scale=1"}, maximum-scale=1`;
  let lastTouchEnd = 0;
  document.addEventListener("touchend", (event) => {
    const now = Date.now();
    if (now - lastTouchEnd < 300 && !event.target.closest?.("input, textarea, select")) {
      event.preventDefault();
      event.target.click?.();   // 被擋掉的那一下照樣算一次點擊（連點 Spin 不漏按）
    }
    lastTouchEnd = now;
  }, { passive: false });
  document.addEventListener("dblclick", (event) => event.preventDefault());
})();

// ==== chart-hover-auto（來源：專案需知/其他/chart_hover.js，改那份再同步）====
/* 倍率線型滑鼠提示（通用版）：滑鼠移到圖上，鎖定最近的倍率區間，列出各條線的數值。
 * 適用直接畫好的 SVG 折線圖（縱軸 % 刻度＋橫軸旋轉 -90° 的區間標籤），數值由 SVG 座標反推。
 * 已有自己提示的圖（.chart[data-hover]、或 SVG 內有透明 rect 偵測層）不處理。
 * 來源：專案需知/其他/chart_hover.js；由 _chart_hover.py 內嵌進網頁、demogame_common.js 也帶同一份。
 */
(function () {
  if (window.__chartHoverAuto) return;
  window.__chartHoverAuto = true;
  var NS = "http://www.w3.org/2000/svg";
  var tip = null, cur = null;

  function own(svg) {
    return svg.closest(".chart[data-hover]") || svg.querySelector('rect[fill="transparent"]');
  }
  function toSvg(svg, el) {   // el 的座標 → svg viewBox 座標
    var a = svg.getScreenCTM(), b = el.getScreenCTM();
    return a && b ? a.inverse().multiply(b) : null;
  }
  function pt(m, x, y) { return { x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f }; }
  function rotated(t) {
    var s = (t.getAttribute("transform") || "") + " " + (t.parentNode.getAttribute && t.parentNode.getAttribute("transform") || "");
    return /rotate\(\s*-?90/.test(s);
  }
  function colorOf(el, prop) {
    var c = getComputedStyle(el)[prop];
    return c && c !== "none" && !/rgba\([^)]*,\s*0(\.0+)?\)$/.test(c) ? c : "";
  }
  function hiddenEl(el) {
    for (var e = el; e && e.nodeType === 1; e = e.parentNode) {
      if (getComputedStyle(e).display === "none") return true;
    }
    return false;
  }
  function parse(svg) {
    var texts = [].slice.call(svg.querySelectorAll("text"));
    var labels = [], ticks = [];
    texts.forEach(function (t) {
      var m = toSvg(svg, t); if (!m) return;
      var p = pt(m, parseFloat(t.getAttribute("x")) || 0, parseFloat(t.getAttribute("y")) || 0);
      var s = t.textContent.trim();
      if (rotated(t)) { if (s) labels.push({ x: p.x, lab: s }); }
      else {
        var v = /^(-?\d+(?:\.\d+)?)\s*%$/.exec(s);
        if (v) ticks.push({ y: p.y, v: parseFloat(v[1]), x: p.x });
      }
    });
    if (labels.length < 3 || ticks.length < 2) return null;
    labels.sort(function (a, b) { return a.x - b.x; });
    // 刻度字的 y 是基線；改用最近的水平格線
    var hlines = [].slice.call(svg.querySelectorAll("line")).map(function (l) {
      var m = toSvg(svg, l); if (!m) return null;
      var p1 = pt(m, +l.getAttribute("x1"), +l.getAttribute("y1")), p2 = pt(m, +l.getAttribute("x2"), +l.getAttribute("y2"));
      return Math.abs(p1.y - p2.y) < 0.5 && Math.abs(p1.x - p2.x) > 50 ? p1.y : null;
    }).filter(function (y) { return y !== null; });
    ticks.forEach(function (k) {
      var best = null;
      hlines.forEach(function (y) { var d = k.y - y; if (d >= 0 && d < 8 && (best === null || d < k.y - best)) best = y; });
      k.gy = best !== null ? best : k.y - 3.5;
    });
    ticks.sort(function (a, b) { return a.v - b.v; });
    var t0 = ticks[0], t1 = ticks[ticks.length - 1];
    if (t1.v === t0.v || t1.gy === t0.gy) return null;
    var k = (t1.v - t0.v) / (t1.gy - t0.gy);
    var val = function (y) { return t0.v + (y - t0.gy) * k; };
    var plotL = Math.max.apply(null, ticks.map(function (t) { return t.x; }));
    var pitch = labels.length > 1 ? (labels[labels.length - 1].x - labels[0].x) / (labels.length - 1) : 10;
    var idxOf = function (x) {
      var best = -1, bd = Infinity;
      labels.forEach(function (l, i) { var d = Math.abs(l.x - x); if (d < bd) { bd = d; best = i; } });
      return bd <= pitch * 0.6 ? best : -1;
    };
    // 各條線：依顏色分組（折線＋單點）
    var series = [], byColor = {};
    function ser(c) {
      if (!byColor[c]) { byColor[c] = { c: c, v: {}, els: [] }; series.push(byColor[c]); }
      return byColor[c];
    }
    [].slice.call(svg.querySelectorAll("path, polyline")).forEach(function (el) {
      if (el.closest("defs, clipPath, clippath") || el.classList.contains("cha-ui")) return;
      var c = colorOf(el, "stroke"); if (!c) return;
      if ((parseFloat(getComputedStyle(el).strokeWidth) || 1) < 1.4) return;
      if (colorOf(el, "fill")) return;
      var m = toSvg(svg, el); if (!m) return;
      var nums = el.tagName.toLowerCase() === "polyline" ? (el.getAttribute("points") || "")
        : (el.getAttribute("d") || "");
      if (/[a-z]/.test(nums.replace(/[ML]/g, "").replace(/e-?\d/gi, ""))) return;   // 只認絕對座標 M/L
      var arr = (nums.match(/-?\d+(?:\.\d+)?(?:e-?\d+)?/gi) || []).map(Number);
      var s = ser(c); s.els.push(el);
      for (var i = 0; i + 1 < arr.length; i += 2) {
        var p = pt(m, arr[i], arr[i + 1]), ix = idxOf(p.x);
        if (ix >= 0) s.v[ix] = p.y;
      }
    });
    [].slice.call(svg.querySelectorAll("circle")).forEach(function (el) {
      if (el.classList.contains("cha-ui") || +el.getAttribute("r") < 1.5) return;
      if (el.getAttribute("opacity") === "0") return;
      var c = colorOf(el, "fill"); if (!c) return;
      var m = toSvg(svg, el); if (!m) return;
      var p = pt(m, +el.getAttribute("cx"), +el.getAttribute("cy")), ix = idxOf(p.x);
      if (ix < 0) return;
      var s = ser(c); s.els.push(el);
      if (s.v[ix] === undefined) s.v[ix] = p.y;
    });
    series = series.filter(function (s) { return Object.keys(s.v).length; });
    if (!series.length) return null;
    // 名稱：附近圖例中同色的項目
    var root = svg.parentNode;
    for (var up = 0; up < 3 && root && !root.querySelector(".legend, .lg, [class*=legend]"); up++) root = root.parentNode;
    var probe = document.createElement("i"); document.body.appendChild(probe);
    var norm = function (c) { probe.style.color = ""; probe.style.color = c; return getComputedStyle(probe).color; };
    var swatches = root ? [].slice.call(root.querySelectorAll(".legend i, .legend span[style], .lg i, [class*=legend] i, [class*=legend] [style*=background]")) : [];
    series.forEach(function (s, i) {
      var c = norm(s.c), name = "";
      swatches.some(function (sw) {
        if (norm(sw.style.background || sw.style.backgroundColor || sw.style.borderColor || "") !== c) return false;
        var host = sw.closest("button, label, li, span:not([style])") || sw.parentNode;
        name = host.textContent.trim(); return !!name;
      });
      s.n = name || (series.length === 1 ? (svg.getAttribute("aria-label") || "") : "線 " + (i + 1));
    });
    probe.remove();
    return { labels: labels, series: series, val: val, top: t1.gy, max: t1.v, bottom: t0.gy, plotL: plotL };
  }
  function fmt(v) {
    if (Math.abs(v) < 1e-9) return "0%";
    return (Math.abs(v) >= 1 ? v.toFixed(2) : Math.abs(v) >= 0.01 ? v.toFixed(4) : v.toPrecision(3)) + "%";
  }
  function ensureTip() {
    if (tip) return tip;
    tip = document.createElement("div");
    tip.setAttribute("style", "position:fixed;z-index:2147483000;pointer-events:none;display:none;background:rgba(10,12,16,.92);color:#f0efec;"
      + "border:1px solid rgba(255,255,255,.15);border-radius:6px;padding:6px 9px;font:12px/1.5 ui-monospace,Consolas,monospace;white-space:nowrap;"
      + "box-shadow:0 4px 14px rgba(0,0,0,.25)");
    document.body.appendChild(tip);
    return tip;
  }
  function clear() {
    if (tip) tip.style.display = "none";
    if (cur) cur.ui.forEach(function (e) { e.remove(); });
    cur = null;
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
  document.addEventListener("mousemove", function (e) {
    var svg = e.target.closest && e.target.closest("svg");
    while (svg && svg.ownerSVGElement) svg = svg.ownerSVGElement;
    if (!svg || own(svg)) { if (cur) clear(); return; }
    if (!cur || cur.svg !== svg) {
      clear();
      var info = parse(svg);
      if (!info) return;
      cur = { svg: svg, info: info, ui: [], ix: -1 };
    }
    var info = cur.info, m = svg.getScreenCTM(); if (!m) return;
    var p = pt(m.inverse(), e.clientX, e.clientY);
    if (p.x < info.plotL || p.y < info.top - 20 || p.y > info.bottom + 10) { if (tip) tip.style.display = "none"; cur.ui.forEach(function (u) { u.remove(); }); cur.ui = []; cur.ix = -1; return; }
    var ix = -1, bd = Infinity;
    info.labels.forEach(function (l, i) { var d = Math.abs(l.x - p.x); if (d < bd) { bd = d; ix = i; } });
    if (ix !== cur.ix) {
      cur.ix = ix;
      cur.ui.forEach(function (u) { u.remove(); }); cur.ui = [];
      var x = info.labels[ix].x;
      var ln = document.createElementNS(NS, "line");
      [["x1", x], ["x2", x], ["y1", info.top], ["y2", info.bottom], ["stroke", "currentColor"], ["stroke-dasharray", "3 3"], ["opacity", ".45"], ["class", "cha-ui"], ["pointer-events", "none"]]
        .forEach(function (a) { ln.setAttribute(a[0], a[1]); });
      svg.appendChild(ln); cur.ui.push(ln);
      var html = "<b style=\"display:block;margin-bottom:2px\">" + esc(info.labels[ix].lab) + "</b>";
      info.series.forEach(function (s) {
        if (s.els.length && s.els.every(hiddenEl)) return;   // 圖例關掉的線不列
        var y = s.v[ix], txt = "—";
        if (y !== undefined) {
          var v = info.val(y);
          txt = y <= info.top + 0.6 && v >= info.max - 1e-9 ? "≥ " + fmt(info.max) : fmt(Math.max(0, v));
          var c = document.createElementNS(NS, "circle");
          [["cx", info.labels[ix].x], ["cy", y], ["r", 4.5], ["fill", s.c], ["stroke", "#fff"], ["stroke-width", 1.5], ["class", "cha-ui"], ["pointer-events", "none"]]
            .forEach(function (a) { c.setAttribute(a[0], a[1]); });
          svg.appendChild(c); cur.ui.push(c);
        }
        html += "<div style=\"display:flex;justify-content:space-between;gap:18px\"><span><i style=\"display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:"
          + s.c + "\"></i>" + esc(s.n) + "</span><span>" + txt + "</span></div>";
      });
      ensureTip().innerHTML = html;
    }
    var t = ensureTip(); t.style.display = "block";
    var lx = e.clientX + 16, ly = e.clientY + 14;
    if (lx + t.offsetWidth > innerWidth - 4) lx = e.clientX - t.offsetWidth - 16;
    if (ly + t.offsetHeight > innerHeight - 4) ly = e.clientY - t.offsetHeight - 14;
    t.style.left = Math.max(4, lx) + "px"; t.style.top = Math.max(4, ly) + "px";
  });
  document.addEventListener("mouseleave", clear);
  window.addEventListener("scroll", function () { if (tip) tip.style.display = "none"; }, true);
})();
// ==== /chart-hover-auto ====

// ==== fg-banner + help-render（2026-11-20 共用 API）====
// window.demogameFgBanner：FG 觸發／結算看板（行為與外觀照 H032）。window.demogameHelp：game_help.md 解析輸出到 #helpContent
// （格式見 Demogame規範 §2.8），並可由 config 產生賠率表（全盤計數型／Ways／Lines）。舊遊戲自己的實作不受影響。
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const isZh = (lang) => /^zh/i.test(lang || $("languageSelect")?.value || document.documentElement.lang || "");
  const resolve = (value) => (typeof value === "function" ? value() : value);

  // ===== FG 看板 =====
  // show({ icon, title, sub, count, note, html, holdStop, auto, autoMs, board }) → Promise（看板關閉時 resolve）
  //   icon：符號代號（取 DEMOGAME_SYMBOL_ART）、圖片網址、HTML 字串或元素；可省略。固定 72px。
  //   卡片內依序：.fg-banner-icon、.fg-banner-title、.fg-banner-sub、.fg-banner-count、.fg-banner-sub（note）；html 給了就整段取代。
  //   holdStop：加 data-hold-stop（結算看板用；長按連續 Spin 到這張就停）。
  //   auto：true（或回傳 true 的函式）時 autoMs（預設 1000）後自動關；不論 Auto 與否，點盤面／看板或按 #spinBtn 都會關
  //   （顯示期間暫時解除 #spinBtn 的 disabled，關閉後還原）。期間 <html> 加 dg-modal-open（背景不可捲動）。
  let current = null;
  function iconNode(icon) {
    if (!icon) return null;
    if (icon instanceof Element) return icon;
    const text = String(icon).trim();
    if (!text) return null;
    if (text.startsWith("<")) { const t = document.createElement("template"); t.innerHTML = text; return t.content; }
    let src = "";
    if (/^(data:|blob:|https?:)|[\/\\]|\.(png|jpe?g|gif|webp|svg)$/i.test(text)) src = text;
    else if (/^[A-Za-z]+\d*$/.test(text)) {
      if (window.DEMOGAME_SYMBOL_IMAGES_ENABLED === false) return null;
      src = window.DEMOGAME_SYMBOL_ART?.[text] || "";
      if (!src) return null;
    } else return document.createTextNode(text);   // emoji 等文字
    const img = document.createElement("img");
    img.src = src; img.alt = ""; img.draggable = false;
    img.addEventListener("error", () => img.remove(), { once: true });
    return img;
  }
  function show(opts = {}) {
    const board = opts.board || $("board");
    if (current) current.close();
    if (!board) return Promise.resolve();
    return new Promise((done) => {
      const spinBtn = $("spinBtn");
      const banner = document.createElement("div");
      banner.className = "fg-banner dg-fg-banner";
      if (opts.holdStop) banner.dataset.holdStop = "1";
      const card = document.createElement("div");
      card.className = "fg-banner-card";
      if (opts.html != null) card.innerHTML = String(opts.html);
      else {
        const icon = iconNode(opts.icon);
        if (icon) { const box = document.createElement("span"); box.className = "fg-banner-icon"; box.appendChild(icon); card.appendChild(box); }
        for (const [cls, value] of [["title", opts.title], ["sub", opts.sub], ["count", opts.count], ["sub", opts.note]]) {
          if (value == null || value === "") continue;
          const span = document.createElement("span");
          span.className = `fg-banner-${cls}`;
          span.textContent = String(value);
          card.appendChild(span);
        }
      }
      banner.appendChild(card);
      const fixPosition = getComputedStyle(board).position === "static";
      if (fixPosition) board.style.position = "relative";
      board.appendChild(banner);
      document.documentElement.classList.add("dg-modal-open");
      const wasDisabled = spinBtn ? spinBtn.disabled : false;
      if (spinBtn) spinBtn.disabled = false;
      let timer = 0;
      const close = () => {
        if (current !== entry) return;
        current = null;
        clearTimeout(timer);
        board.removeEventListener("click", close);
        spinBtn?.removeEventListener("click", close, true);
        if (spinBtn) spinBtn.disabled = wasDisabled;
        banner.remove();
        if (fixPosition) board.style.position = "";
        if (!document.querySelector(".dg-fg-banner")) document.documentElement.classList.remove("dg-modal-open");
        done();
      };
      const entry = { close, banner };
      current = entry;
      board.addEventListener("click", close);
      spinBtn?.addEventListener("click", close, true);
      if (resolve(opts.auto)) timer = setTimeout(close, Number(opts.autoMs) || 1000);
    });
  }
  const BANNER_TEXT = {
    zh: { title: "免費遊戲", count: "{n} 場", endTitle: "免費遊戲結束", endTotal: "總贏分" },
    en: { title: "Free Game", count: "{n} SPINS", endTitle: "FREE GAME COMPLETE", endTotal: "TOTAL WIN" }
  };
  const bannerText = (lang) => BANNER_TEXT[isZh(lang) ? "zh" : "en"];
  window.demogameFgBanner = {
    show,
    // 觸發看板：免費遊戲／N 場（icon 預設 C1）
    trigger: ({ spins, icon = "C1", auto, lang, ...rest } = {}) => {
      const t = bannerText(lang);
      return show({ icon, title: t.title, count: t.count.replace("{n}", spins), auto, ...rest });
    },
    // 結算看板：免費遊戲結束／總贏分／金額／倍數（win ÷ bet，2 位小數）；預設 holdStop
    end: ({ win = 0, bet, format, auto, lang, ...rest } = {}) => {
      const t = bannerText(lang);
      const money = typeof format === "function" ? format(win)
        : Number(win).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const note = Number(bet) > 0 ? `${(Number(win) / Number(bet)).toFixed(2)}x` : "";
      return show({ title: t.endTitle, sub: t.endTotal, count: money, note, holdStop: true, auto, ...rest });
    },
    close: () => current?.close(),
    isOpen: () => Boolean(current)
  };

  // ===== Help =====
  const LABEL_ZH = /^(?:繁中|简中|簡中|中文)[：:]$/;
  const LABEL_EN = /^(?:英文|English)[：:]$/i;
  const SKIP_HEAD = new Set(["Item", "Field", "中文欄", "符号"]);
  const isPaytableName = (text) => /pay\s*table|賠率表|赔率表/i.test(String(text || ""));
  const isSeparator = (cells) => cells.every((cell) => /^:?-{3,}:?$/.test(cell));
  const isFlatPayout = (cell) => /[-–]\s*\{?[\d.,]+\}?\s*x?$/i.test(cell);
  function tableCells(line) {
    const t = line.trim();
    return t.startsWith("|") && t.endsWith("|") && t.length > 1 ? t.slice(1, -1).split("|").map((x) => x.trim()) : null;
  }

  // parse(md, { plainText }) → [{ key, titleZh, titleEn, rules:[{zh,en}], groups:[{ key, titleZh, titleEn, rules, tables:[{lang, rows}], items:[] }] }]
  //   tables：新格式「繁中：／英文：」賠率表（第一列表頭）；items：舊格式「[M1] 5 - 50」平鋪派彩。
  //   plainText：true 時表格外的純文字行也當規則（舊離線副本）。
  function parse(md, opts = {}) {
    const sections = [];
    let section = null, group = null, payLang = "zh", table = null, prevTable = false;
    for (const raw of String(md || "").split(/\r?\n/)) {
      const line = raw.trim();
      let m;
      const cells = tableCells(line);
      if (!cells) { if (prevTable) table = null; prevTable = false; }
      if (LABEL_ZH.test(line)) { payLang = "zh"; table = null; continue; }
      if (LABEL_EN.test(line)) { payLang = "en"; table = null; continue; }
      if ((m = line.match(/^##\s+(.+)/)) && !line.startsWith("###")) {
        const key = m[1].trim();
        section = /meta/i.test(key) ? null : { key, titleZh: "", titleEn: "", rules: [], groups: [] };
        if (section) sections.push(section);
        group = null; payLang = "zh"; table = null; continue;
      }
      if (!section) continue;
      if ((m = line.match(/^###\s+(.+)/))) {
        group = { key: m[1].trim(), titleZh: "", titleEn: "", rules: [], tables: [], items: [] };
        section.groups.push(group); payLang = "zh"; table = null; continue;
      }
      if (!cells) {
        if (opts.plainText && line && line !== "---" && !/^(#|>|<!--|```)/.test(line)) (group || section).rules.push({ zh: line, en: line });
        continue;
      }
      prevTable = true;
      if (!cells.length || isSeparator(cells)) continue;
      const [item, zh = "", en = ""] = cells;
      if (item === "主要標題") { section.titleZh = zh; section.titleEn = en; table = null; continue; }
      if (item === "副標題") { if (group) { group.titleZh = zh; group.titleEn = en; } else { section.titleZh ||= zh; section.titleEn ||= en; } table = null; continue; }
      if (item === "規則說明") { (group || section).rules.push({ zh, en }); table = null; continue; }
      if (SKIP_HEAD.has(item)) { table = null; continue; }
      const owner = group && (isPaytableName(group.key) || isPaytableName(group.titleZh) || isPaytableName(group.titleEn)) ? group : null;
      if (!owner || cells.length < 2) continue;
      // 舊格式：每格一個「[M1] 5 - 50」
      if (!table && cells.filter(Boolean).every(isFlatPayout)) { owner.items.push(...cells.filter(Boolean)); continue; }
      if (!table) { table = { lang: payLang, rows: [] }; owner.tables.push(table); }
      table.rows.push(cells);
    }
    return sections.filter((s) => s.rules.length || s.groups.some((g) => g.rules.length || g.tables.length || g.items.length));
  }

  const defaultFormat = (n) => Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  function currentBetValue() {
    const value = Number(String($("betValue")?.textContent || "").replace(/[^\d.\-]/g, ""));
    return Number.isFinite(value) && value > 0 ? value : 1;
  }
  function scaler(opts, fallbackUnit) {
    const bet = Number(resolve(opts.bet) ?? currentBetValue()) || currentBetValue();
    const unit = Number(resolve(opts.baseBet) ?? fallbackUnit) || 1;
    const format = typeof opts.format === "function" ? opts.format : defaultFormat;
    return (n) => format(Number(n) / unit * bet);
  }
  const numberOf = (text) => {
    const clean = String(text).replace(/[{}]/g, "").replace(/,/g, "").trim();
    return clean !== "" && Number.isFinite(Number(clean)) ? Number(clean) : null;
  };

  // configPaytable(cfg, { type, bet, baseBet, format, counts, reels, skip }) → <div class="help-payout-table"> 或 null
  //   type 不給時依 config 判斷：有 paylines／line_num／lines → "lines"；pays 是物件或有 max_ways／ways → "ways"；其餘 → "count"（全盤計數）。
  //   派彩來源：pay_table → pays → paytable（陣列依符號 index，或物件 key＝符號 index／代號）；每列為依連線數（或計數）遞增的派彩。
  //   符號名稱：symbol_str → symbol_names → symbol_codes → symbols（字串陣列）。
  //   Ways／Lines：派彩欄＝(reel_num − 欄數 + 1)…reel_num 連；計數型：counts → count_labels → min_cluster 起算（最後一欄加「+」）。
  //   單位：派彩 ÷ baseBet（預設 cfg.base_bet → cfg.default_coin_in → 1）× 目前押注。全 0 的符號與欄位略過；之後共用模組自動排成每個符號一張「N - 派彩」卡片。
  function configPaytable(cfg, opts = {}) {
    if (!cfg || typeof cfg !== "object") return null;
    const source = cfg.pay_table || cfg.pays || cfg.paytable;
    if (!source || typeof source !== "object") return null;
    const type = opts.type
      || (Array.isArray(cfg.paylines) || Number(cfg.line_num) > 0 || Number(cfg.lines) > 0 ? "lines"
        : (!Array.isArray(source) || Number(cfg.max_ways) > 0 || Number(cfg.ways) > 0 ? "ways" : "count"));
    const names = cfg.symbol_str || cfg.symbol_names || cfg.symbol_codes
      || (Array.isArray(cfg.symbols) && cfg.symbols.every((s) => typeof s === "string") ? cfg.symbols : null) || {};
    const nameOf = (key) => {
      if (!/^\d+$/.test(String(key))) return String(key);
      const n = names[key] ?? names[String(key)] ?? names[Number(key)];
      return typeof n === "string" ? n : (n && typeof n === "object" && (n.code || n.name)) || `S${key}`;
    };
    const skip = new Set(opts.skip || []);
    const entries = (Array.isArray(source) ? source.map((pays, i) => [i, pays]) : Object.entries(source))
      .map(([key, pays]) => ({ code: nameOf(key), pays: Array.isArray(pays) ? pays.map(Number) : null }))
      .filter((e) => e.pays && !skip.has(e.code) && e.pays.some((v) => v > 0));
    if (!entries.length) return null;
    const width = Math.max(...entries.map((e) => e.pays.length));
    let labels;
    if (Array.isArray(opts.counts) && opts.counts.length === width) labels = opts.counts.map(String);
    else if (type === "count") {
      if (Array.isArray(cfg.count_labels) && cfg.count_labels.length === width) labels = cfg.count_labels.map(String);
      else if (Number.isFinite(Number(cfg.min_cluster))) labels = Array.from({ length: width }, (_, i) => `${Number(cfg.min_cluster) + i}${i === width - 1 ? "+" : ""}`);
      else labels = Array.from({ length: width }, (_, i) => String(i + 1));
    } else {
      const reels = Number(opts.reels ?? cfg.reel_num ?? cfg.reels_num ?? cfg.reel_count ?? cfg.cols) || 5;
      const start = width <= reels ? reels - width + 1 : 1;
      labels = Array.from({ length: width }, (_, i) => String(start + i));
    }
    const used = labels.map((_, i) => entries.some((e) => e.pays[i] > 0));
    const fmt = scaler(opts, cfg.base_bet ?? cfg.default_coin_in ?? 1);
    const table = document.createElement("div");
    table.className = "help-payout-table";
    table.dataset.paytableType = type;
    const addRow = (values) => {
      const row = document.createElement("div");
      row.className = "help-payout-row";
      for (const v of values) { const cell = document.createElement("div"); cell.className = "help-payout-cell"; cell.textContent = v; row.appendChild(cell); }
      table.appendChild(row);
    };
    addRow(["Symbol", ...labels.filter((_, i) => used[i])]);
    for (const e of entries) addRow([e.code, ...labels.map((_, i) => i).filter((i) => used[i]).map((i) => (e.pays[i] > 0 ? fmt(e.pays[i]) : "—"))]);
    return table;
  }

  // render(md, { lang, target, bet, baseBet, format, config, configOptions, plainText }) → 目標元素
  //   lang：zh／en（預設讀 #languageSelect）；bet：目前底注（數字或函式，預設讀 #betValue）；baseBet：md 賠率數字的基準（預設 config.base_bet → 100）。
  //   md 賠率表數字換算成「數字 ÷ baseBet × bet」；非數字原樣。md 沒有賠率表、而有給 config 時，用 configPaytable 補在賠率表區塊。
  //   都沒有內容時輸出 .help-load-error。Help 開著時押注或語言改變會自動重畫（只限用本 API 畫的內容）。
  let last = null;
  const rendered = new WeakSet();
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function render(md, opts = {}) {
    const target = opts.target || $("helpContent");
    if (!target) return null;
    const zh = isZh(resolve(opts.lang));
    const pick = (o) => (zh ? (o.zh || o.en) : (o.en || o.zh)) || "";
    const unitFallback = opts.config?.base_bet ?? 100;
    const fmt = scaler(opts, unitFallback);
    const sections = parse(md, opts);
    const frag = document.createDocumentFragment();
    let hasPaytable = false, paytableCard = null;
    const addRule = (parent, rule) => {
      const row = el("div", "help-rule");
      row.appendChild(el("div", zh ? "help-rule-zh" : "help-rule-en", pick(rule).replace(/[{}]/g, "")));
      parent.appendChild(row);
    };
    for (const section of sections) {
      const card = el("section", "help-section");
      card.appendChild(el("h3", "help-section-title", pick({ zh: section.titleZh, en: section.titleEn }) || section.key));
      section.rules.forEach((rule) => addRule(card, rule));
      if (isPaytableName(section.key) || isPaytableName(section.titleEn) || isPaytableName(section.titleZh)) paytableCard ||= card;
      for (const group of section.groups) {
        const langTables = group.tables.filter((t) => t.lang === (zh ? "zh" : "en"));
        const tables = langTables.length ? langTables : group.tables.filter((t) => t.lang === group.tables[0]?.lang);
        if (!group.rules.length && !tables.length && !group.items.length) continue;
        card.appendChild(el("h4", "help-group-title", pick({ zh: group.titleZh, en: group.titleEn }) || group.key));
        group.rules.forEach((rule) => addRule(card, rule));
        for (const t of tables) {
          const box = el("div", "help-payout-table");
          t.rows.forEach((cells, r) => {
            const row = el("div", "help-payout-row");
            cells.forEach((value, c) => {
              const n = r > 0 && c > 0 ? numberOf(value) : null;
              row.appendChild(el("div", "help-payout-cell", n != null ? fmt(n) : value.replace(/[{}]/g, "")));
            });
            box.appendChild(row);
          });
          card.appendChild(box);
          hasPaytable = true;
        }
        if (group.items.length) {
          const grid = el("div", "help-payout-grid");
          for (const item of group.items) {
            const text = item.replace(/[{}]/g, "").replace(/([-–]\s*)([\d.,]+)(\s*x?)\s*$/i, (all, sep, raw, x) => (x.trim() ? all : `${sep}${fmt(Number(raw.replace(/,/g, "")))}`));
            grid.appendChild(el("div", "help-payout-item", text));
          }
          card.appendChild(grid);
          hasPaytable = true;
        }
      }
      frag.appendChild(card);
    }
    if (!hasPaytable && opts.config) {
      const table = configPaytable(opts.config, { bet: opts.bet, format: opts.format, ...(opts.configOptions || {}) });
      if (table) {
        if (!paytableCard) {
          paytableCard = el("section", "help-section");
          paytableCard.appendChild(el("h3", "help-section-title", zh ? "賠率表" : "Paytable"));
          frag.insertBefore(paytableCard, frag.firstChild);
        }
        paytableCard.appendChild(el("h4", "help-group-title", zh ? "賠率表" : "Paytable"));   // 讓共用版式認得這區是賠率表（標題會被換成「賠率表（目前押注：x）」）
        paytableCard.appendChild(table);
      }
    }
    target.replaceChildren(frag);
    if (!target.children.length) target.appendChild(el("div", "help-load-error", zh ? "無法載入遊戲規則。" : "Unable to load game rules."));
    for (const child of target.children) rendered.add(child);
    last = { md, opts, target };
    return target;
  }

  // load({ url, embeddedId }) → Promise<string>：先 fetch 其他/game_help.md（中間檔放 其他/，2026-11-26）（file:// 略過），讀不到用內嵌 <script id="embeddedGameHelpMarkdown">
  async function load({ url = "./其他/game_help.md", embeddedId = "embeddedGameHelpMarkdown" } = {}) {
    let md = "";
    if (location.protocol !== "file:" && url) {
      try { const r = await fetch(url, { cache: "no-store" }); if (r.ok) md = await r.text(); } catch (_) { /* 用內嵌 */ }
    }
    return md.trim() || $(embeddedId)?.textContent?.trim() || "";
  }
  // open(opts)：load → render → 開 #helpDialog
  async function open(opts = {}) {
    const md = opts.markdown ?? await load(opts);
    render(md, opts);
    const dialog = $("helpDialog");
    if (dialog && !dialog.open) dialog.showModal?.();
    return md;
  }

  let rerenderQueued = false;
  function rerender() {
    if (rerenderQueued || !last) return;
    rerenderQueued = true;
    setTimeout(() => {
      rerenderQueued = false;
      if (!last || !last.target.isConnected || !$("helpDialog")?.open) return;
      if (!rendered.has(last.target.firstElementChild)) { last = null; return; }   // 之後被遊戲自己的 renderer 改寫過就不接手
      render(last.md, last.opts);
    });
  }
  const betValue = $("betValue");
  if (betValue) new MutationObserver(rerender).observe(betValue, { childList: true, subtree: true, characterData: true });
  $("languageSelect")?.addEventListener("change", rerender);

  window.demogameHelp = { parse, render, load, open, configPaytable, close: () => $("helpDialog")?.close?.() };
})();
// ==== /fg-banner + help-render ====

// ==== phone-layout：遊玩區手機直式排版（2026-11-27 使用者，照 H027 index2.html 定案；規範見 專案需知/開發規範/Omniplay/Demo規範.md「遊玩區」）====
// 遊玩區：（彩金列）→ Mult → 盤面 → 訊息橫幅 → 押注模式 → 餘額列 → 操作列（設定／押注／SPIN／自動／加速）
// 桌機：遊玩區包手機外框、固定在畫面上不隨捲動；標題列與除錯區放右欄；手機（≤ 760px）：標題列＋遊玩區剛好一個螢幕
// 只搬節點、不改 id 與事件；頁面自帶 <style id="m2-layout">（H027 index2.html）或 window.DEMOGAME_PHONE_LAYOUT === false 時不套用
(function () {
  const $ = (id) => document.getElementById(id);
  function setup() {
    if (window.DEMOGAME_PHONE_LAYOUT === false || /[?&]nophone/.test(location.search) || $("m2-layout") || $("m2")) return;
    const shell = $("app-shell"), gp = $("grid-panel");
    if (!shell || !gp || !document.body.classList.contains("slot-simulator")) return;
    document.body.classList.add("m2");

    const css = `
  html body.slot-simulator.m2 #app-shell #m2-col { grid-column: 1; grid-row: 1 / span 2; min-width: 0; align-self: start; }
  html body.slot-simulator.m2 #demogame-under-board:empty { display: none !important; }
  @media (min-width: 761px) {
    html body.slot-simulator.m2 #right-panel > * { margin-top: 0 !important; }
    html body.slot-simulator.m2 #m2.m2-fixed { position: fixed !important; z-index: 20; margin: 0 !important; transform-origin: top left; }
  }
  #m2 { position: relative; display: flex; flex-direction: column; gap: 8px; min-width: 0; box-sizing: border-box; overflow: hidden;
    container-type: inline-size; color: var(--sim-text); font-family: "Segoe UI", "Microsoft JhengHei", system-ui, sans-serif; }
  #m2 * { box-sizing: border-box; }
  @media (min-width: 761px) {
    #m2 { margin: 6px; padding: 40px 10px 28px; border: 10px solid #02070f; border-radius: 44px; background: var(--sim-bg);
      box-shadow: 0 0 0 1px var(--sim-border), 0 0 0 3px #071528, 0 0 0 4px var(--sim-border), 0 16px 44px rgba(0, 0, 0, .55); }
    #m2::before { content: ""; position: absolute; top: 9px; left: 50%; width: 96px; height: 24px; transform: translateX(-50%);
      border-radius: 14px; background: #02070f; box-shadow: inset 0 0 0 1px rgba(29, 70, 104, .35); pointer-events: none; }
    #m2::after { content: ""; position: absolute; bottom: 10px; left: 50%; width: 120px; height: 5px; transform: translateX(-50%);
      border-radius: 3px; background: var(--sim-border); pointer-events: none; }
  }
  @media (max-width: 760px) {
    #m2 { height: 100dvh; gap: clamp(6px, 0.9dvh, 9px); padding: max(6px, env(safe-area-inset-top)) 2px max(6px, env(safe-area-inset-bottom)); }
  }
  html body.slot-simulator.m2 #right-panel > #feature-bar, html body.slot-simulator.m2 #m2 > #feature-bar { flex: 0 0 auto; width: auto !important; margin: 0 !important; }
  html body.slot-simulator.m2 #m2 > #feature-bar { min-height: 40px !important; padding: 6px 12px !important; }

  /* 彩金列（遊戲自帶 #jpBar 就用遊戲的；有 OP Jackpot 但沒有 #jpBar 用這條展示列） */
  html body.slot-simulator.m2 #m2 > #jpBar { flex: 0 0 auto; width: 100% !important; margin: 0 !important; }
  #m2-jp { flex: 0 0 auto; display: grid; grid-template-columns: 1fr 1fr 76px 1fr 1fr; align-items: center; height: 54px; padding: 0 6px; border-radius: 12px;
    background: linear-gradient(90deg, #030b17 0, #06152b 50%, #030b17 100%); border: 1px solid rgba(120, 170, 230, .16); box-shadow: inset 0 2px 10px rgba(0, 0, 0, .7); overflow: hidden; }
  #m2-jp .jp-box { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; height: 100%; min-width: 0; line-height: 1; transition: opacity .2s, filter .2s; }
  #m2-jp .jp-major::before, #m2-jp .jp-mini::before { content: ""; position: absolute; left: 0; top: 14px; bottom: 14px; width: 1px; background: linear-gradient(180deg, transparent, rgba(120, 170, 230, .28), transparent); }
  #m2-jp .jp-k { font-size: 10.5px; font-weight: 800; letter-spacing: .12em; }
  #m2-jp .jp-v { max-width: 100%; padding: 0 3px; overflow: hidden; font-size: 14px; font-weight: 800; font-variant-numeric: tabular-nums; color: #f2f7ff; white-space: nowrap; }
  #m2-jp .jp-grand .jp-k { color: #ff7a84; } #m2-jp .jp-grand .jp-v { text-shadow: 0 0 10px rgba(255, 110, 120, .55); }
  #m2-jp .jp-major .jp-k { color: #c597ff; } #m2-jp .jp-major .jp-v { text-shadow: 0 0 10px rgba(190, 140, 255, .55); }
  #m2-jp .jp-minor .jp-k { color: #62b9ff; } #m2-jp .jp-minor .jp-v { text-shadow: 0 0 10px rgba(90, 180, 255, .55); }
  #m2-jp .jp-mini .jp-k { color: #6ce49c; } #m2-jp .jp-mini .jp-v { text-shadow: 0 0 10px rgba(100, 224, 150, .5); }
  #m2-jp .jp-box.is-locked { opacity: .45; filter: grayscale(.85); }
  #m2-jp .jp-box.is-locked .jp-v { text-shadow: none; }
  #m2-jp .jp-op { position: relative; justify-self: center; display: flex; align-items: center; justify-content: center; width: 76px; height: 54px; }
  #m2-jp .jp-op::before { content: ""; position: absolute; left: 50%; top: 50%; width: 90px; height: 90px; transform: translate(-50%, -50%); border-radius: 50%; pointer-events: none;
    background: radial-gradient(circle, rgba(95, 180, 255, .45), rgba(95, 180, 255, .12) 45%, transparent 70%); }
  #m2-jp .jp-op::after { content: ""; position: absolute; left: 50%; top: 50%; width: 86px; height: 86px; transform: translate(-50%, -50%); border-radius: 50%; pointer-events: none;
    background: repeating-conic-gradient(from 0deg, rgba(150, 210, 255, .22) 0 8deg, transparent 8deg 22deg);
    -webkit-mask: radial-gradient(circle, transparent 30%, #000 45%, transparent 70%); mask: radial-gradient(circle, transparent 30%, #000 45%, transparent 70%); animation: m2-spot-spin 14s linear infinite; }
  @keyframes m2-spot-spin { to { transform: translate(-50%, -50%) rotate(360deg); } }
  #m2-jp .jp-op svg { position: relative; z-index: 1; display: block; width: 56px; height: 56px; overflow: visible; }
  #m2-jp .jp-op .lvp { display: none; }
  #m2-jp .jp-op .l1 { display: inline; }
  #m2-jp .jp-op .root { transform: translateY(-3.6px); }
  #m2-jp .jp-op .glow { opacity: 0; }

  /* Mult：置中膠囊、兩側細線（沒有資訊時整列不顯示） */
  #m2-mult { flex: 0 0 auto; display: flex; align-items: center; gap: 10px; }
  #m2-top { flex: 0 0 auto; display: flex; flex-direction: column; align-items: stretch; gap: 4px; min-width: 0; padding: 0 6px; }
  #m2-top:empty { display: none; }
  #m2-top > * { margin: 0 !important; max-width: 100%; box-sizing: border-box; }
  #m2-mult:not(:has(#demogame-info-bar:not([hidden]))) { display: none; }
  #m2-mult::before, #m2-mult::after { content: ""; flex: 1 1 0; height: 1px; }
  #m2-mult::before { background: linear-gradient(90deg, transparent, rgba(120, 170, 230, .35)); }
  #m2-mult::after { background: linear-gradient(90deg, rgba(120, 170, 230, .35), transparent); }
  html body.slot-simulator.m2 #m2 #demogame-info-bar { flex: 0 0 auto; width: auto !important; min-width: 128px; max-width: 80%; height: 30px !important; min-height: 0 !important; margin: 0 !important; padding: 0 16px !important;
    gap: 4px 12px !important; flex-wrap: nowrap !important; border-radius: 999px !important; border: 1px solid rgba(120, 170, 230, .22) !important;
    background: linear-gradient(180deg, rgba(120, 170, 230, .08), rgba(0, 0, 0, 0) 55%), #030b17 !important; box-shadow: inset 0 2px 8px rgba(0, 0, 0, .7), 0 0 14px rgba(51, 187, 255, .12) !important; }
  html body.slot-simulator.m2 #m2 #demogame-info-bar .dib-item { gap: 8px !important; }
  html body.slot-simulator.m2 #m2 #demogame-info-bar .dib-k { font-size: 11px !important; letter-spacing: .14em !important; }
  html body.slot-simulator.m2 #m2 #demogame-info-bar .dib-v { font-size: 17px !important; }

  /* 盤面：遊戲自己的盤面面板整塊搬進來；手機吃剩餘高度，放不下時 JS 等比縮小 */
  #m2-stage { flex: 0 0 auto; display: flex; align-items: center; justify-content: center; min-width: 0; }
  html body.slot-simulator.m2 #m2 #grid-panel { width: 100% !important; max-width: none !important; margin: 0 !important; flex: 0 0 auto; }
  @media (max-width: 760px) {
    #m2-stage { flex: 1 1 0; min-height: 0; overflow: visible; }
    html body.slot-simulator.m2 #m2 #grid-panel { transform-origin: center center; }
  }

  /* 訊息橫幅（實機 UP TO 2500x 橫幅的位置）：低調緞帶，中間亮、兩端淡出 */
  html body.slot-simulator.m2 #m2 #messageBar { position: relative; flex: 0 0 auto; width: 100% !important; height: 34px !important; min-height: 0 !important; margin: 0 !important; padding: 0 28px !important;
    border: 0 !important; border-radius: 0 !important; box-shadow: none !important;
    background: linear-gradient(90deg, transparent 0, rgba(12, 34, 64, .55) 18%, rgba(12, 34, 64, .75) 50%, rgba(12, 34, 64, .55) 82%, transparent 100%) !important;
    color: var(--sim-text) !important; font: 700 13px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; letter-spacing: .4px; text-shadow: none;
    display: flex !important; align-items: center; justify-content: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  html body.slot-simulator.m2 #m2 #messageBar::before, html body.slot-simulator.m2 #m2 #messageBar::after { content: ""; position: absolute; left: 6%; right: 6%; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(110, 190, 255, .28), transparent); pointer-events: none; }
  html body.slot-simulator.m2 #m2 #messageBar::before { top: 0; }
  html body.slot-simulator.m2 #m2 #messageBar::after { bottom: 0; }
  html body.slot-simulator.m2 #m2 #messageBar.win { color: var(--sim-green, #33ff99) !important; }
  html body.slot-simulator.m2 #m2 #messageBar.error { color: #ffc2cf !important; }

  /* 押注模式：三欄卡片；有一般＋額外押注時，額外押注做成開關（一般押注鈕隱藏）；不足三的倍數補空格 */
  html body.slot-simulator.m2 #m2 #bet-mode-panel { flex: 0 0 auto; margin: 0 !important; padding: 0 !important; border: 0 !important; background: transparent !important; box-shadow: none !important; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel > .zone-label { display: none !important; }
  /* 一列三格寬；沒有內容的格子不放，剩下的置中（2026-11-27 使用者） */
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body { display: flex !important; flex-wrap: wrap !important; justify-content: center !important; gap: 6px !important; padding: 0 !important; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button, #m2-wins { flex: 0 0 calc((100% - 12px) / 3) !important; max-width: calc((100% - 12px) / 3) !important; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > .m2-mode-empty { order: 9; height: 60px; border: 1px solid var(--sim-border); border-radius: 12px; background: var(--sim-panel); }
  /* 一般押注不放按鈕（2026-11-27 使用者）：預設就是一般押注，額外押注開關關掉即回到一般押注 */
  html body.slot-simulator.m2 #m2 #bet-mode-panel #normalBetBtn { display: none !important; }
  /* 押注模式列的空格：顯示這一局的得獎明細（同 dev 環境：顆數｜符號｜金額），最多三列、多的自動輪播 */
  #m2-wins { order: 8; height: 60px; min-width: 0; overflow: hidden; display: flex; flex-direction: column; justify-content: stretch; gap: 0; padding: 3px 10px;
    border: 1px solid var(--sim-border); border-radius: 12px; background: var(--sim-panel); font: 700 12px/1 "Segoe UI", system-ui, sans-serif; font-variant-numeric: tabular-nums; }
  #m2-wins .w-row { flex: 1 1 0; min-height: 0; display: grid; grid-template-columns: 22px 20px minmax(0, 1fr); align-items: center; gap: 6px; color: var(--sim-text); }
  #m2-wins .w-row + .w-row { border-top: 1px solid rgba(120, 170, 230, .2); }   /* 固定三格、細線分隔，新的一列從最下面補上（同 dev 環境） */
  #m2-wins .w-n { text-align: right; color: var(--sim-sub); }
  #m2-wins .w-s { width: 18px; height: 18px; display: grid; place-items: center; font-size: 9px; color: var(--sim-sub); }
  #m2-wins .w-s img { width: 18px; height: 18px; object-fit: contain; }
  #m2-wins .w-v { text-align: right; color: #ffe27a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #m2-wins .w-t { grid-column: 1 / -1; text-align: left; color: var(--sim-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button { position: relative; order: 5; width: auto !important; height: 60px !important; min-height: 0 !important; margin: 0 !important; padding: 0 4px !important;
    display: flex !important; flex-direction: column; align-items: center; justify-content: center; gap: 5px; text-align: center;
    border: 1px solid var(--sim-border) !important; border-radius: 12px !important; color: #fff !important; opacity: 1 !important; background: var(--sim-surface) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12), inset 0 -3px 0 rgba(0, 0, 0, .22) !important;
    font: 800 12.5px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; letter-spacing: .5px; text-transform: uppercase !important; white-space: nowrap !important; text-shadow: 0 1px 2px rgba(0, 0, 0, .35); }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button .mode-price { display: block; margin: 0; padding: 2px 9px; border-radius: 999px; background: rgba(0, 0, 0, .28);
    color: #ffe27a; font-size: 11px; font-weight: 800; letter-spacing: .3px; opacity: 1; text-shadow: none; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button .mode-price[data-p] { font-size: 0 !important; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button .mode-price[data-p]::after { content: attr(data-p); font-size: 12px; text-transform: none; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.is-active:not(.demogame-buy-btn),
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.active:not(.demogame-buy-btn) { background: linear-gradient(180deg, #22c07e 0%, #13955f 100%) !important; border-color: #2fd48f !important; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.demogame-buy-btn { background: linear-gradient(180deg, #2a8ff0 0%, #0a63bd 100%) !important; border-color: #4aa8ff !important; }
  html body.slot-simulator.m2 #m2 #normalBetBtn { order: 0; }
  html body.slot-simulator.m2 #m2 #extraBetBtn, html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.m2-eb { order: 1; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.m2-eb-hidden { display: none !important; }
  html body.slot-simulator.m2 #m2 #buyFeatureBtn { order: 2; }
  html body.slot-simulator.m2 #m2 #superFeatureBtn { order: 3; }
  html body.slot-simulator.m2.m2-eb-toggle #m2 #bet-mode-panel .zone-body > button.m2-eb { background: linear-gradient(180deg, #22c07e 0%, #13955f 100%) !important; border-color: #2fd48f !important; }
  html body.slot-simulator.m2.m2-eb-toggle #m2 #bet-mode-panel .zone-body > button.m2-eb.is-active { background: linear-gradient(180deg, #3ee49a 0%, #19b273 100%) !important; border-color: #9dffcf !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .3), inset 0 -3px 0 rgba(0, 0, 0, .2), 0 0 14px rgba(62, 228, 154, .55) !important; }
  /* 額外押注開關：跟「額外押注」同一行、整組置中（2026-11-27 使用者：要同高、不要歪） */
  #m2 .m2-eb-label { display: inline-flex; align-items: center; justify-content: center; gap: 7px; line-height: 1; }
  #m2 .m2-sw { position: relative; flex: 0 0 auto; width: 24px; height: 13px; border-radius: 999px; background: rgba(0, 0, 0, .35); }
  #m2 .m2-sw::after { content: ""; position: absolute; top: 2.5px; left: 3px; width: 8px; height: 8px; border-radius: 50%; background: rgba(255, 255, 255, .6); transition: left .15s; }
  html body.slot-simulator.m2 #m2 button.m2-eb.is-active .m2-sw { background: #eafff4; }
  html body.slot-simulator.m2 #m2 button.m2-eb.is-active .m2-sw::after { left: 13px; background: #13955f; }
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button:disabled,
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.is-locked,
  html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button.dg-buy-active { opacity: .45 !important; }

  /* 餘額列：原本的面板樣式 */
  html body.slot-simulator.m2 #m2 #credit-bar { flex: 0 0 auto; margin: 0 !important; }

  /* 操作列：設定｜押注｜SPIN（大圓）｜自動｜加速 */
  #m2-dock { flex: 0 0 auto; position: relative; display: grid; grid-template-columns: 1fr 1fr auto 1fr 1fr; align-items: center; justify-items: center; gap: 2px; padding: 6px 0 2px; }
  .m2-cell { display: grid; place-items: center; min-width: 0; }
  #m2-dock .m2-key, html body.slot-simulator.m2 #m2 #betBtn, html body.slot-simulator.m2 #m2 #autoBtn {
    width: clamp(46px, 13cqw, 58px) !important; height: clamp(46px, 13cqw, 58px) !important; min-width: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important;
    display: flex !important; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
    border: 0 !important; border-radius: 12px !important; background: transparent !important; box-shadow: none !important;
    color: var(--sim-text) !important; cursor: pointer; font: 800 10px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; letter-spacing: .4px; white-space: nowrap; }
  #m2-dock .m2-key svg { width: 28px; height: 28px; flex: 0 0 auto; }
  #m2-dock .m2-key:hover, html body.slot-simulator.m2 #m2 #betBtn:hover, html body.slot-simulator.m2 #m2 #autoBtn:hover { background: rgba(120, 170, 230, .08) !important; }
  html body.slot-simulator.m2 #m2 #betBtn, html body.slot-simulator.m2 #m2 #autoBtn { font-size: 0 !important; color: transparent !important; }
  html body.slot-simulator.m2 #m2 #betBtn::before, html body.slot-simulator.m2 #m2 #autoBtn::before { content: ""; width: 28px; height: 28px; background: var(--sim-text);
    -webkit-mask: var(--m2-ico) center / contain no-repeat; mask: var(--m2-ico) center / contain no-repeat; }
  html body.slot-simulator.m2 #m2 #betBtn::after, html body.slot-simulator.m2 #m2 #autoBtn::after { content: attr(data-cap); color: var(--sim-text); font: 800 10px/1 "Segoe UI", "Microsoft JhengHei", sans-serif; letter-spacing: .4px; }
  html body.slot-simulator.m2 #m2 #betBtn { --m2-ico: var(--m2-coins); }
  html body.slot-simulator.m2 #m2 #autoBtn { --m2-ico: var(--m2-play); }
  html body.slot-simulator.m2 #m2 #autoBtn.m2-on { --m2-ico: var(--m2-stop); }
  html body.slot-simulator.m2 #m2 #autoBtn.m2-on::before { background-color: var(--sim-green, #33ff99); }
  html body.slot-simulator.m2 #m2 #autoBtn.m2-on::after { color: var(--sim-green, #33ff99); }
  #m2-dock #m2-turboBtn.on, #m2-dock #m2-menuBtn.on { color: var(--sim-mauve, #b06aff) !important; }
  html body.slot-simulator.m2 #m2 .bet-stepper { position: static !important; display: block !important; width: auto !important; min-width: 0 !important; }
  html body.slot-simulator.m2 #m2 #betMinusBtn, html body.slot-simulator.m2 #m2 #betPlusBtn { display: none !important; }
  html body.slot-simulator.m2 #m2 #betMenu { position: absolute !important; left: 0 !important; right: 0 !important; top: auto !important; bottom: calc(100% + 8px) !important; width: auto !important; transform: none !important;
    max-height: 48dvh; overflow: auto; z-index: 60; padding: 12px !important; border: 1px solid var(--sim-blue, #33bbff) !important; border-radius: 12px !important;
    background: var(--sim-surface, #0c2240) !important; box-shadow: 0 0 0 1px rgba(51, 187, 255, .35), 0 0 24px rgba(51, 187, 255, .25), 0 16px 40px rgba(0, 0, 0, .7) !important;
    display: grid !important; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
  /* 押注選單與設定同一套樣式：亮框＋光暈，打開時遊玩區其他部分壓暗（2026-11-27 使用者） */
  html body.slot-simulator.m2 #m2:has(#betMenu:not(.hidden)) #m2-scrim { display: block; }
  html body.slot-simulator.m2 #m2:has(#betMenu:not(.hidden)) #m2-dock { position: relative; z-index: 58; }
  html body.slot-simulator.m2 #m2 #betMenu.hidden { display: none !important; }
  html body.slot-simulator.m2 #m2 #betMenu > button { min-width: 0 !important; width: auto !important; height: 34px !important; margin: 0 !important; padding: 0 4px !important;
    border: 1px solid rgba(51, 187, 255, .22) !important; border-radius: 8px !important; background: rgba(2, 10, 22, .55) !important; color: var(--sim-text) !important;
    font: 700 13px/1 "Segoe UI", sans-serif !important; font-variant-numeric: tabular-nums; white-space: nowrap !important; cursor: pointer; }
  html body.slot-simulator.m2 #m2 #betMenu > button:hover { border-color: var(--sim-blue, #33bbff) !important; }
  html body.slot-simulator.m2 #m2 #betMenu > button.is-active { background: #0077cc !important; border-color: #0077cc !important; color: #fff !important; }
  html body.slot-simulator.m2 #m2 #spinBtn { position: relative !important; width: clamp(76px, 23cqw, 100px) !important; height: clamp(76px, 23cqw, 100px) !important; min-width: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important;
    display: grid !important; place-items: center; border: 2px solid #33bbff !important; border-radius: 50% !important;
    background: radial-gradient(circle at 50% 35%, #1a8fe0 0%, #0077cc 55%, #005499 100%) !important;
    box-shadow: 0 0 0 4px var(--sim-surface), 0 0 0 5px var(--sim-border), 0 6px 16px rgba(0, 0, 0, .5) !important;
    font-size: 0 !important; color: transparent !important; cursor: pointer; }
  html body.slot-simulator.m2 #m2 #spinBtn::before { content: ""; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: clamp(34px, 10cqw, 44px); height: clamp(34px, 10cqw, 44px); background: #fff; -webkit-mask: var(--m2-spin) center / contain no-repeat; mask: var(--m2-spin) center / contain no-repeat; }
  html body.slot-simulator.m2 #m2 #spinBtn:active { transform: scale(.96); }
  html body.slot-simulator.m2 #m2 #spinBtn:disabled { opacity: .55; }

  /* 原「遊戲」區只剩速度滑桿（加速鈕取代）與除錯鈕：平常隱藏，開除錯模式才出現（右欄） */
  html body.slot-simulator.m2 #play-panel .play-main-controls { display: none !important; }
  html body.slot-simulator.m2 #play-panel:has(#play-debug-controls.debug-hidden) { display: none !important; }
  html body.slot-simulator.m2 #play-panel:not(:has(#play-debug-controls)) { display: none !important; }

  /* 設定：由遊玩區操作列的「設定」打開，浮在遊玩區裡（不另放懸浮鈕） */
  html body.slot-simulator.m2 #m2 > #settings-wrap { position: absolute !important; left: 10px !important; right: 10px !important; top: auto !important; bottom: 96px !important; z-index: 60;
    width: auto !important; max-height: calc(100% - 140px); overflow: auto; margin: 0 !important;
    border: 1px solid var(--sim-border) !important; border-radius: 12px !important; box-shadow: 0 12px 40px rgba(0, 0, 0, .6) !important; display: none !important; }
  html body.slot-simulator.m2.m2-settings-open #m2 > #settings-wrap { display: block !important; }
  /* 設定打開時：遊玩區其他部分壓暗，視窗亮框＋光暈，比較明顯（2026-11-27 使用者） */
  #m2-scrim { display: none; position: absolute; inset: 0; z-index: 55; background: rgba(1, 6, 14, .62); backdrop-filter: blur(1.5px); }
  html body.slot-simulator.m2.m2-settings-open #m2-scrim { display: block; }
  html body.slot-simulator.m2 #m2 > #settings-wrap { background: var(--sim-surface, #0c2240) !important; border-color: var(--sim-blue, #33bbff) !important;
    box-shadow: 0 0 0 1px rgba(51, 187, 255, .35), 0 0 24px rgba(51, 187, 255, .25), 0 16px 40px rgba(0, 0, 0, .7) !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap > .setting-header { color: var(--sim-text) !important; font-size: 14px !important; background: rgba(51, 187, 255, .08) !important; }
  html body.slot-simulator.m2 #settings-wrap > .setting-header { display: flex !important; align-items: center; justify-content: space-between; }
  #m2-settings-close { position: absolute; top: 7px; right: 8px; z-index: 1; width: 28px; height: 28px; padding: 0; border: 0; border-radius: 6px; background: transparent; color: var(--sim-sub); font: 700 16px/1 "Segoe UI", sans-serif; cursor: pointer; }
  #m2-settings-close:hover { background: var(--sim-surface); color: var(--sim-text); }
  html body.slot-simulator.m2 #settings-wrap > .setting-body { display: flex !important; flex-direction: column !important; align-items: stretch !important; flex-wrap: nowrap !important; gap: 12px !important; }
  html body.slot-simulator.m2 #settings-wrap > .setting-body > * { margin: 0 !important; }
  html body.slot-simulator.m2 #settings-wrap .setting-toggle-group { display: flex !important; flex-wrap: wrap !important; gap: 8px 16px !important; margin: 0 !important; padding-bottom: 12px; border-bottom: 1px solid var(--sim-surface); }
  html body.slot-simulator.m2 #settings-wrap .setting-control-group { display: flex !important; flex-direction: column !important; align-items: stretch !important; gap: 8px !important; margin: 0 !important; width: 100% !important; }
  html body.slot-simulator.m2 #settings-wrap .setting-control-group > .config-control:not(.demogame-source-control) { display: flex !important; align-items: center; justify-content: space-between; gap: 10px; width: 100% !important; margin: 0 !important; }
  html body.slot-simulator.m2 #settings-wrap .setting-control-group select { flex: 0 0 66%; width: 66% !important; max-width: none !important; }

  /* 設定視窗排版（2026-11-27 使用者：重新排版）：標題列＋✕；勾選做成兩格卡片；版本／Config／語言 標籤＋下拉一行一個 */
  html body.slot-simulator.m2 #m2 > #settings-wrap { padding: 0 !important; overflow: auto; }
  html body.slot-simulator.m2 #m2 > #settings-wrap > .setting-header { height: 46px !important; min-height: 0 !important; margin: 0 !important; padding: 0 52px 0 16px !important;
    border-bottom: 1px solid rgba(51, 187, 255, .18) !important; display: flex !important; align-items: center !important;
    font: 700 14px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; letter-spacing: .5px !important; color: var(--sim-text) !important; text-transform: none !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap > #m2-settings-close { top: 9px !important; right: 10px !important; width: 28px !important; height: 28px !important; min-height: 0 !important; padding: 0 !important;
    border: 0 !important; border-radius: 8px !important; background: transparent !important; color: var(--sim-sub) !important; font: 700 15px/28px "Segoe UI", sans-serif !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap > #m2-settings-close:hover { background: rgba(51, 187, 255, .14) !important; color: #fff !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap > .setting-body { padding: 14px 16px 16px !important; gap: 14px !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-toggle-group { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 8px !important; padding: 0 !important; border: 0 !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-toggle { height: 36px !important; min-height: 0 !important; margin: 0 !important; padding: 0 12px !important; align-items: center !important; gap: 8px !important;
    border: 1px solid rgba(51, 187, 255, .22) !important; border-radius: 8px !important; background: rgba(2, 10, 22, .55) !important; cursor: pointer;
    font: 600 12.5px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; color: var(--sim-text) !important; white-space: nowrap; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-toggle span { color: inherit !important; font: inherit !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-toggle:has(input:checked) { border-color: var(--sim-blue, #33bbff) !important; background: rgba(51, 187, 255, .12) !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-toggle input { margin: 0 !important; flex: 0 0 auto; accent-color: #33bbff; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-control-group { gap: 8px !important; padding-top: 14px !important; border-top: 1px solid rgba(51, 187, 255, .14) !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-control-group > .config-control { height: 36px !important; min-height: 0 !important; gap: 12px !important;
    font: 600 12.5px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; color: var(--sim-sub) !important; }
  html body.slot-simulator.m2 #m2 > #settings-wrap .setting-control-group select { flex: 0 0 70% !important; width: 70% !important; height: 36px !important; min-height: 0 !important; padding: 0 10px !important;
    border: 1px solid rgba(51, 187, 255, .22) !important; border-radius: 8px !important; background-color: rgba(2, 10, 22, .55) !important; color: var(--sim-text) !important; font: 700 13px/1 "Segoe UI", sans-serif !important; }

  @media (max-width: 760px) {
    html body.slot-simulator.m2 #m2-stage > #grid-panel { display: flex !important; flex-direction: column !important; justify-content: center !important; box-sizing: border-box !important; transform-origin: center center; }
    html body.slot-simulator.m2 #m2 #bet-mode-panel { min-height: clamp(60px, 8.4dvh, 74px); }
    #m2-jp { height: clamp(54px, 7.4dvh, 64px); }
    html body.slot-simulator.m2 #m2 #messageBar { height: clamp(34px, 5dvh, 42px) !important; }
    html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button, html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > .m2-mode-empty, #m2-wins { height: clamp(60px, 8.4dvh, 74px) !important; }
  }
  /* 矮螢幕（手機瀏覽器扣掉網址列後約 760px）：下半部壓扁一點，空間留給盤面（2026-11-27 使用者「宙斯畫面會變小」） */
  @media (max-width: 760px) and (max-height: 860px) {
    #m2-jp { height: 52px; }
    html body.slot-simulator.m2 #m2 #messageBar { height: 32px !important; }
    html body.slot-simulator.m2 #m2 #bet-mode-panel .zone-body > button, #m2-wins { height: 56px !important; }
    html body.slot-simulator.m2 #m2 #bet-mode-panel { min-height: 56px; }
    html body.slot-simulator.m2 #m2 #credit-bar > * { padding-top: 6px !important; padding-bottom: 6px !important; }
    #m2-dock { padding: 0; }
    html body.slot-simulator.m2 #m2 #spinBtn { width: 80px !important; height: 80px !important; }
  }`;
    const st = document.createElement("style");
    st.id = "dg-phone-layout"; st.textContent = css;
    const addStyle = () => document.head.appendChild(st);   // 放在 head 最後，蓋過共用與各遊戲樣式
    addStyle();
    addEventListener("load", () => setTimeout(addStyle, 10), { once: true });

    const zh = () => (($("languageSelect") || {}).value || "zh") !== "en";
    const SVG = (d, extra = "") => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ${extra}>${d}</svg>`;
    const PATH = {
      gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
      turbo: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
      coins: '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v4c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 10v4c0 1.7 3.1 3 7 3s7-1.3 7-3v-4"/><path d="M5 14v4c0 1.7 3.1 3 7 3s7-1.3 7-3v-4"/>',
      spin: '<path d="M3 12a9 9 0 0 1 15.36-6.36L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.36 6.36L3 16"/><path d="M3 21v-5h5"/>',
    };
    const mask = (d, filled) => `url("data:image/svg+xml,${encodeURIComponent(filled ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">${d}</svg>` : SVG(d))}")`;
    Object.entries({ "--m2-coins": mask(PATH.coins), "--m2-spin": mask(PATH.spin),
      "--m2-play": mask('<path d="M8 5v14l11-7z"/>', true), "--m2-stop": mask('<rect x="6" y="6" width="12" height="12" rx="2"/>', true) })
      .forEach(([k, v]) => document.body.style.setProperty(k, v));
    const icon = (d) => SVG(d, 'aria-hidden="true"').replace('stroke="#000"', 'stroke="currentColor"');

    // 有 OP Jackpot（Help 有 OP JACKPOT 段）但遊戲沒有自己的彩金列 → 放展示用彩金列（寶箱圖同 H032）
    const helpText = ($("embeddedGameHelpMarkdown") || {}).textContent || "";
    const ownJp = $("jpBar");
    const showJp = !ownJp && /OP JACKPOT/i.test(helpText);
    function jpChestSvg() {
      return `<svg viewBox="0 0 48 48" aria-hidden="true"><defs>
        <linearGradient id="m2cBody" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a5d9f"/><stop offset="1" stop-color="#0f2a52"/></linearGradient>
        <linearGradient id="m2cLid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f66ad"/><stop offset="1" stop-color="#16376a"/></linearGradient>
        <linearGradient id="m2cLock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe66a"/><stop offset="1" stop-color="#b57e10"/></linearGradient></defs><g class="root">
        <path d="M5 24.5L8.5 19H39.5L43 24.5Z" fill="#071227"/>
        <path d="M4 24H44V39C44 42 41.5 44 38.5 44H9.5C6.5 44 4 42 4 39Z" fill="url(#m2cBody)"/>
        <path d="M4 24H44V27H4Z" fill="#5fb4ff"/><rect x="11" y="24" width="3" height="20" fill="#5fb4ff"/><rect x="34" y="24" width="3" height="20" fill="#5fb4ff"/>
        <rect x="20.5" y="27.5" width="7" height="8.5" rx="1" fill="url(#m2cLock)"/><circle cx="24" cy="31.5" r="1.5" fill="#0f2a52"/>
        <path d="M4 24C4 14 8.5 10 24 10S44 14 44 24Z" fill="url(#m2cLid)"/><path d="M4 21.5H44V24.5H4Z" fill="#5fb4ff"/><path d="M11 10.5V24.5H14V10.5ZM34 10.5V24.5H37V10.5Z" fill="#5fb4ff"/>
        </g></svg>`;
    }

    const root = document.createElement("section");
    root.id = "m2";
    root.setAttribute("aria-label", "Play area");
    root.innerHTML = `${showJp ? `
      <div id="m2-jp" aria-label="OP Jackpot">
        <div class="jp-box jp-grand" data-jp="0"><span class="jp-k">GRAND</span><span class="jp-v"></span></div>
        <div class="jp-box jp-major" data-jp="1"><span class="jp-k">MAJOR</span><span class="jp-v"></span></div>
        <div class="jp-op">${jpChestSvg()}</div>
        <div class="jp-box jp-minor" data-jp="2"><span class="jp-k">MINOR</span><span class="jp-v"></span></div>
        <div class="jp-box jp-mini" data-jp="3"><span class="jp-k">MINI</span><span class="jp-v"></span></div>
      </div>` : ""}
      <div id="m2-mult"></div>
      <div id="m2-top"></div>
      <div id="m2-stage"></div>
      <div id="m2-banner-slot"></div>
      <div id="m2-modes-slot"></div>
      <div id="m2-info-slot"></div>
      <div id="m2-dock">
        <button id="m2-menuBtn" class="m2-key" type="button">${icon(PATH.gear)}<span data-zh="設定" data-en="SETTING"></span></button>
        <div class="m2-cell" id="m2-bet-slot"></div>
        <div class="m2-cell" id="m2-spin-slot"></div>
        <div class="m2-cell" id="m2-auto-slot"></div>
        <button id="m2-turboBtn" class="m2-key" type="button">${icon(PATH.turbo)}<span id="m2-turboCap"></span></button>
      </div>`;
    const col = document.createElement("div");
    col.id = "m2-col";
    shell.insertBefore(col, shell.firstChild);
    col.appendChild(root);

    const put = (node, parent, before) => { if (node && parent) (before ? parent.insertBefore(node, before) : parent.appendChild(node)); };
    const swap = (slotId, node) => { const slot = $(slotId); if (node) slot.parentNode.insertBefore(node, slot); slot.remove(); };
    if (ownJp) root.insertBefore(ownJp, root.firstChild);
    put($("demogame-info-bar"), $("m2-mult"));
    put(gp, $("m2-stage"));
    // 盤面上方的倍數列移出盤面框、放在盤面正上方（2026-11-27 使用者「乘倍數丟出去」）；遊戲可用 window.DEMOGAME_PHONE_TOP 指定其他元素（字串或陣列）
    ["#grid-panel .multiplier-track"].concat(window.DEMOGAME_PHONE_TOP || []).forEach((sel) => document.querySelectorAll(sel).forEach((n) => put(n, $("m2-top"))));
    swap("m2-banner-slot", $("messageBar"));
    swap("m2-modes-slot", $("bet-mode-panel"));
    swap("m2-info-slot", $("credit-bar"));
    put(document.querySelector(".bet-stepper"), $("m2-bet-slot"));
    put($("spinBtn"), $("m2-spin-slot"));
    put($("autoBtn"), $("m2-auto-slot"));

    // 右欄：除錯模式的區塊（上一步／下一步、指定 RNG、紀錄、版本紀錄、模擬…）都放到右欄
    const right = $("right-panel"), phone = shell.parentElement;
    if (right) {
      put($("play-panel"), right);
      [...(phone ? phone.children : [])].forEach((n) => {
        if (n === shell || ["feature-bar", "strip-bar", "settings-wrap"].includes(n.id) || /^(SCRIPT|DIALOG|STYLE|IFRAME)$/.test(n.tagName) || n.classList.contains("footer-note")) return;
        if (n.matches("section, .control-zone, .diagnostic-region")) right.appendChild(n);
      });
    }

    // 標題列：桌機放右欄最上面；手機放遊玩區最上面（同一個螢幕內）
    const titleBar = $("feature-bar");
    const mqMobile = window.matchMedia ? matchMedia("(max-width: 760px)") : null;
    const isMobile = () => !!(mqMobile && mqMobile.matches);
    const placeTitle = () => {
      if (!titleBar) return;
      // 只有真的手機（觸控、窄螢幕）才放進遊玩區最上面；電腦上視窗再窄也放右欄最上面（2026-11-27 使用者）
      const phone = isMobile() && window.matchMedia && matchMedia("(pointer: coarse)").matches;
      if (phone) root.insertBefore(titleBar, root.firstChild);
      else if (right) right.insertBefore(titleBar, right.firstChild);
    };
    placeTitle();
    if (mqMobile) (mqMobile.addEventListener ? mqMobile.addEventListener("change", placeTitle) : mqMobile.addListener(placeTitle));

    // 押注模式：有一般押注＋額外押注時，額外押注只放一顆、做成開關（2026-11-27 使用者，所有遊戲統一）：
    // 一種 EB：點一下開、再點一下關；兩種以上：點一下 EB1、第二下 EB2、再點一下回一般押注。
    // 額外押注＝一般押注以外、不是購買類的模式鈕；同時只顯示「選取中的那顆」（都沒選就顯示第一顆）
    const nb = $("normalBetBtn"), zone = document.querySelector("#bet-mode-panel .zone-body");
    const isOn = (b) => b.classList.contains("is-active") || b.classList.contains("active");
    const ebList = () => zone ? [...zone.children].filter((b) => b.tagName === "BUTTON" && b !== nb && !b.classList.contains("demogame-buy-btn")
      && !/buy|super|購買|超級|^(BF|SF)(?![A-Za-z])/i.test(b.textContent || "")) : [];
    if (nb && ebList().length) {
      document.body.classList.add("m2-eb-toggle");
      ebList().forEach((b) => b.addEventListener("click", (e) => {
        const list = ebList(), i = list.indexOf(b);
        if (!isOn(b)) return;   // 目前是一般押注 → 照原本選這個額外押注
        e.preventDefault(); e.stopImmediatePropagation();
        (list[i + 1] || nb).click();   // 已開啟 → 下一種額外押注，最後一種再點回一般押注
        syncEbVisible();
      }, true));
    }
    const eb = ebList()[0] || null;
    const syncEbVisible = () => {
      const list = ebList();
      if (!nb || !list.length) return;
      const shown = list.find(isOn) || list[0];
      // 只在真的要改時才動 class（即使值相同，改 class 也會產生 mutation，會跟下面的觀察者互相觸發而卡死）
      list.forEach((b) => {
        if (!b.classList.contains("m2-eb")) b.classList.add("m2-eb");
        const hide = b !== shown;
        if (b.classList.contains("m2-eb-hidden") !== hide) b.classList.toggle("m2-eb-hidden", hide);
      });
    };
    // 得獎明細只給 N 消（Pay Anywhere）與聚集消除（Cluster）的遊戲（2026-11-27 使用者）；Line／Ways 不顯示。
    // 依 Help 判斷，遊戲可用 window.DEMOGAME_WIN_DETAIL = true／false 指定
    const winDetail = typeof window.DEMOGAME_WIN_DETAIL === "boolean" ? window.DEMOGAME_WIN_DETAIL
      : /pay\s*anywhere|任意位置|cluster|聚集|相連/i.test(helpText);
    const wins = document.createElement("div");
    wins.id = "m2-wins"; wins.setAttribute("aria-label", "Win detail");
    const ensureEbLabel = () => {
      if (!nb) return;
      ebList().forEach((b) => {
        if (b.querySelector(".m2-eb-label")) return;
        const texts = [...b.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim());
        if (!texts.length) return;
        const wrap = document.createElement("span"); wrap.className = "m2-eb-label";
        b.insertBefore(wrap, texts[0]);
        texts.forEach((t) => wrap.appendChild(t));
        const sw = document.createElement("span"); sw.className = "m2-sw"; sw.setAttribute("aria-hidden", "true");
        wrap.appendChild(sw);
      });
    };
    const fillModes = () => {
      ensureEbLabel();
      syncEbVisible();
      if (!zone) return;
      zone.querySelectorAll(".m2-mode-empty").forEach((n) => n.remove());
      const shown = [...zone.children].filter((n) => n.tagName === "BUTTON" && getComputedStyle(n).display !== "none").length;
      let empty = shown % 3 ? 3 - shown % 3 : 0;
      // 得獎明細：N 消／聚集消除的遊戲一律保留這一格（沒得獎時是空框，同實機；2026-11-27 使用者「any8、cluster 的都要這個」）
      if (empty && winDetail) { if (wins.parentNode !== zone) zone.appendChild(wins); empty--; } else if (wins.parentNode) wins.remove();
      // 其餘空格不補（沒有內容的格子拿掉，剩下的置中）
    };
    // 得獎明細：讀除錯區的得獎清單（#lineList，例「C1 | J × 8」「0.40」），轉成「8｜J 圖｜0.40」；找不到格式就顯示原文
    const symImg = {};
    const learnSyms = () => document.querySelectorAll("#board .cell").forEach((c) => {
      const code = [...c.classList].map((k) => (k.match(/^symbol-([a-z0-9]+)$/i) || [])[1]).find(Boolean);
      const img = c.querySelector("img");
      if (code && img && img.src && !symImg[code.toUpperCase()]) symImg[code.toUpperCase()] = img.src;
    });
    // 每消除一次即時更新（2026-11-27 使用者）：盤面出現中獎格（.cell.hit）時，依符號數顆數＋這次增加的得分；
    // 一局結束再用 #lineList 的正式明細（顆數、符號、各自得分）校正。只顯示最新三列，塞不下的跳過（不輪播）
    let winRows = [], prevWin = 0, ended = true, lastHit = 0;
    const MAX_ROWS = 3;
    const drawWins = () => {
      const view = winRows.slice(-MAX_ROWS);
      while (view.length < MAX_ROWS) view.unshift({ empty: true });
      wins.innerHTML = view.map((r) => r.empty ? `<div class="w-row"></div>` : r.text != null ? `<div class="w-row"><span class="w-t">${r.text}</span></div>`
        : `<div class="w-row"><span class="w-n">${r.n}</span><span class="w-s">${symImg[r.sym] ? `<img src="${symImg[r.sym]}" alt="${r.sym}">` : r.sym}</span><span class="w-v">${r.v}</span></div>`).join("");
      fillModes();
    };
    const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const msgWin = () => { const m = (($("messageBar") || {}).textContent || "").match(/win[^0-9]*([0-9][0-9,]*(?:\.[0-9]+)?)/i); return m ? Number(m[1].replace(/,/g, "")) : null; };
    const onHit = () => {
      const cells = document.querySelectorAll("#board .cell.hit, #board .cell.win, #board .cell.is-win");
      const n = cells.length;
      if (n === lastHit) return;
      lastHit = n;
      if (!n) return;
      learnSyms();
      if (ended) { winRows = []; prevWin = 0; ended = false; }
      const groups = {};
      cells.forEach((c) => {
        const code = [...c.classList].map((k) => (k.match(/^symbol-([a-z0-9]+)$/i) || [])[1]).find(Boolean);
        if (code) groups[code.toUpperCase()] = (groups[code.toUpperCase()] || 0) + 1;
      });
      const syms = Object.keys(groups), now = msgWin();
      const delta = now != null && now > prevWin ? now - prevWin : null;
      if (now != null) prevWin = Math.max(prevWin, now);
      syms.forEach((sym) => winRows.push({ n: groups[sym], sym, v: syms.length === 1 && delta != null ? fmt(delta) : "" }));
      drawWins();
    };
    const readWins = () => {
      learnSyms();
      const rows = [...document.querySelectorAll("#lineList .line-row, #lineList > *")].filter((r, i, a) => a.indexOf(r.closest(".line-row") || r) === i);
      winRows = rows.map((r) => {
        const parts = [...r.children].map((c) => c.textContent.trim()), all = r.textContent.trim();
        if (/沒有|no .*win|^—?$/i.test(all)) return null;
        const m = (parts.length > 1 ? parts.slice(0, -1).join(" ") : all).match(/([A-Z][A-Z0-9]{0,3})\s*[×x]\s*(\d+)/);
        const v = (parts[parts.length - 1] || "").match(/[0-9][0-9,]*(?:\.[0-9]+)?/);
        return m ? { n: m[2], sym: m[1].toUpperCase(), v: v ? v[0] : "" } : { text: esc(all) };
      }).filter(Boolean);
      ended = true; lastHit = 0;
      drawWins();
    };
    const lineList = $("lineList");
    if (lineList) new MutationObserver(readWins).observe(lineList, { childList: true, subtree: true, characterData: true });
    const boardEl = $("board");
    if (boardEl) new MutationObserver(onHit).observe(boardEl, { attributes: true, subtree: true, attributeFilter: ["class"] });
    // 按 SPIN 開新的一局就先清空上一局的明細
    $("spinBtn")?.addEventListener("click", () => { if (ended) { winRows = []; prevWin = 0; lastHit = 0; drawWins(); } }, true);

    // 自動：播放圖示＋文字，自動進行中（原文字變「停止」）換成停止圖示
    const auto = $("autoBtn");
    const syncAuto = () => { if (!auto) return; auto.dataset.cap = auto.textContent.trim().toUpperCase(); auto.classList.toggle("m2-on", /stop|停/i.test(auto.textContent)); };
    if (auto) new MutationObserver(syncAuto).observe(auto, { childList: true, characterData: true, subtree: true });

    // 加速：x1 → x3 → x5 → x10 循環（即原本的速度滑桿，上限放寬到 10）
    const speed = $("speedRange"), turbo = $("m2-turboBtn");
    const syncTurbo = () => {
      const v = Number(speed ? speed.value : 1);
      $("m2-turboCap").textContent = (zh() ? "加速 " : "TURBO ") + "x" + v;
      turbo.classList.toggle("on", v > 1);
    };
    if (speed) {
      turbo.addEventListener("click", () => {
        const STEPS = [1, 3, 5, 10];
        speed.max = "10";
        const cur = Number(speed.value), next = STEPS.find((v) => v > cur) || STEPS[0];
        speed.value = String(next);
        speed.dispatchEvent(new Event("input", { bubbles: true }));
        speed.dispatchEvent(new Event("change", { bubbles: true }));
        syncTurbo();
      });
      speed.addEventListener("input", syncTurbo);
    } else turbo.disabled = true;

    // 設定：遊玩區「設定」開關，浮在遊玩區裡；✕、Esc、點視窗外關閉
    const settings = $("settings-wrap");
    const toggleSettings = (open) => { document.body.classList.toggle("m2-settings-open", open); $("m2-menuBtn").classList.toggle("on", document.body.classList.contains("m2-settings-open")); };
    const scrim = document.createElement("div");
    scrim.id = "m2-scrim"; root.appendChild(scrim);
    scrim.addEventListener("click", (e) => { e.stopPropagation(); toggleSettings(false); });
    if (settings) {
      root.appendChild(settings);
      const x = document.createElement("button"); x.id = "m2-settings-close"; x.type = "button"; x.setAttribute("aria-label", "Close"); x.textContent = "✕";
      settings.appendChild(x); x.addEventListener("click", () => toggleSettings(false));   // 掛在視窗上（標題文字會被語言切換重寫）
    }
    $("m2-menuBtn").addEventListener("click", (e) => { e.stopPropagation(); toggleSettings(!document.body.classList.contains("m2-settings-open")); });
    document.addEventListener("click", (e) => {
      if (!document.body.classList.contains("m2-settings-open") || !settings) return;
      if (settings.contains(e.target) || e.target.closest("dialog, #demogame-zoom, #demogame-guide")) return;
      toggleSettings(false);
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") toggleSettings(false); });

    // 展示用彩金列：Demo 不模擬彩金累積，GRAND／MAJOR 顯示 OP Jackpot 起始值 1,000／200，MINOR／MINI 為底注 × 50／× 10；實際押注未滿 2.00 時 GRAND／MAJOR 變灰
    const fmt = (v) => v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const num = (el) => parseFloat(((el || {}).textContent || "0").replace(/[^0-9.]/g, "")) || 0;
    // 底注：目前押注（已乘模式倍數）÷ 選取中模式的倍數；各模式按鈕金額一律 底注 × 該模式倍數（額外押注開啟不影響購買特色，2026-11-27 使用者）
    const modeMult = (btn) => { const m = String((btn && btn.querySelector(".mode-price") || {}).textContent || "").match(/([0-9]+(?:\.[0-9]+)?)\s*x/i); return m ? Number(m[1]) : 1; };
    const baseBet = () => {
      const wager = num($("betValue"));
      const active = document.querySelector("#bet-mode-panel .zone-body > button.is-active, #bet-mode-panel .zone-body > button.active");
      return wager ? wager / modeMult(active) : num($("betBtn"));
    };
    const syncJp = () => {
      if (!showJp) return;
      const base = baseBet(), wager = num($("betValue"));
      const vals = [1000, 200, base * 50, base * 10];
      root.querySelectorAll("#m2-jp .jp-box").forEach((box) => {
        const k = Number(box.dataset.jp), el = box.querySelector(".jp-v");
        // 塞不下就拿掉小數點，再塞不下改 K／M 縮寫（2026-11-27 使用者）
        const forms = [fmt(vals[k]), Math.round(vals[k]).toLocaleString("en-US"),
          vals[k] >= 1e6 ? +(vals[k] / 1e6).toFixed(1) + "M" : +(vals[k] / 1e3).toFixed(1) + "K"];
        for (const t of forms) { el.textContent = t; if (!el.clientWidth || el.scrollWidth <= el.clientWidth) break; }
        box.classList.toggle("is-locked", k < 2 && wager < 2);
      });
    };
    ["betBtn", "betValue"].forEach((id) => { const el = $(id); if (el) new MutationObserver(syncJp).observe(el, { childList: true, characterData: true, subtree: true }); });

    // 押注模式鈕：顯示按下去要花多少錢（底注 × 模式倍數，例如額外押注 2.00、購買特色 100.00），不顯示 (2x) 與括號
    const syncPrices = () => {
      const base = baseBet();
      document.querySelectorAll("#bet-mode-panel .mode-price").forEach((el) => {
        const m = String(el.textContent).match(/([0-9]+(?:\.[0-9]+)?)\s*x/i);
        if (!m || !base) return el.removeAttribute("data-p");
        const p = fmt(base * Number(m[1]));
        if (el.getAttribute("data-p") !== p) el.setAttribute("data-p", p);
      });
    };
    ["betBtn", "betValue"].forEach((id) => { const el = $(id); if (el) new MutationObserver(syncPrices).observe(el, { childList: true, characterData: true, subtree: true }); });

    const syncLang = () => {
      root.querySelectorAll("[data-zh]").forEach((el) => { el.textContent = zh() ? el.dataset.zh : el.dataset.en; });
      const bet = $("betBtn"); if (bet) bet.dataset.cap = zh() ? "押注" : "BET";
      syncTurbo(); syncAuto();
    };
    const lang = $("languageSelect");
    if (lang) lang.addEventListener("change", () => setTimeout(syncLang, 0));

    // 手機：盤面面板放不下時等比縮小（不同遊戲盤面比例不同，量實際高度）
    const stage = $("m2-stage");
    const fitBoard = () => {
      gp.style.transform = ""; gp.style.minHeight = ""; stage.style.flex = "";
      [$("m2-mult"), $("m2-top"), stage].forEach((n) => { if (n) n.style.marginTop = ""; });
      if (!isMobile()) return;
      // 2026-11-27 使用者：下方 SPIN 區每款位置固定，上方空的地方用盤面填滿。
      // 盤面等比縮放撐滿可用寬或高（上限 1.8 倍）；寬度先頂到時把盤面底框拉高填滿剩下的高度，內容置中
      const avail = stage.clientHeight, w = stage.clientWidth, h = gp.offsetHeight, gw = gp.offsetWidth;
      const s = Math.min(1.8, avail / Math.max(1, h), w / Math.max(1, gw));
      if (h * s < avail - 1) gp.style.minHeight = (avail / s) + "px";
      if (Math.abs(s - 1) > 0.001) gp.style.transform = `scale(${s})`;
    };


    // 桌機：遊玩區固定在畫面上（右欄捲動時不動）；位置對齊左欄（以頁面最上方時為準），畫面不夠高時等比縮小
    let baseTop = null;
    // 更新資訊（頁尾 .footer-note：最後調性更新／唯一碼…）：桌機放手機框正下方、跟手機框一起在畫面上下置中；手機放整頁最下面（2026-11-27 使用者）
    const note = document.querySelector(".footer-note");
    const placeNote = () => {
      if (!note) return;
      const want = isMobile() ? (shell.parentNode || document.body) : col;
      if (note.parentNode !== want || note !== want.lastElementChild) want.appendChild(note);
    };
    // 桌機：遊玩區固定在畫面上（右欄捲動時不動）；左右位置對齊左欄，上下置中（2026-11-27 使用者「手機畫面上下置中就好、不用左右」），畫面不夠高時等比縮小
    const pin = () => {
      placeNote();
      if (isMobile()) { root.classList.remove("m2-fixed"); root.style.cssText = ""; col.style.minHeight = ""; if (note) note.style.cssText = ""; baseTop = null; return; }
      const r = col.getBoundingClientRect();
      const gap = 6, w = r.width - gap * 2;
      root.classList.add("m2-fixed");
      root.style.width = w + "px";
      root.style.transform = "none";
      const noteCss = `position:fixed;z-index:20;margin:0 !important;text-align:center;box-sizing:border-box;left:${r.left + gap}px;width:${w}px;`;
      if (note) note.style.cssText = noteCss + "top:0;visibility:hidden;";   // 先用最終寬度量高度
      const h = root.offsetHeight, nh = note ? note.offsetHeight + 10 : 0;
      const s = Math.min(1, (window.innerHeight - 24 - nh) / h);
      const top = Math.max(12, (window.innerHeight - h * s - nh) / 2);
      root.style.top = top + "px";
      root.style.left = (r.left + gap + w * (1 - s) / 2) + "px";
      root.style.transform = s < 1 ? `scale(${s})` : "none";
      if (note) note.style.cssText = noteCss + `top:${top + h * s + 10}px;`;
      col.style.minHeight = (h * s + nh + gap * 2) + "px";
    };

    let raf = 0;
    const relayout = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { fillModes(); syncPrices(); syncJp(); fitBoard(); pin(); }); };
    addEventListener("resize", () => { baseTop = null; relayout(); });
    addEventListener("load", () => { baseTop = null; relayout(); });
    if (window.ResizeObserver) { const ro = new ResizeObserver(relayout); ro.observe(shell); ro.observe(gp); }
    // 模式切換時立即更新顯示哪顆額外押注與金額（不等下一個畫格；背景分頁 requestAnimationFrame 會停）
    if (zone) {
      const zoneOpts = { attributes: true, subtree: true, childList: true, characterData: true, attributeFilter: ["class", "style", "hidden"] };
      const zoneObs = new MutationObserver(() => {
        zoneObs.disconnect();   // 自己改的不再觸發自己（防無限循環）
        try { syncEbVisible(); syncPrices(); } finally { zoneObs.takeRecords(); zoneObs.observe(zone, zoneOpts); }
        relayout();
      });
      zoneObs.observe(zone, zoneOpts);
    }

    // 盤面倍數字級跟著格子大小（部分遊戲用 --cell-size，原本固定 64px）
    const board = $("board");
    if (board && window.ResizeObserver) new ResizeObserver(() => {
      const cell = board.querySelector(".cell");
      if (cell) board.style.setProperty("--cell-size", cell.getBoundingClientRect().width + "px");
    }).observe(board);

    syncLang(); syncJp(); fillModes(); syncPrices(); readWins(); fitBoard(); pin();

    // 手機：開啟時直接對齊遊玩區（標題列＋遊玩區剛好一個螢幕）
    if (isMobile()) addEventListener("load", () => [50, 400].forEach((ms) => setTimeout(() => window.scrollTo(0, root.getBoundingClientRect().top + window.scrollY), ms)), { once: true });
  }
  // 等各遊戲在共用 JS 之後的初始化（例如 h027BindCommonControls）跑完再排版
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", setup); else setTimeout(setup, 0);
})();
// ==== /phone-layout ====

// ==== dev-skin：Dev 模式（遊玩區換成跟 dev 環境一樣的美術，2026-11-27 使用者）====
// 遊戲設 window.DEMOGAME_DEV_SKIN = "./Source/Dev/"（dev 版美術放的資料夾）才有；設定多一個「Dev 模式」開關，預設開。
// 只換手機框裡的畫面（背景、彩金列、盤面底與框、緞帶、押注模式、餘額列、操作列），外框與功能不變。
(function () {
  const $ = (id) => document.getElementById(id);
  // 意象物（宙斯等）：dev 骨架動畫預先逐格算好的透明動畫圖（本機直接開檔也能顯示）
  // cfg = { img, x0, x1, y0, y1（圖的世界座標範圍）, yBottom, yTop（要露出的範圍：腰帶到頭頂）, width（人物寬） }
  // 腰帶對齊盤面上緣，露出部分約占意象區高 72%、寬約 62%（同 dev）
  function setupHero(base, root, cfg) {
    const img = new Image();
    img.id = "m2-zeus"; img.alt = ""; img.draggable = false; img.decoding = "async";
    img.src = base + cfg.img;
    root.insertBefore(img, root.firstChild);
    const splitCss = document.createElement("style");
    splitCss.id = "dg-dev-split";
    document.head.appendChild(splitCss);
    const place = () => {
      const gp = document.getElementById("grid-panel");
      if (!gp || !root.classList.contains("dv")) return;
      const rr = root.getBoundingClientRect(), sc = rr.width / Math.max(1, root.offsetWidth);
      const w = root.clientWidth, hero = (gp.getBoundingClientRect().top - rr.top) / sc;
      if (w < 10 || hero < 10) return;
      const k = Math.min(hero * (cfg.fill || 0.72) / (cfg.yTop - cfg.yBottom), w * (cfg.widthFrac || 0.62) / (cfg.width || 600));
      const css = `width:${((cfg.x1 - cfg.x0) * k).toFixed(1)}px;height:${((cfg.y1 - cfg.y0) * k).toFixed(1)}px;` +
        `left:${(w / 2 + cfg.x0 * k).toFixed(1)}px;top:${(hero + 6 - (cfg.y1 - cfg.yBottom) * k).toFixed(1)}px;`;
      if (img.style.cssText !== css) img.style.cssText = css;
      // FG 上下背景分界（盤面中線）；寫在樣式表（遊玩區 inline style 會被版面程式清掉）
      const split = `html body.slot-simulator.m2 #m2.dv { --dv-split: ${Math.round(hero + gp.offsetHeight / 2)}px; }`;
      if (splitCss.textContent !== split) splitCss.textContent = split;
    };
    let raf = 0;
    const later = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(place); };
    const ro = new ResizeObserver(later);
    ro.observe(root);
    const gp = document.getElementById("grid-panel");
    if (gp) ro.observe(gp);
    new MutationObserver(later).observe(root, { attributes: true, attributeFilter: ["class", "style"] });
    addEventListener("resize", later);
    addEventListener("scroll", later, { passive: true });
    later();
  }
  // ---- dev 特色畫面（2026-11-27 使用者：FG、買特色確認、轉場、結算都要跟 dev 一樣）----
  function setupFeature(base, root, cfg) {
    const body = document.body, bar = $("messageBar");
    const dv = () => root.classList.contains("dv");
    const fg = () => body.classList.contains("fg-mode");
    const img = (n) => `url("${base}${n}.webp")`;
    const zh = () => (($("languageSelect") || {}).value || "zh") !== "en";
    const txt = (sel) => ((document.querySelector(sel) || {}).textContent || "").trim();

    // 緞帶：待機（或 FG 進行中的狀態文字）改顯示 dev 的待機文字圖，3 秒輪播
    const READY = /ready|press spin|準備|请按|請按/i, FGSTAT = /^(FG|免費遊戲|免费游戏)\s*\d+\s*\/\s*\d+/i;
    let idleIdx = 0;
    const syncBar = () => {
      if (!bar) return;
      const t = bar.textContent.trim();
      const list = fg() ? cfg.idleFg : cfg.idle;
      const on = !!(dv() && list && list.length && (READY.test(t) || FGSTAT.test(t) || t === ""));
      if (bar.classList.contains("dv-idle") !== on) bar.classList.toggle("dv-idle", on);
      const v = on ? img(list[idleIdx % list.length]) : "";
      if (bar.style.getPropertyValue("--dv-idleImg") !== v) { if (v) bar.style.setProperty("--dv-idleImg", v); else bar.style.removeProperty("--dv-idleImg"); }
    };
    setInterval(() => { idleIdx++; syncBar(); }, 3000);
    if (bar) new MutationObserver(syncBar).observe(bar, { childList: true, characterData: true, subtree: true });
    new MutationObserver(syncBar).observe(root, { attributes: true, attributeFilter: ["class"] });
    new MutationObserver(syncBar).observe(body, { attributes: true, attributeFilter: ["class"] });

    // FG 下半部：左「FREE SPINS 剩餘場次」、中間倍數球、右 FG 贏分（押注、餘額、操作列收起來，同 dev）
    const panel = document.createElement("div");
    panel.id = "m2-fg";
    panel.innerHTML = `<div class="fg-left"><span class="fg-k">FREE SPINS</span><span class="fg-n" id="m2-fg-left">0</span></div>`
      + `<div class="fg-orb"><span class="fg-x" id="m2-fg-mult">1x</span></div>`
      + `<div class="fg-right"><span class="fg-k">TOTAL WIN</span><span class="fg-w" id="m2-fg-win">0.00</span></div>`;
    if (bar) bar.after(panel);
    const setT = (id, v) => { const e = $(id); if (e && e.textContent !== v) e.textContent = v; };
    const syncFg = () => {
      if (!fg()) return;
      const m = txt("#fgLeftValue").match(/(\d+)\s*\/\s*(\d+)/);
      if (m) setT("m2-fg-left", m[1]);
      const x = (txt("#demogame-info-bar .dib-v") || txt("#multiplierValue")).replace(/[^\d.]/g, "") || "1";
      setT("m2-fg-mult", x + "x");
      setT("m2-fg-win", txt("#credit-bar .credit-cell:nth-child(3) .i-value") || "0.00");
    };

    // 全畫面演出（轉場、結算、買特色確認）
    const fx = document.createElement("div");
    fx.id = "m2-fx"; fx.hidden = true;
    root.appendChild(fx);
    let fxBusy = false, fxTimer = 0;
    const closeFx = () => { clearTimeout(fxTimer); fx.hidden = true; fx.className = ""; fx.innerHTML = ""; fxBusy = false; };
    const showFx = (cls, html, ms) => {
      clearTimeout(fxTimer); fx.className = cls; fx.innerHTML = html; fx.hidden = false; fxBusy = true;
      if (ms) fxTimer = setTimeout(closeFx, ms);
    };
    fx.addEventListener("click", () => { if (fx.classList.contains("fx-auto")) closeFx(); });

    // 進 FG 轉場／FG 結算
    let wasFg = fg(), trigWin = 0;
    const num = (t) => parseFloat(String(t).replace(/[^\d.-]/g, "")) || 0;
    const winCell = () => txt("#credit-bar .credit-cell:nth-child(3) .i-value");
    const onMode = () => {
      const now = fg();
      if (now === wasFg) return;
      wasFg = now;
      if (!dv()) return;
      if (now) {
        trigWin = num(winCell());   // 觸發局（BF 為入場盤）的贏分；FG 中 WIN 欄＝觸發局＋FG 累積
        setTimeout(() => {
          syncFg();
          const m = txt("#fgLeftValue").match(/(\d+)\s*\/\s*(\d+)/);
          showFx("fx-auto fx-trans", `<div class="fx-card"><div class="fx-img fx-won"></div><div class="fx-num">${m ? m[2] : ""}</div><div class="fx-img fx-fs"></div></div>`, 2600);
        }, 60);
      } else {
        setTimeout(() => {
          const total = Math.max(0, num(winCell()) - trigWin);
          showFx("fx-auto fx-result", `<div class="fx-card"><div class="fx-img fx-won"></div><div class="fx-num">${total.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>`
            + `<div class="fx-sub">${zh() ? "免費遊戲總贏分" : "FREE SPINS TOTAL WIN"}</div></div>`, 3500);
        }, 250);
      }
    };
    new MutationObserver(onMode).observe(body, { attributes: true, attributeFilter: ["class"] });

    // FG 自動接續（dev 的 FG 不用按）；演出播放中先等
    const spin = $("spinBtn");
    let readySince = 0;
    setInterval(() => {
      syncFg();
      if (!dv() || !fg() || fxBusy || !spin || spin.disabled) { readySince = 0; return; }
      if (!readySince) { readySince = performance.now(); return; }
      if (performance.now() - readySince > 450) { readySince = 0; spin.click(); }
    }, 150);

    // 買特色：先跳 dev 的確認框
    const buy = $("buyFeatureBtn");
    let confirmed = false;
    // 掛在 window 的捕獲階段：比遊戲與共用模組的任何點擊處理都早，確認前不讓遊戲切到 BF
    if (buy) window.addEventListener("click", (e) => {
      if (!e.target || !e.target.closest || !e.target.closest("#buyFeatureBtn")) return;
      if (!dv() || confirmed) { confirmed = false; return; }
      e.stopImmediatePropagation(); e.preventDefault();
      if (buy.disabled) return;
      const pe = buy.querySelector(".mode-price");
      const price = (pe && (pe.dataset.p || pe.textContent)) || "";
      showFx("fx-buy", `<div class="fx-board"><div class="fx-title">${zh() ? "購買特色" : "BUY FEATURE"}</div>`
        + `<div class="fx-q">${zh() ? "確定要購買免費遊戲嗎？" : "BUY FREE SPINS FOR"}</div><div class="fx-price">${price}</div>`
        + `<div class="fx-btns"><button type="button" class="fx-cancel">${zh() ? "取消" : "CANCEL"}</button>`
        + `<button type="button" class="fx-ok">${zh() ? "購買" : "BUY"}</button></div></div>`, 0);
      fx.querySelector(".fx-cancel").onclick = closeFx;
      fx.querySelector(".fx-ok").onclick = () => { closeFx(); confirmed = true; buy.click(); };
    }, true);

    const P = "html body.slot-simulator.m2 #m2.dv", F = "html body.slot-simulator.m2.fg-mode #m2.dv";
    const st = document.createElement("style");
    st.id = "dg-dev-feature";
    st.textContent = `
  #m2-fg { display: none; }
  ${P} #messageBar.dv-idle { color: transparent !important; text-shadow: none !important; }
  ${F} > #bet-mode-panel, ${F} > #credit-bar, ${F} > #m2-dock { display: none !important; }
  ${F} > #m2-fg { display: block; position: relative; flex: 1 1 auto; min-height: 210px; }
  #m2-fg .fg-orb { position: absolute; left: 50%; top: 0; width: 46%; aspect-ratio: 308 / 296; transform: translateX(-50%); isolation: isolate;
    background: ${img("Free_BG_Golden")} center / 100% 100% no-repeat; display: grid; place-items: center; }
  #m2-fg .fg-orb::before { content: ""; position: absolute; inset: 13% 18% 22%; z-index: -1; border-radius: 50%; background: ${img("Free_BG_Ball")} center / 100% 100% no-repeat; }
  #m2-fg .fg-x, #m2-fx .fx-num, #m2-fg .fg-n { font: 900 34px/1 Georgia, "Times New Roman", serif; background: linear-gradient(180deg, #fff6b0 0%, #ffd23a 45%, #ff9a00 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-stroke: 1.2px #8a1d00; filter: drop-shadow(0 2px 0 #5a0d00) drop-shadow(0 0 6px rgba(0, 0, 0, .6)); }
  #m2-fg .fg-x { font-size: 40px; margin-top: -10%; }
  #m2-fg .fg-left, #m2-fg .fg-right { position: absolute; bottom: 8px; width: 34%; height: 86px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
    border: 14px solid transparent; }
  #m2-fg .fg-left { left: 6px; border-image: ${img("FG_FreespinLeft_Board")} 30 fill / 14px stretch; }
  #m2-fg .fg-right { right: 6px; border-image: ${img("FG_Win_Board")} 28 fill / 14px stretch; }
  #m2-fg .fg-k { color: #ffe9a8; font: 900 13px/1 Georgia, serif; letter-spacing: .5px; text-shadow: 0 2px 0 #3a1c00; white-space: nowrap; }
  #m2-fg .fg-n { font-size: 32px; }
  #m2-fg .fg-w { color: #fff; font: 800 17px/1 "Segoe UI", sans-serif; text-shadow: 0 1px 2px #000; }
  #m2-fx { position: absolute; inset: 0; z-index: 70; display: grid; place-items: center; background: rgba(4, 2, 18, .72); }
  #m2-fx[hidden], #m2:not(.dv) #m2-fx { display: none; }
  #m2-fx .fx-card { display: flex; flex-direction: column; align-items: center; gap: 10px; animation: dvPop .45s cubic-bezier(.2, 1.4, .4, 1) both; }
  #m2-fx .fx-img { background: center / contain no-repeat; }
  #m2-fx .fx-won { width: 300px; height: 82px; background-image: ${img("FSpinWin")}; }
  #m2-fx .fx-fs { width: 300px; height: 52px; background-image: ${img("Freespin")}; }
  #m2-fx .fx-num { font-size: 80px; }
  #m2-fx.fx-result .fx-num { font-size: 54px; }
  #m2-fx .fx-sub { color: #ffe9a8; font: 900 15px/1 Georgia, serif; text-shadow: 0 2px 0 #3a1c00; }
  #m2-fx .fx-board { position: relative; width: min(86%, 330px); aspect-ratio: 630 / 748; box-sizing: border-box; padding: 9% 17% 10%; display: flex; flex-direction: column; align-items: center; gap: 12px;
    background: ${img("FeatureBoard")} center / 100% 100% no-repeat; animation: dvPop .35s ease-out both; }
  #m2-fx .fx-title { margin-top: 1%; color: #ffe9a8; font: 900 20px/1 Georgia, "Microsoft JhengHei", serif; text-shadow: 0 2px 0 #3a1c00; }
  #m2-fx .fx-q { margin-top: 22%; color: #fff; font: 700 15px/1.3 "Segoe UI", "Microsoft JhengHei", sans-serif; text-align: center; }
  #m2-fx .fx-price { color: #ffd23a; font: 900 34px/1 Georgia, serif; text-shadow: 0 2px 0 #5a0d00; }
  #m2-fx .fx-btns { margin-top: auto; margin-bottom: 4%; display: flex; gap: 10px; width: 100%; }
  #m2-fx .fx-btns button { flex: 1; height: 46px; border: 0; padding: 0; cursor: pointer; color: #fff; font: 900 15px/1 "Segoe UI", "Microsoft JhengHei", sans-serif; text-shadow: 0 1px 2px #000;
    background: center / 100% 100% no-repeat; }
  html body #m2 #m2-fx .fx-btns button.fx-ok { background: ${img("Btn_Buy")} center / 100% 100% no-repeat !important; }
  html body #m2 #m2-fx .fx-btns button.fx-cancel { background: ${img("Btn_Cancel")} center / 100% 100% no-repeat !important; }
  @keyframes dvPop { from { transform: scale(.6); opacity: 0; } to { transform: scale(1); opacity: 1; } }`;
    document.head.appendChild(st);
    syncBar();
  }
  function setup() {
    const base = window.DEMOGAME_DEV_SKIN;
    const root = $("m2");
    if (!base || !root) return;
    const url = (n) => `url("${base}${n}.webp")`;
    const vars = {
      bg: "Base_BG", bgDown: "Base_BG_Down", fgBg: "Free_BG", fgBgDown: "Free_BG_Down", reelBg: "BG_ReelBG", reelFrame: "BG_ReelFrame",
      grand: "Grand_pool", major: "Major_pool", minor: "Minor_pool", mini: "Mini_pool", opTop: "IconText_Top", opBoard: "IconText_Board",
      tGrand: "TitleText_Grand", tMajor: "TitleText_Major", tMinor: "TitleText_Minor", tMini: "TitleText_Mini",
      btnEb: "Btn_ExtraBet", btnBf: "Btn_BuyFeature", swOn: "Switch_On_Btn", swOff: "Switch_Off_Btn", winFrame: "Win_Frame_BG",
      start: "UiBtn_Start", ring: "UiBtn_Start_ring", arrow: "Ui_SpinArrow", setting: "UiIcon_Setting", betOpt: "UiIcon_BetOption",
      auto: "UiIcon_Auto", autoStop: "UiIcon_AutoStop", turbo: "UiIcon_Turbo", quick: "UiIcon_Quick", normal: "UiIcon_Normal",
      credit: "UiIcon_Credit", bet: "UiIcon_Bet", win: "UiIcon_Win", fgWin: "FG_Win_Board"
    };
    // 變數寫在樣式表裡（遊玩區的 inline style 會被版面程式清掉）
    const varCss = Object.entries(vars).map(([k, n]) => `--dv-${k}: ${url(n)};`).join(" ");

    const P = "html body.slot-simulator.m2 #m2.dv";
    const css = `
  html body.slot-simulator.m2 #m2 { ${varCss} }
  /* 背景：上半天空神殿、下半大理石（FG 換夜景） */
  ${P} { background: var(--dv-bg) center top / 100% auto no-repeat, var(--dv-bgDown) center bottom / 100% auto no-repeat, #e6d2b0 !important; }
  /* FG：上圖延伸到盤面中線、下圖從中線接起（等比、只裁左右），中間不露底色（--dv-split 由程式依盤面位置設定） */
  html body.slot-simulator.m2.fg-mode #m2.dv { background: var(--dv-fgBg) center top / auto calc(var(--dv-split, 50%) + 2px) no-repeat,
    var(--dv-fgBgDown) center bottom / auto calc(100% - var(--dv-split, 50%) + 2px) no-repeat, #1b1736 !important; }
  ${P} > #feature-bar { background: rgba(4, 14, 26, .55) !important; }
  /* 彩金列：GRAND／MAJOR 上排、MINOR／MINI 下排，中間 OP JACKPOT */
  ${P} #m2-jp { height: auto !important; grid-template-columns: 1fr 78px 1fr !important; grid-template-rows: 38px 38px; gap: 14px 4px !important; padding: 12px 0 0 !important;
    background: none !important; border: 0 !important; box-shadow: none !important; overflow: visible !important; }
  /* 彩金牌：九宮格（兩端圓角維持比例，只拉中間） */
  ${P} #m2-jp .jp-box { height: 34px !important; box-sizing: border-box !important; justify-content: center; background: none !important; border-style: solid !important; border-width: 0 17px !important; border-color: transparent; border-radius: 0 !important; box-shadow: none !important;
    border-image-source: var(--dv-jpArt) !important; border-image-slice: 0 50 fill !important; border-image-width: 0 17px !important; border-image-repeat: stretch !important; }
  ${P} #m2-jp .jp-box::before { display: none !important; }
  ${P} #m2-jp .jp-grand { grid-area: 1 / 1 !important; --dv-jpArt: var(--dv-grand); }
  ${P} #m2-jp .jp-major { grid-area: 1 / 3 !important; --dv-jpArt: var(--dv-major); }
  ${P} #m2-jp .jp-minor { grid-area: 2 / 1 !important; --dv-jpArt: var(--dv-minor); }
  ${P} #m2-jp .jp-mini { grid-area: 2 / 3 !important; --dv-jpArt: var(--dv-mini); }
  ${P} #m2-jp .jp-k { position: absolute; top: -13px; left: -11px; width: 64%; height: 18px; font-size: 0 !important; background: left center / contain no-repeat; }
  ${P} #m2-jp .jp-major .jp-k, ${P} #m2-jp .jp-mini .jp-k { left: auto; right: -11px; background-position: right center; }
  ${P} #m2-jp .jp-grand .jp-k { background-image: var(--dv-tGrand); }
  ${P} #m2-jp .jp-major .jp-k { background-image: var(--dv-tMajor); }
  ${P} #m2-jp .jp-minor .jp-k { background-image: var(--dv-tMinor); }
  ${P} #m2-jp .jp-mini .jp-k { background-image: var(--dv-tMini); }
  ${P} #m2-jp .jp-v { margin-top: 4px; color: #ffe27a !important; font: 900 18px/1 "Segoe UI", sans-serif !important; text-shadow: 0 1px 0 #6b3a00, 0 0 6px rgba(0, 0, 0, .8) !important; }
  ${P} #m2-jp .jp-op { grid-area: 1 / 2 / 3 / 3 !important; width: 78px !important; height: 70px !important; align-self: start; padding-top: 0; margin-top: -12px;
    background: var(--dv-opTop) center top / 82% auto no-repeat, var(--dv-opBoard) center 30px / 100% 26px no-repeat; }
  ${P} #m2-jp .jp-op > * { display: none !important; }
  ${P} #m2-jp .jp-op::before { display: none !important; }
  ${P} #m2-jp .jp-op::after { content: "JACKPOT"; position: absolute; left: 0; right: 0; top: 34px; width: auto; height: auto; transform: none; animation: none; background: none;
    -webkit-mask: none; mask: none; border-radius: 0; text-align: center; color: #ffe27a; font: 900 13px/1 "Segoe UI", sans-serif; letter-spacing: .5px; text-shadow: 0 1px 0 #6b3a00; }
  /* Mult：金框紫底膠囊 */
  ${P} #m2-mult::before, ${P} #m2-mult::after { background: linear-gradient(90deg, transparent, rgba(201, 154, 46, .7)) !important; }
  ${P} #m2-mult::after { background: linear-gradient(90deg, rgba(201, 154, 46, .7), transparent) !important; }
  ${P} #demogame-info-bar { border: 2px solid #c99a2e !important; background: linear-gradient(180deg, #4a2a78, #2b1748) !important; box-shadow: 0 2px 6px rgba(0, 0, 0, .5) !important; }
  ${P} #demogame-info-bar .dib-k { color: #ffe9a8 !important; } ${P} #demogame-info-bar .dib-v { color: #fff !important; text-shadow: 0 0 6px rgba(255, 210, 90, .8) !important; }
  /* 盤面：紫色底＋金框 */
  /* 框整張疊在盤面上（框的長寬比跟盤面接近，直接貼不會錯位）；紫底只鋪在柱子內側 */
  ${P} #grid-panel { position: relative !important; isolation: isolate; background: none !important; border: 0 !important; border-image: none !important; border-radius: 0 !important; box-shadow: none !important;
    padding: 4.4% 6.6% 3.2% !important; }
  ${P} #grid-panel::before { content: ""; position: absolute; inset: 3% 5% 2.5%; z-index: -1; background: var(--dv-reelBg) center / cover no-repeat; pointer-events: none; }
  ${P} #grid-panel::after { content: ""; position: absolute; inset: 0; z-index: 5; background: var(--dv-reelFrame) center / 100% 100% no-repeat; pointer-events: none; }
  ${P} #grid-panel .cell { background: transparent !important; border-color: transparent !important; }
  /* 訊息緞帶：左右對稱的翅膀框 */
  ${P} #messageBar { height: 46px !important; background: none !important; color: #ffe27a !important; font: 900 16px/1 "Segoe UI", "Microsoft JhengHei", sans-serif !important; text-shadow: 0 1px 0 #3a1c00, 0 0 6px rgba(0, 0, 0, .8) !important; z-index: 0; }
  /* 緞帶：左翅＋中段（拉長）＋右翅三張圖當背景，待機文字圖（--dv-idleImg）疊最上層 */
  ${P} #messageBar { --dv-idleImg: none; background: var(--dv-idleImg) center / auto 58% no-repeat, url("${base}Win_Frame_L.webp") left center / auto 100% no-repeat,
    url("${base}Win_Frame_R.webp") right center / auto 100% no-repeat, url("${base}Win_Frame_M.webp") center / calc(100% - 100px) 100% no-repeat !important; }
  ${P} #messageBar::before, ${P} #messageBar::after { display: none !important; }
  ${P} #messageBar.win { color: #ffffff !important; }
  /* 押注模式：dev 的額外押注（青）／購買特色（藍）按鈕圖，開關用 dev 的 on／off 圖 */
  ${P} #bet-mode-panel .zone-body > button, ${P} #m2-wins { height: clamp(66px, 9dvh, 80px) !important; }
  ${P} #bet-mode-panel .zone-body > button { gap: 2px !important; padding: 4px 6px !important; border: 0 !important; box-shadow: none !important; background: center / 100% 100% no-repeat !important; color: #fff2c4 !important;
    font: 900 13px/1.05 "Segoe UI", sans-serif !important; text-shadow: 0 2px 0 #1a2a3a, 0 0 4px rgba(0, 0, 0, .8) !important; }
  ${P} #bet-mode-panel .zone-body > button.is-active { filter: brightness(1.12); }
  /* 押注模式按鈕、第三格：九宮格（八角邊框不變形） */
  ${P} #bet-mode-panel .zone-body > button:is(#extraBetBtn, #buyFeatureBtn, .mode-btn, .demogame-buy-btn, button), ${P} #m2-wins { box-sizing: border-box !important; border-style: solid !important; border-color: transparent !important; border-width: 15px !important; border-radius: 0 !important;
    background: none !important; border-image: var(--dv-btnArt) 28 fill / 15px stretch !important; padding: 0 !important; }
  ${P} #bet-mode-panel .zone-body > button.m2-eb, ${P} #bet-mode-panel .zone-body > #extraBetBtn { --dv-btnArt: var(--dv-btnEb); }
  ${P} #bet-mode-panel .zone-body > button.demogame-buy-btn { --dv-btnArt: var(--dv-btnBf); }
  ${P} #m2-wins { --dv-btnArt: var(--dv-fgWin); }
  ${P} #bet-mode-panel .zone-body > button .mode-price { background: none !important; color: #ffe27a !important; padding: 0 !important; text-shadow: 0 1px 0 #3a1c00 !important; }
  ${P} #bet-mode-panel .zone-body > button .mode-price[data-p] { font-size: 0 !important; }
  ${P} #bet-mode-panel .zone-body > button .mode-price[data-p]::after { font-size: 15px; }
  ${P} .m2-eb-label { flex-direction: column; gap: 2px !important; font-size: 12.5px; }
  ${P} .m2-sw { order: 9; width: 40px !important; height: 18px !important; border-radius: 0 !important; background: var(--dv-swOff) center / contain no-repeat !important; }
  ${P} .m2-sw::after { display: none !important; }
  ${P} button.is-active .m2-sw { background-image: var(--dv-swOn) !important; }
  ${P} #m2-wins .w-row + .w-row { border-top-color: rgba(255, 226, 122, .25) !important; }
  ${P} #m2-wins .w-v { color: #ffe27a !important; } ${P} #m2-wins .w-n { color: #fff !important; }
  /* 餘額列：深色半透明格、黃色圖示＋白色數字 */
  ${P} #credit-bar { background: transparent !important; border: 0 !important; box-shadow: none !important; gap: 6px !important; }
  ${P} #credit-bar .credit-cell { display: flex !important; align-items: center !important; flex-direction: row !important; justify-content: flex-start !important; gap: 8px !important; padding: 6px 8px !important; border: 0 !important;
    border-radius: 6px !important; background: rgba(40, 24, 8, .55) !important; }
  ${P} #credit-bar .credit-cell::before { content: ""; display: block; flex: 0 0 auto; width: 22px; height: 22px; background: var(--dv-ico) center / contain no-repeat; }
  ${P} #credit-bar .credit-cell:nth-child(1) { --dv-ico: var(--dv-credit); } ${P} #credit-bar .credit-cell:nth-child(2) { --dv-ico: var(--dv-bet); } ${P} #credit-bar .credit-cell:nth-child(3) { --dv-ico: var(--dv-win); }
  ${P} #credit-bar .i-label { order: 2; font-size: 0 !important; }
  ${P} #credit-bar .i-label button { font-size: 12px !important; }
  ${P} #credit-bar .i-value { order: 1; flex: 1 1 auto; text-align: right; color: #fff !important; font: 800 15px/1 "Segoe UI", sans-serif !important; text-shadow: 0 1px 2px rgba(0, 0, 0, .8); }
  /* 操作列：黃色圖示、紫色 SPIN（dev 的圖） */
  ${P} #m2-dock .m2-key > svg, ${P} #m2-dock .m2-key > span, ${P} #betBtn::after, ${P} #autoBtn::after { display: none !important; }
  ${P} #m2-dock .m2-key::before, ${P} #betBtn::before, ${P} #autoBtn::before { content: "" !important; width: 44px !important; height: 44px !important; background: var(--dv-ico) center / contain no-repeat !important;
    -webkit-mask: none !important; mask: none !important; }
  ${P} #m2-menuBtn { --dv-ico: var(--dv-setting); }
  ${P} #betBtn { --dv-ico: var(--dv-betOpt); }
  ${P} #autoBtn { --dv-ico: var(--dv-auto); } ${P} #autoBtn.m2-on { --dv-ico: var(--dv-autoStop); }
  ${P} #m2-turboBtn { --dv-ico: var(--dv-normal); } ${P} #m2-turboBtn[data-speed="3"] { --dv-ico: var(--dv-quick); } ${P} #m2-turboBtn[data-speed="5"], ${P} #m2-turboBtn[data-speed="10"] { --dv-ico: var(--dv-turbo); }
  ${P} #spinBtn { border: 0 !important; box-shadow: none !important; background: var(--dv-ring) center / 100% 100% no-repeat, var(--dv-start) center / 84% 84% no-repeat !important; }
  ${P} #spinBtn::before { width: 58% !important; height: 58% !important; background: var(--dv-arrow) center / contain no-repeat !important; -webkit-mask: none !important; mask: none !important; }
  ${P} #spinBtn:disabled { opacity: 1 !important; filter: brightness(.7); }
  /* 上方意象區：彩金列下面放 dev 的宙斯（#m2-zeus 動畫圖），剩下的高度都給這區；盤面維持原本大小不拉高 */
  ${P} { isolation: isolate; }
  html body.slot-simulator.m2 #m2.dv:not(.m2-fixed) { position: relative; }
  #m2-zeus { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; display: block; max-width: none; user-select: none; }
  #m2:not(.dv) #m2-zeus { display: none; }
  ${P} #m2-jp { flex: 1 1 auto !important; min-height: 196px; align-content: start; }
  ${P} #m2-stage { flex: 0 0 auto !important; }
  /* 盤面框貼齊手機左右邊（抵掉遊玩區左右內距：桌機 10px、手機 2px） */
  ${P} #m2-stage { margin-left: -10px !important; margin-right: -10px !important; }
  html body.slot-simulator.m2 #m2.dv:not(.m2-fixed) #m2-stage { margin-left: -2px !important; margin-right: -2px !important; }
  ${P} #m2-mult { display: none !important; }   /* dev 沒有的區域不出現（2026-11-27 使用者） */
  /* 盤面：格子撐滿寬度、比例同 dev（寬一點） */
  ${P} .board-shell { width: 100% !important; }
  ${P} #board .cell { aspect-ratio: 1.12 / 1 !important; }
  ${P} #board .cell .sym-img { inset: -3% !important; width: 106% !important; height: 106% !important; }
  /* 額外押注：標題 → 金額 → 開關（同 dev） */
  ${P} .m2-eb-label { display: contents !important; }
  ${P} #bet-mode-panel .zone-body > button .mode-price { order: 1; }
  ${P} .m2-sw { order: 2 !important; }
  /* 第三格（贏分明細）：dev 的深色面板 */
  ${P} #m2-wins { visibility: visible !important; }`;
    const st = document.createElement("style");
    st.id = "dg-dev-skin"; st.textContent = css;
    const addStyle = () => document.head.appendChild(st);
    addStyle();
    addEventListener("load", () => setTimeout(addStyle, 20), { once: true });

    // 加速鈕依速度換 dev 圖示（x1 一般、x3 快、x5／x10 極速）
    const speed = $("speedRange"), turbo = $("m2-turboBtn");
    const syncSpeed = () => { if (turbo && speed && turbo.dataset.speed !== speed.value) turbo.dataset.speed = speed.value; };
    if (speed) { speed.addEventListener("input", syncSpeed); turbo?.addEventListener("click", () => setTimeout(syncSpeed, 0)); syncSpeed(); }

    // 宙斯等意象物（window.DEMOGAME_DEV_HERO），放在彩金列與盤面之間
    const heroCfg = window.DEMOGAME_DEV_HERO;
    if (heroCfg && !$("m2-zeus")) setupHero(base, root, heroCfg);
    // 訊息緞帶待機文字換成 dev 的（window.DEMOGAME_DEV_IDLE_MSG）
    // dev 的特色畫面（window.DEMOGAME_DEV_FEATURE）：緞帶待機圖、FG 下半部、自動接續 FG、買特色確認、進 FG 轉場、FG 結算
    const feat = window.DEMOGAME_DEV_FEATURE;
    if (feat) setupFeature(base, root, feat);

    // 設定：多一個「Dev 模式」開關（預設開，記在這台瀏覽器）
    const KEY = "dg-dev-skin";
    let on = true;
    try { on = localStorage.getItem(KEY) !== "0"; } catch (_) {}
    const apply = () => root.classList.toggle("dv", on);
    const group = document.querySelector("#settings-wrap .setting-toggle-group") || document.querySelector("#settings-wrap .setting-body");
    if (group && !$("devSkinInput")) {
      const label = document.createElement("label");
      label.className = "setting-toggle"; label.htmlFor = "devSkinInput";
      label.innerHTML = `<input id="devSkinInput" type="checkbox"> <span data-zh="Dev 模式" data-en="Dev Mode"></span>`;
      group.insertBefore(label, group.firstChild);
      const input = label.querySelector("input"), text = label.querySelector("span");
      input.checked = on;
      input.addEventListener("change", () => { on = input.checked; try { localStorage.setItem(KEY, on ? "1" : "0"); } catch (_) {} apply(); });
      const zh = () => (($("languageSelect") || {}).value || "zh") !== "en";
      const syncLang = () => { text.textContent = zh() ? text.dataset.zh : text.dataset.en; };
      $("languageSelect")?.addEventListener("change", () => setTimeout(syncLang, 0));
      syncLang();
    }
    apply();
  }
  // 在 phone-layout 之後執行
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(setup, 0)); else setTimeout(setup, 10);
})();
// ==== /dev-skin ====

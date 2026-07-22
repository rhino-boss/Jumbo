(() => {
  "use strict";

  const root = document.getElementById("helpContent");
  if (!root) return;

  const style = document.createElement("style");
  style.textContent = `
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

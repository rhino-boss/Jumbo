import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";
import path from "node:path";

const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9333;
const profile = path.resolve(".tmp", `chrome-slot-ui-audit-${process.pid}`);
const files = process.argv.slice(2).map((file) => path.resolve(file));
const chrome = spawn(chromePath, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`,
  "about:blank"
], { stdio: "ignore", windowsHide: true });

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForDebugger() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (response.ok) return response.json();
    } catch {}
    await delay(100);
  }
  throw new Error("Chrome DevTools endpoint did not start.");
}

let socket;
let nextId = 1;
const pending = new Map();
const exceptions = new Map();

function command(method, params = {}, sessionId) {
  const id = nextId++;
  socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

try {
  const version = await waitForDebugger();
  socket = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const task = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) task.reject(new Error(message.error.message));
      else task.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown" && message.sessionId) {
      const list = exceptions.get(message.sessionId) || [];
      list.push(message.params.exceptionDetails.text);
      exceptions.set(message.sessionId, list);
    }
  });

  const { targetId } = await command("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await command("Target.attachToTarget", { targetId, flatten: true });
  await command("Page.enable", {}, sessionId);
  await command("Runtime.enable", {}, sessionId);

  const results = [];
  for (const file of files) {
    exceptions.set(sessionId, []);
    await command("Page.navigate", { url: pathToFileURL(file).href }, sessionId);
    await delay(1400);
    const expression = `(async () => {
      const debugInput = document.querySelector("#debugModeInput, #debugInput");
      if (debugInput && !debugInput.checked) {
        debugInput.click();
        debugInput.dispatchEvent(new Event("change", { bubbles: true }));
      }
      const helpButton = document.getElementById("helpBtn");
      if (helpButton) helpButton.click();
      await new Promise(resolve => setTimeout(resolve, 80));
      const dialog = document.getElementById("helpDialog");
      const visible = element => Boolean(element) && getComputedStyle(element).display !== "none";
      const previous = document.querySelector("#previousStepBtn, #prevBtn");
      const next = document.querySelector("#nextStepBtn, #nextBtn");
      const diagnostics = [...document.querySelectorAll("#rng-wrap, #log-wrap, #live-log-wrap")];
      return {
        title: document.title,
        englishTitle: !/[\\u3400-\\u9fff]/.test(document.title),
        helpOpened: Boolean(dialog?.open),
        standardizedHelpCards: document.querySelectorAll("#helpContent .help-standard-card").length,
        helpFrameTextLength: document.querySelector("#helpFrame, #helpSourceFrame")?.contentDocument?.body?.innerText?.length || 0,
        debugToggle: Boolean(debugInput),
        debugVisible: diagnostics.length >= 3 && diagnostics.every(visible),
        historyControls: Boolean(previous && next),
        rngInput: Boolean(document.querySelector("#reelRngInput, #rngInput, #reelInput")),
        clearLog: Boolean(document.getElementById("clearLogBtn")),
        sharedDropStyle: [...document.querySelectorAll("style")].some(style => style.textContent.includes("slot-symbol-drop"))
      };
    })()`;
    const evaluated = await command("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true
    }, sessionId);
    results.push({
      game: path.basename(path.dirname(file)),
      ...evaluated.result.value,
      exceptions: exceptions.get(sessionId)
    });
  }

  console.log(JSON.stringify(results, null, 2));
  const failed = results.some((result) =>
    !result.englishTitle
    || !result.helpOpened
    || result.standardizedHelpCards < 1
    || !result.debugToggle
    || !result.debugVisible
    || !result.historyControls
    || !result.rngInput
    || !result.clearLog
    || !result.sharedDropStyle
    || result.exceptions.length
  );
  if (failed) process.exitCode = 1;
} finally {
  try {
    socket?.close();
  } catch {}
  chrome.kill();
}

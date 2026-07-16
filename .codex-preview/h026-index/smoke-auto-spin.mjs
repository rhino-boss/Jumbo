const port = Number(process.argv[2]);
let pages = [];
for (let attempt = 0; attempt < 100 && !pages.length; attempt += 1) {
  try { pages = await fetch(`http://127.0.0.1:${port}/json`).then((response) => response.json()); } catch {}
  if (!pages.length) await new Promise((resolve) => setTimeout(resolve, 100));
}
if (!pages.length) throw new Error("Chrome DevTools endpoint unavailable");
const socket = new WebSocket((pages.find((item) => item.type === "page") || pages[0]).webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let id = 0;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (!message.id || !pending.has(message.id)) return;
  const callbacks = pending.get(message.id);
  pending.delete(message.id);
  message.error ? callbacks.reject(new Error(message.error.message)) : callbacks.resolve(message.result);
});
function send(method, params = {}) {
  const requestId = ++id;
  socket.send(JSON.stringify({ id: requestId, method, params }));
  return new Promise((resolve, reject) => pending.set(requestId, { resolve, reject }));
}
async function evaluate(expression) {
  const response = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  return response.result.value;
}
for (let attempt = 0; attempt < 100 && !(await evaluate("document.readyState === 'complete' && typeof state === 'object'")); attempt += 1) {
  await new Promise((resolve) => setTimeout(resolve, 50));
}
if (await evaluate("document.querySelector('#spinBtn').disabled")) throw new Error("Spin should start enabled");
await evaluate("document.querySelector('#autoBtn').click()");
if (!(await evaluate("state.autoEnabled && document.querySelector('#spinBtn').disabled"))) throw new Error("Spin was not disabled when Auto turned on");
await evaluate("document.querySelector('#autoBtn').click()");
if (!(await evaluate("!state.autoEnabled && !document.querySelector('#spinBtn').disabled"))) throw new Error("Spin was not restored when Auto turned off before playback");
console.log("Auto ON disables Spin; Auto OFF restores Spin.");
socket.close();

const messagesEl = document.querySelector("#messages");
const welcomeEl = document.querySelector("#welcome");
const form = document.querySelector("#chat-form");
const promptEl = document.querySelector("#prompt");
const sendEl = document.querySelector("#send");
const languageEl = document.querySelector("#language");
const modelEl = document.querySelector("#model");
const statusDot = document.querySelector("#status-dot");
const statusText = document.querySelector("#status-text");

let sessionId = localStorage.getItem("local-llm-session") || null;
let busy = false;

function messageElement(role, content = "") {
  if (welcomeEl) welcomeEl.hidden = true;
  const item = document.createElement("article");
  item.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "YOU" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const label = document.createElement("p");
  label.className = "role";
  label.textContent = role === "user" ? "You" : "Assistant";
  const text = document.createElement("p");
  text.className = "content";
  text.textContent = content;
  bubble.append(label, text);
  item.append(avatar, bubble);
  messagesEl.append(item);
  item.scrollIntoView({ behavior: "smooth", block: "end" });
  return { item, text };
}

function setBusy(value) {
  busy = value;
  sendEl.disabled = value;
  promptEl.disabled = value;
}

function resizePrompt() {
  promptEl.style.height = "auto";
  promptEl.style.height = `${Math.min(promptEl.scrollHeight, 160)}px`;
}

async function sendMessage(message) {
  if (!message.trim() || busy) return;
  setBusy(true);
  messageElement("user", message.trim());
  const assistant = messageElement("assistant");
  assistant.text.classList.add("cursor");

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message.trim(),
        session_id: sessionId,
        language: languageEl.value,
        model: modelEl.value || null,
      }),
    });
    if (!response.ok || !response.body) {
      const problem = await response.json().catch(() => ({}));
      throw new Error(problem.detail || `Request failed (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        if (event.type === "meta") {
          sessionId = event.session_id;
          localStorage.setItem("local-llm-session", sessionId);
        } else if (event.type === "token") {
          assistant.text.textContent += event.content;
          assistant.item.scrollIntoView({ behavior: "smooth", block: "end" });
        } else if (event.type === "error") {
          throw new Error(event.detail);
        }
      }
      if (done) break;
    }
  } catch (error) {
    assistant.item.classList.add("error");
    assistant.text.textContent = `Ollama error: ${error.message}`;
  } finally {
    assistant.text.classList.remove("cursor");
    setBusy(false);
    promptEl.focus();
  }
}

async function loadSession() {
  if (!sessionId) return;
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`);
    if (!response.ok) return;
    const data = await response.json();
    for (const message of data.messages) messageElement(message.role, message.content);
  } catch (_) {
    // A new chat remains usable when old process-local memory is gone.
  }
}

async function loadModels() {
  try {
    const response = await fetch("/api/models");
    if (!response.ok) throw new Error("Ollama unavailable");
    const data = await response.json();
    modelEl.innerHTML = "";
    for (const name of data.models) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name === data.default ? `${name} (default)` : name;
      option.selected = name === data.default;
      modelEl.append(option);
    }
    if (!data.models.length) {
      const option = document.createElement("option");
      option.value = data.default;
      option.textContent = `${data.default} (pull required)`;
      modelEl.append(option);
    }
    statusDot.className = "status-dot online";
    statusText.textContent = "Ollama connected";
  } catch (_) {
    statusDot.className = "status-dot offline";
    statusText.textContent = "Ollama offline";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = promptEl.value;
  promptEl.value = "";
  resizePrompt();
  sendMessage(message);
});

promptEl.addEventListener("input", resizePrompt);
promptEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.textContent));
});

document.querySelector("#clear-chat").addEventListener("click", async () => {
  if (busy) return;
  if (sessionId) await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
  sessionId = null;
  localStorage.removeItem("local-llm-session");
  messagesEl.querySelectorAll(".message").forEach((item) => item.remove());
  if (welcomeEl) welcomeEl.hidden = false;
  promptEl.focus();
});

function exportConversation(format) {
  if (!sessionId) return;
  window.location.assign(`/api/sessions/${encodeURIComponent(sessionId)}/export?format=${format}`);
}

document.querySelector("#export-json").addEventListener("click", () => exportConversation("json"));
document.querySelector("#export-md").addEventListener("click", () => exportConversation("markdown"));

loadSession();
loadModels();
promptEl.focus();


import axios from "axios";

const client = axios.create({ baseURL: "/api" });

export const sendMessage = (message, sessionId = "default", topK = null) =>
  client.post("/chat", { message, session_id: sessionId, top_k: topK }).then((r) => r.data);

/**
 * Consumes the backend's Server-Sent Events stream (POST /api/chat/stream).
 * Native EventSource can't send a POST body, so we read the raw
 * `text/event-stream` response with fetch and parse it to spec ourselves:
 * messages are separated by a blank line, each made of `event:`/`data:`/`id:`
 * fields. Yields { event, data, id } for each parsed message.
 */
export async function* streamMessage(message, sessionId = "default") {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, session_id: sessionId, stream: true }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE messages are separated by a blank line ("\n\n")
    const rawMessages = buffer.split("\n\n");
    buffer = rawMessages.pop(); // last chunk may be incomplete, keep it buffered

    for (const raw of rawMessages) {
      if (!raw.trim()) continue;

      let eventName = "message";
      let id = null;
      const dataLines = [];

      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("id:")) id = line.slice(3).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        // lines starting with ":" are SSE comments/heartbeats - ignored
      }

      if (dataLines.length === 0) continue;
      const payload = JSON.parse(dataLines.join("\n"));
      yield { event: eventName, id, data: payload.data ?? payload };
    }
  }
}

export const uploadDocuments = (files) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return client.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const listDocuments = () => client.get("/documents").then((r) => r.data);

export const deleteDocument = (source) => client.delete(`/documents/${encodeURIComponent(source)}`).then((r) => r.data);

export const runEvaluation = () => client.post("/evaluate", {}).then((r) => r.data);

export default client;

import { createSlice, nanoid } from "@reduxjs/toolkit";
import { streamMessage } from "../api/client.js";

const initialState = {
  sessionId: "default",
  messages: [], // { id, role, content, sources, latencyMs, cached, streaming, error }
  status: "idle", // idle | streaming | error
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    userMessageAdded: {
      reducer(state, action) {
        state.messages.push(action.payload);
      },
      prepare(content) {
        return { payload: { id: nanoid(), role: "user", content } };
      },
    },
    assistantPlaceholderAdded: {
      reducer(state, action) {
        state.messages.push(action.payload);
      },
      prepare(id) {
        return { payload: { id, role: "assistant", content: "", sources: [], streaming: true } };
      },
    },
    assistantSourcesReceived(state, action) {
      const { id, sources } = action.payload;
      const msg = state.messages.find((m) => m.id === id);
      if (msg) msg.sources = sources;
    },
    assistantTokenReceived(state, action) {
      const { id, token } = action.payload;
      const msg = state.messages.find((m) => m.id === id);
      if (msg) msg.content += token;
    },
    assistantStreamFinished(state, action) {
      const { id, latencyMs } = action.payload;
      const msg = state.messages.find((m) => m.id === id);
      if (msg) {
        msg.streaming = false;
        msg.latencyMs = latencyMs;
      }
      state.status = "idle";
    },
    assistantStreamFailed(state, action) {
      const { id, message } = action.payload;
      const msg = state.messages.find((m) => m.id === id);
      if (msg) {
        msg.streaming = false;
        msg.error = message;
        if (!msg.content) msg.content = message;
      }
      state.status = "error";
    },
    streamingStarted(state) {
      state.status = "streaming";
    },
  },
});

export const {
  userMessageAdded,
  assistantPlaceholderAdded,
  assistantSourcesReceived,
  assistantTokenReceived,
  assistantStreamFinished,
  assistantStreamFailed,
  streamingStarted,
} = chatSlice.actions;

/**
 * Thunk that drives the SSE stream and dispatches incremental Redux updates
 * as "sources", "token", "done", and "error" events arrive from the backend.
 */
export const sendMessageStream = (question) => async (dispatch, getState) => {
  const { sessionId } = getState().chat;
  const assistantId = nanoid();

  dispatch(userMessageAdded(question));
  dispatch(assistantPlaceholderAdded(assistantId));
  dispatch(streamingStarted());

  try {
    for await (const evt of streamMessage(question, sessionId)) {
      if (evt.event === "sources") {
        dispatch(assistantSourcesReceived({ id: assistantId, sources: evt.data }));
      } else if (evt.event === "token") {
        dispatch(assistantTokenReceived({ id: assistantId, token: evt.data }));
      } else if (evt.event === "done") {
        dispatch(assistantStreamFinished({ id: assistantId, latencyMs: evt.data?.latency_ms ?? null }));
      } else if (evt.event === "error") {
        dispatch(assistantStreamFailed({ id: assistantId, message: evt.data?.message || "Stream error" }));
      }
    }
  } catch (err) {
    dispatch(assistantStreamFailed({
      id: assistantId,
      message: "Could not reach the backend. Is the FastAPI server running on :8000?",
    }));
  }
};

export default chatSlice.reducer;

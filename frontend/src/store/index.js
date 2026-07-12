import { configureStore } from "@reduxjs/toolkit";
import chatReducer from "./chatSlice.js";
import documentsReducer from "./documentsSlice.js";
import evaluationReducer from "./evaluationSlice.js";

export const store = configureStore({
  reducer: {
    chat: chatReducer,
    documents: documentsReducer,
    evaluation: evaluationReducer,
  },
});

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { runEvaluation } from "../api/client.js";

export const runRagasEvaluation = createAsyncThunk(
  "evaluation/run",
  async (_, { rejectWithValue }) => {
    try {
      return await runEvaluation();
    } catch (err) {
      return rejectWithValue(
        "Evaluation failed. Make sure documents are ingested and GROQ_API_KEY is set."
      );
    }
  }
);

const evaluationSlice = createSlice({
  name: "evaluation",
  initialState: {
    result: null,
    status: "idle", // idle | running | error
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(runRagasEvaluation.pending, (state) => {
        state.status = "running";
        state.error = null;
      })
      .addCase(runRagasEvaluation.fulfilled, (state, action) => {
        state.status = "idle";
        state.result = action.payload;
      })
      .addCase(runRagasEvaluation.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload || "Evaluation failed.";
      });
  },
});

export default evaluationSlice.reducer;

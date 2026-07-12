import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { listDocuments, uploadDocuments, deleteDocument } from "../api/client.js";

export const fetchDocuments = createAsyncThunk("documents/fetch", async () => {
  return await listDocuments();
});

export const uploadFiles = createAsyncThunk("documents/upload", async (files, { dispatch, rejectWithValue }) => {
  try {
    const result = await uploadDocuments(files);
    dispatch(fetchDocuments());
    return result;
  } catch (err) {
    return rejectWithValue("Upload failed. Check that the backend is running.");
  }
});

export const removeDocument = createAsyncThunk("documents/remove", async (source, { dispatch }) => {
  await deleteDocument(source);
  dispatch(fetchDocuments());
  return source;
});

const documentsSlice = createSlice({
  name: "documents",
  initialState: {
    items: [],
    status: "idle", // idle | loading | uploading | error
    lastUploadMessage: null,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.status = "idle";
        state.items = action.payload;
      })
      .addCase(fetchDocuments.rejected, (state) => {
        state.status = "error";
      })
      .addCase(uploadFiles.pending, (state) => {
        state.status = "uploading";
        state.error = null;
        state.lastUploadMessage = null;
      })
      .addCase(uploadFiles.fulfilled, (state, action) => {
        state.status = "idle";
        state.lastUploadMessage = `Ingested ${action.payload.total_chunks_added} chunks.`;
      })
      .addCase(uploadFiles.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload || "Upload failed.";
      });
  },
});

export default documentsSlice.reducer;

# Enterprise RAG Chatbot

A production-shaped Retrieval-Augmented Generation chatbot: **FastAPI** backend,
**React (Vite)** frontend, **ChromaDB** vector store, **Groq** for free/fast LLM
inference, and **RAGAS** for automated quality evaluation.

## Architecture

```
┌─────────────┐      REST/SSE       ┌──────────────────────┐
│   React UI  │ ──────────────────► │      FastAPI          │
│  (Vite)     │ ◄────────────────── │                        │
└─────────────┘                     │  ┌──────────────────┐  │
                                     │  │  RAG Pipeline     │  │
                                     │  │  - embed query    │  │
                                     │  │  - retrieve       │  │
                                     │  │  - build context  │  │
                                     │  │  - generate       │  │
                                     │  └──────────────────┘  │
                                     │        │      │        │
                              ┌──────┴───┐ ┌──┴───┐ ┌┴─────┐  │
                              │ ChromaDB │ │ Groq │ │Cache │  │
                              │ (vectors)│ │ (LLM)│ │(TTL) │  │
                              └──────────┘ └──────┘ └──────┘  │
                                     │                        │
                                     │  ┌──────────────────┐  │
                                     └─►│  RAGAS Evaluator  │  │
                                        │  (faithfulness,   │  │
                                        │  relevancy, etc.) │  │
                                        └──────────────────┘  │
                                     └──────────────────────┘
```

## Folder structure

```
enterprise-rag-chatbot/
├── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── app/
│   │   ├── main.py                 # FastAPI app + router wiring
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env-driven)
│   │   │   └── logging_config.py   # Structured loguru logging
│   │   ├── models/
│   │   │   └── schemas.py          # Request/response contracts
│   │   ├── services/
│   │   │   ├── embeddings.py       # Local sentence-transformers embedder
│   │   │   ├── chunking.py         # Recursive text splitter
│   │   │   ├── vectorstore.py      # ChromaDB wrapper
│   │   │   ├── llm.py              # Groq client (sync + streaming)
│   │   │   ├── cache.py            # TTL/LRU query cache
│   │   │   ├── ingestion.py        # PDF/DOCX/TXT -> chunks -> Chroma
│   │   │   ├── rag_pipeline.py     # Retrieval + generation orchestration
│   │   │   └── evaluation.py       # RAGAS evaluation harness
│   │   └── api/routes/
│   │       ├── health.py
│   │       ├── chat.py             # POST /api/chat, /api/chat/stream
│   │       ├── documents.py        # upload/list/delete documents
│   │       └── evaluation.py       # POST /api/evaluate
│   └── eval/
│       ├── test_dataset.json       # sample eval questions
│       └── run_evaluation.py       # CLI RAGAS runner
└── frontend/
    ├── package.json / vite.config.js / Dockerfile
    └── src/
        ├── App.jsx, main.jsx, styles.css
        ├── api/client.js           # axios + spec-compliant SSE parser
        ├── store/
        │   ├── index.js            # Redux store config
        │   ├── chatSlice.js        # messages/session state + SSE-driving thunk
        │   ├── documentsSlice.js   # ingestion state + async thunks
        │   └── evaluationSlice.js  # RAGAS run state + async thunk
        ├── utils/
        │   └── speech.js           # native Web Speech API TTS wrapper
        └── components/
            ├── Sidebar.jsx
            ├── ChatWindow.jsx      # streaming chat UI + mic input + auto-read toggle
            ├── MessageBubble.jsx / SourceCard.jsx  # manual speak / pause-resume / stop controls
            ├── DocumentUpload.jsx  # drag-drop ingestion + doc list
            └── EvaluationDashboard.jsx
```

## Voice input & voice output

- **Speech-to-text (query input)**: the mic button next to the composer uses
  the [`react-speech-recognition`](https://www.npmjs.com/package/react-speech-recognition)
  library, which wraps the browser's native `SpeechRecognition` API. Tap the
  mic, speak your question, tap again (or it keeps listening continuously)
  — the live transcript fills the input box, ready to edit or send.
- **Text-to-speech (responses)**: each assistant reply gets a 🔊 **Speak**
  button, entirely manual — nothing is read aloud automatically. Once
  playing, it's replaced by a **⏸ Pause / ▶ Resume** toggle plus a **⏹ Stop**
  button, backed by the browser's native `speechSynthesis` API
  (`src/utils/speech.js`, using `pause()`/`resume()`/`cancel()`).
- **Browser support**: both are built on the Web Speech API family, which is
  best supported in Chrome/Edge; Firefox and Safari have partial or no
  `SpeechRecognition` support (the mic button and hint text are
  auto-hidden/shown based on `browserSupportsSpeechRecognition`). Microphone
  access requires HTTPS in production (localhost is exempt during dev).

## Why these choices (and the optimizations built in)

- **Groq** for the LLM: free API tier, very low-latency inference over open
  models (default `llama-3.3-70b-versatile`). Swap `GROQ_MODEL` freely.
- **Local embeddings** (`sentence-transformers/all-MiniLM-L6-v2`): no API
  cost or rate limit for embedding, runs on CPU, loaded once as a singleton.
- **ChromaDB**: embedded/persistent vector store, no external service to run.
- **Recursive chunking with overlap**: preserves context across chunk
  boundaries — a major RAG quality lever.
- **Similarity threshold filtering**: low-relevance chunks are dropped before
  they reach the LLM, reducing hallucination and token spend.
- **TTL/LRU query cache**: repeated or duplicate questions skip both
  retrieval and generation entirely.
- **Streaming responses (SSE)**: tokens render as they arrive from Groq for
  a responsive UI, sources are sent first so citations show immediately.
- **RAGAS evaluation**: faithfulness, answer relevancy, context precision,
  and context recall — computed with Groq as the judge LLM, so evaluation
  stays free of paid API dependencies too.

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GROQ_API_KEY (get a free key at https://console.groq.com/keys)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. Vite proxies `/api` and `/health` to the
backend on port 8000 (see `vite.config.js`).

### 3. Docker (both services + persistent volume)

```bash
cp backend/.env.example backend/.env   # set GROQ_API_KEY first
docker compose up --build
```

Frontend: `http://localhost:4173` · Backend: `http://localhost:8000`

## Using it

1. Open the **Documents** tab, drag in a PDF/DOCX/TXT/MD file. It's chunked,
   embedded locally, and stored in ChromaDB.
2. Open **Chat** and ask a question. The assistant retrieves relevant
   chunks, streams a grounded answer, and shows a "retrieval trace" of the
   sources it used with similarity scores.
3. Open **Evaluation**, click **Run Evaluation** to score the pipeline
   against `backend/eval/test_dataset.json` with RAGAS. Edit that file (or
   POST your own `items` to `/api/evaluate`) with real questions and
   `ground_truth` answers drawn from your ingested documents for meaningful
   scores.

## API reference

| Method | Path                    | Purpose                              |
|--------|-------------------------|---------------------------------------|
| GET    | `/health`               | Service + index health check          |
| POST   | `/api/chat`              | Ask a question (non-streaming)        |
| POST   | `/api/chat/stream`       | Ask a question (SSE token stream)     |
| POST   | `/api/documents/upload`  | Upload & ingest one or more files     |
| GET    | `/api/documents`         | List ingested sources + chunk counts  |
| DELETE | `/api/documents/{name}`  | Remove a source and its chunks        |
| POST   | `/api/evaluate`          | Run RAGAS evaluation                  |

## Extending toward production

- Swap the TTL cache for Redis if running multiple backend replicas.
- Add hybrid search (BM25 + vector) in `vectorstore.py` for keyword-sensitive queries.
- Add a reranker (e.g. a cross-encoder) between retrieval and prompt-building for higher precision.
- Add auth (API key / OAuth) and per-tenant Chroma collections for multi-tenant isolation.
- Wire `logs/app.log` and RAGAS scores into an observability stack (e.g. Prometheus/Grafana) for regression tracking over time.

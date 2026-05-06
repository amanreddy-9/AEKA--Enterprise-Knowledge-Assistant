# AEKA — Enterprise Knowledge Assistant
### React + FastAPI + ChromaDB + Ollama

---

## Project Structure

```
AEKA/
├── backend/
│   ├── main.py                  ← FastAPI app (REST API)
│   ├── document_processor.py    ← PDF + DOCX extraction
│   ├── vector_store.py          ← ChromaDB wrapper
│   ├── llm_handler.py           ← Ollama LLM integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx     ← Main chat interface
│   │   │   └── KnowledgePage.jsx← Document repository
│   │   ├── components/
│   │   │   ├── FileUpload.jsx   ← Drag & drop uploader
│   │   │   └── ModelSelector.jsx← 4-model dropdown
│   │   ├── hooks/
│   │   │   └── useSpeech.js     ← TTS (American English female)
│   │   └── utils/
│   │       └── api.js           ← Axios REST client
│   ├── package.json
│   └── vite.config.js
├── start.bat                    ← One-click startup (Windows)
└── README.md
```

---

## Prerequisites

Install these once:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org/downloads |
| Node.js | 18+ | https://nodejs.org |
| Ollama | Latest | https://ollama.com/download |

> ⚠️ When installing Python: check **"Add Python to PATH"**
> ⚠️ When installing Node.js: leave all defaults checked

---

## Setup (Do Once)

### Step 1 — Backend Setup

Open VS Code terminal (`Ctrl + `` `) and run:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected output: lots of install messages, ending without errors.

### Step 2 — Frontend Setup

Open a second terminal and run:

```bash
cd frontend
npm install
```

Expected output: `added XXX packages`

### Step 3 — Pull an LLM Model

In any terminal:

```bash
ollama pull mistral
```

This downloads ~4 GB. Do it once. For a lighter option:
```bash
ollama pull phi3
```

---

## Running the App (Every Time)

You need **3 terminals** running simultaneously:

### Terminal 1 — Ollama
```bash
ollama serve
```
Leave it running. You'll see: `Listening on 127.0.0.1:11434`

### Terminal 2 — FastAPI Backend
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
Leave it running. You'll see: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 3 — React Frontend
```bash
cd frontend
npm run dev
```
Leave it running. You'll see: `Local: http://localhost:5173`

### Open the App
Go to: **http://localhost:5173**

> 💡 **Shortcut**: Double-click `start.bat` — it opens all 3 terminals automatically and launches the browser.

---

## Using AEKA

1. **Upload Documents** — Click "Upload" in the top bar → drag PDF/DOCX files → click "Process"
2. **Ask Questions** — Type in the chat box, press Enter
3. **Choose Mode** — "From Documents" uses your knowledge base; "General Knowledge" uses the LLM directly
4. **Select Model** — Choose from Mistral / Llama 3 / Phi-3 / Gemma in the sidebar dropdown
5. **Read Aloud** — Click the 🔊 "Read" button under any answer for TTS in American English (female voice)
6. **View Sources** — Click "X sources" button to see which document chunks were used
7. **Knowledge Repository** — Click the docs/chunks counter in the header to view all ingested documents

---

## API Endpoints

The backend exposes a full REST API at `http://localhost:8000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System + Ollama status |
| POST | `/documents/upload` | Upload PDF/DOCX files |
| GET | `/documents` | List all documents |
| GET | `/documents/stats` | Doc + chunk counts |
| DELETE | `/documents/{filename}` | Remove a document |
| DELETE | `/documents` | Clear all |
| POST | `/chat` | Send a query, get an answer |
| GET | `/models` | List available LLM models |

Interactive API docs: **http://localhost:8000/docs**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `venv\Scripts\activate` error | Run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Ollama offline badge | Start `ollama serve` in a terminal |
| Model not found | Run `ollama pull mistral` |
| Port 8000 in use | Change to `--port 8001` and update `vite.config.js` proxy target |
| Port 5173 in use | Vite auto-picks next available port |
| CORS error in browser | Make sure backend is on port 8000 |
| No text extracted from PDF | PDF may be scanned/image-based — only text PDFs are supported |
| Slow responses | Switch to `phi3` model in the dropdown |

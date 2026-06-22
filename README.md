# ⚡ AI App Compiler

> **Natural language → structured config → validated → executable working app**

A multi-stage AI compiler that converts plain English app descriptions into complete, validated, and immediately runnable applications — with UI, API, database, and auth schemas all generated and cross-validated automatically.

🔗 **Live Demo**: [ai-app-compiler-two.vercel.app](https://ai-app-compiler-two.vercel.app)  
🚀 **Backend API**: [Railway Production](https://ai-app-compiler-production-0995.up.railway.app)  
🎥 **Loom Video**: [Watch walkthrough](https://loom.com) *(Add your link here before submitting!)*

---

## 🏗️ Architecture

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────┐
│              4-Stage Pipeline                    │
│                                                  │
│  1. Intent Extraction                            │
│     Natural language → structured intent JSON    │
│     (app_name, type, features, roles, assumptions)│
│                                                  │
│  2. System Design                                │
│     Intent → architecture blueprint             │
│     (entities, flows, access patterns)           │
│                                                  │
│  3. Schema Generation                            │
│     Architecture → 4 schemas simultaneously:    │
│     UI config · API endpoints · DB tables · Auth │
│                                                  │
│  4. Refinement                                   │
│     Cross-layer consistency resolution           │
│     (UI↔API↔DB field mapping, auth alignment)    │
└─────────────────────────────────────────────────┘
    │
    ▼
Validation + Repair Engine
    │  ├── Detect: invalid JSON, missing keys, mismatches
    │  ├── Repair: targeted field-level auto-fix (not blind retry)
    │  └── Max 2 repair attempts before surfacing error
    │
    ▼
Runtime Generator
    │  └── Compiles schemas → self-contained React app
    │      with RBAC, CRUD, live dashboard
    ▼
Working App in Browser
```

---

## 🚀 Features

- **Multi-stage compiler pipeline** — 4 isolated stages, not a single monolithic prompt
- **Strict schema enforcement** — valid JSON, required fields, type safety, cross-layer consistency
- **Validation + auto-repair** — detects and fixes issues without full regeneration
- **Live RBAC runtime** — role-aware sidebar, per-role permissions, Access Denied pages
- **Live "Thinking" panel** — streams each pipeline stage in real time (SSE)
- **Download & Deploy** — export as self-contained HTML, push directly to GitHub
- **Evaluation framework** — 20 test prompts (10 real + 10 edge cases), tracks success rate, retries, latency

---

## 📁 Project Structure

```
ai-app-compiler/
├── backend/
│   ├── pipeline/
│   │   ├── intent.py       # Stage 1: Intent extraction
│   │   ├── design.py       # Stage 2: System design
│   │   ├── schema.py       # Stage 3: Schema generation
│   │   └── refine.py       # Stage 4: Cross-layer refinement
│   ├── validator/
│   │   ├── validate.py     # JSON + schema + cross-layer validation
│   │   └── repair.py       # Targeted auto-repair (not blind retry)
│   ├── evaluator/
│   │   └── evaluate.py     # 20-prompt evaluation framework
│   ├── runtime/
│   │   └── generator.py    # React app compiler with full RBAC
│   ├── gemini_client.py    # LLM client with JSON mode + repair
│   └── main.py             # FastAPI app + SSE streaming endpoint
└── frontend/
    └── src/
        ├── App.jsx                  # SSE streaming consumer
        ├── components/
        │   ├── ThinkingPanel.jsx    # Live pipeline visualizer
        │   ├── OutputViewer.jsx     # Schema viewer + Live App
        │   ├── GitHubPushModal.jsx  # One-click GitHub deploy
        │   └── PromptInput.jsx      # Input UI
        └── index.css
```

---

## ⚙️ Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Full pipeline (returns JSON) |
| `POST` | `/generate-stream` | Full pipeline with SSE live streaming |
| `POST` | `/evaluate` | Run 20-prompt evaluation suite |
| `GET` | `/health` | Health check |

---

## 📊 Design Decisions & Tradeoffs

### Why 4 stages instead of 1 prompt?
A single prompt generates inconsistent output — different runs produce different schemas with no guarantee of cross-layer alignment. By isolating each concern into a dedicated stage, each stage has a focused, smaller output contract that is far easier to validate and repair.

### Why auto-repair instead of full regeneration?
Full regeneration on every validation failure is expensive (latency + API cost) and often fixes non-broken parts too. Targeted repair patches only the specific field or key that failed, leaving everything else intact. This is the compiler analogy: a compiler fixes the specific syntax error, not the whole file.

### Why Gemini Flash Lite?
| Model | Latency | Cost | Quality |
|---|---|---|---|
| Gemini Pro | ~8s/stage | High | Best |
| Gemini Flash | ~3s/stage | Medium | Great |
| **Flash Lite** | **~1.5s/stage** | **Free tier** | Good enough |

For a demo/internship task, Flash Lite gives the best latency/cost balance while still producing valid structured schemas.

### Why self-contained HTML runtime?
No build step = zero friction for end users. The generated app uses React via CDN, which means the output file works by double-clicking. This also makes GitHub Pages deployment trivial (just upload one file).

---

## 🧪 Evaluation

Run the full 20-prompt evaluation suite:

```bash
curl -X POST http://localhost:8000/evaluate
```

Tracks per-prompt: **success**, **retries**, **latency_ms**, **failure_type**

---

## 📋 Submission

Built for the **AI Engineer Internship — Demo Task**  
Reference: [base44.com](https://base44.com)

# AI App Compiler 🤖

> Convert natural language app descriptions into complete, validated, executable configurations using a multi-stage AI pipeline.

**Live Demo:** [Coming soon]  
**Built for:** AI Engineer Internship Demo Task

---

## 🚀 What It Does

Converts plain English like:
> *"Build a CRM with login, contacts, dashboard, role-based access, and Stripe payments"*

Into complete structured output:
- 🖥️ **UI Schema** — pages, components, layouts
- 🔌 **API Schema** — endpoints, methods, auth
- 🗄️ **DB Schema** — tables, fields, relations
- 🔐 **Auth Schema** — roles, permissions, JWT config

---

## 🏗️ Architecture — Multi-Stage Pipeline

```
User Prompt
    ↓
[Stage 1] Intent Extraction      ← Parses structured intent from raw text
    ↓
[Stage 2] System Design          ← Designs pages, entities, flows, roles
    ↓
[Stage 3] Schema Generation      ← Generates all 4 schemas in parallel
    ↓
[Stage 4] Refinement             ← Cross-validates & fixes inconsistencies
    ↓
[Validation + Auto-Repair]       ← Detects errors → repairs without full retry
    ↓
Validated JSON Output
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| LLM | Groq (Llama 3.3 70B) |
| Validation | Pydantic + jsonschema |
| Deployment | Vercel (frontend) + Render (backend) |

---

## 📁 Project Structure

```
ai-app-compiler/
├── backend/
│   ├── main.py               ← FastAPI app + /generate + /evaluate endpoints
│   ├── gemini_client.py      ← Groq LLM client
│   ├── pipeline/
│   │   ├── intent.py         ← Stage 1: Intent extraction
│   │   ├── design.py         ← Stage 2: System design
│   │   ├── schema.py         ← Stage 3: Schema generation
│   │   └── refine.py         ← Stage 4: Refinement
│   ├── validator/
│   │   ├── validate.py       ← JSON + cross-layer validation
│   │   └── repair.py         ← Auto-repair engine
│   └── evaluator/
│       └── evaluate.py       ← 20-prompt evaluation framework
└── frontend/
    └── src/
        ├── App.jsx
        └── components/
            ├── PromptInput.jsx
            ├── PipelineVisualizer.jsx
            └── OutputViewer.jsx
```

---

## ⚙️ Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
# Create .env with GROQ_API_KEY=your_key
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## 🧪 Evaluation Framework

Tests 20 prompts automatically:
- 10 real product prompts (CRM, e-commerce, hospital, etc.)
- 10 edge cases (vague, conflicting, incomplete)

Tracks: success rate, retries, latency, failure types.

**Run it:**
```bash
curl -X POST http://localhost:8000/evaluate
```

---

## 🔑 Key Design Decisions

1. **Multi-stage over single prompt** — Each stage has a focused role, making failures easier to isolate and repair
2. **Targeted repair over blind retry** — When validation fails, we repair only the broken parts
3. **Cross-layer consistency checks** — UI components must reference valid API endpoints, which must reference valid DB tables
4. **Rule-based + AI repair** — Standard fields (id, timestamps) added by rules; complex issues delegated to AI repair

import time
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from pipeline.intent import extract_intent
from pipeline.design import design_system
from pipeline.schema import generate_schemas
from pipeline.refine import refine_schemas
from validator.validate import run_validation
from validator.repair import repair_schemas, add_missing_db_fields
from evaluator.evaluate import run_evaluation

app = FastAPI(
    title="AI App Compiler",
    description="Convert natural language into structured, validated app configurations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str


@app.get("/")
def root():
    return {"message": "AI App Compiler API is running 🚀", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Full pipeline: prompt → intent → design → schemas → validate → refine → output."""
    if not req.prompt or len(req.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt is too short or empty.")

    pipeline_log = []
    start_total = time.time()
    total_retries = 0

    try:
        # ── Stage 1: Intent Extraction ─────────────────────────────────────────
        t = time.time()
        pipeline_log.append({"stage": "intent_extraction", "status": "running"})
        intent = extract_intent(req.prompt)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        # ── Stage 2: System Design ─────────────────────────────────────────────
        t = time.time()
        pipeline_log.append({"stage": "system_design", "status": "running"})
        design = design_system(intent)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        # ── Stage 3: Schema Generation ─────────────────────────────────────────
        t = time.time()
        pipeline_log.append({"stage": "schema_generation", "status": "running"})
        schemas = generate_schemas(intent, design)
        schemas = add_missing_db_fields(schemas)  # rule-based repair
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        # ── Stage 4: Refinement ────────────────────────────────────────────────
        t = time.time()
        pipeline_log.append({"stage": "refinement", "status": "running"})
        refined = refine_schemas(schemas)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        # ── Validation + Repair Loop (max 2 retries) ───────────────────────────
        t = time.time()
        pipeline_log.append({"stage": "validation_repair", "status": "running"})
        current = refined
        validation_report = None
        for attempt in range(3):
            validation_report = run_validation(current)
            if validation_report["is_valid"]:
                break
            if attempt < 2:
                total_retries += 1
                current = repair_schemas(current, validation_report["errors"])
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        total_latency = round((time.time() - start_total) * 1000)

        return {
            "success": True,
            "prompt": req.prompt,
            "intent": intent,
            "design": design,
            "schemas": {
                "ui_schema": current.get("ui_schema"),
                "api_schema": current.get("api_schema"),
                "db_schema": current.get("db_schema"),
                "auth_schema": current.get("auth_schema"),
            },
            "refinement_log": current.get("_refinement_log"),
            "validation_report": validation_report,
            "metrics": {
                "total_latency_ms": total_latency,
                "retries": total_retries,
                "pipeline_stages": pipeline_log,
            },
        }

    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "traceback": tb, "pipeline_log": pipeline_log},
        )


@app.post("/evaluate")
async def evaluate():
    """Run the full evaluation framework across 20 test prompts."""
    try:
        results = run_evaluation()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import time
import json
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from pipeline.intent import extract_intent
from pipeline.design import design_system
from pipeline.schema import generate_schemas
from pipeline.refine import refine_schemas
from validator.validate import run_validation
from validator.repair import repair_schemas, add_missing_db_fields
from evaluator.evaluate import run_evaluation
from runtime.generator import generate_runtime

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


from fastapi.responses import HTMLResponse

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/test", response_class=HTMLResponse)
def test_page():
    with open("test.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Full pipeline: prompt → intent → design → schemas → validate → refine → output."""
    if not req.prompt or len(req.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt is too short or empty.")

    pipeline_log = []
    start_total = time.time()
    total_retries = 0

    try:
        t = time.time()
        pipeline_log.append({"stage": "intent_extraction", "status": "running"})
        intent = extract_intent(req.prompt)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        t = time.time()
        pipeline_log.append({"stage": "system_design", "status": "running"})
        design = design_system(intent)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        t = time.time()
        pipeline_log.append({"stage": "schema_generation", "status": "running"})
        schemas = generate_schemas(intent, design)
        schemas = add_missing_db_fields(schemas)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

        t = time.time()
        pipeline_log.append({"stage": "refinement", "status": "running"})
        refined = refine_schemas(schemas)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

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

        t = time.time()
        pipeline_log.append({"stage": "runtime_generation", "status": "running"})
        runtime_app = generate_runtime(current, intent)
        pipeline_log[-1].update({"status": "done", "latency_ms": round((time.time() - t) * 1000)})

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
            "runtime": runtime_app,
        }

    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "traceback": tb, "pipeline_log": pipeline_log},
        )


@app.post("/generate-stream")
async def generate_stream(req: GenerateRequest):
    """
    Streaming SSE endpoint: emits a live JSON event after each pipeline stage
    completes, then emits the full result at the end.
    """
    if not req.prompt or len(req.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt is too short or empty.")

    def event_stream():
        pipeline_log = []
        start_total = time.time()
        total_retries = 0

        def emit(event_type: str, data: dict):
            payload = json.dumps({"type": event_type, **data})
            return f"data: {payload}\n\n"

        try:
            # ── Stage 1: Intent Extraction ──────────────────────────────────────
            yield emit("stage_start", {
                "stage": "intent_extraction",
                "label": "Intent Extraction",
                "icon": "🧠",
                "thought": f'Analyzing your prompt: "{req.prompt[:80]}{"..." if len(req.prompt) > 80 else ""}"',
                "detail": "Parsing natural language → structured app intent (name, type, features, roles, assumptions)...",
            })
            t = time.time()
            intent = extract_intent(req.prompt)
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "intent_extraction", "status": "done", "latency_ms": latency})
            yield emit("stage_done", {
                "stage": "intent_extraction",
                "latency_ms": latency,
                "summary": f'App: "{intent.get("app_name")}" · Type: {intent.get("app_type")} · Complexity: {intent.get("complexity")} · {len(intent.get("user_roles", []))} roles · {len(intent.get("core_features", []))} features',
                "assumptions": intent.get("assumptions", []),
            })

            # ── Stage 2: System Design ──────────────────────────────────────────
            yield emit("stage_start", {
                "stage": "system_design",
                "label": "System Design",
                "icon": "🏗️",
                "thought": f'Designing architecture for "{intent.get("app_name")}"...',
                "detail": "Converting intent → app architecture. Defining entities, data flows, access patterns, and module boundaries...",
            })
            t = time.time()
            design = design_system(intent)
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "system_design", "status": "done", "latency_ms": latency})
            entities = design.get("entities", design.get("core_entities", []))
            flows = design.get("flows", design.get("user_flows", []))
            yield emit("stage_done", {
                "stage": "system_design",
                "latency_ms": latency,
                "summary": f'{len(entities)} entities defined · {len(flows)} user flows · architecture ready',
            })

            # ── Stage 3: Schema Generation ──────────────────────────────────────
            yield emit("stage_start", {
                "stage": "schema_generation",
                "label": "Schema Generation",
                "icon": "📐",
                "thought": "Generating all 4 schemas in parallel...",
                "detail": "Creating: UI pages + components, REST API endpoints, database tables + fields, auth roles + permissions...",
            })
            t = time.time()
            schemas = generate_schemas(intent, design)
            schemas = add_missing_db_fields(schemas)
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "schema_generation", "status": "done", "latency_ms": latency})
            tables = schemas.get("db_schema", {}).get("tables", [])
            endpoints = schemas.get("api_schema", {}).get("endpoints", [])
            pages = schemas.get("ui_schema", {}).get("pages", [])
            roles = schemas.get("auth_schema", {}).get("roles", [])
            yield emit("stage_done", {
                "stage": "schema_generation",
                "latency_ms": latency,
                "summary": f'{len(pages)} UI pages · {len(endpoints)} API endpoints · {len(tables)} DB tables · {len(roles)} auth roles',
            })

            # ── Stage 4: Refinement ─────────────────────────────────────────────
            yield emit("stage_start", {
                "stage": "refinement",
                "label": "Refinement",
                "icon": "🔧",
                "thought": "Checking cross-layer consistency...",
                "detail": "Resolving inconsistencies: ensuring UI→API→DB field mappings align, auth permissions match roles, no orphaned references...",
            })
            t = time.time()
            refined = refine_schemas(schemas)
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "refinement", "status": "done", "latency_ms": latency})
            refine_log = refined.get("_refinement_log", {})
            fixes = refine_log.get("fixes_applied", 0) if isinstance(refine_log, dict) else 0
            yield emit("stage_done", {
                "stage": "refinement",
                "latency_ms": latency,
                "summary": f'{fixes} inconsistencies resolved · schemas are cross-layer consistent',
            })

            # ── Stage 5: Validation + Repair ────────────────────────────────────
            yield emit("stage_start", {
                "stage": "validation_repair",
                "label": "Validation & Repair",
                "icon": "🛡️",
                "thought": "Running strict validation suite...",
                "detail": "Checking: JSON structure, required fields, type safety, cross-layer consistency. Auto-repairing any issues without full regeneration...",
            })
            t = time.time()
            current = refined
            validation_report = None
            for attempt in range(3):
                validation_report = run_validation(current)
                if validation_report["is_valid"]:
                    break
                if attempt < 2:
                    total_retries += 1
                    current = repair_schemas(current, validation_report["errors"])
                    yield emit("repair", {
                        "attempt": attempt + 1,
                        "errors_found": validation_report["error_count"],
                        "thought": f'Found {validation_report["error_count"]} issue(s). Applying targeted repair (attempt {attempt+1}/2)...',
                    })
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "validation_repair", "status": "done", "latency_ms": latency})
            yield emit("stage_done", {
                "stage": "validation_repair",
                "latency_ms": latency,
                "summary": f'{"✓ All checks passed" if validation_report["is_valid"] else "⚠ Repaired"} · {total_retries} auto-repair(s) applied',
                "is_valid": validation_report["is_valid"],
            })

            total_latency = round((time.time() - start_total) * 1000)

            # ── Stage 6: Runtime Generation ─────────────────────────────────────
            yield emit("stage_start", {
                "stage": "runtime_generation",
                "label": "Runtime Generation",
                "icon": "🚀",
                "thought": "Compiling schemas → executable React application...",
                "detail": "Generating self-contained React app with RBAC: role-aware sidebar, CRUD pages, permission guards, and live dashboard...",
            })
            t = time.time()
            runtime_app = generate_runtime(current, intent)
            latency = round((time.time() - t) * 1000)
            pipeline_log.append({"stage": "runtime_generation", "status": "done", "latency_ms": latency})
            yield emit("stage_done", {
                "stage": "runtime_generation",
                "latency_ms": latency,
                "summary": f'React app compiled · {len(runtime_app.get("features", []))} features · ready to run',
            })

            # ── Final Result ────────────────────────────────────────────────────
            result = {
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
                "runtime": runtime_app,
            }
            yield emit("done", {"result": result})

        except Exception as e:
            tb = traceback.format_exc()
            yield emit("error", {"error": str(e), "traceback": tb})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
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

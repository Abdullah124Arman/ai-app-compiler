import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.intent import extract_intent
from pipeline.design import design_system
from pipeline.schema import generate_schemas
from pipeline.refine import refine_schemas
from validator.validate import run_validation
from validator.repair import repair_schemas, add_missing_db_fields

TEST_PROMPTS_REAL = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    "Create an e-commerce store with product listings, shopping cart, checkout with Stripe, and order tracking.",
    "Build a project management tool like Trello with boards, cards, drag-and-drop, and team collaboration.",
    "Create a hospital management system with patient records, appointments, doctor schedules, and billing.",
    "Build a learning management system with courses, quizzes, progress tracking, and certificates.",
    "Create a food delivery app with restaurant listings, menus, real-time order tracking, and driver management.",
    "Build a social media platform with posts, likes, comments, follow system, and messaging.",
    "Create an HR management system with employee records, leave management, payroll, and performance reviews.",
    "Build an inventory management system with stock tracking, suppliers, purchase orders, and alerts.",
    "Create a real estate platform with property listings, search filters, virtual tours, and agent management.",
]

TEST_PROMPTS_EDGE = [
    "Build something for my business.",  # vague
    "Create an app with login but also without login, and users should be admins but not admins.",  # conflicting
    "Build an app.",  # incomplete
    "Make a website.",  # too vague
    "Build a platform with everything — payments, chat, video, AI, blockchain, AR/VR.",  # overspecified
    "Create an app like Uber but also like Airbnb and also like Amazon.",  # conflicting models
    "Build a system that manages things.",  # underspecified
    "Create a database.",  # incomplete
    "Build an app with 100 user types and 500 features.",  # unrealistic
    "Make something that does everything automatically with no user input.",  # contradictory
]


def run_single_prompt(prompt: str, prompt_id: str) -> dict:
    start = time.time()
    retries = 0
    failure_type = None
    success = False
    result = {}

    try:
        # Stage 1
        intent = extract_intent(prompt)
        # Stage 2
        design = design_system(intent)
        # Stage 3
        schemas = generate_schemas(intent, design)
        # Rule-based repair
        schemas = add_missing_db_fields(schemas)
        # Stage 4
        refined = refine_schemas(schemas)

        # Validation loop (max 2 retries)
        current = refined
        for attempt in range(3):
            report = run_validation(current)
            if report["is_valid"]:
                success = True
                break
            if attempt < 2:
                retries += 1
                current = repair_schemas(current, report["errors"])
            else:
                failure_type = "validation_failed_after_retries"

        result = current
        result["_validation_report"] = report

    except Exception as e:
        failure_type = f"exception: {str(e)}"
        success = False

    latency = round((time.time() - start) * 1000)
    return {
        "prompt_id": prompt_id,
        "prompt": prompt[:80] + "..." if len(prompt) > 80 else prompt,
        "success": success,
        "retries": retries,
        "latency_ms": latency,
        "failure_type": failure_type,
    }


def run_evaluation():
    """Run all 20 test prompts and return metrics."""
    results = []
    all_prompts = (
        [(p, f"real_{i+1}") for i, p in enumerate(TEST_PROMPTS_REAL)] +
        [(p, f"edge_{i+1}") for i, p in enumerate(TEST_PROMPTS_EDGE)]
    )
    for prompt, pid in all_prompts:
        r = run_single_prompt(prompt, pid)
        results.append(r)

    total = len(results)
    successes = sum(1 for r in results if r["success"])
    avg_latency = sum(r["latency_ms"] for r in results) // total
    avg_retries = round(sum(r["retries"] for r in results) / total, 2)
    failure_types = {}
    for r in results:
        if r["failure_type"]:
            ft = r["failure_type"]
            failure_types[ft] = failure_types.get(ft, 0) + 1

    return {
        "summary": {
            "total_prompts": total,
            "success_count": successes,
            "success_rate": f"{round(successes/total*100)}%",
            "average_latency_ms": avg_latency,
            "average_retries": avg_retries,
            "failure_types": failure_types,
        },
        "results": results,
    }

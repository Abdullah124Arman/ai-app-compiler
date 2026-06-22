from gemini_client import call_gemini
import json

REFINE_PROMPT = """
You are a strict technical reviewer. Review the following schemas for cross-layer consistency and fix any issues.

Schemas to review:
{schemas}

Check for these issues:
1. UI components referencing non-existent API endpoint IDs
2. API endpoints referencing non-existent DB tables
3. DB tables missing required fields (id, created_at, updated_at)
4. Auth roles that don't match across schemas
5. Missing permissions for existing endpoints
6. API response fields that don't match DB table fields

Return the COMPLETE fixed schema JSON (same structure as input) with all issues resolved.
Also add a "_refinement_log" field listing what was fixed:
{{
  ... (all original schema keys fixed) ...,
  "_refinement_log": {{
    "issues_found": ["list of issues found"],
    "fixes_applied": ["list of fixes applied"],
    "consistency_score": 0-100
  }}
}}

Always return valid JSON.
"""

def refine_schemas(schemas: dict) -> dict:
    """Stage 4: Cross-validate and repair inconsistencies across all schemas."""
    prompt = REFINE_PROMPT.format(schemas=json.dumps(schemas, indent=2))
    result = call_gemini(prompt)
    result["_stage"] = "refinement"
    return result

from gemini_client import call_gemini
import json

DESIGN_PROMPT = """
You are a senior software architect. Based on the following app intent, design the complete system architecture.

App Intent:
{intent}

Return a JSON object with EXACTLY this structure:
{{
  "pages": [
    {{
      "name": "string",
      "route": "string - e.g. /dashboard",
      "access": ["roles that can access this page"],
      "description": "string"
    }}
  ],
  "entities": [
    {{
      "name": "string - entity/model name",
      "description": "string",
      "owned_by": "string - role that owns this entity or 'all'"
    }}
  ],
  "user_flows": [
    {{
      "name": "string",
      "steps": ["step 1", "step 2", "..."],
      "actors": ["roles involved"]
    }}
  ],
  "role_permissions": {{
    "role_name": {{
      "can_read": ["entity names"],
      "can_write": ["entity names"],
      "can_delete": ["entity names"]
    }}
  }},
  "business_rules": ["list of important business logic rules"]
}}

Rules:
- Every page must have at least one role in access
- Every entity from the intent must appear
- Role permissions must be complete for all roles
- Always return valid JSON
"""

def design_system(intent: dict) -> dict:
    """Stage 2: Convert intent into full system architecture design."""
    prompt = DESIGN_PROMPT.format(intent=json.dumps(intent, indent=2))
    result = call_gemini(prompt)
    result["_stage"] = "system_design"
    return result

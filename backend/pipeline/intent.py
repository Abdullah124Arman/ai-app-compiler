from gemini_client import call_gemini

INTENT_PROMPT = """
You are an expert software architect. Analyze the following user request and extract structured intent.

User Request: "{user_input}"

Return a JSON object with EXACTLY this structure:
{{
  "app_name": "string - short name for the app",
  "app_type": "string - type of application (CRM, E-commerce, Dashboard, etc.)",
  "description": "string - one sentence description",
  "core_features": ["list of main features"],
  "user_roles": ["list of user roles e.g. admin, user, manager"],
  "integrations": ["list of third party integrations e.g. stripe, email, maps"],
  "complexity": "simple | medium | complex",
  "assumptions": ["list of reasonable assumptions made for underspecified parts"]
}}

Rules:
- If input is vague, make reasonable assumptions and document them in "assumptions"
- If input is conflicting, pick the most reasonable interpretation
- Always return valid JSON
"""

def extract_intent(user_input: str) -> dict:
    """Stage 1: Extract structured intent from raw user input."""
    prompt = INTENT_PROMPT.format(user_input=user_input)
    result = call_gemini(prompt)
    result["_stage"] = "intent_extraction"
    return result

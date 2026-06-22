from gemini_client import call_gemini
import json

SCHEMA_PROMPT = """
You are an expert full-stack engineer. Based on the app intent and system design, generate complete schemas for all 4 layers.

App Intent:
{intent}

System Design:
{design}

Return a JSON object with EXACTLY this structure:
{{
  "ui_schema": {{
    "theme": {{"primary_color": "#hex", "font": "string", "mode": "dark|light"}},
    "pages": [
      {{
        "name": "string",
        "route": "string",
        "layout": "sidebar|topnav|blank",
        "components": [
          {{
            "type": "Table|Form|Card|Chart|Button|Modal|Input|Select",
            "id": "unique_component_id",
            "label": "string",
            "data_source": "api_endpoint_id or null",
            "fields": ["field names if applicable"]
          }}
        ]
      }}
    ]
  }},
  "api_schema": {{
    "base_url": "/api/v1",
    "endpoints": [
      {{
        "id": "unique_endpoint_id",
        "path": "string - e.g. /users",
        "method": "GET|POST|PUT|DELETE|PATCH",
        "description": "string",
        "auth_required": true,
        "roles_allowed": ["role names"],
        "request_body": {{"field_name": "type"}} ,
        "response": {{"field_name": "type"}},
        "db_table": "string - which DB table this uses"
      }}
    ]
  }},
  "db_schema": {{
    "tables": [
      {{
        "name": "string - table name (snake_case)",
        "fields": [
          {{
            "name": "string",
            "type": "string|integer|boolean|datetime|float|text|uuid",
            "required": true,
            "unique": false,
            "default": null,
            "foreign_key": "table.field or null"
          }}
        ],
        "indexes": ["field names to index"]
      }}
    ]
  }},
  "auth_schema": {{
    "strategy": "JWT|session|oauth",
    "token_expiry": "string - e.g. 24h",
    "roles": ["list of all roles"],
    "role_hierarchy": {{"role": "parent_role or null"}},
    "protected_routes": ["/route_path"],
    "public_routes": ["/route_path"],
    "permissions": {{
      "role_name": {{
        "endpoints": ["endpoint_ids allowed"],
        "features": ["feature names"]
      }}
    }}
  }}
}}

Critical rules:
- Every UI component's data_source must match an endpoint id in api_schema
- Every endpoint's db_table must match a table name in db_schema
- Every table used in an endpoint must exist in db_schema
- All roles in auth_schema must match roles in system design
- Always include id, created_at, updated_at fields in every DB table
- Always return valid JSON
"""

def generate_schemas(intent: dict, design: dict) -> dict:
    """Stage 3: Generate all 4 schemas (UI, API, DB, Auth)."""
    prompt = SCHEMA_PROMPT.format(
        intent=json.dumps(intent, indent=2),
        design=json.dumps(design, indent=2)
    )
    result = call_gemini(prompt)
    result["_stage"] = "schema_generation"
    return result

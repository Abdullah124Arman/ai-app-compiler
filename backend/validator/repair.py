import json
from gemini_client import call_gemini

REPAIR_PROMPT = """
You are a JSON repair specialist. The following schemas failed validation with these errors:

Errors:
{errors}

Broken Schemas:
{schemas}

Fix ONLY the reported errors. Do not change anything else.
Return the complete, fixed JSON schemas with all errors resolved.
Always return valid JSON.
"""


def repair_schemas(schemas: dict, errors: list) -> dict:
    """Attempt to automatically repair schemas given a list of validation errors."""
    if not errors:
        return schemas

    prompt = REPAIR_PROMPT.format(
        errors=json.dumps(errors, indent=2),
        schemas=json.dumps(schemas, indent=2)
    )
    repaired = call_gemini(prompt)
    repaired["_repaired"] = True
    repaired["_repair_errors_fixed"] = errors
    return repaired


def add_missing_db_fields(schemas: dict) -> dict:
    """Rule-based repair: ensure all DB tables have id, created_at, updated_at."""
    standard_fields = [
        {"name": "id", "type": "uuid", "required": True, "unique": True, "default": "auto", "foreign_key": None},
        {"name": "created_at", "type": "datetime", "required": True, "unique": False, "default": "now()", "foreign_key": None},
        {"name": "updated_at", "type": "datetime", "required": True, "unique": False, "default": "now()", "foreign_key": None},
    ]
    if "db_schema" in schemas and "tables" in schemas["db_schema"]:
        for table in schemas["db_schema"]["tables"]:
            existing_names = {f["name"] for f in table.get("fields", [])}
            for sf in standard_fields:
                if sf["name"] not in existing_names:
                    table["fields"].insert(0, sf)
    return schemas

import json
from typing import Tuple

REQUIRED_SCHEMA_KEYS = ["ui_schema", "api_schema", "db_schema", "auth_schema"]
REQUIRED_UI_KEYS = ["pages", "theme"]
REQUIRED_API_KEYS = ["endpoints", "base_url"]
REQUIRED_DB_KEYS = ["tables"]
REQUIRED_AUTH_KEYS = ["roles", "strategy", "permissions"]


def validate_json(data) -> Tuple[bool, list]:
    """Check if data is a valid dict (already parsed JSON)."""
    errors = []
    if not isinstance(data, dict):
        errors.append("Output is not a JSON object")
        return False, errors
    return True, errors


def validate_top_level_keys(schemas: dict) -> Tuple[bool, list]:
    """Check all 4 required schema sections exist."""
    errors = []
    for key in REQUIRED_SCHEMA_KEYS:
        if key not in schemas:
            errors.append(f"Missing required section: '{key}'")
    return len(errors) == 0, errors


def validate_ui_schema(ui: dict) -> Tuple[bool, list]:
    errors = []
    for key in REQUIRED_UI_KEYS:
        if key not in ui:
            errors.append(f"UI schema missing: '{key}'")
    if "pages" in ui and not isinstance(ui["pages"], list):
        errors.append("UI schema 'pages' must be a list")
    return len(errors) == 0, errors


def validate_api_schema(api: dict) -> Tuple[bool, list]:
    errors = []
    for key in REQUIRED_API_KEYS:
        if key not in api:
            errors.append(f"API schema missing: '{key}'")
    if "endpoints" in api:
        for i, ep in enumerate(api["endpoints"]):
            if "id" not in ep:
                errors.append(f"Endpoint {i} missing 'id'")
            if "method" not in ep:
                errors.append(f"Endpoint {i} missing 'method'")
            if "path" not in ep:
                errors.append(f"Endpoint {i} missing 'path'")
    return len(errors) == 0, errors


def validate_db_schema(db: dict) -> Tuple[bool, list]:
    errors = []
    if "tables" not in db:
        errors.append("DB schema missing 'tables'")
        return False, errors
    for table in db["tables"]:
        if "name" not in table:
            errors.append("A DB table is missing 'name'")
        if "fields" not in table:
            errors.append(f"DB table '{table.get('name', '?')}' missing 'fields'")
    return len(errors) == 0, errors


def validate_auth_schema(auth: dict) -> Tuple[bool, list]:
    errors = []
    for key in REQUIRED_AUTH_KEYS:
        if key not in auth:
            errors.append(f"Auth schema missing: '{key}'")
    return len(errors) == 0, errors


def validate_cross_layer(schemas: dict) -> Tuple[bool, list]:
    """Check consistency across UI, API, DB layers."""
    errors = []
    try:
        # Collect endpoint IDs
        endpoint_ids = {
            ep["id"]
            for ep in schemas.get("api_schema", {}).get("endpoints", [])
            if "id" in ep
        }
        # Collect DB table names
        table_names = {
            t["name"]
            for t in schemas.get("db_schema", {}).get("tables", [])
            if "name" in t
        }
        # Check UI components reference valid endpoints
        for page in schemas.get("ui_schema", {}).get("pages", []):
            for comp in page.get("components", []):
                ds = comp.get("data_source")
                if ds and ds not in endpoint_ids:
                    errors.append(
                        f"UI component '{comp.get('id', '?')}' references unknown endpoint '{ds}'"
                    )
        # Check API endpoints reference valid DB tables
        for ep in schemas.get("api_schema", {}).get("endpoints", []):
            db_table = ep.get("db_table")
            if db_table and db_table not in table_names:
                errors.append(
                    f"API endpoint '{ep.get('id', '?')}' references unknown DB table '{db_table}'"
                )
    except Exception as e:
        errors.append(f"Cross-layer validation error: {str(e)}")
    return len(errors) == 0, errors


def run_validation(schemas: dict) -> dict:
    """Run full validation suite and return report."""
    all_errors = []
    warnings = []

    valid_json, json_errors = validate_json(schemas)
    all_errors.extend(json_errors)

    if valid_json:
        _, key_errors = validate_top_level_keys(schemas)
        all_errors.extend(key_errors)

        if "ui_schema" in schemas:
            _, ui_errors = validate_ui_schema(schemas["ui_schema"])
            all_errors.extend(ui_errors)

        if "api_schema" in schemas:
            _, api_errors = validate_api_schema(schemas["api_schema"])
            all_errors.extend(api_errors)

        if "db_schema" in schemas:
            _, db_errors = validate_db_schema(schemas["db_schema"])
            all_errors.extend(db_errors)

        if "auth_schema" in schemas:
            _, auth_errors = validate_auth_schema(schemas["auth_schema"])
            all_errors.extend(auth_errors)

        _, cross_errors = validate_cross_layer(schemas)
        all_errors.extend(cross_errors)

    return {
        "is_valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": warnings,
        "error_count": len(all_errors),
    }

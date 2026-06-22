import json, time
from pipeline.intent import extract_intent
from pipeline.design import design_system
from pipeline.schema import generate_schemas
from pipeline.refine import refine_schemas
from validator.validate import run_validation
from validator.repair import add_missing_db_fields

start = time.time()
prompt = 'Build a CRM with login, contacts, dashboard, and role-based access'

print('Running Stage 1...')
intent = extract_intent(prompt)
print('Stage 1 done:', intent['app_name'])

print('Running Stage 2...')
design = design_system(intent)
pages = len(design.get('pages', []))
entities = len(design.get('entities', []))
print('Stage 2 done:', pages, 'pages,', entities, 'entities')

print('Running Stage 3...')
schemas = generate_schemas(intent, design)
schemas = add_missing_db_fields(schemas)
ui_pages = len(schemas.get('ui_schema', {}).get('pages', []))
api_eps = len(schemas.get('api_schema', {}).get('endpoints', []))
db_tables = len(schemas.get('db_schema', {}).get('tables', []))
print('Stage 3 done: UI pages:', ui_pages, '| API endpoints:', api_eps, '| DB tables:', db_tables)

print('Running Stage 4...')
refined = refine_schemas(schemas)
print('Stage 4 done')

print('Running Validation...')
report = run_validation(refined)
status = 'VALID' if report['is_valid'] else str(report['errors'])
print('Validation:', status)

elapsed = round((time.time() - start) * 1000)
print('Total time:', elapsed, 'ms')

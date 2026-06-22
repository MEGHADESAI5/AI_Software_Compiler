import json
from concurrent.futures import ThreadPoolExecutor
from config import client

# ==========================
# Prompt templates for each schema
# ==========================

DB_PROMPT = """
Based on the system design, generate a database schema.

System Design (JSON):
{design_json}

Output EXACT JSON with a "tables" array. Each table has:
- "name": string
- "columns": array of {{"name": string, "type": "string|integer|uuid|datetime|boolean", "required": bool}}
- "foreign_keys": optional array of {{"column": string, "references": "table.column"}}

Example:
{{
  "tables": [
    {{
      "name": "users",
      "columns": [
        {{"name": "id", "type": "uuid", "required": true}},
        {{"name": "email", "type": "string", "required": true}}
      ]
    }}
  ]
}}
"""

API_PROMPT = """
Based on the system design, generate REST API endpoints.

System Design (JSON):
{design_json}

Output EXACT JSON with an "endpoints" array. Each endpoint has:
- "path": string (e.g., "/api/users")
- "method": "GET|POST|PUT|DELETE"
- "auth_required": bool
- "request_schema": optional JSON object (for POST/PUT)
- "response_schema": JSON object

Example:
{{
  "endpoints": [
    {{
      "path": "/api/users",
      "method": "GET",
      "auth_required": true,
      "response_schema": {{"type": "array", "items": {{"$ref": "#/components/schemas/User"}}}}
    }}
  ]
}}
"""

UI_PROMPT = """
Based on the system design, generate UI page and component structure.

System Design (JSON):
{design_json}

Output EXACT JSON with a "pages" array. Each page has:
- "route": string (e.g., "/dashboard")
- "components": array of string (component names, e.g., ["Sidebar", "DataTable"])

Example:
{{
  "pages": [
    {{"route": "/dashboard", "components": ["Header", "StatsCards", "RecentActivity"]}}
  ]
}}
"""

AUTH_PROMPT = """
Based on the system design, generate role-based access control rules.

System Design (JSON):
{design_json}

Output EXACT JSON with a "roles" array. Each role has:
- "name": string
- "permissions": array of string (e.g., ["view_users", "edit_users"])

Example:
{{
  "roles": [
    {{"name": "admin", "permissions": ["view_analytics", "manage_users"]}}
  ]
}}
"""

# ==========================
# Generation functions
# ==========================

def generate_db(design: dict) -> dict:
    print("  📊 Generating DB schema...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": DB_PROMPT.format(design_json=json.dumps(design))}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def generate_api(design: dict) -> dict:
    print("  🌐 Generating API schema...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": API_PROMPT.format(design_json=json.dumps(design))}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def generate_ui(design: dict) -> dict:
    print("  🖥️  Generating UI schema...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": UI_PROMPT.format(design_json=json.dumps(design))}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def generate_auth(design: dict) -> dict:
    print("  🔐 Generating Auth schema...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": AUTH_PROMPT.format(design_json=json.dumps(design))}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# ==========================
# Master function: parallel generation
# ==========================

def generate_all_schemas(design: dict) -> dict:
    """
    Generates DB, API, UI, Auth schemas in parallel.
    Returns a dictionary with keys: 'db', 'api', 'ui', 'auth'
    """
    print("\n🚀 Stage 3: Generating schemas in parallel...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_db = executor.submit(generate_db, design)
        future_api = executor.submit(generate_api, design)
        future_ui = executor.submit(generate_ui, design)
        future_auth = executor.submit(generate_auth, design)
        
        db = future_db.result()
        api = future_api.result()
        ui = future_ui.result()
        auth = future_auth.result()
    
    print("✅ All schemas generated.\n")
    return {"db": db, "api": api, "ui": ui, "auth": auth}
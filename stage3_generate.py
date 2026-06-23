import json
import time
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
# Helper: API call with retry
# ==========================

def call_with_retry(prompt: str, design_json: str, max_retries: int = 3):
    """Calls the API with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Higher rate limit than 70B
                messages=[{"role": "user", "content": prompt.format(design_json=design_json)}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if "429" in str(e) or "Rate limit" in str(e):
                wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                print(f"      ⏳ Rate limit hit, waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Max retries exceeded for API call")

# ==========================
# Generation functions (sequential)
# ==========================

def generate_db(design: dict) -> dict:
    print("  📊 Generating DB schema...")
    design_json = json.dumps(design)
    result = call_with_retry(DB_PROMPT, design_json)
    print("  ✅ DB schema done")
    return result

def generate_api(design: dict) -> dict:
    print("  🌐 Generating API schema...")
    design_json = json.dumps(design)
    result = call_with_retry(API_PROMPT, design_json)
    print("  ✅ API schema done")
    return result

def generate_ui(design: dict) -> dict:
    print("  🖥️  Generating UI schema...")
    design_json = json.dumps(design)
    result = call_with_retry(UI_PROMPT, design_json)
    print("  ✅ UI schema done")
    return result

def generate_auth(design: dict) -> dict:
    print("  🔐 Generating Auth schema...")
    design_json = json.dumps(design)
    result = call_with_retry(AUTH_PROMPT, design_json)
    print("  ✅ Auth schema done")
    return result

# ==========================
# Master function: sequential generation (to avoid rate limits)
# ==========================

def generate_all_schemas(design: dict) -> dict:
    """
    Generates DB, API, UI, Auth schemas sequentially.
    Returns a dictionary with keys: 'db', 'api', 'ui', 'auth'
    """
    print("\n🚀 Stage 3: Generating schemas sequentially (to avoid rate limits)...")
    
    # Sequential calls with delays between them
    db = generate_db(design)
    time.sleep(1.5)
    
    api = generate_api(design)
    time.sleep(1.5)
    
    ui = generate_ui(design)
    time.sleep(1.5)
    
    auth = generate_auth(design)
    
    print("✅ All schemas generated.\n")
    return {"db": db, "api": api, "ui": ui, "auth": auth}
import json
from config import client

DESIGN_PROMPT = """
Based on the Intent IR, design the system architecture.

Intent: {intent_json}

Output EXACT JSON:
{{
  "entities": [
    {{"name": "User", "fields": [{{"name": "email", "type": "string"}}], "relationships": []}}
  ],
  "role_permissions": {{
    "admin": ["view_analytics", "manage_users"],
    "user": ["view_profile"]
  }},
  "business_rules": [
    {{"name": "premium_gating", "logic": "Only premium users can access /premium-features"}}
  ]
}}
"""

def design_system(intent: dict) -> dict:
    print("🏗️ Stage 2: Designing system architecture...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Or "gpt-4o-mini" if using OpenAI
        messages=[
            {"role": "user", "content": DESIGN_PROMPT.format(intent_json=json.dumps(intent))}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    design = json.loads(response.choices[0].message.content)
    print(f"✅ System designed. Entities: {len(design.get('entities', []))}")
    return design
import json
from config import client

INTENT_PROMPT = """
You are a Requirements Analyst. Extract structured intent from the user request.

User Request: {user_input}

Output EXACT JSON. No extra text. No markdown.
{{
  "app_name": "string",
  "app_type": "crm | ecommerce | blog | social | task-mgmt | other",
  "core_features": ["feature1", "feature2"],
  "user_roles": ["admin", "user"],
  "data_entities": [{{"name": "EntityName", "attributes": ["attr1", "attr2"]}}],
  "ambiguities": ["Unclear points. Leave empty list if clear."]
}}
"""

def extract_intent(user_input: str) -> dict:
    print(f"🔍 Stage 1: Extracting intent from: {user_input[:50]}...")
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Or "gpt-4o-mini" if using OpenAI
        messages=[
            {"role": "user", "content": INTENT_PROMPT.format(user_input=user_input)}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    intent = json.loads(response.choices[0].message.content)
    print(f"✅ Intent extracted. App Type: {intent.get('app_type')}")
    return intent
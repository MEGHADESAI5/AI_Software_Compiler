from openai import OpenAI

# Your Groq API key (hardcoded for simplicity)
GROQ_API_KEY = "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"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

print("✅ Config loaded successfully")
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

def call_llm(prompt: str) -> dict:
    """Call Groq (Llama 3.3 70B) and return parsed JSON."""
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a JSON-only assistant. Always respond with valid JSON only. No markdown, no explanation, no code fences. Just raw JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

# Keep old name for compatibility
call_gemini = call_llm

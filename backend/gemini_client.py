import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_client_configured = False

def configure_client():
    global _client_configured
    if not _client_configured:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        _client_configured = True

def call_llm(prompt: str) -> dict:
    """Call Gemini 1.5 Flash and return parsed JSON."""
    configure_client()
    
    # Use gemini-flash-lite-latest which has massive free tier quotas!
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    system_prompt = "You are a JSON-only assistant. Always respond with valid JSON only. No markdown, no explanation, no code fences. Just raw JSON."
    
    response = model.generate_content(
        f"{system_prompt}\n\n{prompt}",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=8192,
        )
    )
    
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
            
    # Use json-repair to automatically fix missing commas, quotes, and trailing garbage
    import json_repair
    res = json_repair.loads(text)
    
    if isinstance(res, str):
        # Find the first { or [ to force it to parse the object
        start_idx = -1
        for i, c in enumerate(text):
            if c in "{[":
                start_idx = i
                break
        if start_idx != -1:
            res = json_repair.loads(text[start_idx:])
            
    if isinstance(res, str):
        raise ValueError(f"LLM did not return a valid JSON object. Got string instead: {text[:200]}")
        
    return res

# Keep old name for compatibility
call_gemini = call_llm

"""
diagnostics.py — Connectivity and model-availability checks for the
People Research Agent.

Run this first after setting up your .env file to confirm both APIs
are reachable and to find which Gemini model name is available to
your key before running the main agent.

Usage:
    python diagnostics.py
"""

import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not all([GOOGLE_API_KEY, SEARCH_API_KEY, SEARCH_ENGINE_ID]):
    print("❌ Missing one or more required environment variables.")
    print("   Copy .env.example to .env and fill in your values first.")
    sys.exit(1)

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
]

def list_available_models():
    """Query Google for every model this key can access."""
    print("🔍 Listing models available to your key...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Connection Failed: {response.status_code}")
            print(response.text)
            return []

        data = response.json()
        models = data.get('models', [])
        chat_models = []
        for m in models:
            if "generateContent" in m.get('supportedGenerationMethods', []):
                name = m['name'].replace('models/', '')
                chat_models.append(name)
                print(f"   • {name}")
        return chat_models
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def find_working_model(candidates):
    """Try each candidate model name and report the first one that responds."""
    print("\n🧪 Testing candidate model names...")
    for model_name in candidates:
        print(f"   Trying: {model_name}...", end=" ")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_API_KEY}"
        try:
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "Hi"}]}]}
            )
            if res.status_code == 200:
                print("✅ WORKS!")
                return model_name
            else:
                print(f"❌ {res.status_code}")
        except Exception:
            print("❌ Error")
    return None

def check_search_api():
    """Confirm the Custom Search API key and Search Engine ID are valid."""
    print("\n👀 Testing Custom Search API...")
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": SEARCH_API_KEY, "cx": SEARCH_ENGINE_ID, "q": "test query", "num": 1}
        res = requests.get(url, params=params)
        if res.status_code == 200:
            items = res.json().get('items', [])
            title = items[0].get('title', 'No title found') if items else '(no results)'
            print(f"✅ Search API works. Sample result: {title}")
        else:
            print(f"❌ Search API Failed: {res.status_code} — {res.text}")
    except Exception as e:
        print(f"❌ Search API Connection Error: {e}")

if __name__ == "__main__":
    available = list_available_models()
    if available:
        working = find_working_model(available)
        if working:
            print(f"\n🎉 Use this model name in people_research_agent.py: {working}")
    else:
        print("\n⚠️ No models found. Check that your Gemini API key is valid and has permissions.")

    check_search_api()

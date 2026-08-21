import requests
import json
import time
import sys
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Keys are loaded from environment variables — never hardcoded.
# Copy .env.example to .env and fill in your own values before running.
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not all([GOOGLE_API_KEY, SEARCH_API_KEY, SEARCH_ENGINE_ID]):
    print("❌ Missing one or more required environment variables.")
    print("   Copy .env.example to .env and fill in GOOGLE_API_KEY, SEARCH_API_KEY, and SEARCH_ENGINE_ID.")
    sys.exit(1)

# Switch to the most stable, high-quota model available
MODEL_NAME = "gemini-2.5-flash"

# --- HELPER FUNCTIONS ---

def get_safe_filename(name):
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
    return f"reports/{safe_name}.md"

def ask_gemini(prompt):
    """Sends a request to Gemini with retry logic for rate limits."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    # Aggressive Retry: Wait longer if we hit a limit
    delays = [60, 120, 180]  # Wait 1 min, 2 mins, 3 mins

    for attempt, wait_time in enumerate(delays):
        try:
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']

            elif response.status_code == 429:
                print(f"   ⚠️ Quota Hit (429). Cooling down for {wait_time}s...")
                time.sleep(wait_time)
                continue

            else:
                print(f"   ❌ Gemini Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return None
    return None

def search_google(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": SEARCH_API_KEY, "cx": SEARCH_ENGINE_ID,
        "q": query, "num": 3
    }
    try:
        res = requests.get(url, params=params)
        results = ""
        if res.status_code == 200:
            data = res.json()
            if 'items' in data:
                for item in data['items']:
                    results += f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\nLink: {item.get('link')}\n\n"
        return results
    except Exception:
        return ""

def save_report(name, content):
    if not os.path.exists("reports"):
        os.makedirs("reports")
    filename = get_safe_filename(name)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"   💾 Saved report to: {filename}")

# --- CORE RESEARCH LOGIC ---

def research_person(name):
    filename = get_safe_filename(name)
    if os.path.exists(filename):
        print(f"   ⏭️  Exists: {name}")
        return "SKIPPED"

    print(f"\n🕵️‍♀️  Processing: {name}")

    # Standard, effective queries generated directly — saves an API call per person
    # versus having the model plan its own search queries.
    queries = [
        f'"{name}" LinkedIn',
        f'"{name}" interview podcast',
        f'"{name}" history biography',
    ]

    # EXECUTE SEARCHES
    raw_data = ""
    for q in queries:
        print(f"   -> Searching: {q}...")
        res = search_google(q)
        raw_data += f"\n--- Query: {q} ---\n{res}\n"
        time.sleep(1)  # Be nice to the Search API

    # SYNTHESIZE (the only AI call)
    print("   🧠 Writing report...")
    report_prompt = f"""
    Write a deep executive dossier for '{name}' based on this data.

    RAW DATA:
    {raw_data}

    FORMAT:
    # Profile: {name}
    ## 1. The One-Liner (Who are they?)
    ## 2. Professional Timeline (Current & Past)
    ## 3. Key Beliefs & Mental Models (What makes them tick?)
    ## 4. Sources
    """
    final_report = ask_gemini(report_prompt)
    return final_report

# --- BATCH RUNNER ---

def run_batch(file_path):
    print(f"🚀 Starting batch run, reading from {file_path}...")

    try:
        with open(file_path, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: '{file_path}' not found.")
        return

    total = len(targets)
    print(f"📂 Found {total} targets.\n")

    for index, person in enumerate(targets):
        print(f"[{index+1}/{total}] Checking {person}...")

        report = research_person(person)

        if report and report != "SKIPPED":
            save_report(person, report)
            # Pause between people to stay within rate limits
            print("   💤 Safety Pause: 15 seconds...")
            time.sleep(15)
        elif report == "SKIPPED":
            continue

    print("\n✅ Batch Complete! Check the 'reports' folder.")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "targets.example.txt"
    run_batch(input_file)

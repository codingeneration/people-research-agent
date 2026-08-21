# People Research Agent

A Python agent that chains Google Custom Search with Gemini to generate structured executive-style research dossiers on named individuals from public web data. Built for pre-meeting research and prospect intelligence — turning "who am I meeting with tomorrow" into a five-minute batch job instead of a manual search spiral.

## How it works

1. For each name in a target list, the agent runs a small set of targeted search queries (LinkedIn presence, interviews/podcasts, general biography) against the Google Custom Search API.
2. The raw search results are handed to Gemini in a single synthesis call, which writes a structured markdown dossier: a one-line summary, professional timeline, key beliefs/mental models, and sources.
3. Reports are saved to a local `reports/` folder, one markdown file per person.

Only one Gemini API call is made per person (the synthesis step) — search queries are generated directly rather than through an extra planning call, keeping token usage and cost down for batch runs.

## Features

- **Batch processing** — reads a plain text list of names and runs the full pipeline for each.
- **Resumable** — skips anyone who already has a saved report, so a batch can be safely re-run after an interruption.
- **Rate-limit aware** — aggressive retry/backoff (1/2/3 minute waits) on Gemini 429 responses, plus a pause between people to stay within Search API quotas.
- **Environment-based config** — no keys in code; everything loads from a local `.env` file.

## Setup

```bash
git clone <this-repo>
cd people-research-agent
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in your own values:

```
GOOGLE_API_KEY=your_gemini_api_key_here
SEARCH_API_KEY=your_custom_search_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here
```

- **Gemini API key** — from [Google AI Studio](https://aistudio.google.com/).
- **Custom Search API key + Search Engine ID** — from the [Programmable Search Engine](https://programmablesearchengine.google.com/) control panel and [Google Cloud Console](https://console.cloud.google.com/).

## Usage

Run diagnostics first to confirm both APIs are reachable and to find a working Gemini model name for your key:

```bash
python diagnostics.py
```

Create your own target list (one `Name<TAB>Company` pair per line — see `targets.example.txt` for the format), then run:

```bash
python people_research_agent.py targets.txt
```

Reports land in `reports/<Name>.md`.

## Project structure

| File | Purpose |
|---|---|
| `people_research_agent.py` | Main batch runner — search, synthesize, save |
| `diagnostics.py` | Connectivity checks + Gemini model discovery |
| `.env.example` | Template for required environment variables |
| `targets.example.txt` | Example input format (placeholder names) |
| `requirements.txt` | Python dependencies |

## A note on privacy

This tool is intended for legitimate business use — pre-meeting research, sales/prospect prep, and similar workflows — using publicly available web data. Your own target lists (`targets.txt`) and generated reports (`reports/`) are gitignored by default and should stay local; only the example template is meant to be shared publicly.

## License

All rights reserved. Shared publicly for portfolio/demonstration purposes. Please reach out before reusing or forking for production use.

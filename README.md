# Autonomous Lead Enrichment Agent

An autonomous lead enrichment pipeline built in Python 3.13 using **LangGraph**, **Playwright**, and **OpenAI Structured Outputs**. The agent crawls target company domains, extracts high-value business intelligence, dynamically validates missing leadership profiles via search APIs, and logs per-domain token costs.

---

## Demo Video

- **Loom Walkthrough**: [Link to Loom Video](https://www.loom.com/share/9c5213ca455046e4b0233072e6786bae) *(Replace with your recording)*

---

## Features

- **Dynamic Headless Crawling:** Async Playwright navigates client-rendered SPAs (React/Next.js/Vue) and discovers strategic subpages (`/about`, `/team`, `/company`, `/pricing`, `/contact`).
- **Aggressive Token Optimization:** BeautifulSoup and `html2text` prune boilerplate nodes (SVGs, scripts, cookie banners, tracking iframes), reducing token consumption by 80–90%.
- **Guaranteed Schema Conformance:** Strictly enforces Pydantic v2 data models via OpenAI's structured outputs API.
- **Autonomous Agent Graph:** Built on LangGraph state machines with conditional branching (`should_search_linkedin`).
- **External Search Fallback:** Automatically queries Serper (Google Search API) if founder LinkedIn profile URLs are missing from website text.
- **Cost & Token Accounting:** Tracks prompt/completion tokens per domain and calculates exact USD costs.
- **Resilience & Fault Isolation:** Uses concurrency semaphores and defensive try/except boundary blocks so that failing sites (404s, bot challenges, timeouts) never crash batch execution.

---

## Architecture Flow

```text
                     Target Domain
                           │
                           ▼
                    ┌──────────────┐
                    │  crawl_node  │  <── Playwright crawls homepage & subpages
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  clean_node  │  <── HTML pruned & converted to Markdown
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ extract_node │  <── OpenAI Structured Output + Token Accounting
                    └──────┬───────┘
                           │
              [should_search_linkedin?]
                    /             \
               YES /               \ NO
                  ▼                 ▼
          ┌──────────────┐       [ END ]
          │ search_node  │
          └──────┬───────┘
                 ▼
              [ END ] ──► output.json
```

## Prerequisites

- **Python 3.13+**
- [**uv**](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- **OpenAI API Key**
- **Serper API Key** (for Google Search fallback)

## Setup & Installation

### Option 1: Using `uv` (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/aryuskumar1122/Autonomous-Lead-Enrichment-Agent.git
   cd autonomous-lead-enrichment-agent
   ```

2. **Sync virtual environment & dependencies:**

   ```bash
   uv sync
   ```

3. **Install Playwright browser binaries:**

   ```bash
   uv run playwright install chromium
   ```

### Option 2: Using standard `pip`

1. **Clone the repository:**

   ```bash
   git clone https://github.com/aryuskumar1122/Autonomous-Lead-Enrichment-Agent.git
   cd autonomous-lead-enrichment-agent
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Environment Variables (`.env`)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Set the following variables inside `.env`:

```ini
# Required: OpenAI API Key for structured extraction
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Model name (Default: gpt-4o-mini)
OPENAI_MODEL=gpt-5.4-mini

# Required: Serper API Key for Google Search fallback
SERPER_API_KEY=your_serper_api_key_here

# Crawler Configuration
PAGE_TIMEOUT_MS=20000
MAX_SUBPAGES=4
```

### Configuration Parameters

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | **Yes** | — | OpenAI API authorization token |
| `OPENAI_MODEL` | No | `gpt-5.4-mini` | Extraction model (`gpt-5.4-mini`, `gpt-5.4`) |
| `SERPER_API_KEY` | **Yes** | — | Google search API key for LinkedIn profile recovery |
| `PAGE_TIMEOUT_MS` | No | `20000` | Playwright page navigation timeout in milliseconds |
| `MAX_SUBPAGES` | No | `4` | Maximum strategic subpages crawled per domain |

## Running the Project

Run the pipeline against the default test targets (`postman.com`, `supabase.com`, `vapi.ai`):

```bash
# Using uv:
uv run main.py

# Using standard Python:
python main.py
```

### Execution Output

- Real-time logging displays crawling status, DOM cleaning compression, structured extraction, and search fallback queries.
- Once complete, results and cost summaries are written to **`output.json`**.

## Output Schema

The pipeline produces structured JSON matching the format below:

```json
[
  {
    "domain": "postman.com",
    "status": "success",
    "error_message": null,
    "crawled_urls": [
      "https://postman.com",
      "https://postman.com/about-postman",
      "https://postman.com/pricing"
    ],
    "intelligence": {
      "company_overview": "Postman is an enterprise API platform that simplifies each step of the API lifecycle.",
      "target_audience": "Software developers, API engineers, QA testers, and DevOps teams.",
      "contact_points": [
        "help@postman.com",
        "sales@postman.com"
      ],
      "key_leadership": [
        {
          "name": "Abhinav Asthana",
          "role": "CEO and Co-Founder",
          "linkedin_url": "https://www.linkedin.com/in/abhinavasthana"
        }
      ],
      "data_confidence_score": 0.95
    },
    "metrics": {
      "prompt_tokens": 3840,
      "completion_tokens": 182,
      "total_tokens": 4022,
      "estimated_cost_usd": 0.000685
    }
  }
]
```

## Project Structure

```text
lead-enrichment-agent/
├── src/
│   ├── __init__.py
│   ├── cleaner.py      # DOM pruner and HTML-to-Markdown token reducer
│   ├── crawler.py      # Async Playwright crawler with subpage discovery
│   ├── graph.py        # LangGraph StateGraph, conditional edges, and execution nodes
│   ├── models.py       # Pydantic schemas and AgentState TypedDict definition
│   └── search.py       # Serper Google Search fallback client
├── .env.example        # Environment variable templates
├── main.py             # Pipeline orchestrator & CLI runner
├── output.json         # Scraped intelligence and metrics output
├── pyproject.toml      # uv / PEP 621 package configuration
├── requirements.txt    # Frozen pip requirements
└── README.md
```

import asyncio
import json
import logging
import sys
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from src.graph import build_lead_graph
from src.models import AgentState

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LangGraphLeadAgent")

TARGET_DOMAINS = ["postman.com", "supabase.com", "vapi.ai"]


async def run_pipeline():
    graph = build_lead_graph()
    sem = asyncio.Semaphore(2)

    async def process(domain: str):
        async with sem:
            initial_state: AgentState = {
                "domain": domain,
                "crawled_urls": [],
                "raw_pages": {},
                "cleaned_context": "",
                "intelligence": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "status": "pending",
                "error_message": None,
            }
            logger.info(f"Starting graph execution for: {domain}")
            final_state = await graph.ainvoke(initial_state)
            return final_state

    tasks = [process(d) for d in TARGET_DOMAINS]
    completed_states = await tqdm.gather(*tasks, desc="Enriching Leads")

    # Serialize outputs cleanly
    formatted_output = []
    for s in completed_states:
        formatted_output.append(
            {
                "domain": s["domain"],
                "status": s["status"],
                "error_message": s["error_message"],
                "crawled_urls": s["crawled_urls"],
                "intelligence": s["intelligence"],
                "metrics": {
                    "prompt_tokens": s["prompt_tokens"],
                    "completion_tokens": s["completion_tokens"],
                    "total_tokens": s["total_tokens"],
                    "estimated_cost_usd": s["estimated_cost_usd"],
                },
            }
        )

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(formatted_output, f, indent=2, ensure_ascii=False)

    total_tokens = sum(s["total_tokens"] for s in completed_states)
    total_cost = sum(s["estimated_cost_usd"] for s in completed_states)

    print("\n--- Execution Summary ---")
    print(f"Domains Processed: {len(completed_states)}")
    print(f"Total Tokens:      {total_tokens}")
    print(f"Total Cost (USD):  ${total_cost:.5f}")
    print("Results saved to output.json\n")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
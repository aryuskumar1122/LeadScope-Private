import os
import re
from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from src.models import AgentState, LLMExtractedIntelligence
from src.cleaner import clean_html_to_markdown
from src.crawler import crawl_site
from src.search import search_linkedin_fallback

# Pricing for gpt-4o-mini ($0.15 / 1M prompt, $0.60 / 1M completion)
PRICE_PER_M_IN = 0.15
PRICE_PER_M_OUT = 0.60


async def crawl_node(state: AgentState) -> dict:
    domain = state["domain"]
    try:
        timeout_ms = int(os.getenv("PAGE_TIMEOUT_MS", "20000"))
        max_sub = int(os.getenv("MAX_SUBPAGES", "4"))
        pages = await crawl_site(domain, timeout_ms=timeout_ms, max_subpages=max_sub)
        return {
            "raw_pages": pages,
            "crawled_urls": list(pages.keys()),
            "status": "crawled" if pages else "failed",
            "error_message": None if pages else "No content returned",
        }
    except Exception as e:
        return {"raw_pages": {}, "crawled_urls": [], "status": "failed", "error_message": str(e)}


def clean_node(state: AgentState) -> dict:
    if state["status"] == "failed":
        return {}

    markdown_parts = []
    for url, html in state["raw_pages"].items():
        cleaned = clean_html_to_markdown(html)
        markdown_parts.append(f"--- SOURCE: {url} ---\n{cleaned}")

    return {"cleaned_context": "\n\n".join(markdown_parts)}


async def extract_node(state: AgentState) -> dict:
    if state["status"] == "failed" or not state.get("cleaned_context"):
        return {"status": "failed"}

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.1)

    # Enforce strict Pydantic output while retaining usage tokens
    structured_llm = llm.with_structured_output(LLMExtractedIntelligence, include_raw=True)

    system_prompt = (
        "You are an expert corporate intelligence analyst. Inspect the crawled website text and extract "
        "accurate intelligence. Do not guess; leave values null/empty if not present in the source."
    )
    user_prompt = (
        f"Analyze company domain '{state['domain']}' from this web context:\n\n{state['cleaned_context']}"
    )

    response = await structured_llm.ainvoke(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    )

    parsed: LLMExtractedIntelligence = response["parsed"]
    raw_msg = response["raw"]

    # Calculate token usage and cost
    usage = getattr(raw_msg, "usage_metadata", {}) or {}
    p_tokens = usage.get("input_tokens", 0)
    c_tokens = usage.get("output_tokens", 0)
    t_tokens = usage.get("total_tokens", 0)
    cost = (p_tokens / 1e6 * PRICE_PER_M_IN) + (c_tokens / 1e6 * PRICE_PER_M_OUT)

    # Regex safety fallback for contact emails
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    found_emails = set(re.findall(email_pattern, state["cleaned_context"]))
    valid_emails = [e for e in found_emails if not any(e.endswith(ext) for ext in [".png", ".jpg", ".webp"])]
    all_contacts = list(set(parsed.contact_points + valid_emails))
    parsed.contact_points = all_contacts

    return {
        "intelligence": parsed.model_dump(),
        "prompt_tokens": p_tokens,
        "completion_tokens": c_tokens,
        "total_tokens": t_tokens,
        "estimated_cost_usd": round(cost, 6),
        "status": "success",
    }


def should_search_linkedin(state: AgentState) -> Literal["search_node", "__end__"]:
    """Conditional edge router: trigger fallback search if a leader lacks a LinkedIn URL."""
    intelligence = state.get("intelligence")
    if state.get("status") == "failed" or not intelligence:
        return "__end__"

    leadership = intelligence.get("key_leadership", [])
    needs_search = any(
        isinstance(member, dict) and member.get("name") and not member.get("linkedin_url")
        for member in leadership
    )
    return "search_node" if needs_search else "__end__"


def search_node(state: AgentState) -> dict:
    intelligence = state.get("intelligence")
    # Early exit: narrows `intelligence` from `dict | None` to `dict`
    if not intelligence:
        return {}

    leadership = intelligence.get("key_leadership", [])
    domain_label = state["domain"].split(".")[0]

    for member in leadership:
        if isinstance(member, dict) and not member.get("linkedin_url") and member.get("name"):
            url = search_linkedin_fallback(member["name"], domain_label)
            if url:
                member["linkedin_url"] = url

    intelligence["key_leadership"] = leadership
    return {"intelligence": intelligence}


def build_lead_graph():
    builder = StateGraph(AgentState)

    builder.add_node("crawl_node", crawl_node)
    builder.add_node("clean_node", clean_node)
    builder.add_node("extract_node", extract_node)
    builder.add_node("search_node", search_node)

    builder.add_edge(START, "crawl_node")
    builder.add_edge("crawl_node", "clean_node")
    builder.add_edge("clean_node", "extract_node")
    builder.add_conditional_edges("extract_node", should_search_linkedin)
    builder.add_edge("search_node", END)

    return builder.compile()
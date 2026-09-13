import logging
import os
import re
from typing import Optional
import httpx

logger = logging.getLogger("SerperLinkedInSearch")


def clean_linkedin_url(url: str) -> Optional[str]:
    """Extracts and cleans public LinkedIn profile URLs."""
    if not url:
        return None
    match = re.search(r"(https?://[a-z]{2,3}\.linkedin\.com/in/[a-zA-Z0-9%_-]+)", url)
    return match.group(1).rstrip("/") if match else None


def search_linkedin_fallback(person_name: str, company: str) -> Optional[str]:
    """
    Uses Serper API (Google Search) to locate a founder or executive's LinkedIn profile.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        logger.warning("SERPER_API_KEY is not set in environment variables.")
        return None

    if not person_name:
        return None

    query = f'"{person_name}" "{company}" site:linkedin.com/in/'
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "num": 5,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Serper API error {response.status_code}: {response.text}")
                return None

            data = response.json()
            organic_results = data.get("organic", [])

            for item in organic_results:
                link = item.get("link", "")
                cleaned = clean_linkedin_url(link)
                if cleaned:
                    logger.info(f"Serper found LinkedIn profile for {person_name}: {cleaned}")
                    return cleaned

    except Exception as e:
        logger.error(f"Serper search failed for {person_name}: {str(e)}")

    logger.warning(f"Serper found no LinkedIn URL for {person_name}")
    return None
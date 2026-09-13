from typing import Dict, Set
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

SUBPAGE_KEYWORDS = ["about", "team", "company", "leadership", "contact", "pricing"]


async def crawl_site(domain: str, timeout_ms: int = 20000, max_subpages: int = 4) -> Dict[str, str]:
    pages: Dict[str, str] = {}
    base_url = f"https://{domain}" if not domain.startswith("http") else domain
    parsed_base = urlparse(base_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            # 1. Fetch Homepage
            await page.goto(base_url, timeout=timeout_ms, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            pages[base_url] = await page.content()

            # 2. Discover strategic internal subpages
            links: Set[str] = set()
            hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
            for href in hrefs:
                if not href:
                    continue
                full_url = urljoin(base_url, href).split("#")[0].rstrip("/")
                parsed_href = urlparse(full_url)
                if parsed_href.netloc == parsed_base.netloc:
                    if any(k in parsed_href.path.lower() for k in SUBPAGE_KEYWORDS):
                        links.add(full_url)

            # 3. Scrape discovered subpages
            for sub_url in list(links)[:max_subpages]:
                try:
                    sub_page = await context.new_page()
                    await sub_page.goto(sub_url, timeout=timeout_ms, wait_until="domcontentloaded")
                    await sub_page.wait_for_timeout(1000)
                    pages[sub_url] = await sub_page.content()
                    await sub_page.close()
                except Exception:
                    continue
        finally:
            await context.close()
            await browser.close()

    return pages
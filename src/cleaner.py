import re
from bs4 import BeautifulSoup
import html2text


def clean_html_to_markdown(html_content: str, max_chars: int = 12000) -> str:
    if not html_content or not html_content.strip():
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Remove non-informational and decorative elements
    for el in soup.find_all(["script", "style", "svg", "noscript", "iframe", "canvas", "meta", "link"]):
        el.decompose()

    # 2. Strip cookie/consent notices & banner clutter (Type-safe single pass)
    clutter_keywords = ("cookie", "banner", "modal", "popup", "advertisement")
    for tag in soup.find_all(True):
        classes = tag.get("class")
        if classes:
            class_str = " ".join(classes) if isinstance(classes, list) else str(classes)
            if any(kw in class_str.lower() for kw in clutter_keywords):
                tag.decompose()

    # 3. Convert to clean Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = False
    h.body_width = 0

    markdown = h.handle(str(soup))
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r" +", " ", markdown)

    return markdown[:max_chars].strip()
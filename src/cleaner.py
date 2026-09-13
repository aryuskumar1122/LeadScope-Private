import logging
from bs4 import BeautifulSoup, Comment
import html2text

logger = logging.getLogger("HTMLCleaner")

def clean_html_to_markdown(html_content: str) -> str:
    """
    Safely strips boilerplate, scripts, SVGs, and non-semantic elements from raw HTML 
    and converts the remainder into token-optimized Markdown.
    """
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 2. Decompose heavy or non-semantic boilerplate tags
        for unwanted in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg", "form", "link", "meta"]):
            unwanted.decompose()

        # 3. Safely iterate and clean tags (with NoneType guards)
        for tag in soup.find_all(True):
            if tag and hasattr(tag, "attrs") and tag.attrs:
                # Safely check classes or attributes without risking NoneType crashes
                classes = tag.get("class")
                if classes and isinstance(classes, list):
                    # Optional: remove hidden or tracking elements by class name
                    class_str = " ".join(classes).lower()
                    if any(term in class_str for term in ["cookie", "banner", "popup", "modal", "advertisement", "tracker"]):
                        tag.decompose()

        # 4. Convert cleaned HTML soup to Markdown
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.body_width = 0  # No line wrapping
        
        markdown_text = converter.handle(str(soup))
        return markdown_text

    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        # Fallback to basic text extraction if parsing fails entirely
        return BeautifulSoup(html_content, "html.parser").get_text(separator=" ", strip=True)
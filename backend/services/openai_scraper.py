"""OpenAI pricing page scraper using Playwright.

Scrapes https://platform.openai.com/docs/pricing to get accurate pricing data.
"""

import asyncio
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def _ensure_browsers_installed() -> bool:
    """Ensure Playwright browsers are installed. Returns True if successful."""
    try:
        # Check if chromium is already installed by trying to get the path
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # This will raise if browser not installed
            p.chromium.executable_path
        return True
    except Exception:
        pass

    # Try to install chromium
    logger.info("Installing Playwright chromium browser...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=settings.scraper_subprocess_timeout,
        )
        if result.returncode == 0:
            logger.info("Playwright chromium installed successfully")
            return True
        else:
            logger.error(f"Failed to install chromium: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to install chromium: {e}")
        return False


@dataclass
class ScrapedModel:
    """Raw model data scraped from OpenAI pricing page."""

    model_id: str
    model_name: str
    category: str  # e.g., "Language models", "Audio models"
    input_price: Optional[float] = None  # per 1M tokens
    output_price: Optional[float] = None
    cached_input_price: Optional[float] = None
    batch_input_price: Optional[float] = None
    batch_output_price: Optional[float] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None


def _parse_price(text: str) -> Optional[float]:
    """Parse price string like '$2.50' or '$0.075' to float."""
    if not text:
        return None
    text = text.strip()
    if text == "-" or text == "—" or text.lower() == "free" or not text:
        return None
    # Remove $ and commas, handle "per 1M tokens" suffix
    match = re.search(r"\$?([\d,.]+)", text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _parse_context_length(text: str) -> Optional[int]:
    """Parse context length like '128K' or '1,047,576' to int."""
    if not text:
        return None
    text = text.strip().upper().replace(",", "")
    # Handle "128K" format
    if "K" in text:
        match = re.search(r"([\d.]+)K", text)
        if match:
            return int(float(match.group(1)) * 1000)
    # Handle "1M" format
    if "M" in text:
        match = re.search(r"([\d.]+)M", text)
        if match:
            return int(float(match.group(1)) * 1000000)
    # Handle plain numbers
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def _normalize_model_id(name: str) -> str:
    """Convert model name to lowercase ID format."""
    # Remove special characters, lowercase, replace spaces with dashes
    model_id = name.lower().strip()
    model_id = re.sub(r"[^\w\s-]", "", model_id)
    model_id = re.sub(r"\s+", "-", model_id)
    return model_id


# Names that are NOT models but rather quality/size options or table headers
INVALID_MODEL_NAMES = {
    # Image quality/size options (DALL-E, GPT-Image)
    "low", "medium", "high", "hd", "standard",
    "small", "large", "xl", "xxl",
    "square", "portrait", "landscape",
    "1024x1024", "1024x1792", "1792x1024", "512x512", "256x256",
    # Table headers
    "model", "input", "output", "cached input", "context",
    "price", "pricing", "cost", "token", "tokens",
    "quality", "size", "resolution", "format",
}

# Keywords that indicate a feature/service description, not a model name
FEATURE_KEYWORDS = [
    "storage", "tool call", "api only", "responses api",
    "file search", "web search", "image upload", "file upload",
    "chatkit", "all models", "reasoning models", "non-reasoning",
    "data sharing", "with sharing", "including",
]


def _is_valid_model_name(name: str) -> bool:
    """Check if a name looks like a valid model name."""
    if not name:
        return False

    name_lower = name.lower().strip()

    # Reject if it's in the invalid names list
    if name_lower in INVALID_MODEL_NAMES:
        return False

    # Reject if too short (likely not a model name)
    if len(name_lower) < 2:
        return False

    # Reject if too long (model names are typically concise)
    if len(name_lower) > 50:
        return False

    # Reject if it contains feature/service keywords
    for keyword in FEATURE_KEYWORDS:
        if keyword in name_lower:
            return False

    # Reject if it contains footnote markers like [1], [2], etc.
    if re.search(r"\[\d+\]", name_lower):
        return False

    # Reject if it contains parentheses with long descriptions
    # (valid: "gpt-4 (deprecated)", invalid: "Web search (all models)")
    paren_match = re.search(r"\([^)]{15,}\)", name_lower)
    if paren_match:
        return False

    # Reject if it's just a number or dimension
    if re.match(r"^\d+x\d+$", name_lower):
        return False

    # Reject entries that look like concatenated text (missing space before "with")
    if re.search(r"\d{4}-\d{2}-\d{2}with", name_lower):
        return False

    # Model names typically start with a letter or number (for o1, o3, etc.)
    if not re.match(r"^[a-z0-9]", name_lower):
        return False

    # Valid model name patterns usually contain:
    # - Version numbers (gpt-4, gpt-3.5, o1)
    # - Known prefixes (gpt, claude, whisper, dall-e, tts, text-embedding)
    known_prefixes = [
        "gpt", "o1", "o3", "o4", "claude", "whisper", "dall-e", "tts",
        "text-embedding", "chatgpt", "davinci", "curie", "babbage", "ada",
        "codex", "omni", "computer-use",
    ]
    has_known_prefix = any(name_lower.startswith(prefix) for prefix in known_prefixes)

    # If no known prefix, at least require a version-like pattern (letter + number)
    has_version_pattern = bool(re.search(r"[a-z][-.]?\d|^\d+[.-]", name_lower))

    return has_known_prefix or has_version_pattern


async def scrape_openai_pricing() -> list[ScrapedModel]:
    """Scrape OpenAI pricing page using Playwright.

    Returns:
        List of ScrapedModel objects with pricing data (deduplicated, Standard tier preferred).

    Raises:
        Exception: If Playwright is not installed or scraping fails.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "Playwright is not installed. Run: uv add playwright && playwright install chromium"
        )

    # Ensure browser is installed (auto-install if needed)
    if not _ensure_browsers_installed():
        raise RuntimeError("Failed to install Playwright browser")

    all_models: list[ScrapedModel] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        logger.info(f"Navigating to {settings.openai_pricing_url}")
        await page.goto(
            settings.openai_pricing_url,
            wait_until="networkidle",
            timeout=settings.scraper_page_load_timeout,
        )

        # Wait for the page to fully load
        await page.wait_for_timeout(settings.scraper_wait_timeout)

        # First, parse the default "Standard" pricing that's visible on page load
        logger.info("Parsing default Standard pricing")
        all_models.extend(await _parse_pricing_tables(page, "Standard"))

        # Find pricing tier tabs (Batch, Flex, Standard, Priority)
        # We only want Standard tier for the main pricing
        tabs = await page.query_selector_all('[role="tab"], [data-radix-collection-item]')

        # Collect Batch pricing separately
        batch_pricing: dict[str, tuple[Optional[float], Optional[float]]] = {}
        for tab in tabs:
            tab_name = await tab.text_content()
            if not tab_name:
                continue
            tab_name = tab_name.strip()

            if tab_name == "Batch":
                try:
                    await tab.click()
                    await page.wait_for_timeout(1000)
                    logger.info("Parsing Batch pricing")
                    batch_models = await _parse_pricing_tables(page, "Batch")
                    for m in batch_models:
                        batch_pricing[m.model_id] = (m.input_price, m.output_price)
                except Exception as e:
                    logger.warning(f"Failed to parse Batch tab: {e}")
                break  # Only parse first Batch tab

        await browser.close()

    # Deduplicate models by model_id, keeping the one with most complete pricing
    model_map: dict[str, ScrapedModel] = {}
    for m in all_models:
        existing = model_map.get(m.model_id)
        if existing is None:
            model_map[m.model_id] = m
        else:
            # Prefer the one with both input and output prices
            existing_complete = (existing.input_price is not None and existing.output_price is not None)
            new_complete = (m.input_price is not None and m.output_price is not None)
            if new_complete and not existing_complete:
                model_map[m.model_id] = m

    # Add batch pricing to models
    for model_id, (batch_input, batch_output) in batch_pricing.items():
        if model_id in model_map:
            model_map[model_id].batch_input_price = batch_input
            model_map[model_id].batch_output_price = batch_output

    models = list(model_map.values())
    logger.info(f"Scraped {len(models)} unique models from OpenAI pricing page")
    return models


async def _parse_pricing_tables(page, category: str) -> list[ScrapedModel]:
    """Parse pricing tables from the current page state."""
    models: list[ScrapedModel] = []

    # Find all tables on the page
    tables = await page.query_selector_all("table")

    for table in tables:
        rows = await table.query_selector_all("tr")

        # Skip header row
        for row in rows[1:]:
            cells = await row.query_selector_all("td, th")
            if len(cells) < 2:
                continue

            cell_texts = []
            for cell in cells:
                text = await cell.text_content()
                cell_texts.append(text.strip() if text else "")

            if not cell_texts[0]:
                continue

            model_name = cell_texts[0]

            # Skip invalid model names (quality options, table headers, etc.)
            if not _is_valid_model_name(model_name):
                continue

            model_id = _normalize_model_id(model_name)

            model = ScrapedModel(
                model_id=model_id,
                model_name=model_name,
                category=category,
            )

            # Parse prices based on column count
            # Common formats:
            # [Model, Input, Output]
            # [Model, Input, Cached Input, Output]
            # [Model, Input, Output, Context]
            if len(cell_texts) >= 3:
                model.input_price = _parse_price(cell_texts[1])
                model.output_price = _parse_price(cell_texts[2])
            if len(cell_texts) >= 4:
                # Check if 3rd column is cached input or context
                text = cell_texts[2].lower()
                if "cached" in text or _parse_price(cell_texts[2]) is not None:
                    model.cached_input_price = _parse_price(cell_texts[2])
                    model.output_price = _parse_price(cell_texts[3])
                else:
                    model.context_length = _parse_context_length(cell_texts[3])
            if len(cell_texts) >= 5:
                model.context_length = _parse_context_length(cell_texts[4])

            models.append(model)

    # Also try to find pricing in non-table formats (cards, lists)
    # OpenAI sometimes uses card-based layouts
    cards = await page.query_selector_all('[class*="pricing"], [class*="model"]')
    for card in cards:
        text = await card.text_content()
        if not text or "$" not in text:
            continue

        # Try to extract model name and prices from card text
        lines = text.strip().split("\n")
        if len(lines) >= 2:
            model_name = lines[0].strip()
            if len(model_name) > 50 or not _is_valid_model_name(model_name):
                continue

            model_id = _normalize_model_id(model_name)

            # Check if we already have this model
            if any(m.model_id == model_id for m in models):
                continue

            model = ScrapedModel(
                model_id=model_id,
                model_name=model_name,
                category=category,
            )

            # Try to find prices in the remaining text
            for line in lines[1:]:
                if "input" in line.lower():
                    model.input_price = _parse_price(line)
                elif "output" in line.lower():
                    model.output_price = _parse_price(line)
                elif "cached" in line.lower():
                    model.cached_input_price = _parse_price(line)

            if model.input_price is not None or model.output_price is not None:
                models.append(model)

    return models


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    async def main():
        models = await scrape_openai_pricing()
        for m in models:
            print(f"{m.model_name}: input=${m.input_price}, output=${m.output_price}")

    asyncio.run(main())

"""Google Gemini API pricing page scraper using Playwright.

Scrapes https://ai.google.dev/pricing to get accurate pricing data.
This source has more complete model coverage than Vertex AI pricing page.
"""

import asyncio
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def _ensure_browsers_installed() -> bool:
    """Ensure Playwright browsers are installed. Returns True if successful."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.executable_path
        return True
    except Exception:
        pass

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
class ScrapedGoogleModel:
    """Raw model data scraped from Google Gemini API pricing page."""

    model_id: str
    model_name: str
    category: str  # e.g., "Gemini 3", "Gemini 2.5", "Imagen", "Veo"

    # Token-based pricing (per 1M tokens) - Paid tier
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    cached_input_price: Optional[float] = None

    # Batch pricing (per 1M tokens)
    batch_input_price: Optional[float] = None
    batch_output_price: Optional[float] = None

    # Audio pricing (per 1M tokens)
    audio_input_price: Optional[float] = None
    audio_output_price: Optional[float] = None

    # Image pricing
    image_input_price: Optional[float] = None  # per 1M tokens or per image
    image_output_price: Optional[float] = None  # per 1M tokens or per image

    # Video pricing (per second)
    video_price_per_second: Optional[float] = None

    # Context info
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None

    # Capabilities
    capabilities: list[str] = field(default_factory=lambda: ["text"])

    # Free tier available
    has_free_tier: bool = False


def _parse_price(text: str) -> Optional[float]:
    """Parse price string like '$2.50' or '$0.075' to float."""
    if not text:
        return None
    text = text.strip()
    if text == "-" or text == "—" or text.lower() == "free" or text.lower() == "n/a" or not text:
        return None
    if text.lower() == "free":
        return 0.0
    match = re.search(r"\$?([\d,.]+)", text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _normalize_model_id(name: str) -> str:
    """Convert model name to lowercase ID format."""
    model_id = name.strip()

    # Remove parenthetical notes like "(Preview)" but track it
    preview_match = re.search(r"\((Preview|Deprecated)\)", model_id, re.IGNORECASE)
    has_preview = preview_match is not None
    model_id = re.sub(r"\s*\([^)]*\)\s*", "", model_id)

    # Normalize to lowercase
    model_id = model_id.lower()

    # Remove special characters except spaces, dots, and dashes
    model_id = re.sub(r"[^\w\s.-]", "", model_id)

    # Collapse multiple spaces
    model_id = re.sub(r"\s+", " ", model_id).strip()

    # Replace spaces with dashes
    model_id = model_id.replace(" ", "-")

    # Collapse multiple dashes
    model_id = re.sub(r"-+", "-", model_id)

    # Add preview suffix if it was in parentheses and not already there
    if has_preview and not model_id.endswith("-preview"):
        model_id += "-preview"

    return model_id


def _detect_capabilities(model_name: str, category: str) -> list[str]:
    """Detect model capabilities from name and category."""
    name_lower = model_name.lower()

    capabilities = []

    # Check for specific model types (early return for specialized models)
    if "embedding" in name_lower:
        capabilities.append("embedding")
        return capabilities

    if "imagen" in name_lower:
        capabilities.append("image_generation")
        return capabilities

    if "veo" in name_lower:
        capabilities.append("video_generation")
        return capabilities

    if "gemma" in name_lower:
        # Gemma models: text only (some newer versions may have vision, but default to text)
        capabilities.append("text")
        return capabilities

    # Default: text capability
    capabilities.append("text")

    # Gemini models
    if "gemini" in name_lower:
        # All Gemini models have vision
        capabilities.append("vision")

        # Check for special model variants first
        is_image_model = "image" in name_lower
        is_tts_model = "tts" in name_lower
        is_lite_model = "lite" in name_lower

        # Image generation for image-preview models
        if is_image_model:
            capabilities.append("image_generation")

        # TTS models have audio output capability
        if is_tts_model:
            capabilities.append("tts")

        # Audio input support for most Gemini models
        # Excluded: lite models, image generation models, TTS models
        if "flash" in name_lower or "pro" in name_lower:
            if not is_lite_model and not is_image_model and not is_tts_model:
                capabilities.append("audio")

        # Reasoning capability for Gemini 2.5 Pro and Flash (not lite, not image)
        if "2.5" in name_lower or "2-5" in name_lower:
            if ("pro" in name_lower or "flash" in name_lower) and not is_lite_model and not is_image_model:
                capabilities.append("reasoning")

        # Computer use
        if "computer" in name_lower:
            capabilities.append("computer_use")

        # Tool use - all Gemini chat models support function calling
        if not is_tts_model:
            capabilities.append("tool_use")

    return capabilities


# Known model prefixes to include
KNOWN_MODEL_PREFIXES = [
    "gemini", "imagen", "veo", "gemma", "embedding",
]

# Patterns to exclude (not actual models)
EXCLUDE_PATTERNS = [
    r"^(input|output|cached|batch)",
    r"^(price|pricing|cost|per|usd|\$)",
    r"^(text|audio|video|image)\s*(input|output)",
    r"^(free|paid)\s*tier",
    r"^\d+[mk]?\s*(input|output|token)",
]


def _is_valid_model_name(name: str) -> bool:
    """Check if a name looks like a valid Google model name."""
    if not name:
        return False

    name_lower = name.lower().strip()

    # Too short or too long
    if len(name_lower) < 4 or len(name_lower) > 80:
        return False

    # Check against exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, name_lower):
            return False

    # Must have a known prefix
    has_known_prefix = any(name_lower.startswith(prefix) for prefix in KNOWN_MODEL_PREFIXES)

    return has_known_prefix


async def scrape_gemini_api_pricing() -> list[ScrapedGoogleModel]:
    """Scrape Google Gemini API pricing page using Playwright.

    Returns:
        List of ScrapedGoogleModel objects with pricing data.

    Raises:
        Exception: If Playwright is not installed or scraping fails.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "Playwright is not installed. Run: uv add playwright && playwright install chromium"
        )

    if not _ensure_browsers_installed():
        raise RuntimeError("Failed to install Playwright browser")

    all_models: list[ScrapedGoogleModel] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        logger.info(f"Navigating to {settings.gemini_pricing_url}")
        await page.goto(settings.gemini_pricing_url, wait_until="networkidle", timeout=settings.scraper_page_load_timeout)

        # Wait for the page to fully load
        await page.wait_for_timeout(settings.gemini_scraper_wait_timeout)

        # Parse all pricing tables
        all_models = await _parse_pricing_page(page)

        await browser.close()

    # Deduplicate by model_id, preferring more complete entries
    model_map: dict[str, ScrapedGoogleModel] = {}
    for m in all_models:
        existing = model_map.get(m.model_id)
        if existing is None:
            model_map[m.model_id] = m
        else:
            # Prefer the one with more complete pricing
            existing_score = sum([
                existing.input_price is not None,
                existing.output_price is not None,
                existing.cached_input_price is not None,
                existing.batch_input_price is not None,
            ])
            new_score = sum([
                m.input_price is not None,
                m.output_price is not None,
                m.cached_input_price is not None,
                m.batch_input_price is not None,
            ])
            if new_score > existing_score:
                model_map[m.model_id] = m

    models = list(model_map.values())
    logger.info(f"Scraped {len(models)} unique models from Gemini API pricing page")
    return models


async def _parse_pricing_page(page) -> list[ScrapedGoogleModel]:
    """Parse pricing data from the page."""
    models: list[ScrapedGoogleModel] = []

    # Extract model sections with their pricing tables using JavaScript
    sections_data = await page.evaluate("""
        () => {
            const results = [];

            // Find all pricing tables
            const tables = document.querySelectorAll('table.pricing-table, table');

            for (const table of tables) {
                // Try to find the model name from preceding headers
                let modelName = '';
                let category = '';

                // Walk up to find section context
                let el = table;
                for (let i = 0; i < 10 && el; i++) {
                    el = el.previousElementSibling || el.parentElement;
                    if (!el) break;

                    // Check for h2, h3, h4 headers
                    const tag = el.tagName?.toLowerCase();
                    if (tag === 'h2' || tag === 'h3' || tag === 'h4') {
                        if (!modelName) modelName = el.textContent.trim();
                        if (tag === 'h2') category = el.textContent.trim();
                    }

                    // Also check for headers within the element
                    const headers = el.querySelectorAll?.('h2, h3, h4');
                    if (headers) {
                        for (const h of headers) {
                            const text = h.textContent.trim();
                            if (!modelName && text) modelName = text;
                            if (h.tagName.toLowerCase() === 'h2') category = text;
                        }
                    }
                }

                // Get table type (Standard or Batch) from nearby text
                let tableType = 'standard';
                const prevEl = table.previousElementSibling;
                if (prevEl) {
                    const prevText = prevEl.textContent?.toLowerCase() || '';
                    if (prevText.includes('batch')) tableType = 'batch';
                }

                // Extract headers
                const headerCells = table.querySelectorAll('thead th, tr:first-child th');
                const headers = Array.from(headerCells).map(h => h.textContent.trim());

                // Extract rows
                const rows = [];
                const bodyRows = table.querySelectorAll('tbody tr, tr:not(:first-child)');
                for (const row of bodyRows) {
                    // Skip if this is actually a header row
                    if (row.querySelectorAll('th').length > 1) continue;

                    const cells = row.querySelectorAll('td, th');
                    const cellData = Array.from(cells).map(c => c.textContent.trim());
                    if (cellData.length > 0 && cellData.some(c => c)) {
                        rows.push(cellData);
                    }
                }

                if (rows.length > 0 && modelName) {
                    results.push({
                        modelName,
                        category: category || modelName,
                        tableType,
                        headers,
                        rows
                    });
                }
            }

            return results;
        }
    """)

    logger.info(f"Found {len(sections_data)} pricing sections")

    # Group sections by model name
    model_sections: dict[str, list] = {}
    for section in sections_data:
        model_name = section.get("modelName", "")
        if not model_name or not _is_valid_model_name(model_name):
            continue

        if model_name not in model_sections:
            model_sections[model_name] = []
        model_sections[model_name].append(section)

    # Process each model
    for model_name, sections in model_sections.items():
        model = _parse_model_sections(model_name, sections)
        if model:
            models.append(model)

    return models


def _parse_model_sections(model_name: str, sections: list) -> Optional[ScrapedGoogleModel]:
    """Parse all sections for a single model."""
    model_id = _normalize_model_id(model_name)
    category = sections[0].get("category", "") if sections else ""
    capabilities = _detect_capabilities(model_name, category)

    model = ScrapedGoogleModel(
        model_id=model_id,
        model_name=model_name,
        category=category,
        capabilities=capabilities,
    )

    for section in sections:
        table_type = section.get("tableType", "standard")
        headers = section.get("headers", [])
        rows = section.get("rows", [])

        # Find price column indices (usually "Free Tier" and "Paid Tier")
        free_col = -1
        paid_col = -1
        for i, h in enumerate(headers):
            h_lower = h.lower()
            if "free" in h_lower:
                free_col = i
            elif "paid" in h_lower:
                paid_col = i

        # If no explicit tier columns, assume last columns are prices
        if paid_col == -1 and len(headers) >= 2:
            paid_col = len(headers) - 1

        for row in rows:
            if not row:
                continue

            feature = row[0].lower() if row else ""

            # Get paid tier price (what we care about)
            price = None
            if paid_col > 0 and paid_col < len(row):
                price = _parse_price(row[paid_col])
            elif len(row) >= 2:
                # Try last column
                price = _parse_price(row[-1])

            if price is None:
                continue

            # Check for free tier
            if free_col > 0 and free_col < len(row):
                free_price = row[free_col].lower()
                if "free" in free_price or free_price == "0" or free_price == "$0":
                    model.has_free_tier = True

            # Map feature to price field
            if table_type == "batch":
                if "input" in feature:
                    model.batch_input_price = price
                elif "output" in feature:
                    model.batch_output_price = price
            else:
                # Standard pricing
                if "cached" in feature and "input" in feature:
                    model.cached_input_price = price
                elif "audio" in feature and "input" in feature:
                    model.audio_input_price = price
                elif "audio" in feature and "output" in feature:
                    model.audio_output_price = price
                elif "image" in feature and "input" in feature:
                    model.image_input_price = price
                elif "image" in feature and "output" in feature:
                    model.image_output_price = price
                elif "video" in feature:
                    model.video_price_per_second = price
                elif "input" in feature and model.input_price is None:
                    model.input_price = price
                elif "output" in feature and model.output_price is None:
                    model.output_price = price

    # Special handling for image/video generation models
    if "image_generation" in capabilities and model.image_output_price:
        if model.output_price is None:
            model.output_price = model.image_output_price

    if "video_generation" in capabilities and model.video_price_per_second:
        if model.output_price is None:
            model.output_price = model.video_price_per_second

    return model


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    async def main():
        models = await scrape_gemini_api_pricing()
        print(f"\nScraped {len(models)} models:\n")
        for m in sorted(models, key=lambda x: x.model_id):
            print(f"{m.model_name} ({m.model_id})")
            print(f"  Capabilities: {m.capabilities}")
            if m.input_price is not None:
                print(f"  Input: ${m.input_price}/1M tokens")
            if m.output_price is not None:
                print(f"  Output: ${m.output_price}/1M tokens")
            if m.cached_input_price is not None:
                print(f"  Cached: ${m.cached_input_price}/1M tokens")
            if m.batch_input_price is not None:
                print(f"  Batch: in=${m.batch_input_price}, out=${m.batch_output_price}")
            if m.has_free_tier:
                print(f"  Free tier: Yes")
            print()

    asyncio.run(main())

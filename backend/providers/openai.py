"""OpenAI pricing provider.

Uses Playwright to scrape official pricing from https://platform.openai.com/docs/pricing
Falls back to static data if scraping fails.
"""

import logging
from datetime import datetime
from typing import List, Optional

from models import ModelPricing, Pricing, BatchPricing
from .base import BaseProvider, detect_modalities
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)


def _detect_scraped_capabilities(model_id: str, model_name: str, category: str) -> List[str]:
    """Detect capabilities for scraped OpenAI models.

    This ensures proper multi-tag capabilities based on model type.
    Based on official documentation and third-party verification (artificialanalysis.ai).
    """
    cat_lower = category.lower()
    id_lower = model_id.lower()

    # Image generation models - no text capability
    if "image" in cat_lower or "dall-e" in id_lower or "gpt-image" in id_lower:
        return ["image_generation"]

    # Embedding models - no text capability
    if "embedding" in cat_lower or "embed" in id_lower:
        return ["embedding"]

    # Pure transcription/whisper - audio only
    if "transcribe" in id_lower or "whisper" in id_lower:
        return ["audio"]

    # TTS models - audio output only
    if "tts" in id_lower:
        return ["tts"]

    # Moderation models
    if "moderation" in id_lower:
        return ["moderation"]

    # Start with text as base for all other models
    capabilities = ["text"]

    # Audio capability - check for audio/realtime/speech models
    if "audio" in cat_lower or "speech" in cat_lower or "realtime" in id_lower:
        capabilities.append("audio")

    # Vision capability - based on official OpenAI documentation
    if "vision" in cat_lower or "media" in cat_lower:
        capabilities.append("vision")
    else:
        # Models with CONFIRMED vision capability:
        # - GPT-4o (all variants except realtime/audio-only)
        # - GPT-4.1 (all variants)
        # - GPT-4.5
        # - GPT-5 (all variants except nano/codex)
        # - O3, O4-mini (first reasoning models with "think with images")
        # - O1 (has vision but limited)
        # Vision NOT available: O1-mini, O1-pro, O3-mini, GPT-5-nano, GPT-5-codex
        vision_models = ["gpt-4o", "gpt-4.1", "gpt-4.5", "gpt-5", "o3", "o4-mini", "o1"]
        no_vision = ["realtime", "audio", "o1-mini", "o1-pro", "o3-mini", "gpt-5-nano", "gpt-5-codex", "5.1-codex", "5-codex"]
        if any(x in id_lower for x in vision_models):
            if not any(x in id_lower for x in no_vision):
                capabilities.append("vision")

    # Reasoning capability - models with chain-of-thought or extended thinking
    # O-series: All are reasoning models
    # GPT-5 series: All have reasoning capability (trained on reasoning data)
    # GPT-4.1, GPT-4o, etc: NOT reasoning models (fast response, no thinking)
    reasoning_models = ["o1", "o3", "o4", "gpt-5"]
    if any(x in id_lower for x in reasoning_models):
        capabilities.append("reasoning")

    # Tool use capability - based on official OpenAI documentation
    # O3, O4-mini: Full tool use (web, code, files, images)
    # O1: Has tool use capability
    # O1-mini, O1-pro, O3-mini: Limited or NO tool use
    # GPT-5, GPT-4.x, GPT-3.5: Full tool use
    tool_use_models = ["gpt-5", "gpt-4", "gpt-3.5", "chatgpt", "o3", "o4", "o1"]
    no_tool_use = ["o1-mini", "o1-pro", "o3-mini", "transcribe", "whisper", "tts", "embed"]

    if any(x in id_lower for x in tool_use_models):
        if not any(x in id_lower for x in no_tool_use):
            capabilities.append("tool_use")

    # Web search
    if "search" in id_lower:
        capabilities.append("web_search")

    # Computer use
    if "computer" in id_lower:
        capabilities.append("computer_use")

    return capabilities


async def _fetch_from_scraper() -> Optional[List[dict]]:
    """Try to fetch pricing data using Playwright scraper."""
    try:
        from services.openai_scraper import scrape_openai_pricing

        scraped = await scrape_openai_pricing()
        if not scraped:
            logger.warning("Scraper returned no models")
            return None

        # Convert ScrapedModel to dict format
        models = []
        for m in scraped:
            # Determine capabilities based on category and model name
            capabilities = _detect_scraped_capabilities(m.model_id, m.model_name, m.category)

            pricing_dict: dict = {}
            if m.input_price is not None:
                pricing_dict["input"] = m.input_price
            if m.output_price is not None:
                pricing_dict["output"] = m.output_price
            if m.cached_input_price is not None:
                pricing_dict["cached_input"] = m.cached_input_price

            batch_dict: Optional[dict] = None
            if m.batch_input_price is not None or m.batch_output_price is not None:
                batch_dict = {}
                if m.batch_input_price is not None:
                    batch_dict["input"] = m.batch_input_price
                if m.batch_output_price is not None:
                    batch_dict["output"] = m.batch_output_price

            model_data: dict = {
                "model_id": m.model_id,
                "model_name": m.model_name,
                "pricing": pricing_dict,
                "capabilities": capabilities,
            }

            if m.context_length:
                model_data["context_length"] = m.context_length
            if m.max_output_tokens:
                model_data["max_output_tokens"] = m.max_output_tokens
            if batch_dict:
                model_data["batch_pricing"] = batch_dict

            models.append(model_data)

        logger.info(f"Scraper returned {len(models)} models")
        return models

    except ImportError as e:
        logger.warning(f"Playwright not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return None

class OpenAIProvider(BaseProvider):
    """Provider for OpenAI pricing data.

    Tries to scrape official pricing page using Playwright.
    Falls back to static data if scraping fails.
    """

    name = "openai"
    display_name = "OpenAI"

    async def fetch(self) -> List[ModelPricing]:
        """Fetch OpenAI pricing - try scraper first, fallback to static data."""
        # Try scraping first
        scraped_models = await _fetch_from_scraper()

        if scraped_models:
            # Convert scraped data to ModelPricing
            models: List[ModelPricing] = []
            now = datetime.now()

            for model_data in scraped_models:
                model_id = model_data["model_id"]
                full_id = f"{self.name}:{model_id}"

                # Build Pricing object
                pricing_data = model_data.get("pricing", {})
                pricing = Pricing(
                    input=pricing_data.get("input"),
                    output=pricing_data.get("output"),
                    cached_input=pricing_data.get("cached_input"),
                    cached_write=pricing_data.get("cached_write"),
                    audio_input=pricing_data.get("audio_input"),
                    audio_output=pricing_data.get("audio_output"),
                    embedding=pricing_data.get("embedding"),
                )

                # Build BatchPricing if present
                batch_data = model_data.get("batch_pricing")
                batch_pricing = None
                if batch_data:
                    batch_pricing = BatchPricing(
                        input=batch_data.get("input"),
                        output=batch_data.get("output"),
                    )

                # Detect input/output modalities from capabilities
                capabilities = model_data.get("capabilities", ["text"])
                input_mods, output_mods = detect_modalities(capabilities, model_data["model_name"])

                model = ModelPricing(
                    id=full_id,
                    provider=self.name,
                    model_id=model_id,
                    model_name=model_data["model_name"],
                    pricing=pricing,
                    batch_pricing=batch_pricing,
                    context_length=model_data.get("context_length"),
                    max_output_tokens=model_data.get("max_output_tokens"),
                    is_open_source=model_data.get("is_open_source"),
                    capabilities=capabilities,
                    input_modalities=input_mods,
                    output_modalities=output_mods,
                    last_updated=now,
                )
                models.append(model)

            logger.info(f"OpenAI: returning {len(models)} models (scraped data)")
            return models

        # Fall back to static data from JSON
        logger.info("Using static fallback data for OpenAI")
        return self.load_fallback_data()


# Register provider
ProviderRegistry.register(OpenAIProvider())

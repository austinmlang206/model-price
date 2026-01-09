"""Google Gemini API pricing provider.

Sources pricing data by scraping Google's Gemini API pricing page.
This source has more complete model coverage than Vertex AI.

Reference: https://ai.google.dev/pricing
"""

import logging
from datetime import datetime
from typing import List, Optional

from models import ModelPricing, Pricing, BatchPricing
from .base import BaseProvider, detect_modalities
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)


async def _fetch_from_scraper() -> Optional[List["ModelPricing"]]:
    """Attempt to fetch pricing data from the web scraper."""
    try:
        from services.google_gemini_scraper import scrape_gemini_api_pricing

        scraped_models = await scrape_gemini_api_pricing()
        if not scraped_models:
            return None

        models: List[ModelPricing] = []
        now = datetime.now()

        for scraped in scraped_models:
            # Build Pricing object from scraped data
            pricing = Pricing(
                input=scraped.input_price,
                output=scraped.output_price,
                cached_input=scraped.cached_input_price,
                audio_input=scraped.audio_input_price,
            )

            # Build BatchPricing if present
            batch_pricing = None
            if scraped.batch_input_price is not None or scraped.batch_output_price is not None:
                batch_pricing = BatchPricing(
                    input=scraped.batch_input_price,
                    output=scraped.batch_output_price,
                )

            # Special handling for image/video generation models
            if scraped.image_output_price is not None and "image_generation" in scraped.capabilities:
                if pricing.output is None:
                    pricing.output = scraped.image_output_price

            if scraped.video_price_per_second is not None and "video_generation" in scraped.capabilities:
                if pricing.output is None:
                    pricing.output = scraped.video_price_per_second

            # Detect input/output modalities from capabilities
            input_mods, output_mods = detect_modalities(scraped.capabilities, scraped.model_name)

            model = ModelPricing(
                id=f"google_gemini:{scraped.model_id}",
                provider="google_gemini",
                model_id=scraped.model_id,
                model_name=scraped.model_name,
                pricing=pricing,
                batch_pricing=batch_pricing,
                context_length=scraped.context_length,
                max_output_tokens=scraped.max_output_tokens,
                is_open_source="gemma" in scraped.model_id.lower(),
                capabilities=scraped.capabilities,
                input_modalities=input_mods,
                output_modalities=output_mods,
                last_updated=now,
            )
            models.append(model)

        logger.info(f"Google Gemini: scraped {len(models)} models from pricing page")
        return models

    except ImportError as e:
        logger.warning(f"Scraper not available (missing dependency): {e}")
        return None
    except Exception as e:
        logger.warning(f"Scraper failed, falling back to static data: {e}")
        return None


class GoogleGeminiProvider(BaseProvider):
    """Provider for Google Gemini API pricing data.

    Attempts to scrape pricing from Google's Gemini API pricing page.
    Falls back to static data if scraping fails.
    """

    name = "google_gemini"
    display_name = "Google Gemini"

    async def fetch(self) -> List[ModelPricing]:
        """Fetch Google Gemini pricing, preferring scraped data."""
        # Try to scrape fresh data first
        scraped_models = await _fetch_from_scraper()
        if scraped_models:
            return scraped_models

        # Fall back to static data from JSON
        logger.info("Using static fallback data for Google Gemini")
        return self.load_fallback_data()


# Register provider
ProviderRegistry.register(GoogleGeminiProvider())

"""xAI (Grok) pricing provider.

Sources pricing data from xAI's documentation.
Since xAI doesn't provide a public pricing API, this uses static data
that should be updated periodically.

Reference: https://docs.x.ai/docs/models
"""

import logging
from typing import List

from models import ModelPricing
from .base import BaseProvider
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)


class XAIProvider(BaseProvider):
    """Provider for xAI (Grok) pricing data.

    Uses static pricing data from xAI documentation.
    xAI does not provide a public pricing API.
    """

    name = "xai"
    display_name = "xAI"

    async def fetch(self) -> List[ModelPricing]:
        """Fetch xAI pricing from static fallback data."""
        return self.load_fallback_data()


# Register provider
ProviderRegistry.register(XAIProvider())

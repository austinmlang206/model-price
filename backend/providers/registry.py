"""Provider registry for managing multiple pricing sources."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .base import BaseProvider
from models import ModelPricing

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for all pricing providers."""

    _providers: Dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, provider: BaseProvider) -> None:
        """Register a provider instance."""
        cls._providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name}")

    @classmethod
    def get(cls, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def all(cls) -> List[BaseProvider]:
        """Get all registered providers."""
        return list(cls._providers.values())

    @classmethod
    async def fetch_all(cls) -> List[ModelPricing]:
        """Fetch from all providers concurrently.

        Failed providers are logged but don't stop other fetches.
        """
        if not cls._providers:
            logger.warning("No providers registered")
            return []

        tasks = [p.fetch() for p in cls._providers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_models: List[ModelPricing] = []
        for provider, result in zip(cls._providers.values(), results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.name} failed: {result}")
            else:
                logger.info(f"Provider {provider.name}: fetched {len(result)} models")
                all_models.extend(result)

        return all_models

    @classmethod
    async def fetch_provider(cls, name: str) -> List[ModelPricing]:
        """Fetch from a single provider."""
        provider = cls.get(name)
        if not provider:
            raise ValueError(f"Unknown provider: {name}")
        return await provider.fetch()

    @classmethod
    async def fetch_all_grouped(cls) -> Dict[str, List[ModelPricing]]:
        """Fetch from all providers concurrently, returning results grouped by provider.

        Returns a dict mapping provider name to list of models.
        Failed providers are logged but don't stop other fetches.
        """
        if not cls._providers:
            logger.warning("No providers registered")
            return {}

        tasks = [p.fetch() for p in cls._providers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        grouped: Dict[str, List[ModelPricing]] = {}
        for provider, result in zip(cls._providers.values(), results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.name} failed: {result}")
            else:
                logger.info(f"Provider {provider.name}: fetched {len(result)} models")
                grouped[provider.name] = result

        return grouped

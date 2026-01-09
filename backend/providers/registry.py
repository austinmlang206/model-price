"""Provider registry for managing multiple pricing sources."""

import asyncio
import logging
from datetime import datetime

from .base import BaseProvider
from models import ModelPricing

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for all pricing providers."""

    _providers: dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, provider: BaseProvider) -> None:
        """Register a provider instance."""
        cls._providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name}")

    @classmethod
    def get(cls, name: str) -> BaseProvider | None:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def all(cls) -> list[BaseProvider]:
        """Get all registered providers."""
        return list(cls._providers.values())

    @classmethod
    async def fetch_all(cls) -> list[ModelPricing]:
        """Fetch from all providers concurrently.

        Failed providers are logged but don't stop other fetches.
        """
        if not cls._providers:
            logger.warning("No providers registered")
            return []

        tasks = [p.fetch() for p in cls._providers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_models: list[ModelPricing] = []
        for provider, result in zip(cls._providers.values(), results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.name} failed: {result}")
            else:
                logger.info(f"Provider {provider.name}: fetched {len(result)} models")
                all_models.extend(result)

        return all_models

    @classmethod
    async def fetch_provider(cls, name: str) -> list[ModelPricing]:
        """Fetch from a single provider."""
        provider = cls.get(name)
        if not provider:
            raise ValueError(f"Unknown provider: {name}")
        return await provider.fetch()

"""Abstract base class for pricing providers."""

from abc import ABC, abstractmethod

from models import ModelPricing


class BaseProvider(ABC):
    """Base class for all pricing data providers."""

    name: str  # e.g., "aws_bedrock"
    display_name: str  # e.g., "AWS Bedrock"

    @abstractmethod
    async def fetch(self) -> list[ModelPricing]:
        """Fetch all model prices from this provider.

        Returns:
            List of ModelPricing objects.

        Raises:
            Exception: If fetching fails.
        """
        pass

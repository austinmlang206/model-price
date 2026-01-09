"""Pricing data service for CRUD and query operations."""

import json
import logging
from datetime import datetime
from pathlib import Path

from models import ModelPricing, PricingDatabase, ProviderInfo

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "pricing.json"


class PricingService:
    """Service for managing pricing data."""

    @classmethod
    def _ensure_data_dir(cls) -> None:
        """Ensure data directory exists."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_database(cls) -> PricingDatabase:
        """Load database from JSON file."""
        cls._ensure_data_dir()
        if not DATA_FILE.exists():
            return PricingDatabase(last_refresh=datetime.now(), models=[])

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PricingDatabase.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            return PricingDatabase(last_refresh=datetime.now(), models=[])

    @classmethod
    def _save_database(cls, db: PricingDatabase) -> None:
        """Save database to JSON file atomically."""
        cls._ensure_data_dir()
        temp_file = DATA_FILE.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(db.model_dump_json(indent=2))

        temp_file.replace(DATA_FILE)
        logger.info(f"Saved {len(db.models)} models to {DATA_FILE}")

    @classmethod
    def get_all(
        cls,
        provider: str | None = None,
        capability: str | None = None,
        search: str | None = None,
        sort_by: str = "model_name",
        sort_order: str = "asc",
    ) -> list[ModelPricing]:
        """Get all models with optional filters and sorting."""
        db = cls._load_database()
        models = db.models

        # Filter by provider
        if provider:
            models = [m for m in models if m.provider == provider]

        # Filter by capability
        if capability:
            models = [m for m in models if capability in m.capabilities]

        # Search by model name
        if search:
            search_lower = search.lower()
            models = [m for m in models if search_lower in m.model_name.lower()]

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "model_name":
            models.sort(key=lambda m: m.model_name.lower(), reverse=reverse)
        elif sort_by == "input":
            models.sort(key=lambda m: m.pricing.input or 0, reverse=reverse)
        elif sort_by == "output":
            models.sort(key=lambda m: m.pricing.output or 0, reverse=reverse)
        elif sort_by == "context_length":
            models.sort(key=lambda m: m.context_length or 0, reverse=reverse)

        return models

    @classmethod
    def get_by_id(cls, model_id: str) -> ModelPricing | None:
        """Get a single model by ID."""
        db = cls._load_database()
        for model in db.models:
            if model.id == model_id:
                return model
        return None

    @classmethod
    def get_providers(cls) -> list[ProviderInfo]:
        """Get list of all providers with stats."""
        db = cls._load_database()
        provider_stats: dict[str, dict] = {}

        for model in db.models:
            if model.provider not in provider_stats:
                provider_stats[model.provider] = {
                    "count": 0,
                    "last_updated": model.last_updated,
                }
            provider_stats[model.provider]["count"] += 1
            if model.last_updated > provider_stats[model.provider]["last_updated"]:
                provider_stats[model.provider]["last_updated"] = model.last_updated

        # Map provider names to display names
        display_names = {
            "aws_bedrock": "AWS Bedrock",
            "openai": "OpenAI",
            "azure": "Azure OpenAI",
            "google": "Google",
            "openrouter": "OpenRouter",
            "anthropic": "Anthropic",
            "xai": "xAI",
        }

        return [
            ProviderInfo(
                name=name,
                display_name=display_names.get(name, name),
                model_count=stats["count"],
                last_updated=stats["last_updated"],
            )
            for name, stats in sorted(provider_stats.items())
        ]

    @classmethod
    def save_models(cls, models: list[ModelPricing]) -> None:
        """Save models to database (full replace)."""
        db = PricingDatabase(
            last_refresh=datetime.now(),
            models=models,
        )
        cls._save_database(db)

    @classmethod
    def update_provider(cls, provider_name: str, models: list[ModelPricing]) -> None:
        """Update models for a single provider (keep others)."""
        db = cls._load_database()

        # Remove old models from this provider
        other_models = [m for m in db.models if m.provider != provider_name]

        # Add new models
        db.models = other_models + models
        db.last_refresh = datetime.now()

        cls._save_database(db)

    @classmethod
    def get_stats(cls) -> dict:
        """Get overall statistics."""
        db = cls._load_database()
        models = db.models

        if not models:
            return {
                "total_models": 0,
                "providers": 0,
                "avg_input_price": 0,
                "avg_output_price": 0,
                "last_refresh": db.last_refresh.isoformat(),
            }

        input_prices = [m.pricing.input for m in models if m.pricing.input is not None]
        output_prices = [m.pricing.output for m in models if m.pricing.output is not None]

        return {
            "total_models": len(models),
            "providers": len(set(m.provider for m in models)),
            "avg_input_price": sum(input_prices) / len(input_prices) if input_prices else 0,
            "avg_output_price": sum(output_prices) / len(output_prices) if output_prices else 0,
            "last_refresh": db.last_refresh.isoformat(),
        }

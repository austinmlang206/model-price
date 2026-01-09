"""Fetch model metadata from LiteLLM and other sources."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

from config import settings
from models.pricing import ModelPricing

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
METADATA_FILE = DATA_DIR / "model_metadata.json"
USER_OVERRIDES_FILE = DATA_DIR / "user_overrides.json"

# Models known to be open source (weights downloadable)
OPEN_SOURCE_PATTERNS = [
    "llama",
    "mistral",
    "mixtral",
    "qwen",
    "gemma",
    "deepseek",
    "phi",
    "falcon",
    "vicuna",
    "openchat",
    "solar",
    "yi-",
    "internlm",
    "baichuan",
    "codellama",
    "starcoder",
    "wizardlm",
    "zephyr",
    "orca",
    "neural",
    "olmo",
    "mamba",
    "jamba",
    "dbrx",
    "command-r",
    "aya",
    "granite",
    "nemotron",
    "r1",
    "kimi",
    "minimax",
    # Note: "nova" removed - Amazon Nova is proprietary, not open source
]

# Models known to be proprietary
PROPRIETARY_PATTERNS = [
    "gpt-4",
    "gpt-3.5",
    "o1",
    "o3",
    "claude",
    "gemini",
    "palm",
    "bard",
]


class MetadataFetcher:
    """Fetches and manages model metadata from various sources."""

    _litellm_cache: Optional[Dict[str, Any]] = None

    @classmethod
    async def fetch_litellm_data(cls) -> Dict[str, Any]:
        """Fetch model data from LiteLLM GitHub repository."""
        if cls._litellm_cache is not None:
            return cls._litellm_cache

        logger.info("Fetching LiteLLM model data...")
        try:
            async with httpx.AsyncClient(timeout=settings.metadata_timeout) as client:
                response = await client.get(settings.litellm_url)
                response.raise_for_status()
                cls._litellm_cache = response.json()
                logger.info(f"Loaded {len(cls._litellm_cache)} models from LiteLLM")
                return cls._litellm_cache
        except Exception as e:
            logger.error(f"Failed to fetch LiteLLM data: {e}")
            return {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the LiteLLM cache to force re-fetch."""
        cls._litellm_cache = None

    @classmethod
    def load_static_metadata(cls) -> Dict[str, Any]:
        """Load static model metadata from local file."""
        if not METADATA_FILE.exists():
            return {}
        try:
            with open(METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load static metadata: {e}")
            return {}

    @classmethod
    def load_user_overrides(cls) -> Dict[str, Any]:
        """Load user override data."""
        if not USER_OVERRIDES_FILE.exists():
            return {}
        try:
            with open(USER_OVERRIDES_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user overrides: {e}")
            return {}

    @classmethod
    def save_user_override(cls, model_id: str, data: Dict[str, Any]) -> None:
        """Save user override for a specific model."""
        overrides = cls.load_user_overrides()
        if model_id not in overrides:
            overrides[model_id] = {}
        overrides[model_id].update(data)

        USER_OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_OVERRIDES_FILE, "w") as f:
            json.dump(overrides, f, indent=2)
        logger.info(f"Saved user override for {model_id}")

    @classmethod
    def is_open_source(cls, model_name: str) -> Optional[bool]:
        """Determine if a model is open source based on naming patterns."""
        name_lower = model_name.lower()

        for pattern in OPEN_SOURCE_PATTERNS:
            if pattern in name_lower:
                return True

        for pattern in PROPRIETARY_PATTERNS:
            if pattern in name_lower:
                return False

        return None

    @classmethod
    def normalize_model_key(cls, provider: str, model_id: str) -> List[str]:
        """Generate possible LiteLLM keys for a model."""
        keys = []

        # Direct model_id
        keys.append(model_id)

        # With provider prefix
        provider_prefixes = {
            "aws_bedrock": ["bedrock/", "bedrock_converse/", ""],
            "openai": ["openai/", ""],
            "azure_openai": ["azure/", "azure_ai/", ""],
            "anthropic": ["anthropic/", ""],
            "google_vertex_ai": ["gemini/", "vertex_ai/", ""],
            "openrouter": ["openrouter/", ""],
            "xai": ["xai/", ""],
        }

        prefixes = provider_prefixes.get(provider, [""])
        for prefix in prefixes:
            keys.append(f"{prefix}{model_id}")

        return keys

    @classmethod
    def fuzzy_match_litellm_key(
        cls, provider: str, model_id: str, litellm_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find matching LiteLLM model using fuzzy matching."""
        # Extract key parts from our model_id (remove version suffixes like -v2)
        import re

        # Normalize our model_id for comparison
        model_parts = model_id.lower().replace(".", "-").split("-")
        # Filter out version indicators
        model_parts = [p for p in model_parts if p not in ["v1", "v2", "v3", "instruct"]]

        # Provider-specific model prefixes in LiteLLM
        provider_patterns = {
            "aws_bedrock": ["anthropic.", "amazon.", "meta.", "mistral.", "ai21.", "cohere."],
        }

        search_prefixes = provider_patterns.get(provider, [])

        best_match = None
        best_score = 0

        for key, value in litellm_data.items():
            key_lower = key.lower()

            # For AWS Bedrock, prioritize keys starting with known prefixes
            if provider == "aws_bedrock":
                # Skip region-specific keys (prefer generic ones)
                if "/us-" in key or "/eu-" in key or "/ap-" in key or "/ca-" in key:
                    continue
                if "commitment" in key_lower:
                    continue

                # Check if key starts with any known prefix
                has_prefix = any(key_lower.startswith(p) for p in search_prefixes)
                if not has_prefix and not key_lower.startswith("bedrock/"):
                    continue

            # Score based on how many model parts match
            key_normalized = key_lower.replace("-", " ").replace(".", " ").replace("/", " ").replace("_", " ")

            score = 0
            for part in model_parts:
                if len(part) >= 2 and part in key_normalized:
                    score += 1

            # Bonus for exact version match
            if "v2" in model_id.lower() and "v2" in key_lower:
                score += 2
            elif "v1" in model_id.lower() and "v1" in key_lower:
                score += 1

            # Bonus for having context/output data
            if value.get("max_input_tokens") or value.get("max_output_tokens"):
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = value

        # Require at least 2 parts to match
        if best_score >= 2:
            return best_match
        return None

    @classmethod
    async def get_model_metadata(
        cls,
        provider: str,
        model_id: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """Get metadata for a specific model, merging all sources."""
        result: Dict[str, Any] = {
            "context_length": None,
            "max_output_tokens": None,
            "is_open_source": None,
            "pricing": None,  # Will be set if user has pricing overrides
        }

        # 1. Static metadata (lowest priority)
        static_data = cls.load_static_metadata()
        full_id = f"{provider}:{model_id}"
        if full_id in static_data:
            result.update(static_data[full_id])

        # 2. LiteLLM data (higher priority)
        litellm_data = await cls.fetch_litellm_data()
        possible_keys = cls.normalize_model_key(provider, model_id)

        model_info = None
        # Try exact key matching first
        for key in possible_keys:
            if key in litellm_data:
                model_info = litellm_data[key]
                break

        # Fall back to fuzzy matching if no exact match found
        if model_info is None:
            model_info = cls.fuzzy_match_litellm_key(provider, model_id, litellm_data)

        # Extract metadata from matched model info
        if model_info:
            if "max_input_tokens" in model_info:
                result["context_length"] = model_info["max_input_tokens"]
            if "max_output_tokens" in model_info:
                result["max_output_tokens"] = model_info["max_output_tokens"]
            elif "max_tokens" in model_info:
                result["max_output_tokens"] = model_info["max_tokens"]

        # Determine open source status if not set
        if result["is_open_source"] is None:
            result["is_open_source"] = cls.is_open_source(model_name)

        # 3. User overrides (highest priority)
        user_overrides = cls.load_user_overrides()
        if full_id in user_overrides:
            result.update(user_overrides[full_id])

        return result

    @classmethod
    async def enrich_models(
        cls, models: List[Union[ModelPricing, dict]]
    ) -> List[Union[ModelPricing, dict]]:
        """Enrich a list of models with metadata.

        Handles both Pydantic ModelPricing objects and dicts.
        """
        logger.info(f"Enriching {len(models)} models with metadata...")

        for model in models:
            # Handle both Pydantic objects and dicts
            if isinstance(model, ModelPricing):
                provider = model.provider
                model_id = model.model_id
                model_name = model.model_name
            else:
                provider = model["provider"]
                model_id = model["model_id"]
                model_name = model["model_name"]

            metadata = await cls.get_model_metadata(provider, model_id, model_name)

            # Update the model with metadata
            if isinstance(model, ModelPricing):
                model.context_length = metadata["context_length"]
                model.max_output_tokens = metadata["max_output_tokens"]
                model.is_open_source = metadata["is_open_source"]
                # Apply pricing overrides if present
                if metadata.get("pricing"):
                    pricing_overrides = metadata["pricing"]
                    if "input" in pricing_overrides:
                        model.pricing.input = pricing_overrides["input"]
                    if "output" in pricing_overrides:
                        model.pricing.output = pricing_overrides["output"]
                    if "cached_input" in pricing_overrides:
                        model.pricing.cached_input = pricing_overrides["cached_input"]
            else:
                model["context_length"] = metadata["context_length"]
                model["max_output_tokens"] = metadata["max_output_tokens"]
                model["is_open_source"] = metadata["is_open_source"]
                # Apply pricing overrides if present
                if metadata.get("pricing"):
                    pricing_overrides = metadata["pricing"]
                    if "input" in pricing_overrides:
                        model["pricing"]["input"] = pricing_overrides["input"]
                    if "output" in pricing_overrides:
                        model["pricing"]["output"] = pricing_overrides["output"]
                    if "cached_input" in pricing_overrides:
                        model["pricing"]["cached_input"] = pricing_overrides["cached_input"]

        logger.info("Metadata enrichment complete")
        return models

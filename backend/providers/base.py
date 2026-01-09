"""Abstract base class for pricing providers."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models import ModelPricing, Pricing, BatchPricing

logger = logging.getLogger(__name__)

# Path to fallback data directory
FALLBACK_DATA_DIR = Path(__file__).parent.parent / "data" / "fallback"


def detect_modalities(capabilities: List[str], model_name: str = "") -> Tuple[List[str], List[str]]:
    """Detect input and output modalities based on capabilities and model name.

    This function analyzes model capabilities to determine what types of data
    a model can accept as input and produce as output.

    Args:
        capabilities: List of capability strings (e.g., ["text", "vision", "audio"])
        model_name: Optional model name for additional context

    Returns:
        Tuple of (input_modalities, output_modalities)
    """
    name_lower = model_name.lower()
    caps_set = set(capabilities)

    input_mods: List[str] = []
    output_mods: List[str] = []

    # Text - most models have text input/output
    if "text" in caps_set:
        input_mods.append("text")
        output_mods.append("text")

    # Vision - image input capability
    if "vision" in caps_set:
        input_mods.append("image")

    # Audio - can be input, output, or both
    if "audio" in caps_set:
        # Check for specific audio patterns
        if any(x in name_lower for x in ["tts", "text-to-speech"]):
            # TTS: text in, audio out
            if "text" not in input_mods:
                input_mods.append("text")
            output_mods.append("audio")
        elif any(x in name_lower for x in ["transcribe", "whisper", "stt", "speech-to-text"]):
            # STT/Transcription: audio in, text out
            input_mods.append("audio")
            if "text" not in output_mods:
                output_mods.append("text")
        else:
            # General audio models (realtime, etc) - both directions
            input_mods.append("audio")
            output_mods.append("audio")

    # Video input capability
    if "video" in caps_set:
        input_mods.append("video")

    # Image generation - text/image in, image out
    if "image_generation" in caps_set:
        if "text" not in input_mods:
            input_mods.append("text")
        # Some image gen models also accept image input (for editing)
        if "vision" in caps_set and "image" not in input_mods:
            input_mods.append("image")
        output_mods.append("image")

    # Video generation - text in, video out
    if "video_generation" in caps_set:
        if "text" not in input_mods:
            input_mods.append("text")
        output_mods.append("video")

    # Embedding - text/image in, embedding out
    if "embedding" in caps_set:
        if "text" not in input_mods:
            input_mods.append("text")
        output_mods.append("embedding")

    # File processing - some models can handle files (PDF, etc)
    if "file" in caps_set:
        input_mods.append("file")

    # Moderation - typically text/image in, classification out (treat as text)
    if "moderation" in caps_set:
        if "text" not in input_mods:
            input_mods.append("text")
        if "text" not in output_mods:
            output_mods.append("text")

    # Remove duplicates while preserving order
    input_mods = list(dict.fromkeys(input_mods))
    output_mods = list(dict.fromkeys(output_mods))

    return input_mods, output_mods


class BaseProvider(ABC):
    """Base class for all pricing data providers."""

    name: str  # e.g., "aws_bedrock"
    display_name: str  # e.g., "AWS Bedrock"

    @abstractmethod
    async def fetch(self) -> List[ModelPricing]:
        """Fetch all model prices from this provider.

        Returns:
            List of ModelPricing objects.

        Raises:
            Exception: If fetching fails.
        """
        pass

    def load_fallback_data(self) -> List[ModelPricing]:
        """Load static fallback data from JSON file.

        Returns:
            List of ModelPricing objects from fallback data.

        Raises:
            FileNotFoundError: If fallback file doesn't exist.
        """
        fallback_file = FALLBACK_DATA_DIR / f"{self.name}.json"

        with open(fallback_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        models: List[ModelPricing] = []
        for item in data.get("models", []):
            models.append(self._parse_fallback_model(item))

        logger.info(f"{self.display_name}: loaded {len(models)} models from fallback")
        return models

    def _parse_fallback_model(self, item: Dict[str, Any]) -> ModelPricing:
        """Parse a single model from fallback JSON data."""
        model_id = item["model_id"]
        full_id = f"{self.name}:{model_id}"

        # Parse pricing
        pricing_data = item.get("pricing", {})
        pricing = Pricing(
            input=pricing_data.get("input"),
            output=pricing_data.get("output"),
            cached_input=pricing_data.get("cached_input"),
            audio_input=pricing_data.get("audio_input"),
            audio_output=pricing_data.get("audio_output"),
            image_input=pricing_data.get("image_input"),
            embedding=pricing_data.get("embedding"),
        )

        # Parse batch pricing if present
        batch_pricing = None
        if "batch_pricing" in item:
            batch_data = item["batch_pricing"]
            batch_pricing = BatchPricing(
                input=batch_data.get("input"),
                output=batch_data.get("output"),
            )

        # Get capabilities and detect modalities
        capabilities = item.get("capabilities", ["text"])
        input_mods, output_mods = detect_modalities(capabilities, item.get("model_name", ""))

        return ModelPricing(
            id=full_id,
            provider=self.name,
            model_id=model_id,
            model_name=item.get("model_name", model_id),
            pricing=pricing,
            batch_pricing=batch_pricing,
            capabilities=capabilities,
            input_modalities=input_mods,
            output_modalities=output_mods,
            context_length=item.get("context_length"),
            max_output_tokens=item.get("max_output_tokens"),
            is_open_source=item.get("is_open_source", False),
            last_updated=datetime.now(),
        )

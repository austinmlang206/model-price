"""Pydantic models for pricing data."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class Pricing(BaseModel):
    """Price info (USD per million tokens/units)."""

    input: Optional[float] = None
    output: Optional[float] = None
    cached_input: Optional[float] = None
    cached_write: Optional[float] = None
    reasoning: Optional[float] = None
    image_input: Optional[float] = None
    audio_input: Optional[float] = None
    audio_output: Optional[float] = None
    embedding: Optional[float] = None


class BatchPricing(BaseModel):
    """Batch processing discounted prices."""

    input: Optional[float] = None
    output: Optional[float] = None


class ModelPricing(BaseModel):
    """Complete pricing info for a single model."""

    id: str  # Unique: "{provider}:{model_id}"
    provider: str  # aws_bedrock, openai, azure, etc.
    model_id: str  # Original model ID
    model_name: str  # Display name
    pricing: Pricing
    batch_pricing: Optional[BatchPricing] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    is_open_source: Optional[bool] = None  # True if weights are downloadable
    capabilities: List[str] = []  # ["text", "vision", "audio", "embedding"]
    input_modalities: List[str] = []  # ["text", "image", "audio", "video", "file"]
    output_modalities: List[str] = []  # ["text", "image", "audio", "video", "embedding"]
    last_updated: datetime


class PricingDatabase(BaseModel):
    """JSON file root structure."""

    version: str = "1.0"
    last_refresh: datetime
    models: List[ModelPricing] = []


class ProviderInfo(BaseModel):
    """Provider metadata for API response."""

    name: str
    display_name: str
    model_count: int
    last_updated: Optional[datetime] = None


class ProviderFile(BaseModel):
    """Structure for per-provider JSON file (providers/*.json)."""

    provider: str
    last_updated: datetime
    models: List[ModelPricing] = []


class ProviderIndexEntry(BaseModel):
    """Entry in the index file for a single provider."""

    file: str  # Relative path like "providers/openai.json"
    model_count: int
    last_updated: datetime


class IndexFile(BaseModel):
    """Structure for index.json - tracks all provider files."""

    version: str = "2.0"
    last_refresh: datetime
    providers: Dict[str, ProviderIndexEntry] = {}
    total_models: int = 0

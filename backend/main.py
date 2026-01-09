"""Model Price Backend - FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import ModelPricing, ProviderInfo
from services import PricingService, Fetcher

# Configure logging from settings
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


class PricingUpdate(BaseModel):
    """Pricing fields that can be updated."""

    input: Optional[float] = None
    output: Optional[float] = None
    cached_input: Optional[float] = None


class ModelUpdate(BaseModel):
    """Request body for updating model metadata and pricing."""

    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    is_open_source: Optional[bool] = None
    pricing: Optional[PricingUpdate] = None
    capabilities: Optional[List[str]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: use existing static data for fast cold start
    # No network calls on startup - user can manually refresh
    stats = PricingService.get_stats()
    logger.info(f"Starting up with cached data: {stats['total_models']} models")
    if stats['total_models'] == 0:
        logger.warning("No cached data available. Use /api/refresh to fetch data.")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Model Price API",
    description="API for AI model pricing comparison",
    version=settings.api_version,
    lifespan=lifespan,
)

# CORS configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root."""
    return {
        "message": "Welcome to Model Price API",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    stats = PricingService.get_stats()
    return {
        "status": "healthy",
        "models_count": stats["total_models"],
        "last_refresh": stats["last_refresh"],
    }


@app.get("/api/models", response_model=List[ModelPricing])
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    family: Optional[str] = Query(None, description="Filter by model family"),
    search: Optional[str] = Query(None, description="Search model name"),
    sort_by: str = Query("model_name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
):
    """List all models with optional filters and sorting."""
    return PricingService.get_all(
        provider=provider,
        capability=capability,
        family=family,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.get("/api/models/{model_id:path}", response_model=ModelPricing)
async def get_model(model_id: str):
    """Get a single model by ID."""
    model = PricingService.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.get("/api/providers", response_model=List[ProviderInfo])
async def list_providers(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    family: Optional[str] = Query(None, description="Filter by model family"),
    search: Optional[str] = Query(None, description="Search model name"),
):
    """List all providers with stats, filtered by other conditions."""
    return PricingService.get_providers(
        capability=capability,
        family=family,
        search=search,
    )


@app.get("/api/families")
async def list_families(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    search: Optional[str] = Query(None, description="Search model name"),
):
    """List all model families with counts, filtered by other conditions."""
    return PricingService.get_model_families(
        provider=provider,
        capability=capability,
        search=search,
    )


@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    return PricingService.get_stats()


@app.post("/api/refresh")
async def refresh(provider: Optional[str] = Query(None, description="Provider to refresh")):
    """Manually refresh pricing data."""
    try:
        if provider:
            result = await Fetcher.refresh_provider(provider)
        else:
            result = await Fetcher.refresh_all()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Refresh failed")


@app.patch("/api/models/{model_id:path}", response_model=ModelPricing)
async def update_model(model_id: str, updates: ModelUpdate):
    """Update model metadata (context_length, max_output_tokens, is_open_source)."""
    # Use exclude_unset to allow explicit null values (e.g., is_open_source: null)
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    updated = PricingService.update_model(model_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")

    logger.info(f"Updated model {model_id}: {update_data}")
    return updated


@app.post("/api/refresh/metadata")
async def refresh_metadata():
    """Refresh metadata (context_length, max_output_tokens, is_open_source) from LiteLLM."""
    try:
        count = await PricingService.refresh_metadata()
        return {"status": "success", "models_updated": count}
    except Exception as e:
        logger.error(f"Metadata refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Metadata refresh failed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )

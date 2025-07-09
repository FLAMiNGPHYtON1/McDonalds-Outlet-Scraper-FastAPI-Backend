"""
API Response Models

This module contains all Pydantic response models used in the FastAPI application.
All response classes are centralized here for better organization and maintainability.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class OutletResponse(BaseModel):
    """Model for API responses."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: str = Field(..., description="Unique identifier for the outlet")
    name: str = Field(..., description="Name of the McDonald's outlet")
    address: str = Field(..., description="Full address of the outlet")
    operating_hours: Optional[str] = Field(None, description="Operating hours of the outlet")
    waze_link: Optional[str] = Field(None, description="Waze navigation link")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    telephone: Optional[str] = Field(None, description="Telephone number")
    attribute: Optional[str] = Field(None, description="Additional attributes or features")
    search_term: Optional[str] = Field(None, description="Search term used to find this outlet")
    scraped_at: datetime = Field(..., description="When the outlet was scraped")
    created_at: datetime = Field(..., description="When the record was created")
    updated_at: datetime = Field(..., description="When the record was last updated")


class OutletList(BaseModel):
    """Model for paginated outlet lists."""
    
    outlets: List[OutletResponse] = Field(..., description="List of outlets")
    total: int = Field(..., description="Total number of outlets")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of outlets per page")
    pages: int = Field(..., description="Total number of pages")


class ScrapeResponse(BaseModel):
    """Model for scraping responses."""
    
    success: bool = Field(..., description="Whether the scraping was successful")
    message: str = Field(..., description="Success or error message")
    outlets_scraped: int = Field(0, description="Number of outlets scraped")
    outlets_saved: int = Field(0, description="Number of outlets saved to database")
    search_term: str = Field(..., description="Search term used")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the scraping was performed")


class ScrapeOnlyResponse(BaseModel):
    """Response model for scraping without database operations."""
    
    success: bool = Field(..., description="Whether the scraping was successful")
    message: str = Field(..., description="Success or error message")
    outlets: List[Dict[str, Any]] = Field(default=[], description="List of scraped outlets")
    total_outlets: int = Field(0, description="Total number of outlets found")
    search_term: str = Field(..., description="Search term used")


# Export all response models for easy importing
__all__ = [
    "OutletResponse",
    "OutletList", 
    "ScrapeResponse",
    "ScrapeOnlyResponse"
] 
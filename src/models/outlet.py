"""
MongoDB models for McDonald's outlet data.

This module defines the data models used to store McDonald's outlet information
in MongoDB using Pydantic for validation.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from pydantic.config import ConfigDict


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string", format="objectid")
        return field_schema


class OutletBase(BaseModel):
    """Base model for outlet data validation."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Name of the McDonald's outlet")
    address: str = Field(..., min_length=1, max_length=500, description="Full address of the outlet")
    operating_hours: Optional[str] = Field("8am - 12pm", max_length=200, description="Operating hours of the outlet")
    waze_link: Optional[str] = Field(None, max_length=500, description="Waze navigation link")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    telephone: Optional[str] = Field(None, max_length=50, description="Telephone number")
    attribute: Optional[str] = Field(None, max_length=500, description="Additional attributes or features")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the outlet data")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate outlet name."""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate outlet address."""
        if not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip()
    
    @field_validator('waze_link')
    @classmethod
    def validate_waze_link(cls, v):
        """Validate Waze link format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Waze link must be a valid URL')
        return v


class OutletCreate(OutletBase):
    """Model for creating new outlets."""
    
    search_term: Optional[str] = Field(None, max_length=100, description="Search term used to find this outlet")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the outlet was scraped")


class OutletInDB(OutletBase):
    """Model for outlets stored in database."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "McDonald's Bukit Bintang",
                "address": "120-120A Jalan Bukit Bintang, 55100, Kuala Lumpur, Malaysia",
                "operating_hours": "8am - 12pm",
                "waze_link": "https://waze.com/ul/h9icrq0r43",
                "latitude": 3.146847,
                "longitude": 101.710931,
                "telephone": "03-2141 8454",
                "attribute": "24 Hours Drive-Thru, McCafe, Delivery Available",
                "search_term": "Kuala Lumpur",
                "scraped_at": "2024-01-15T10:30:00",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    search_term: Optional[str] = Field(None, max_length=100, description="Search term used to find this outlet")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the outlet was scraped")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was last updated")


class OutletUpdate(BaseModel):
    """Model for updating existing outlets."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    operating_hours: Optional[str] = Field(None, max_length=200)
    waze_link: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    telephone: Optional[str] = Field(None, max_length=50, description="Telephone number")
    attribute: Optional[str] = Field(None, max_length=500, description="Additional attributes or features")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the outlet data")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate outlet name."""
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate outlet address."""
        if v is not None and not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip() if v else v
    
    @field_validator('waze_link')
    @classmethod
    def validate_waze_link(cls, v):
        """Validate Waze link format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Waze link must be a valid URL')
        return v


class ScrapeRequest(BaseModel):
    """Model for scraping requests."""
    
    search_term: str = Field(..., min_length=1, max_length=100, description="Search term to filter outlets")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing data")
    
    @field_validator('search_term')
    @classmethod
    def validate_search_term(cls, v):
        """Validate search term."""
        if not v.strip():
            raise ValueError('Search term cannot be empty')
        return v.strip()


# ScrapeResponse moved to api/responses.py 
"""
Database Utility Functions

This module contains standalone utility functions for database operations
that don't belong to any specific class.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime

from .connection import db_manager

# Configure logging
logger = logging.getLogger(__name__)

async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
        
    Raises:
        RuntimeError: If not connected to database
    """
    if not db_manager.is_connected:
        await db_manager.connect()
        await db_manager.create_indexes()
    
    if db_manager.database is None:
        raise RuntimeError("Failed to establish database connection")
    return db_manager.database


async def get_collection(collection_name: Optional[str] = None):
    """
    Get collection instance.
    
    Args:
        collection_name (str, optional): Name of the collection
        
    Returns:
        AsyncIOMotorCollection: Collection instance
    """
    if not db_manager.is_connected:
        await db_manager.connect()
        await db_manager.create_indexes()
    return await db_manager.get_collection(collection_name)


async def close_database_connection():
    """Close database connection."""
    await db_manager.disconnect()


async def get_db_dependency():
    """Database dependency for FastAPI dependency injection."""
    return await get_database()


async def health_check() -> dict:
    """
    Perform database health check.
    
    Returns:
        dict: Health check results
    """
    return await db_manager.health_check() 


def BSON_to_JSON(data):
    """
    Converts a BSON document (dictionary) to a JSON-serializable dictionary.
    """
    if data is None:
        return None
    
    # Convert ObjectId and datetime objects to strings
    for key, value in data.items():
        if isinstance(value, ObjectId):
            data[key] = str(value)
        elif isinstance(value, datetime):
            data[key] = value.isoformat()
            
    # Rename '_id' to 'id' for frontend convenience
    if "_id" in data:
        data["id"] = str(data.pop("_id"))
        
    return data 
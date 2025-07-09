"""
MongoDB database connection and configuration.

This module handles the connection to MongoDB Atlas and provides
database access for the McDonald's outlet scraper application.
"""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration class."""
    
    def __init__(self):
        """Initialize database configuration."""
        self.mongodb_url: str = os.getenv(
            "MONGODB_URL", 
            "mongodb://localhost:27017"
        )
        self.database_name: str = os.getenv(
            "DATABASE_NAME", 
            "mcdonalds_scraper"
        )
        self.collection_name: str = os.getenv(
            "COLLECTION_NAME", 
            "outlets"
        )
        self.connection_timeout: int = int(os.getenv("CONNECTION_TIMEOUT", "10"))
        self.max_pool_size: int = int(os.getenv("MAX_POOL_SIZE", "10"))
        self.min_pool_size: int = int(os.getenv("MIN_POOL_SIZE", "1"))


class DatabaseManager:
    """
    Database manager for handling MongoDB connections.
    
    This class provides methods to connect to MongoDB, get database
    and collection references, and handle connection lifecycle.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager.
        
        Args:
            config (DatabaseConfig, optional): Database configuration
        """
        self.config = config or DatabaseConfig()
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.is_connected: bool = False
        
    async def connect(self) -> None:
        """
        Connect to MongoDB database.
        
        Raises:
            ServerSelectionTimeoutError: If connection fails
        """
        try:
            logger.info("Connecting to MongoDB...")
            
            # Create MongoDB client
            self.client = AsyncIOMotorClient(
                self.config.mongodb_url,
                serverSelectionTimeoutMS=self.config.connection_timeout * 1000,
                maxPoolSize=self.config.max_pool_size,
                minPoolSize=self.config.min_pool_size
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database reference
            self.database = self.client[self.config.database_name]
            
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB database: {self.config.database_name}")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from MongoDB database."""
        if self.client is not None:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")
            
    async def get_collection(self, collection_name: Optional[str] = None):
        """
        Get MongoDB collection reference.
        
        Args:
            collection_name (str, optional): Name of the collection
            
        Returns:
            AsyncIOMotorCollection: Collection reference
            
        Raises:
            RuntimeError: If not connected to database
        """
        if not self.is_connected or self.database is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
            
        collection_name = collection_name or self.config.collection_name
        return self.database[collection_name]
        
    async def create_indexes(self) -> None:
        """Create database indexes for better performance."""
        if not self.is_connected or self.database is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
            
        try:
            collection = await self.get_collection()
            
            # Create indexes
            await collection.create_index("name")
            await collection.create_index("address")
            await collection.create_index("search_term")
            await collection.create_index("scraped_at")
            await collection.create_index([("name", 1), ("address", 1)], unique=True)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")
            raise
            
    async def health_check(self) -> dict:
        """
        Perform database health check.
        
        Returns:
            dict: Health check results
        """
        if not self.is_connected or self.client is None or self.database is None:
            return {
                "status": "disconnected",
                "message": "Not connected to database"
            }
            
        try:
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database stats
            stats = await self.database.command("dbstats")
            
            return {
                "status": "healthy",
                "database_name": self.config.database_name,
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("indexes", 0)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }


# Global database manager instance
db_manager = DatabaseManager()


# Standalone database utility functions moved to database/utils.py 
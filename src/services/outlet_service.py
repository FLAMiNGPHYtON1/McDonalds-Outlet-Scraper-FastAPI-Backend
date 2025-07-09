"""
Service layer for McDonald's outlet data operations.

This module provides business logic for handling outlet data,
including scraping, storing, and retrieving outlet information.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, cast
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from ..database.utils import get_collection, BSON_to_JSON
from ..models.outlet import OutletInDB, OutletCreate, OutletUpdate
from ..api.responses import OutletResponse
from ..scraper.utils import scrape_mcdonalds_outlets
from .vector_service import generate_embedding, get_outlet_text_representation

# Configure logging
logger = logging.getLogger(__name__)


class OutletService:
    """
    Service class for handling outlet data operations.
    
    This class provides methods for scraping, storing, and retrieving
    McDonald's outlet information from the database.
    """
    
    def __init__(self):
        """Initialize the outlet service."""
        self.collection_name = "outlets"
        
    async def scrape_and_store_outlets(
        self, 
        search_term: str, 
        overwrite_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape outlets from McDonald's website and store them in the database.
        
        Args:
            search_term (str): Search term to filter outlets
            overwrite_existing (bool): Whether to overwrite existing data
            
        Returns:
            Dict containing scraping results
        """
        try:
            logger.info(f"Starting scraping process for search term: {search_term}")
            
            # Scrape outlets from website
            scraped_outlets = scrape_mcdonalds_outlets(search_term)
            
            if not scraped_outlets:
                return {
                    "success": False,
                    "message": "No outlets found for the given search term",
                    "outlets_scraped": 0,
                    "outlets_saved": 0,
                    "search_term": search_term
                }
            
            logger.info(f"Scraped {len(scraped_outlets)} outlets")
            
            # Store outlets in database
            outlets_saved = await self._store_outlets(
                scraped_outlets, 
                search_term, 
                overwrite_existing
            )
            
            return {
                "success": True,
                "message": f"Successfully scraped and stored outlets",
                "outlets_scraped": len(scraped_outlets),
                "outlets_saved": outlets_saved,
                "search_term": search_term
            }
            
        except Exception as e:
            logger.error(f"Error during scraping and storing: {str(e)}")
            return {
                "success": False,
                "message": f"Error during scraping: {str(e)}",
                "outlets_scraped": 0,
                "outlets_saved": 0,
                "search_term": search_term
            }
    
    async def _store_outlets(
        self, 
        outlets_data: List[Dict[str, str]], 
        search_term: str, 
        overwrite_existing: bool
    ) -> int:
        """
        Store outlet data in the database.
        
        Args:
            outlets_data (List[Dict]): List of outlet data
            search_term (str): Search term used for scraping
            overwrite_existing (bool): Whether to overwrite existing data
            
        Returns:
            int: Number of outlets saved
        """
        collection = await get_collection(self.collection_name)
        outlets_saved = 0
        
        for outlet_data in outlets_data:
            try:
                # Skip if no name or address
                if not outlet_data.get("name") or not outlet_data.get("address"):
                    continue
                
                # First, prepare the text for embedding
                text_to_embed = (
                    f"Name: {outlet_data.get('name', '')}. "
                    f"Address: {outlet_data.get('address', '')}. "
                    f"Hours: {outlet_data.get('operating_hours', '')}. "
                    f"Services: {outlet_data.get('attribute', '')}"
                )
                embedding = generate_embedding(text_to_embed)

                # Create outlet model with embedding
                lat = outlet_data.get("latitude")
                lng = outlet_data.get("longitude")
                
                outlet_create = OutletCreate(
                    name=outlet_data["name"],
                    address=outlet_data["address"],
                    operating_hours=outlet_data.get("operating_hours", "8am - 12pm"),
                    waze_link=outlet_data.get("waze_link", ""),
                    latitude=float(lat) if lat and lat != "" else None,
                    longitude=float(lng) if lng and lng != "" else None,
                    telephone=outlet_data.get("telephone", ""),
                    attribute=outlet_data.get("attribute", ""),
                    embedding=embedding,
                    search_term=search_term,
                    scraped_at=datetime.utcnow()
                )
                
                # Check if outlet already exists
                existing_outlet = await collection.find_one({
                    "name": outlet_create.name,
                    "address": outlet_create.address
                })
                
                if existing_outlet:
                    if overwrite_existing:
                        # Update existing outlet
                        await collection.update_one(
                            {"_id": existing_outlet["_id"]},
                            {
                                "$set": {
                                    "operating_hours": outlet_create.operating_hours,
                                    "waze_link": outlet_create.waze_link,
                                    "latitude": outlet_create.latitude,
                                    "longitude": outlet_create.longitude,
                                    "telephone": outlet_create.telephone,
                                    "attribute": outlet_create.attribute,
                                    "embedding": outlet_create.embedding,
                                    "search_term": outlet_create.search_term,
                                    "scraped_at": outlet_create.scraped_at,
                                    "updated_at": datetime.utcnow()
                                }
                            }
                        )
                        outlets_saved += 1
                        logger.info(f"Updated outlet: {outlet_create.name}")
                    else:
                        logger.info(f"Outlet already exists, skipping: {outlet_create.name}")
                else:
                    # Create new outlet
                    outlet_dict = outlet_create.dict()
                    outlet_dict["created_at"] = datetime.utcnow()
                    outlet_dict["updated_at"] = datetime.utcnow()
                    
                    await collection.insert_one(outlet_dict)
                    outlets_saved += 1
                    logger.info(f"Created new outlet: {outlet_create.name}")
                    
            except DuplicateKeyError:
                logger.warning(f"Duplicate outlet found: {outlet_data.get('name', 'Unknown')}")
                continue
            except Exception as e:
                logger.error(f"Error storing outlet {outlet_data.get('name', 'Unknown')}: {str(e)}")
                continue
                
        return outlets_saved

    async def search_outlets(self, query: str, limit: int = 5) -> List[OutletInDB]:
        """
        Performs a vector search on the outlets collection based on a query string.

        Args:
            query: The user's search query.
            limit: The maximum number of results to return.

        Returns:
            A list of matching outlet documents.
        """
        collection = await get_collection(self.collection_name)
        try:
            query_vector = generate_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate embedding for query '{query}': {e}")
            return []

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 100,
                    "limit": limit
                }
            },
            {
                "$project": {
                    "score": {"$meta": "vectorSearchScore"},
                    # Project all other fields from the document
                    "name": 1,
                    "address": 1,
                    "operating_hours": 1,
                    "waze_link": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "telephone": 1,
                    "attribute": 1,
                    "_id": 1,
                    "search_term": 1,
                    "scraped_at": 1,
                    "created_at": 1,
                    "updated_at": 1
                }
            }
        ]

        try:
            results = await collection.aggregate(pipeline).to_list(length=limit)
            return [OutletInDB(**res) for res in results]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def get_outlets(
        self, 
        search_term: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get outlets from the database with pagination.
        
        Args:
            search_term (str, optional): Filter by search term
            page (int): Page number (1-based)
            per_page (int): Number of items per page
            
        Returns:
            Dict containing outlets and pagination info
        """
        collection = await get_collection(self.collection_name)
        
        # Build query
        query = {}
        if search_term:
            query["search_term"] = {"$regex": search_term, "$options": "i"}
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Get outlets
        cursor = collection.find(query).skip(skip).limit(per_page).sort("created_at", -1)
        outlets_list = await cursor.to_list(length=per_page)
        
        # Directly return the list of outlets after converting BSON to JSON
        outlets = [BSON_to_JSON(outlet) for outlet in outlets_list]
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "outlets": outlets,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }
    
    async def get_outlet_by_id(self, outlet_id: str) -> Optional[OutletResponse]:
        """
        Get a specific outlet by ID.
        
        Args:
            outlet_id (str): Outlet ID
            
        Returns:
            OutletResponse or None if not found
        """
        try:
            collection = await get_collection(self.collection_name)
            outlet = await collection.find_one({"_id": ObjectId(outlet_id)})
            
            if not outlet:
                return None
            
            return OutletResponse(
                id=str(outlet["_id"]),
                name=outlet["name"],
                address=outlet["address"],
                operating_hours=outlet.get("operating_hours", "8am - 12pm"),
                waze_link=outlet.get("waze_link", ""),
                latitude=outlet.get("latitude"),
                longitude=outlet.get("longitude"),
                telephone=outlet.get("telephone", ""),
                attribute=outlet.get("attribute", ""),
                search_term=outlet.get("search_term", ""),
                scraped_at=outlet.get("scraped_at", datetime.utcnow()),
                created_at=outlet.get("created_at", datetime.utcnow()),
                updated_at=outlet.get("updated_at", datetime.utcnow())
            )
            
        except Exception as e:
            logger.error(f"Error getting outlet by ID {outlet_id}: {str(e)}")
            return None
    
    async def update_outlet(self, outlet_id: str, outlet_update: OutletUpdate) -> Optional[OutletResponse]:
        """
        Update an existing outlet.
        
        Args:
            outlet_id (str): Outlet ID
            outlet_update (OutletUpdate): Updated outlet data
            
        Returns:
            Updated OutletResponse or None if not found
        """
        try:
            collection = await get_collection(self.collection_name)
            
            # Build update data
            update_data = {}
            if outlet_update.name is not None:
                update_data["name"] = outlet_update.name
            if outlet_update.address is not None:
                update_data["address"] = outlet_update.address
            if outlet_update.operating_hours is not None:
                update_data["operating_hours"] = outlet_update.operating_hours
            if outlet_update.waze_link is not None:
                update_data["waze_link"] = outlet_update.waze_link
            if outlet_update.latitude is not None:
                update_data["latitude"] = outlet_update.latitude
            if outlet_update.longitude is not None:
                update_data["longitude"] = outlet_update.longitude
            if outlet_update.telephone is not None:
                update_data["telephone"] = outlet_update.telephone
            if outlet_update.attribute is not None:
                update_data["attribute"] = outlet_update.attribute
            
            update_data["updated_at"] = datetime.utcnow()
            
            # Update outlet
            result = await collection.update_one(
                {"_id": ObjectId(outlet_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            # Return updated outlet
            return await self.get_outlet_by_id(outlet_id)
            
        except Exception as e:
            logger.error(f"Error updating outlet {outlet_id}: {str(e)}")
            return None
    
    async def delete_outlet(self, outlet_id: str) -> bool:
        """
        Delete an outlet by ID.
        
        Args:
            outlet_id (str): Outlet ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            collection = await get_collection(self.collection_name)
            result = await collection.delete_one({"_id": ObjectId(outlet_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting outlet {outlet_id}: {str(e)}")
            return False

    async def delete_all_outlets(self) -> int:
        """
        Deletes all outlets from the database.
        
        Returns:
            int: The number of deleted documents.
        """
        try:
            collection = await get_collection(self.collection_name)
            result = await collection.delete_many({})
            logger.info(f"Deleted {result.deleted_count} outlets.")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting all outlets: {str(e)}")
            return 0

    async def get_all_search_terms(self) -> List[str]:
        """
        Get all unique search terms from the outlets collection.
        
        Returns:
            List[str]: A list of unique search terms.
        """
        try:
            collection = await get_collection(self.collection_name)
            search_terms = await collection.distinct("search_term")
            # Filter out any None or empty string values that might exist
            return [term for term in search_terms if term]
        except Exception as e:
            logger.error(f"Error getting all search terms: {str(e)}")
            return []

    async def rescrape_all_outlets(self):
        """
        Deletes all outlets and rescrapes them based on existing search terms.
        This is intended to be run as a background task.
        """
        logger.info("Starting 'rescrape all' process.")
        
        # 1. Get all unique search terms before deleting
        search_terms = await self.get_all_search_terms()
        if not search_terms:
            logger.warning("No search terms found in the database. Nothing to rescrape.")
            return

        logger.info(f"Found {len(search_terms)} search terms to rescrape: {search_terms}")
        
        # 2. Delete all existing outlets
        await self.delete_all_outlets()
        
        # 3. Rescrape for each search term
        for term in search_terms:
            logger.info(f"Queueing scrape for search term: {term}")
            try:
                # Since we've already deleted everything, overwrite_existing can be False.
                await self.scrape_and_store_outlets(search_term=term, overwrite_existing=False)
            except Exception as e:
                logger.error(f"Error occurred while scraping for term '{term}': {e}")
        
        logger.info("'Rescrape all' process finished queuing all scrapes.")
    
    async def get_outlets_by_search_term(self, search_term: str) -> List[OutletResponse]:
        """
        Get all outlets for a specific search term.
        
        Args:
            search_term (str): Search term
            
        Returns:
            List of OutletResponse objects
        """
        collection = await get_collection(self.collection_name)
        
        outlets = await collection.find({"search_term": search_term}).to_list(length=None)
        
        outlet_responses = []
        for outlet in outlets:
            outlet_response = OutletResponse(
                id=str(outlet["_id"]),
                name=outlet["name"],
                address=outlet["address"],
                operating_hours=outlet.get("operating_hours", "8am - 12pm"),
                waze_link=outlet.get("waze_link", ""),
                latitude=outlet.get("latitude"),
                longitude=outlet.get("longitude"),
                telephone=outlet.get("telephone", ""),
                attribute=outlet.get("attribute", ""),
                search_term=outlet.get("search_term", ""),
                scraped_at=outlet.get("scraped_at", datetime.utcnow()),
                created_at=outlet.get("created_at", datetime.utcnow()),
                updated_at=outlet.get("updated_at", datetime.utcnow())
            )
            outlet_responses.append(outlet_response)
        
        return outlet_responses
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dict containing statistics
        """
        collection = await get_collection(self.collection_name)
        
        # Get total count
        total_outlets = await collection.count_documents({})
        
        # Get count by search term
        pipeline = [
            {"$group": {"_id": "$search_term", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        search_term_stats = await collection.aggregate(pipeline).to_list(length=None)
        
        # Get recent outlets
        recent_outlets = await collection.find().sort("created_at", -1).limit(5).to_list(length=5)
        
        return {
            "total_outlets": total_outlets,
            "search_term_stats": search_term_stats,
            "recent_outlets": len(recent_outlets)
        } 
"""
McDonald's Outlet API

FastAPI application for scraping and managing McDonald's outlet data.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our scraper and models
from ..scraper.utils import scrape_mcdonalds_outlets
from ..models.outlet import  ScrapeRequest
from ..services.outlet_service import OutletService
from .responses import OutletResponse, OutletList, ScrapeResponse, ScrapeOnlyResponse
from . import search_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="McDonald's Outlet API",
    description="API for scraping and managing McDonald's outlet data",
    version="1.0.0"
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://mcdonalds-outlet-scraper-ne-3w4f3.sevalla.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the search router
app.include_router(search_api.router, prefix="/api/v1", tags=["Search"])

# Initialize outlet service
outlet_service = OutletService()
class ScrapeOnlyRequest(BaseModel):
    """Request model for scraping without saving to database."""
    search_term: str = Field(..., min_length=1, max_length=100, description="Search term to filter outlets")



@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint."""
    return {
        "message": "McDonald's Outlet API is running",
        "endpoints": {
            "scrape": "/scrape-outlets",
            "save": "/save-outlets", 
            "outlets": "/outlets",
            "docs": "/docs"
        }
    }
@app.post(
    "/scrape-outlets",
    response_model=ScrapeOnlyResponse,
    summary="Scrape McDonald's Outlets",
    description="Scrape McDonald's outlets based on search term without saving to database")
async def scrape_outlets_api(request: ScrapeOnlyRequest):
    """
    Scrape McDonald's outlets based on search term.
    
    Args:
        request: ScrapeOnlyRequest containing search term
        
    Returns:
        ScrapeOnlyResponse with scraped outlet data
    """
    try:
        logger.info(f"Starting scrape for search term: {request.search_term}")
        
        # Scrape outlets using our scraper
        outlets = scrape_mcdonalds_outlets(request.search_term)
        
        if not outlets:
            return ScrapeOnlyResponse(
                success=False,
                message=f"No outlets found for search term: {request.search_term}",
                outlets=[],
                total_outlets=0,
                search_term=request.search_term
            )
        
        logger.info(f"Successfully scraped {len(outlets)} outlets")
        
        return ScrapeOnlyResponse(
            success=True,
            message=f"Successfully scraped {len(outlets)} outlets",
            outlets=outlets,
            total_outlets=len(outlets),
            search_term=request.search_term
        )
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )
@app.post(
    "/save-outlets",
    response_model=ScrapeResponse,
    summary="Scrape and Save McDonald's Outlets",
    description="Scrape McDonald's outlets and save them to MongoDB database")
async def save_outlets_api(request: ScrapeRequest):
    """
    Scrape McDonald's outlets and save them to database.
    
    Args:
        request: ScrapeRequest containing search term and options
        
    Returns:
        ScrapeResponse with scraping and saving results
    """
    try:
        logger.info(f"Starting scrape and save for search term: {request.search_term}")
        
        # Use the outlet service to scrape and save
        result = await outlet_service.scrape_and_store_outlets(
            search_term=request.search_term,
            overwrite_existing=request.overwrite_existing
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error during scrape and save: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scrape and save failed: {str(e)}"
        )

@app.post("/scrape/rescrape-all", status_code=202)
async def rescrape_all_outlets_api(
    background_tasks: BackgroundTasks
):
    """
    Deletes all outlets and triggers a background task to rescrape them
    based on all previously used search terms.
    """
    background_tasks.add_task(outlet_service.rescrape_all_outlets)
    return {"message": "Process to delete and rescrape all outlets started in the background."}


@app.delete("/outlets", status_code=200)
async def delete_all_outlets_api():
    """
    Deletes all outlets from the database.
    """
    deleted_count = await outlet_service.delete_all_outlets()
    return {"message": f"Successfully deleted {deleted_count} outlets."}


@app.get(
    "/outlets",
    response_model=OutletList,
    summary="Get Saved Outlets",
    description="Retrieve outlets from database with optional filtering"
)
async def get_outlets_api(
    search_term: Optional[str] = None,
    page: int = 1,
    per_page: int = 10
):
    """
    Get outlets from database.
    
    Args:
        search_term: Optional search term to filter outlets
        page: Page number for pagination
        per_page: Number of outlets per page
        
    Returns:
        A dictionary with paginated outlet data
    """
    try:
        # The service now returns a JSON-serializable dictionary directly.
        result = await outlet_service.get_outlets(
            search_term=search_term,
            page=page,
            per_page=per_page
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to get outlets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get outlets: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
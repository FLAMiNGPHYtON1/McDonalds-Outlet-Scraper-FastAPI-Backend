"""
Scraper Utility Functions

This module contains standalone utility functions for scraping operations
that don't belong to any specific class.
"""

import logging
from typing import List, Dict

from .mcdonalds_scraper import McDonaldsOutletScraper

# Configure logging
logger = logging.getLogger(__name__)


def scrape_mcdonalds_outlets(search_term: str = "") -> List[Dict[str, str]]:
    """
    Main function to scrape McDonald's outlets.
    
    This is a convenience function that creates a scraper instance
    and performs the scraping operation.
    
    Args:
        search_term (str): Search term to filter outlets
        
    Returns:
        List of dictionaries containing outlet information
        
    Raises:
        Exception: If scraping fails
    """
    try:
        logger.info(f"Starting outlet scraping for search term: '{search_term}'")
        
        # Create scraper instance with headless mode for production
        scraper = McDonaldsOutletScraper(headless=True)
        
        # Perform scraping
        outlets = scraper.scrape_outlets(search_term)
        
        logger.info(f"Successfully scraped {len(outlets)} outlets")
        return outlets
        
    except Exception as e:
        logger.error(f"Failed to scrape outlets: {str(e)}")
        raise 
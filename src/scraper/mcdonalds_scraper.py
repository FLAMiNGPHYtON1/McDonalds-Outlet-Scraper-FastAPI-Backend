"""
McDonald's Malaysia Outlet Scraper

This module provides functionality to scrape McDonald's outlet information
from the McDonald's Malaysia website, including search functionality and pagination.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class McDonaldsOutletScraper:
    """
    A scraper for McDonald's Malaysia outlet information.
    
    This class handles searching for outlets, pagination, and extracting
    outlet details including names, addresses, operating hours, and Waze links.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper with Chrome WebDriver.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.base_url = "https://www.mcdonalds.com.my/locate-us"
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.headless = headless
        
    def _ensure_driver_ready(self) -> None:
        """Ensure driver and wait are initialized."""
        if self.driver is None or self.wait is None:
            raise RuntimeError("Driver not initialized. Call _setup_driver() first.")
        assert self.driver is not None
        assert self.wait is not None
        
    def _setup_driver(self) -> None:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Auto-install ChromeDriver with explicit version control
        try:
            # Force fresh download with specific version
            service = Service(ChromeDriverManager().install())
        except Exception as e:
            logger.error(f"ChromeDriver auto-installation failed: {e}")
            logger.info("Trying alternative: manual ChromeDriver path...")
            try:
                # Fallback: try system PATH
                service = Service("chromedriver")
            except Exception as e2:
                logger.error(f"Manual ChromeDriver also failed: {e2}")
                raise Exception(f"ChromeDriver setup failed. Please install Chrome browser and clear cache at: C:\\Users\\Ali Work\\.wdm")
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        if self.driver is None or self.wait is None:
            raise RuntimeError("Failed to initialize WebDriver or WebDriverWait")
        
    def _close_driver(self) -> None:
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            
    def _perform_search(self, search_term: str) -> None:
        """
        Perform search on the McDonald's locate us page.
        
        Args:
            search_term (str): The search term to filter outlets
        """
        self._ensure_driver_ready()
        try:
            # Navigate to the page
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)  # type: ignore
            
            # Wait for page to load
            time.sleep(3)
            
            # Find and interact with search input
            search_input = self.wait.until(  # type: ignore
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][id='address'][name='address']"))
            )
            print("search_input++++++++++++++")
            print(search_input)
            
            # Clear and enter search term
            search_input.clear()
            search_input.send_keys(search_term)
            
            # Click the "Search Now" button
            search_button = self.wait.until(  # type: ignore
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnSearchNow"))
            )
            print("search_button++++++++++++++")
            print(search_button)
            search_button.click()
            
            # Wait for results to load
            time.sleep(3)
            logger.info(f"Search performed for: {search_term}")
            
        except TimeoutException:
            logger.error("Search input not found or page did not load properly")
            raise
            
    def _extract_outlet_info(self, outlet_element) -> Dict[str, str]:
        """
        Extract outlet information from a single outlet element.
        
        Args:
            outlet_element: WebElement representing an outlet
            
        Returns:
            Dict containing outlet information
        """
        outlet_data = {
            "name": "",
            "address": "",
            "operating_hours": "8am - 12pm",  # Default value
            "waze_link": "",
            "latitude": None,
            "longitude": None,
            "telephone": "",
            "attribute": ""
        }
        
        try:
            # Extract name from .addressTitle strong
            name_element = outlet_element.find_element(By.CSS_SELECTOR, ".addressTitle strong")
            outlet_data["name"] = name_element.text.strip()
            print(f"Found name: {outlet_data['name']}")
        except NoSuchElementException:
            logger.warning("Outlet name not found")
            
        try:
            # Extract address from first .addressText
            address_elements = outlet_element.find_elements(By.CSS_SELECTOR, ".addressText")
            if address_elements:
                outlet_data["address"] = address_elements[0].text.strip()
                print(f"Found address: {outlet_data['address']}")
        except NoSuchElementException:
            logger.warning("Outlet address not found")
            
        try:
            # Extract operating hours from tooltip text
            tooltip_elements = outlet_element.find_elements(By.CSS_SELECTOR, ".ed-tooltiptext")
            for tooltip in tooltip_elements:
                tooltip_text = tooltip.text.strip()
                # Look for common hour patterns
                if any(keyword in tooltip_text.lower() for keyword in ['hours', 'hour', '24', 'am', 'pm']):
                    outlet_data["operating_hours"] = tooltip_text.replace('\n', ' ').strip()
                    print(f"Found hours: {outlet_data['operating_hours']}")
                    break
        except NoSuchElementException:
            logger.warning("Operating hours not found")
            
        try:
            # Extract geo coordinates from JSON-LD structured data
            script_elements = outlet_element.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            for script in script_elements:
                try:
                    json_data = json.loads(script.get_attribute("innerHTML"))
                    if "geo" in json_data and isinstance(json_data["geo"], dict):
                        geo_data = json_data["geo"]
                        if "latitude" in geo_data:
                            outlet_data["latitude"] = float(geo_data["latitude"])
                        if "longitude" in geo_data:
                            outlet_data["longitude"] = float(geo_data["longitude"])
                        print(f"Found coordinates: {outlet_data['latitude']}, {outlet_data['longitude']}")
                        
                        # Generate Waze link using coordinates
                        if outlet_data["latitude"] and outlet_data["longitude"]:
                            outlet_data["waze_link"] = f"https://waze.com/ul?ll={outlet_data['latitude']},{outlet_data['longitude']}&z=15"
                            print(f"Generated Waze link: {outlet_data['waze_link']}")
                        break
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Error parsing JSON-LD: {e}")
                    continue
        except NoSuchElementException:
            logger.warning("Geo coordinates not found")
            
        try:
            # Extract telephone and fax from addressText elements
            address_text_elements = outlet_element.find_elements(By.CSS_SELECTOR, ".addressText")
            
            for address_text in address_text_elements:
                text = address_text.text.strip()
                if text and ("Tel:" in text or "Fax:" in text or "Phone:" in text):
                    # Extract the full telephone/fax information
                    outlet_data["telephone"] = text
                    print(f"Found telephone/fax: {outlet_data['telephone']}")
                    break
                    
            # Also check href attributes for tel: links as fallback
            if not outlet_data["telephone"]:
                try:
                    tel_links = outlet_element.find_elements(By.CSS_SELECTOR, "a[href*='tel:']")
                    for link in tel_links:
                        href = link.get_attribute("href")
                        if href and href.startswith("tel:"):
                            outlet_data["telephone"] = href.replace("tel:", "").strip()
                            print(f"Found telephone from href: {outlet_data['telephone']}")
                            break
                except NoSuchElementException:
                    pass
                    
        except Exception as e:
            logger.warning(f"Error extracting telephone: {e}")
            
        try:
            # Extract attributes from addressTop div with ed-tooltip elements
            attribute_parts = []
            # Find the addressTop div
            address_top = outlet_element.find_element(By.CLASS_NAME, "addressTop")
            

            # Find all ed-tooltip elements within addressTop
            tooltip_elements = address_top.find_elements(By.CSS_SELECTOR, "a.ed-tooltip")
            
            for tooltip_element in tooltip_elements:
                try:
                    # Get the tooltip text from the ed-tooltiptext span
                    tooltip_text_element = tooltip_element.find_element(By.CSS_SELECTOR, ".ed-tooltiptext")
                    # Use get_attribute('textContent') to get text from hidden elements
                    tooltip_text = tooltip_text_element.get_attribute("textContent").strip()
                    if tooltip_text:
                        # Clean up the text by removing the caret part
                        lines = tooltip_text.split('\n')
                        cleaned_text = lines[0].strip() if lines else tooltip_text.strip()
                        if cleaned_text:
                            attribute_parts.append(cleaned_text)
                            print(f"Found attribute: {cleaned_text}")
                except NoSuchElementException:
                    continue
                    
            # Combine unique attributes
            if attribute_parts:
                unique_attributes = list(set(attribute_parts))
                outlet_data["attribute"] = ", ".join(unique_attributes)
                print(f"Combined attributes: {outlet_data['attribute']}")
                
        except NoSuchElementException:
            logger.warning("addressTop div not found")
        except Exception as e:
            logger.warning(f"Error extracting attributes: {e}")
            
        return outlet_data
        
    def _get_all_outlets_on_page(self) -> List[Dict[str, str]]:
        """
        Extract all outlet information from the current page.
        
        Returns:
            List of dictionaries containing outlet information
        """
        self._ensure_driver_ready()
        outlets = []
        
        try:
            # Wait for outlets to load using actual McDonald's selectors
            outlet_elements = self.wait.until(  # type: ignore
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".addressBox"))
            )
            
            print(f"Found {len(outlet_elements)} outlet elements")
            
            for outlet_element in outlet_elements:
                outlet_data = self._extract_outlet_info(outlet_element)
                if outlet_data["name"]:  # Only add if we have at least a name
                    outlets.append(outlet_data)
                    
        except TimeoutException:
            logger.warning("No outlets found on current page")
            
        return outlets
        
    def _has_next_page(self) -> bool:
        """
        Check if there is a next page available.
        
        Returns:
            bool: True if next page exists, False otherwise
        """
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR,  # type: ignore
                ".pagination .next:not(.disabled), .next-page:not(.disabled)")
            return next_button.is_enabled()
        except NoSuchElementException:
            return False
            
    def _go_to_next_page(self) -> bool:
        """
        Navigate to the next page if available.
        
        Returns:
            bool: True if successfully navigated to next page, False otherwise
        """
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR,  # type: ignore
                ".pagination .next:not(.disabled), .next-page:not(.disabled)")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(3)  # Wait for page to load
                return True
        except NoSuchElementException:
            pass
        return False
        
    def scrape_outlets(self, search_term: str = "") -> List[Dict[str, str]]:
        """
        Main method to scrape all McDonald's outlets based on search term.
        
        Args:
            search_term (str): Search term to filter outlets (empty for all outlets)
            
        Returns:
            List of dictionaries containing outlet information
        """
        all_outlets = []
        
        try:
            self._setup_driver()
            
            # Perform search if search term is provided
            if search_term:
                self._perform_search(search_term)
            else:
                self.driver.get(self.base_url)  # type: ignore
                time.sleep(3)
            
            page_number = 1
            
            # Scrape all pages
            while True:
                logger.info(f"Scraping page {page_number}")
                
                # Get outlets from current page
                outlets_on_page = self._get_all_outlets_on_page()
                all_outlets.extend(outlets_on_page)
                
                logger.info(f"Found {len(outlets_on_page)} outlets on page {page_number}")
                
                # Check if there's a next page
                if not self._has_next_page():
                    logger.info("No more pages available")
                    break
                    
                # Go to next page
                if not self._go_to_next_page():
                    logger.info("Could not navigate to next page")
                    break
                    
                page_number += 1
                
            logger.info(f"Total outlets scraped: {len(all_outlets)}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
            
        finally:
            self._close_driver()
            
        return all_outlets


# Standalone scraper function moved to scraper/utils.py



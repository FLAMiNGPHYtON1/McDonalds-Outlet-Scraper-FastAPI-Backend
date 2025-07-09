# McDonald's Malaysia Outlet Scraper

A Python web scraper for extracting McDonald's outlet information from the McDonald's Malaysia website and storing it in MongoDB Atlas.

## Features

- 🔍 **Web Scraping**: Scrapes outlet data from https://www.mcdonalds.com.my/locate-us
- 🔎 **Search Functionality**: Supports filtering outlets by search terms
- 📄 **Pagination Handling**: Automatically handles multiple pages of results
- 🗄️ **MongoDB Integration**: Stores data in MongoDB Atlas with proper models
- 📊 **Data Validation**: Uses Pydantic models for data validation
- 🔄 **Async Support**: Built with async/await for better performance

## Extracted Data

For each McDonald's outlet, the scraper extracts:
- **Name**: Outlet name
- **Address**: Full address
- **Operating Hours**: Business hours
- **Waze Link**: Navigation link to Waze app
- **Search Term**: The search term used to find the outlet
- **Timestamps**: Creation and update timestamps

## Installation

1. **Install Dependencies**
   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

2. **Set Up MongoDB Atlas**
   - Create a MongoDB Atlas account
   - Create a new cluster
   - Get your connection string
   - Create a database user with read/write permissions

3. **Configure Environment Variables**
   ```bash
   # Create .env file or set environment variables
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
   DATABASE_NAME=mcdonalds_scraper
   COLLECTION_NAME=outlets
   ```

## Usage

### Basic Usage

```python
from src.mcdonalds_outlet_scraper import scrape_mcdonalds_outlets_sync

# Scrape outlets for Kuala Lumpur
result = scrape_mcdonalds_outlets_sync("Kuala Lumpur")

print(f"Success: {result['success']}")
print(f"Outlets scraped: {result['outlets_scraped']}")
print(f"Outlets saved: {result['outlets_saved']}")
```

### Async Usage

```python
import asyncio
from src.mcdonalds_outlet_scraper import scrape_and_store_mcdonalds_outlets

async def main():
    result = await scrape_and_store_mcdonalds_outlets("Selangor")
    print(f"Scraped {result['outlets_scraped']} outlets")

asyncio.run(main())
```

### Command Line Usage

```bash
# Scrape for specific search term
python -m src.mcdonalds_outlet_scraper "Kuala Lumpur"

# Default search (Kuala Lumpur)
python -m src.mcdonalds_outlet_scraper
```

### Retrieve Stored Data

```python
from src.mcdonalds_outlet_scraper import get_stored_outlets
import asyncio

async def get_data():
    # Get all outlets
    result = await get_stored_outlets()
    
    # Get outlets for specific search term
    result = await get_stored_outlets(search_term="Kuala Lumpur")
    
    # Get with pagination
    result = await get_stored_outlets(page=1, per_page=10)
    
    print(f"Total outlets: {result['total']}")
    for outlet in result['outlets']:
        print(f"- {outlet['name']}: {outlet['address']}")

asyncio.run(get_data())
```

## Project Structure

```
Backend/
├── src/
│   ├── __init__.py
│   ├── mcdonalds_outlet_scraper.py    # Main export function
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── mcdonalds_scraper.py       # Web scraping logic
│   ├── models/
│   │   ├── __init__.py
│   │   └── outlet.py                  # Pydantic models
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py              # MongoDB connection
│   └── services/
│       ├── __init__.py
│       └── outlet_service.py          # Business logic
├── requirements.txt
├── config_example.py
└── README.md
```

## API Reference

### Main Functions

#### `scrape_and_store_mcdonalds_outlets(search_term: str, overwrite_existing: bool = False)`
- **Purpose**: Main async function to scrape and store outlets
- **Parameters**: 
  - `search_term`: Search term to filter outlets
  - `overwrite_existing`: Whether to overwrite existing data
- **Returns**: Dict with scraping results

#### `scrape_mcdonalds_outlets_sync(search_term: str, overwrite_existing: bool = False)`
- **Purpose**: Synchronous wrapper for main function
- **Parameters**: Same as above
- **Returns**: Dict with scraping results

#### `get_stored_outlets(search_term: Optional[str] = None, page: int = 1, per_page: int = 50)`
- **Purpose**: Retrieve stored outlets from database
- **Parameters**:
  - `search_term`: Optional filter by search term
  - `page`: Page number (1-based)
  - `per_page`: Items per page
- **Returns**: Dict with outlets and pagination info

### Data Models

#### OutletResponse
```python
{
    "id": "string",
    "name": "string",
    "address": "string", 
    "operating_hours": "string",
    "waze_link": "string",
    "search_term": "string",
    "scraped_at": "datetime",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `mcdonalds_scraper` |
| `COLLECTION_NAME` | Collection name | `outlets` |
| `CONNECTION_TIMEOUT` | Connection timeout (seconds) | `10` |
| `MAX_POOL_SIZE` | Maximum connection pool size | `10` |
| `MIN_POOL_SIZE` | Minimum connection pool size | `1` |

### MongoDB Atlas Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster
3. Create a database user with read/write permissions
4. Whitelist your IP address or use 0.0.0.0/0 for all IPs
5. Get your connection string from the cluster connect button

## Error Handling

The scraper includes comprehensive error handling:
- Network timeouts and connection errors
- Invalid search terms
- Database connection issues
- Duplicate data handling
- Missing page elements

## Performance Considerations

- Uses headless Chrome for better performance
- Implements proper wait strategies for dynamic content
- Handles pagination automatically
- Uses connection pooling for database operations
- Includes retry logic for failed requests

## Dependencies

- `fastapi`: Web framework (for future API endpoints)
- `motor`: Async MongoDB driver
- `pymongo`: MongoDB driver
- `pydantic`: Data validation
- `selenium`: Web browser automation
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP requests
- `webdriver-manager`: Automatic WebDriver management

## License

This project is for educational and assessment purposes only.

## Contributing

This is a technical assessment project. Please follow the existing code style and patterns.

## Support

For issues related to this technical assessment, please refer to the project documentation or contact the assessment provider. 
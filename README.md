# 🍟 McDonald's Outlet Scraper - FastAPI Backend

A powerful FastAPI-based backend service for scraping, storing, and searching McDonald's outlet data with AI-powered semantic search capabilities.

## ✨ Features

- 🕸️ **Web Scraping**: Automated scraping of McDonald's outlet data using Selenium and BeautifulSoup
- 🗄️ **MongoDB Integration**: Robust data storage with PyMongo and Motor
- 🔍 **AI-Powered Search**: Vector-based semantic search using OpenAI embeddings
- 🚀 **FastAPI Framework**: High-performance async API with automatic documentation
- 📍 **Location Data**: GPS coordinates, addresses, and operating hours
- 🔄 **Background Tasks**: Async processing for large-scale operations
- 📊 **Vector Embeddings**: Advanced search capabilities with similarity matching
- 🐳 **Docker Support**: Containerized deployment
- 📚 **Auto Documentation**: Swagger UI and ReDoc integration

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.115.14
- **Database**: MongoDB (with Motor async driver)
- **AI/ML**: OpenAI GPT-4, LangChain
- **Web Scraping**: Selenium, BeautifulSoup4
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio
- **Server**: Uvicorn

## 📋 Prerequisites

- Python 3.8+
- MongoDB Atlas account or local MongoDB instance
- OpenAI API key
- Chrome/Chromium browser (for Selenium)

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd Backend/McDonalds-Outlet-Scraper-FastAPI-Backend
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
# MongoDB Configuration
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
MONGODB_DB_NAME=mcdonalds_outlets

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# API Configuration (Optional)
API_HOST=127.0.0.1
API_PORT=8000
LOG_LEVEL=info
```

### 4. Run the Application
```bash
# Using the run script (recommended)
python run_api.py

# Or directly with uvicorn
uvicorn src.api.mcdonalds_api:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **Main API**: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and API information |
| `POST` | `/scrape-outlets` | Scrape outlets without saving to DB |
| `POST` | `/save-outlets` | Scrape and save outlets to database |
| `GET` | `/outlets` | Retrieve saved outlets with pagination |
| `DELETE` | `/outlets` | Delete all outlets from database |
| `POST` | `/scrape/rescrape-all` | Background task to rescrape all outlets |

### AI Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/search` | AI-powered semantic search |

### Example API Calls

#### 1. Scrape Outlets (Save to DB)
```bash
curl -X POST "http://127.0.0.1:8000/save-outlets" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Kuala Lumpur",
    "overwrite_existing": false
  }'
```

#### 2. Get Outlets with Pagination
```bash
curl -X GET "http://127.0.0.1:8000/outlets?page=1&per_page=10&search_term=Kuala%20Lumpur"
```

#### 3. AI-Powered Search
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me 24-hour McDonald's outlets with drive-thru in KL"
  }'
```

## 🏗️ Project Structure

```
src/
├── api/                    # API routes and endpoints
│   ├── mcdonalds_api.py   # Main API application
│   ├── search_api.py      # AI search endpoints
│   └── responses.py       # Response models
├── database/              # Database configuration
│   ├── connection.py      # MongoDB connection setup
│   └── utils.py          # Database utilities
├── models/               # Pydantic models
│   └── outlet.py         # Outlet data models
├── scraper/              # Web scraping modules
│   ├── mcdonalds_scraper.py  # Main scraper logic
│   └── utils.py          # Scraping utilities
└── services/             # Business logic services
    ├── outlet_service.py  # Outlet CRUD operations
    └── vector_service.py  # AI/Vector operations
```

## 🗄️ Data Models

### Outlet Model
```python
{
  "_id": "ObjectId",
  "name": "McDonald's Bukit Bintang",
  "address": "120-120A Jalan Bukit Bintang, 55100, Kuala Lumpur",
  "operating_hours": "24 Hours",
  "waze_link": "https://waze.com/ul/h9icrq0r43",
  "latitude": 3.146847,
  "longitude": 101.710931,
  "telephone": "03-2141 8454",
  "attribute": "24 Hours Drive-Thru, McCafe, Delivery Available",
  "search_term": "Kuala Lumpur",
  "embedding": [0.1, 0.2, ...], // Vector embedding for AI search
  "scraped_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## 🔍 AI Search Features

The backend includes advanced AI-powered search capabilities:

- **Vector Embeddings**: Outlet data is converted to OpenAI embeddings
- **Semantic Search**: Find outlets based on meaning, not just keywords
- **Natural Language Queries**: Ask questions in plain English
- **Context-Aware Responses**: GPT-4 powered responses with relevant outlet data

### Example Queries
- "Find 24-hour outlets with drive-thru"
- "Which McDonald's has WiFi and is near KLCC?"
- "Show me outlets with McCafe in Petaling Jaya"

## 🧪 Testing

Run tests with pytest:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_outlet_service.py -v
```

## 🐳 Docker Deployment

### Build and Run with Docker
```bash
# Build the image
docker build -t mcdonalds-outlet-api .

# Run the container
docker run -p 8000:8000 --env-file .env mcdonalds-outlet-api
```

### Docker Compose (if available)
```bash
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONGODB_URL` | MongoDB connection string | - | ✅ |
| `MONGODB_DB_NAME` | Database name | `mcdonalds_outlets` | ❌ |
| `OPENAI_API_KEY` | OpenAI API key for AI features | - | ✅ |
| `API_HOST` | API host address | `127.0.0.1` | ❌ |
| `API_PORT` | API port number | `8000` | ❌ |
| `LOG_LEVEL` | Logging level | `info` | ❌ |

### MongoDB Setup

1. Create a MongoDB Atlas cluster or set up local MongoDB
2. Create a database named `mcdonalds_outlets`
3. The application will automatically create the required collections

## 🔧 Development

### Code Style
- Follow PEP 8 conventions
- Use Black for code formatting
- Type hints are mandatory
- Async/await for I/O operations

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes following the existing patterns
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## 📊 Performance

- **Async Operations**: All database and external API calls are asynchronous
- **Connection Pooling**: MongoDB connection pooling for optimal performance
- **Background Tasks**: Heavy operations run in background to maintain API responsiveness
- **Caching**: Vector embeddings are cached to reduce API calls

## 🚨 Error Handling

The API implements comprehensive error handling:
- HTTP status codes for different error types
- Detailed error messages in JSON format
- Logging for debugging and monitoring
- Graceful degradation for external service failures

## 📈 Monitoring

Monitor your API with:
- FastAPI's built-in metrics
- MongoDB Atlas monitoring
- Application logs
- Custom health checks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the [API documentation](http://127.0.0.1:8000/docs)
- Review the logs for error details
- Open an issue in the repository

---

**Built with ❤️ using FastAPI and modern Python practices** 

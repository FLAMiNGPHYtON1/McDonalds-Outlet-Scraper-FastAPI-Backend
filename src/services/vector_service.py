"""
This service handles the creation of vector embeddings using OpenAI.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
import logging

from ..models.outlet import OutletInDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSIONS = 512

# Initialize OpenAI client
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    raise

def generate_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding for the given text using OpenAI's API.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the vector embedding.
    
    Raises:
        Exception: If the embedding generation fails.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input text must be a non-empty string.")

    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=VECTOR_DIMENSIONS,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding for text: '{text[:50]}...': {e}")
        # In a production scenario, you might want more robust error handling,
        # like retries or fallback mechanisms.
        raise

def get_outlet_text_representation(outlet: OutletInDB) -> str:
    """
    Creates a single text string from an outlet's data for embedding.
    
    Args:
        outlet: The outlet object.
        
    Returns:
        A string combining the outlet's name, address, and attributes.
    """
    parts = [
        f"Name: {outlet.name}",
        f"Address: {outlet.address}",
    ]
    if outlet.operating_hours:
        parts.append(f"Hours: {outlet.operating_hours}")
    if outlet.attribute:
        parts.append(f"Services: {outlet.attribute}")
    
    return ". ".join(parts) 
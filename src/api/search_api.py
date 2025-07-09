"""
API endpoint for performing vector-based semantic search on outlets.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel

from ..services.outlet_service import OutletService
from ..services.vector_service import openai_client, get_outlet_text_representation
from ..models.outlet import OutletInDB

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class SearchQuery(BaseModel):
    query: str

@router.post("/search", response_model=Dict[str, Any])
async def search(
    query: str = Body(..., embed=True),
    outlet_service: OutletService = Depends(OutletService)
):
    """
    Performs a semantic search for outlets based on a user query.

    This endpoint takes a user's query, finds the most relevant outlets
    using vector search, and then uses a language model to generate a
    natural language response based on the search results.
    """
    try:
        # 1. Find relevant outlets using vector search
        logger.info(f"Performing vector search for query: '{query}'")
        search_results = await outlet_service.search_outlets(query, limit=5)

        if not search_results:
            return {"response": "I couldn't find any outlets relevant to your question."}

        # 2. Construct a context for the language model
        context = "You are a helpful assistant for finding McDonald's outlet information. Based on the following data, answer the user's question.\n\n"
        context += "Relevant outlet information:\n"
        for i, outlet in enumerate(search_results):
            context += f"{i+1}. {get_outlet_text_representation(outlet)}\n"
        
        # 3. Call OpenAI's chat model to generate a response
        logger.info("Generating response with OpenAI chat model.")
        completion_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": f"Here is my question: {query}"}
            ],
            temperature=0.7,
            max_tokens=250
        )

        response_content = completion_response.choices[0].message.content
        
        # 4. Return the generated response
        return {"response": response_content.strip()}

    except Exception as e:
        logger.error(f"An error occurred during search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during the search process.") 
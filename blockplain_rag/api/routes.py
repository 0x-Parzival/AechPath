import logging
import aiohttp
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from api.schemas import QueryRequest, QueryResponse, BlockchainStats
from config import BLOCKCHAIN_API_URL, LLM_API_KEY, LLM_API_URL, LLM_MODEL

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "BlockPlain RAG API is running"}

@router.post("/query", response_model=QueryResponse)
async def query_blockchain(request: QueryRequest):
    """Query the blockchain using natural language"""
    try:
        # Query the Pathway index (URL configured to point to the Pathway service)
        pathway_url = "http://localhost:8000/query"  # This is internal to our service
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                pathway_url,
                json={"query": request.query, "top_k": request.top_k}
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Pathway API error: {text}")
                    raise HTTPException(status_code=500, detail="Error querying blockchain data")
                
                results = await response.json()
        
        # Get LLM response if API key is available
        llm_response = None
        if LLM_API_KEY:
            # Create context from the query results
            context = "\n\n".join([item["text"] for item in results])
            llm_response = await get_llm_response(request.query, context)
        
        return QueryResponse(
            results=results,
            llm_response=llm_response
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=BlockchainStats)
async def get_blockchain_stats():
    """Get current blockchain statistics"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BLOCKCHAIN_API_URL}/state") as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Error fetching blockchain state")
                
                state = await response.json()
                
                return BlockchainStats(
                    block_count=state.get("blockCount", 0),
                    tx_count=state.get("txCount", 0),
                    pending_tx_count=state.get("pendingTxCount", 0),
                    latest_block=state.get("latestBlock", {"x": 0, "y": 0}),
                    latest_timestamp=state.get("latestTimestamp", "")
                )
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_llm_response(query: str, context: str) -> str:
    """Get a response from the LLM service"""
    if not LLM_API_KEY:
        return "LLM integration not configured"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare the prompt
            system_prompt = "You are an AI assistant that helps users understand blockchain data from BlockPlain, a 2D blockchain. Answer questions based on the provided context."
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_API_KEY}"
            }
            
            data = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            async with session.post(
                LLM_API_URL,
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    logger.warning(f"LLM API error: {await response.text()}")
                    return "Unable to generate AI response"
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error getting LLM response: {e}")
        return f"Error generating AI response: {str(e)}"
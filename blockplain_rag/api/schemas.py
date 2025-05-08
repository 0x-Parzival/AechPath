from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class QueryResult(BaseModel):
    id: str
    document_type: str
    text: str
    score: float
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    results: List[QueryResult]
    llm_response: Optional[str] = None

class BlockchainStats(BaseModel):
    block_count: int
    tx_count: int
    pending_tx_count: int
    latest_block: Dict[str, int]
    latest_timestamp: str
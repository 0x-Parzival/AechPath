import os
import logging
import pathway as pw
from typing import Dict, Any, List, Optional, Tuple

from pipeline.embeddings import EmbeddingEngine
from config import EMBEDDING_MODEL, PATHWAY_HOST, PATHWAY_PORT

logger = logging.getLogger(__name__)

class BlockchainRAGPipeline:
    """Real-time RAG pipeline for blockchain data using Pathway"""
    
    def __init__(self, embedding_model: str = EMBEDDING_MODEL):
        self.embedding_engine = EmbeddingEngine(embedding_model)
        self.host = PATHWAY_HOST
        self.port = PATHWAY_PORT
        self.pathway_context = None
        self.index = None
    
    def build_pipeline(self, blockchain_connector):
        """Build the Pathway RAG pipeline"""
        # Create Pathway context
        self.pathway_context = pw.io.python.ConnectorContext()
        
        # Create input connector
        @pw.io.python.connector
        def blockchain_data_connector(context):
            blockchain_connector.pathway_connector(context)
        
        # Create input table
        input_table = blockchain_data_connector(self.pathway_context)
        
        # Process the data (extract text, metadata, etc.)
        processed_data = input_table.select(
            id=pw.this["_id"],
            document_type=pw.this["_document_type"],
            text=pw.this["_text"],
            metadata=pw.this
        )
        
        # Generate embeddings
        @pw.udf
        def embed(text: str) -> List[float]:
            return self.embedding_engine.embed_text(text)
        
        embedded_data = processed_data.select(
            id=pw.this.id,
            document_type=pw.this.document_type,
            text=pw.this.text,
            metadata=pw.this.metadata,
            embedding=embed(pw.this.text)
        )
        
        # Build vector index
        self.index = embedded_data.build_vector_index(
            embedding_field="embedding",
            index_field="id"
        )
        
        # Create query service
        @pw.udf
        def process_query(query: str) -> List[float]:
            return self.embedding_engine.embed_text(query)
        
        def query_handler(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
            """Handle queries against the vector index"""
            query_embedding = process_query(query)
            
            # Search the index
            results = self.index.query(
                query_embedding=query_embedding,
                k=top_k
            )
            
            # Format results
            formatted_results = []
            for result in results:
                item = {
                    "id": result.id,
                    "document_type": result.document_type,
                    "text": result.text,
                    "score": result.score,
                    "metadata": result.metadata
                }
                formatted_results.append(item)
                
            return formatted_results
        
        # Set up REST API endpoint
        self.query_service = pw.io.http.rest_connector(
            host=self.host,
            port=self.port,
            query_fn=query_handler
        )
        
        logger.info(f"RAG pipeline built, will serve queries at http://{self.host}:{self.port}")
        
    def run(self):
        """Run the Pathway pipeline"""
        pw.run()
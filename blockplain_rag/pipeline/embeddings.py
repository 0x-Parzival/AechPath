import logging
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    """Generates text embeddings for blockchain data"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Initialized embedding model: {model_name}")
        
    def embed_text(self, text: str) -> List[float]:
        """Convert text to embedding vector"""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.model.get_sentence_embedding_dimension()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert batch of texts to embedding vectors"""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.model.get_sentence_embedding_dimension()] * len(texts)
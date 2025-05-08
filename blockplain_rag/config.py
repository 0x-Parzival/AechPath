import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent

# BlockPlain Go API connection
BLOCKCHAIN_API_URL = os.getenv("BLOCKCHAIN_API_URL", "http://localhost:8080")
BLOCKCHAIN_WS_URL = os.getenv("BLOCKCHAIN_WS_URL", "ws://localhost:8080/ws")

# Pathway settings
PATHWAY_HOST = os.getenv("PATHWAY_HOST", "localhost")
PATHWAY_PORT = int(os.getenv("PATHWAY_PORT", "8000"))

# Embedding model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# LLM API settings
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Web UI settings
WEB_HOST = os.getenv("WEB_HOST", "localhost")
WEB_PORT = int(os.getenv("WEB_PORT", "8050"))
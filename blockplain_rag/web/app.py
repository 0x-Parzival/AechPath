import logging
import aiohttp
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from config import PATHWAY_PORT, WEB_HOST, WEB_PORT

logger = logging.getLogger(__name__)
# Initialize FastAPI app
app = FastAPI(
    title="BlockPlain Explorer",
    description="Web interface for BlockPlain blockchain",
    version="1.0.0"
)

# Set up templates and static files
templates_path = Path(__file__).parent / "templates
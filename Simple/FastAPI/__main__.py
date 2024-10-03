from fastapi import FastAPI
from dotenv import load_dotenv
from loguru import logger
from anthropic.types import Message
from ..types.yelpTypes import Review, BusinessInfo, Location

import anthropic

import json
import os

load_dotenv()

CLAUDE_KEY = os.getenv("CLAUDE_KEY")

assert CLAUDE_KEY is not None and CLAUDE_KEY != "", "FATAL: Could get API key from .env"

client = anthropic.Anthropic(
    api_key=CLAUDE_KEY
)

app = FastAPI()


@app.get("/health")
async def check_endpoint():
    return {
        "Status": "OK",
        "code": 200
        }

@app.get("/upload_results")
async def upload_results(business, reviews: list[str]):
    """
        Uploads json to Claude3.5
    """
    pass

def start_fastapi():
    
     
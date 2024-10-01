from fastapi import FastAPI
from dotenv import load_dotenv
from loguru import logger
import json
import os

load_dotenv()

CLAUDE_KEY = os.getenv("CLAUDE_KEY")

assert CLAUDE_KEY is not None and CLAUDE_KEY != "", "FATAL: Could get API key from .env"

app = FastAPI()

@app.get("/health")
async def check_endpoint():
    return {
        "Status": "OK",
        "code": 200
        }

@app.get("/upload_results")
async def upload_results(json: str):
    """
        Uploads json to Claude3.5
    """
    pass 
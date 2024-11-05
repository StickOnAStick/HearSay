from ..types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS
from ..types.API import LLMOutput, Keyword
from ..types.reviews import Review

from loguru import logger

import csv
import requests

class APIInterface:

    def __init__(
            self, 
            model: ModelType, 
            embedding: EmbeddingModel, 
            sysPrompt: str, 
            reviews: list[Review]
            ):
        # excessive inputs in an attempt to keep this CLI friendly.
        


        self.model: ModelType = model or ModelType.CLAUDE                             # Default to claude (has sys prompt)
        self.embedding_model: EmbeddingModel = embedding or EmbeddingModel.TEXT_SMALL3    # Default to anthropic
        self.sys_prompt: str = sysPrompt or MODEL_SYS_PROMPTS['default']
        self.reviews: list[Review] = None
        self.llmOutput: list[LLMOutput] | None = None
        self.tokenLimit: int = 

    
    def get_token_limit(self, model: ModelType) -> int:
        logger.debug(f"Senting request for model: {model}")
        chunk_size = requests.get(f"{FAST_API_URL}/token_limit/{model.value}")
        if not chunk_size.status_code == 200:
            logger.exception(chunk_size.json())
            raise SystemExit("Fast API token limit not recieved")
        
        # logger.debug(f"Response: {chunk_size.json()}")
        self.tokenLimit = chunk_size.json()['token_limit']
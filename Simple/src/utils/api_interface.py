from Simple.src.types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS, MODEL_TOKEN_LIMITS
from Simple.src.types.reviews import Review
from Simple.src.types.API import LLMOutput, Keyword
from Simple.src.types.client.clientstate import ReadOnlyClientState


from loguru import logger
from collections import deque
from tqdm.asyncio import tqdm

import requests
import asyncio
import aiohttp

class APIInterface:
    def __init__(self, state: ReadOnlyClientState):
        
        if not state:
            raise ValueError("Could not create an API interface due to corrupted client state.")
        self.state = state

    def get_token_limit(self, from_source: bool = False) -> None:
        if not from_source:
            return MODEL_TOKEN_LIMITS[self.state.model]
        
        logger.debug(f"Sending request for model: {self.state.model}")
        token_limit_res = requests.get(f"{self.state.end_point}/token_limit/{self.state.model.value}")
        if not token_limit_res.status_code == 200:
            logger.error(f"Could not obtain token limit via API. {token_limit_res.json()}")
        return token_limit_res.json()["token_limit"]
    
    def get_llmOutput(
            # Filter by product id
            self,
            filter_product_id: set[str] | None = None  # Not implemented
            ) -> deque[LLMOutput]:
        output: deque[LLMOutput] = asyncio.run(self._extract_keywords_sentiment())
        # Fetch the embeddings for all the keywords
        self._get_embeddings(llmOutputs=output)
        return output

    async def _extract_keywords_sentiment(self) -> deque[LLMOutput]:
        """
            Process all chunks concurrently
        """
        output = deque()
        async with aiohttp.ClientSession() as session:
            total_products = len(self.state.reviews.keys())

            tasks = [self._get_chunk_keywords_sentiment(session=session, prod_uuid=key, chunks=chunks) for key, chunks in self.state.reviews.items()]

            results = await tqdm.gather(*tasks, total=total_products, desc="Extracting Keywords and Sentiment from product reviews", unit=" product")

            for res in results:
                output.extend(res)

        return output

    async def _get_chunk_keywords_sentiment(self, session: aiohttp.ClientSession, prod_uuid: str, chunks: deque[deque[Review]]):
        """
            Process chunks for a single product via concurrent async API requests
        """
        tasks = []
        url = f"{self.state.end_point}/feed_model/{self.state.model.value}?prompt={self.state.prompt}"

        for chunk in chunks:
            serialized_reviews = [review.model_dump() for review in chunk]
            tasks.append(self.fetch(session, url, serialized_reviews))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        output = []

        for chunk, res in zip(chunks, responses):
            if isinstance(res, Exception):
                logger.error(res)
                continue
            res['product_id'] = prod_uuid # Add in the product ID to the res-dict.

            for kw in res.get("keywords", []):
                kw["product_id"] = prod_uuid

            llmOut = LLMOutput(**res)
            llmOut._set_reviews(chunk)
            output.append(llmOut)

        return output

    def _get_embeddings(self, llmOutputs: list[LLMOutput]) -> None:
        """
            Function that updates the embeddings for each keyword

            TODO: Batch API requests. 
        """

        for idx, llmOutput in enumerate(llmOutputs):
            res = requests.get(f"{self.state.end_point}/get_embeddings/{self.state.embed_model.value}", json=llmOutput.model_dump())
            if res.status_code != 200:
                logger.exception(f"Failed to connect to fast api. Status code: {res.status_code} Response text: {res.text}")

            # Sanity check
            try:
                response_data = res.json()
            except requests.exceptions.JSONDecodeError:
                logger.exception(f"Failed to decode the JSON response. Status code: {res.status_code} Response text: {res.text}")

            if llmOutput.summary != response_data.get('summary'):
                logger.exception(f"Somehow you recieved the wrong object when trying to embed the keywords. 07")
            
            try:
                keyword_embeddings = response_data.get('keywords', [])
                if len(keyword_embeddings) != len(llmOutput.keywords):
                    logger.exception(f"Mismatch between keywords and embeddings count in response for llmOutput at index {idx}")
                    continue
                
                for keyword_obj, embedding_data in zip(llmOutput.keywords, keyword_embeddings):
                    keyword_obj.embedding = embedding_data.get('embedding')
            except KeyError as e:
                logger.exception(f"Missing expected key in the api response {e}")

            # You need to index this. Otherwise the calling function will not be updated
            llmOutputs[idx] = llmOutput

    async def fetch(self, session: aiohttp.ClientSession, url: str, json_data: any):
        """Handles async requests and error handling"""
        async with session.post(url, json=json_data) as res:
            if res.status != 200:
                res_json = await res.json()
                return Exception(f"API failed: {res_json.get('detail', 'Unknown error')}")
            return await res.json()
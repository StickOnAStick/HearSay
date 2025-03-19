from Simple.src.types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS, MODEL_TOKEN_LIMITS
from Simple.src.types.reviews import Review
from Simple.src.types.API import LLMOutput, Keyword
from Simple.src.types.client.clientstate import ReadOnlyClientState


from tqdm import tqdm
from loguru import logger
from collections import deque

import multiprocessing
import requests

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
        output: deque[LLMOutput] = []
        
        # Get all the responses for extracting KeyWords
        total_products = len(self.state.reviews.keys())
        with tqdm(total=total_products, desc="Embedding all products", unit=" product") as pbar:
            with multiprocessing.Pool(processes=min(8, multiprocessing.cpu_count())) as pool:
                
                for key, chunks in pool.starmap_async()

        for key, chunks in self.state.reviews.items():
            logger.debug(f"Found {len(chunks)} chunks for product_id: {key}")
            for chunk in chunks:

                serialized_reviews = [review.model_dump() for review in chunk]
                logger.debug(f"Serialized {len(serialized_reviews)} reviews\n{serialized_reviews}")
                res = requests.post(
                    f"{self.state.end_point}/feed_model/{self.state.model.value}?prompt={self.state.prompt}",
                    json=serialized_reviews
                    )
                if res.status_code != 200:
                    logger.error(f"API failed to complete request for keywords.\nError msg:\n{res.json()['detail']}")
                llmOut: LLMOutput = LLMOutput(**res.json())
                llmOut._set_reviews(chunk) # Stitch together the reviews used at time of creation
                output.append(llmOut)

        # Fetch the embeddings for all the keywords
        self._get_embeddings(llmOutputs=output)
        return output

    def _extract_keywords_sentiment(self, )

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

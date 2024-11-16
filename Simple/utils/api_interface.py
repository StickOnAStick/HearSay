from ..types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS, MODEL_TOKEN_LIMITS
from ..types.reviews import Review
from ..types.API import LLMOutput, Keyword
from ..constants.constants import FAST_API_URL

from loguru import logger
from typing import Tuple

import requests
import csv

class APIInterface:
    def __init__(self, file_path: str, 
                 model: ModelType | None, 
                 embedding_model: EmbeddingModel | None, 
                 prompt: str | None,
                 max_reviews: int | None
                 ):
        
        # Configuration
        self.model: ModelType =                 model if model else ModelType.CLAUDE
        self.embedding_model: EmbeddingModel =  embedding_model if embedding_model else EmbeddingModel.TEXT_SMALL3
        self.prompt: str =                      prompt if prompt else MODEL_SYS_PROMPTS["default"]
        # Data
        self.token_limit: int = MODEL_TOKEN_LIMITS[ModelType.CLAUDE]
        self.reviews: dict[str, list[list[Review]]] = self.load_data(file=file_path, max_reviews=max_reviews)


    def _parse_csv(self, file: str, max_reviews: int = 500) -> list[Review]:
        if max_reviews is None:
            max_reviews = 500 # Annoying that I have to do this despite a default value

        with open(file=file, newline='', mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)

            column_names = reader.fieldnames
            logger.debug(f"Found field names: {column_names}")
            
            reviews: list[Review] = [] 
            count = 0
            for row in reader:
                if count == max_reviews:
                    break
                review = Review(
                    review_id=row.get("Id"),
                    product_id=row.get("ProductId"),
                    rating=row.get("Score"),
                    summary=row.get("Summary"),
                    text=row.get("Text"),
                    date=row.get("Time")
                )
                #logger.debug(f"Constructed review object: {review}")
                reviews.append(review)
                count += 1
                
        if len(reviews) == 0:
            raise SystemExit("No reviews found in file!")

        return reviews

    def _chunk_reviews(self, reviews: list[Review]) -> dict[str, list[list[Review]]]:
        
        # Sort by product id.
        reviews_by_product: dict[str, list[Review]] = {}
        for review in reviews: 
            reviews_by_product.setdefault(review.product_id, []).append(review)
        logger.debug(f"Chunking reviews for {len(reviews_by_product.keys())} products")
        # Chunk each 
        chunked_reviews: dict[str, list[list[Review]]] = {}
        for prod_id, prod_reveiews in reviews_by_product.items():
            current_chunk: list[Review] = []
            current_chunk_size: int = 0
            
            for review in prod_reveiews:
                review_token_count: int = review.token_count()

                # If the review itself or adding it will exceed max chunk size, create new chunk
                if review_token_count+current_chunk_size > self.get_token_limit():
                   chunked_reviews.setdefault(prod_id, []).append(current_chunk)
                   current_chunk = []
                   current_chunk_size = 0
                
                # Add the review to the current chunk
                current_chunk.append(review)
                current_chunk_size += review_token_count
        
        # append if last chunk is not empty
        if current_chunk:
            chunked_reviews.setdefault(prod_id, []).append(current_chunk)
        return chunked_reviews

    def load_data(self, file: str, max_reviews: int = 500) -> None:
        """
        Function for pasrsing amazon CSV and returning dictionary sorting reviews by product_id and token_limit.

        #### input:
            max_reviews (int) --- keep small for testing
        
        Created Reviews object shape:
        ```
        {
            "product_id": list[list[Review]]
        }
        ```
        Where each outer list contains the "chunked" reviews.
        And each inner list of a chunk is the maximum number of reviews which can fit in one-shot.
        """
        # Load the reviews from a csv
        reviews: list[Review] = self._parse_csv(file=file, max_reviews=max_reviews)
        logger.debug(f"{len(reviews)} reviews found.")
        # Sort the reviews by product id and token_limit:
        return self._chunk_reviews(reviews=reviews)

    def get_token_limit(self, from_source: bool = False) -> None:
        if not from_source:
            return MODEL_TOKEN_LIMITS[self.model]
        
        logger.debug(f"Sending request for model: {self.model}")
        token_limit_res = requests.get(f"{FAST_API_URL}/token_limit/{self.model.value}")
        if not token_limit_res.status_code == 200:
            logger.error(f"Could not obtain token limit via API. {token_limit_res.json()}")
        return token_limit_res.json()["token_limit"]
    
    def get_llmOutput(
            # Filter by product id
            self,
            filter_product_id: set[str] | None = None
            ) -> list[LLMOutput]:
        output: list[LLMOutput] = []
        
        # Get all the responses for extracting KeyWords
        for key, chunks in self.reviews.items():
            if filter_product_id is not None and key in filter_product_id:
                for chunk in chunks:
                    serialized_reviews = [review.model_dump() for review in chunk]
                    
                    res = requests.get(
                        f"{FAST_API_URL}/feed_model/{self.selected_model.value}?prompt={self.prompt}",
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

    def _get_embeddings(self, llmOutputs: list[LLMOutput]) -> None:
        """
            Function that updates the embeddings for each keyword

            #### TODO:
            Batching requests to API server. 
        """

        for idx, llmOutput in enumerate(llmOutputs):
            res = requests.get(f"{FAST_API_URL}/get_embeddings/{self.model.value}", json=llmOutput.model_dump())
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

from ..types.reviews import Review

from abc import ABC, abstractmethod
from loguru import logger
from typing import final

import csv

class DataParser(ABC):
    """ Abstract class for all data parsers
        Similar to virtual classes in c++
    """
    def __init__(self, data_source: str, max_reviews: int = 1000):
        if not data_source:
            raise ValueError("No data source passed in")
        self.data_source: str = data_source
        self.max_reviews: int = max_reviews

    @abstractmethod
    def _parse(self) -> list[Review]:
        """Parses the data source and stores the reviews internally"""
        pass

    @abstractmethod
    def get_batched_reviews(self, token_limit: int) -> dict[str, list[list[Review]]]:
        """
            Batches reviews according to token limit provided by API.
        """
        pass

    @final # Cannot override method implementation
    def set_batch_size(self, batch_size: int) -> None:
        """Set's the parsers batch size"""
        self.batch_size = batch_size


class AmazonParser(DataParser):
    def __init__(self, data_source: str):
        super().__init__(data_source)
    
    def _parse(self) -> list[Review]:
        with open(file=self.data_source, newline='', mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            column_names = reader.fieldnames
            logger.debug(f"Found field names: {column_names}")
            
            reviews: list[Review] = [] 
            count = 0
            for row in reader:
                if count == self.max_reviews:
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
            logger.warning(f"No reviews found in file: {self.data_source}")

        return reviews
    
    def get_batched_reviews(self, token_limit: int) -> dict[str, list[list[Review]]]:
        """
            Batches data according to selected model's token limit and product ID.

            Ex: 
            {
                "1": [ [{text: str, rating: int...}], [{text, str, rating: int...}] ]
                "2": [ [{text: str, rating: int...}], [{text, str, rating: int...}] ]
            }
        """
        # Sort by product id.
        reviews_by_product: dict[str, list[Review]] = {}
        for review in self._parse(): 
            reviews_by_product.setdefault(review.product_id, []).append(review)
        logger.debug(f"Chunking reviews for {len(reviews_by_product.keys())} products")
        # Chunk each 
        chunked_reviews: dict[str, list[list[Review]]] = {}
        for prod_id, prod_reveiws in reviews_by_product.items():
            current_chunk: list[Review] = []
            current_chunk_size: int = 0
            
            for review in prod_reveiws:
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
    
class YelpParser(DataParser):
    pass
    
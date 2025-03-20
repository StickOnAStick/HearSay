from Simple.src.types.reviews import Review
from Simple.src.types.models import MODEL_SYS_PROMPTS

from abc import ABC, abstractmethod
from loguru import logger
from pathlib import Path
from collections import deque
from tqdm import tqdm

import multiprocessing
import tiktoken
import csv

class DataParser(ABC):
    """ Abstract class for all data parsers
        Similar to virtual classes in c++
    """
    def __init__(self, data_source: Path, max_reviews: int = 1000):
        if not data_source:
            raise ValueError("No data source passed in")
        self.data_source: Path = data_source
        self.max_reviews: int = max_reviews

    @abstractmethod
    def _parse(self) -> list[Review]:
        """Parses the data source and stores the reviews internally"""
        pass

    @abstractmethod
    def _chunk_reviews(self,
        prod_id: str,                   # Product ID
        prod_reviews: list[Review],     # Reviews for this ID 
        token_limit: int,               # Token limit
        queue: multiprocessing.Queue,   # Queue to return output
        line_number: int | None         # Line number to print output. If None, no output is printed
        ) -> None:
        """Worker script for chunking reviews according to token count."""

    @abstractmethod
    def get_batched_reviews(self, token_limit: int) -> dict[str, deque[deque[Review]]]:
        """
            Batches reviews according to token limit provided by API.
        """
        pass
        

class AmazonParser(DataParser):
    def __init__(self, data_source: Path | None, max_reviews: int = 1000):
        super().__init__(data_source, max_reviews)
    
    def _parse(self) -> list[Review]:
        # Search every file (including those found in sub-directories) of this directory.
        reviews: list[Review] = [] 

        for file in self.data_source.rglob("*.csv"):
            """
                Open the file and parse the review.
                NOTE: Each file within the selected datasource should be in the __SAME FORMAT__. Otherwise, your parser wont work!
            """
            logger.debug(f"Opening data source: {file}")
            with open(file=file, newline='', mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                
                count = 0
                print("\nExtracting reviews....")
                for row in reader:
                    if count == self.max_reviews:
                        print(f"\nComplete!\n")
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
                    # adhere to the maximum number of reviews for par
                    print(f"\rProgress: [{"=" * (count * 50 // self.max_reviews):<50}] {count / self.max_reviews:.2%}", end="")
                
        
        if len(reviews) == 0:
            logger.warning(f"No reviews found in file: {self.data_source}")

        return reviews

    def _chunk_reviews(self, 
        prod_id: str, 
        prod_reviews: deque[Review], 
        token_limit: int, 
        ):
        """Worker function to chunk reviews for a single product_id """

        chunks: deque[deque[Review]] = deque()
        current_chunk: deque[Review] = deque()
        current_chunk_size: int = 0

        for review in prod_reviews:
            review_token_count = review.token_count()

            # Start a new chunk if needed
            if current_chunk_size + review_token_count > token_limit:
                chunks.append(current_chunk)
                current_chunk = deque()
                current_chunk_size = 0
            
            # Add review to the current chunk
            current_chunk.append(review)
            current_chunk_size += review_token_count
           

        # Append last chunk if remaining reviews
        if current_chunk:        
            chunks.append(current_chunk)
        
        return prod_id, chunks
    
    
    def get_batched_reviews(self, token_limit: int) -> dict[str, deque[deque[Review]]]:
        """
            Batches data according to selected model's token limit and product ID.

            Ex: 
            {
                "1": [ [{text: str, rating: int...}], [{text, str, rating: int...}] ]
                "2": [ [{text: str, rating: int...}], [{text, str, rating: int...}] ]
            }
        """
        # Sort by product id.
        reviews_by_product: dict[str, deque[Review]] = {}
        for review in self._parse():
            reviews_by_product.setdefault(review.product_id, []).append(review)
        
        total_products = len(reviews_by_product)
        logger.debug(f"Chunking reviews for {len(reviews_by_product.keys())} products")
        
        with tqdm(total=total_products, desc="Chunking Reviews", unit=" product") as pbar:
            # Create MP pool
            with multiprocessing.Pool(processes=min(8, multiprocessing.cpu_count())) as pool: # Maximum of 8 processes (Excessive process spawn can overload system)
                results = []
                for result in pool.starmap_async(self._chunk_reviews, [(prod_id, reviews, token_limit) for prod_id, reviews in reviews_by_product.items()]).get():
                    results.append(result)
                    pbar.update(1) #update progress bar
        # Convert results back into dict
        chunked_reviews: dict[str, deque[deque[Review]]] = {prod_id: chunks for prod_id, chunks in results}
        return chunked_reviews
    
class YelpParser(DataParser):
    pass
    
from Simple.src.types.reviews import Review

from abc import ABC, abstractmethod
from loguru import logger
from pathlib import Path
from collections import deque

import multiprocessing
import sys
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
    def get_batched_reviews(self, token_limit: int) -> dict[str, list[list[Review]]]:
        """
            Batches reviews according to token limit provided by API.
        """
        pass
        

class AmazonParser(DataParser):
    def __init__(self, data_source: Path | None, max_reviews: int = 1000):
        super().__init__(data_source, max_reviews)
    
    def _parse(self) -> list[Review]:
        # Search every file (including those found in sub-directories) of this directory.
        for file in self.data_source.rglob("*.csv"):
            """
                Open the file and parse the review.
                NOTE: Each file within the selected datasource should be in the __SAME FORMAT__. Otherwise, your parser wont work!
            """
            logger.debug(f"Opening data source: {file}")
            with open(file=file, newline='', mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                
                reviews: list[Review] = [] 
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
        prod_reviews: list[Review], 
        token_limit: int, 
        queue: multiprocessing.Queue,
        progress_dict,
        line_number
        ):
        """Worker function to chunk reviews for a single product_id """

        chunks: deque[deque[Review]] = deque()
        current_chunk: deque[Review] = deque()
        current_chunk_size: int = 0
        num_reviews: int = 0
        total_reviews: int = len(prod_reviews)

        for review in prod_reviews:
            review_token_count = review.token_count()

            # Start a new chunk if needed
            if current_chunk_size + review_token_count > token_limit:
                chunks.append(current_chunk)
                current_chunk = []
                current_chunk_size = 0
            
            # Add review to the current chunk
            current_chunk.append(review)
            current_chunk_size += review_token_count
            num_reviews += 1
            if num_reviews % 10 == 0:
                sys.stdout.write(f"\033[{line_number};0HProgress ({prod_id}):  [{"=" * (num_reviews * 50 // total_reviews):<50}] {num_reviews /total_reviews:.2%}\n")
                sys.stdout.flush()

        # Append last chunk if remaining reviews
        if current_chunk:        
            chunks.append(current_chunk)
        
        # Place the result into the MP queue for later join
        queue.put((prod_id, list(chunks))) 
    
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
        
        # Create MP queue
        queue = multiprocessing.Queue()

        # Shared dict for tracking progress
        progress_dict = {prod_id: multiprocessing.Value('i', 0) for prod_id in reviews_by_product.keys()}

        # Launch processes
        processes = []
        for idx, (prod_id, prod_reviews) in enumerate(reviews_by_product.items()):
            line_number = idx + 2 # Each process prints on a new line
            p = multiprocessing.Process(target=self._chunk_reviews, args=(prod_id, prod_reviews, token_limit, queue, progress_dict, line_number))
            processes.append(p)
            p.start()
        
        # Collect results
        chunked_reviews: dict[str, list[list[Review]]] = {}
        for _ in processes:
            prod_id, chunks = queue.get()
            chunked_reviews[prod_id] = chunks
        
        return chunked_reviews

        # Chunk each 
        chunked_reviews: dict[str, list[list[Review]]] = {}
        num_reviews = 0
        for prod_id, prod_reveiws in reviews_by_product.items():
            current_chunk: list[Review] = []
            current_chunk_size: int = 0
            
            for review in prod_reveiws:
                review_token_count: int = review.token_count()

                # If the review itself or adding it will exceed max chunk size, create new chunk
                if review_token_count+current_chunk_size > token_limit:
                   chunked_reviews.get(prod_id).append(current_chunk)
                   current_chunk = []
                   current_chunk_size = 0
                
                # Add the review to the current chunk
                current_chunk.append(review)
                current_chunk_size += review_token_count
                # Check to ensure we're not taking all the reviews.
                num_reviews += 1

            #Faster than print, this function is already slow and can use all the help it can get.
            sys.stdout.write(f"\rProgress: [{"=" * (num_reviews * 50 // self.max_reviews):<50}] {num_reviews / self.max_reviews:.2%}")
            sys.stdout.flush()
        
        # append if last chunk is not empty
        if current_chunk:
            chunked_reviews.setdefault(prod_id, []).append(current_chunk)
        return chunked_reviews
    
class YelpParser(DataParser):
    pass
    
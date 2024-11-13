from .reviews import Review

from pydantic import BaseModel, PrivateAttr
from anthropic.types import ContentBlock

class Keyword(BaseModel):
    product_id: str
    keyword: str
    frequency: int
    sentiment: float # +-1
    embedding: list[float] | None = None

class LLMOutput(BaseModel):
    keywords: list[Keyword]
    rating: float
    summary: str # Summary of the
    summary_embedding: list[float] | None = None # To be integrated
    
    # If you don't leave this private it will break JSON extraction
    _reviews: list[Review] = PrivateAttr(default=None)

    # Set reviews after creation
    def _set_reviews(self, reviews: list[Review]) -> None:
        """
            This is a private method intentially!

            This can disassociate LLM responses to their inputs 
            if not managed properly.
        """
        self._reviews = reviews
    
    # Get the reviews
    def get_reviews(self) -> list[Review] | None:
        return self._reviews


class Cluster(BaseModel):
    product_id: str
    gen_keyword: str
    embedding: list[float]
    total_sentiment: float
    num_occur: int
    original_keywords: list[str]
    
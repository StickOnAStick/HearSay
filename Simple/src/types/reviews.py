from pydantic import BaseModel, ConfigDict
from pendulum import DateTime
from tokenizers import Tokenizer
import tiktoken
import pendulum
from loguru import logger



class Review(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    review_id: str
    product_id: str
    rating: float
    summary: str
    text: str
    date: int | DateTime

    def convert_timestamp(self):
        self.date = pendulum.from_timestamp(self.date)

    def token_count(self) -> int:
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(self.text))
    


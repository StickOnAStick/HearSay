from pydantic import BaseModel, ConfigDict
from pendulum import DateTime
from tokenizers import Tokenizer
from typing import Tuple
import pendulum

class Review(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    review_id: str
    product_id: str
    rating: float
    summary: str
    text: str
    date: int | DateTime

    @classmethod
    def convert_timestamp(self):
        self.date = pendulum.from_timestamp(self.date)

    def token_count(self) -> int:
        tokenizer = Tokenizer.from_pretrained('gpt2')

        tokens = tokenizer.encode(self.text)
        return len(tokens.ids)
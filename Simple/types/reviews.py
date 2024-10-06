from pydantic import BaseModel, ConfigDict
from pendulum import DateTime
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
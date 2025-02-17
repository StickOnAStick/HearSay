import json
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime 

""""
 @DEPRECATED

 For the concerns of this project, the Yelp types are currently deprecated

 We have no current intention to re-instantiate the use of Yelp reviews. 

"""


class Review(BaseModel):
    id: UUID = uuid4()
    biz_id: UUID
    username: str
    rating: float
    date: str
    text: str
    #user_prof_id: str | None
    images: list[str] | None # List of s3 bucket ID's

    @classmethod
    def format_date(self) -> datetime:
        '''DEPRECATED: Could be used in future.'''
        date_obj = datetime.strptime(self.date, "%b %d, %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date

    
    def to_csv(self):
        return {
                'biz_id': self.biz_id, 
                'username': self.username, 
                'rating':self.rating, 
                'text': self.text, 
                'date': self.date,
                'images': json.dumps(self.images)
                }
    
    @classmethod
    def from_csv(cls, csv_row: dict):
        return cls(
            biz_id=csv_row['biz_id'],
            username=csv_row['username'],
            rating=csv_row['rating'],
            text=csv_row['text'],
            date=csv_row['date'],
            images=json.loads(csv_row['images']) if csv_row.get('images') else None 
        )


class Location(BaseModel):
    id: UUID = uuid4()
    unit: str | None
    street_addr: str 
    city: str 
    #address_code: str
    #region: str # State, province, etc
    country: str = "United States"

    @classmethod
    def from_csv(cls, json_data: str):
         # Parse the JSON string back into a dictionary
        data = json.loads(json_data)
        # Ensure the id is converted to a UUID object
        data['id'] = UUID(data['id'])
        return cls(**data)


class BusinessInfo(BaseModel):
    id: UUID = uuid4()
    name: str
    imgs: list[str] | None # S3 image ids
    rating: float
    num_ratings: int
    offerings: list[str]      # What genre / offerings the buisness has. ("dining", "steakhouse", etc)
    price_range: int
    location: Location | None
    
    def to_csv(self):
        return {
            'id': str(self.id),
            'name': self.name, 
            'imgs': json.dumps(self.imgs) if self.imgs else None, 
            'rating': self.rating, 
            'num_ratings': self.num_ratings, 
            'offerings': json.dumps(self.offerings),
            'price_range': self.price_range,
            'location': self.location.model_dump_json() if self.location else None # This will output json inside a single cell. Janky, but working.
        }
    
    @classmethod
    def from_csv(cls, csv_row: dict):
        return cls(
            id=UUID(csv_row['id']),
            name=csv_row['name'],
            imgs= json.loads(csv_row['imgs']) if csv_row.get('imgs') else None,
            rating=float(csv_row['rating']),
            num_ratings=int(csv_row['num_ratings']),
            offerings=json.loads(csv_row['offerings']),
            price_range=int(csv_row['price_range']),
            location=Location.from_csv(csv_row['location']) if csv_row.get('location') else None
        )


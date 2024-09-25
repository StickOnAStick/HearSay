from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime 

class Review(BaseModel):
    id: UUID = uuid4()
    buis_id: UUID
    username: str
    rating: float
    date_posted: str
    text: str
    #user_prof_id: str | None
    images: list[str] | None # List of s3 bucket ID's

    @classmethod
    def format_date(self) -> datetime:
        '''DEPRECATED: Could be used in future.'''
        date_obj = datetime.strptime(self.date_posted, "%b %d, %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date

    def encode(self) -> str:
        '''Function to generate .txt format'''
        parts =  [
            #f"{len(self.buis_id)}#{self.buis_id}"
            f"{len(self.username)}#{self.username}"
            f"{len(str(self.rating))}#{self.rating}"
            #f"{len(self.user_prof_id) if self.user_prod_id is not None else '2'}#{self.user_prof_id if self.user_prof_id is not None else 'NA'}"
            f"{len(self.text)}#{self.text}"
            f"{len(self.date_posted)}#{self.date_posted}"
        ]
        return "".join(parts)

    @classmethod
    def decode(cls, text: str) -> 'Review':
        '''Function to take .txt line output into object'''
        def extract_value(encoded_text: str):
            # Find the position of the first '#'
            hash_index = encoded_text.index('#')
            # Get the length (the substring before the '#')
            length = int(encoded_text[:hash_index])
            # Extract the actual value (length characters after the '#')
            value = encoded_text[hash_index + 1:hash_index + 1 + length]
            # Return the extracted value and the remaining encoded text
            return value, encoded_text[hash_index + 1 + length:]
        
        # Start decoding the text
        remaining_text = text.strip()
        
        # Extract each field based on its length prefix
        #id_val, remaining_text = extract_value(remaining_text)
        #buis_id_val, remaining_text = extract_value(remaining_text)
        username_val, remaining_text = extract_value(remaining_text)
        rating_val, remaining_text = extract_value(remaining_text)
        #user_prof_id_val, remaining_text = extract_value(remaining_text)
        text_val, remaining_text = extract_value(remaining_text)
        date_val, remaining_text = extract_value(remaining_text)
        
        # Return the Review object with the extracted values
        return cls(
            #id=id_val if id_val != 'None' else None,
            #buis_id=buis_id_val if buis_id_val != 'None' else None,
            username=username_val,
            rating=int(rating_val),
            text=text_val,
            # user_prof_id=user_prof_id_val if user_prof_id_val != 'NA' else None,
            # Assuming `format_date` in the `to_text` method generates a formatted date string
            date=date_val
        )

class Location(BaseModel):
    id: UUID = uuid4()
    unit: str | None
    street_addr: str 
    city: str 
    #address_code: str
    #region: str # State, province, etc
    country: str = "United States"

    def encode(self) -> str:
        """Encode the Location object into a string."""
        parts = [
            f"{len(self.street_addr)}#{self.street_addr}",
            f"{len(self.city)}#{self.city}",
            f"{len(self.country)}#{self.country}",
            f"{len(self.unit) if self.unit else '0'}#{self.unit if self.unit else ''}"
        ]
        return "".join(parts)

    @classmethod
    def decode(cls, encoded_str: str) -> 'Location':
        """Decode a string into a Location object."""
        def extract_value(encoded_text: str):
            hash_index = encoded_text.index('#')
            length = int(encoded_text[:hash_index])
            value = encoded_text[hash_index + 1:hash_index + 1 + length]
            return value, encoded_text[hash_index + 1 + length:]
        
        remaining_text = encoded_str.strip()
        
        #id_val, remaining_text = extract_value(remaining_text)
        unit_val, remaining_text = extract_value(remaining_text)
        street_addr_val, remaining_text = extract_value(remaining_text)
        city_val, remaining_text = extract_value(remaining_text)
        country_val, remaining_text = extract_value(remaining_text)
        
        return cls(
            #id=UUID(id_val),
            unit=None,
            street_addr=street_addr_val,
            city=city_val,
            country=country_val
        )


class BusinessInfo(BaseModel):
    id: UUID = uuid4()
    name: str
    imgs: list[str] | None # S3 image ids
    rating: float
    num_ratings: int
    reviews: list[str] | None # Review Id's
    offerings: list[str]      # What genre / offerings the buisness has. ("dining", "steakhouse", etc)
    price_range: int
    location: Location  

    def encode(self) -> str:
        def encode_list(lst):
            if len(lst) < 1:
                return "0#"
            return f"{len(lst)}#" + "#".join([f"{len(item)}#{item}" for item in lst])
        
        parts = [
            #f"{len(str(self.id))}#{self.id}",
            f"{len(self.name)}#{self.name}",
            encode_list(self.imgs) if self.imgs else "0#",
            f"{len(str(self.rating))}#{self.rating}",
            f"{len(str(self.num_ratings))}#{self.num_ratings}",
            encode_list(self.offerings), # 
            f"{len(str(self.price_range))}#{self.price_range}", # ISSUE
            f"{len(self.location.encode())}#{self.location.encode()}"
        ]
        return "".join(parts)

    @classmethod
    def decode(cls, encoded_str: str) -> 'BusinessInfo':
        def extract_value(encoded_text):
            hash_index = encoded_text.index('#')
            length = int(encoded_text[:hash_index])
            value = encoded_text[hash_index + 1:hash_index + 1 + length]
            return value, encoded_text[hash_index + 1 + length:]

        def decode_list(encoded_text):
            count, encoded_text = extract_value(encoded_text)
            items = []
            for _ in range(int(count)):
                item, encoded_text = extract_value(encoded_text)
                items.append(item)
            return items, encoded_text

        remaining_text = encoded_str.strip()

        #id_val, remaining_text = extract_value(remaining_text)
        name_val, remaining_text = extract_value(remaining_text)
        imgs_val, remaining_text = decode_list(remaining_text)
        rating_val, remaining_text = extract_value(remaining_text)
        num_ratings_val, remaining_text = extract_value(remaining_text)
        reviews_val, remaining_text = decode_list(remaining_text)
        offerings_val, remaining_text = decode_list(remaining_text)
        price_range_val, remaining_text = extract_value(remaining_text)
        location_val, remaining_text = extract_value(remaining_text)
        
        return cls(
            #id=UUID(id_val),
            name=name_val,
            imgs=imgs_val if imgs_val else None,
            rating=float(rating_val),
            num_ratings=int(num_ratings_val),
            reviews=reviews_val if reviews_val else None,
            offerings=offerings_val,
            price_range=int(price_range_val),
            location=Location.decode(location_val)
        )
    


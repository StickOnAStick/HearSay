from lib.Scrapper.yelp.review import Review, BusinessInfo, Location
from uuid import uuid4
from typing import Type, TypeVar, Generic
from loguru import logger
import csv
import os

T = TypeVar('T')

def append_csv(obj: T):
    #TODO - Add a path for the file
    file_name = 'business_test.csv'
    field_names: list[str] = [
                            'id', 'name', 'imgs', 'rating', 
                            'num_ratings', 'offerings', 
                            'price_range', 'location'
                        ]

    if isinstance(obj, Review):
        field_names = ['biz_id', 'username', 'rating', 'text', 'date', 'images']
        file_name = 'reviews_test.csv'
    
    #TODO - Fix me! This is only relative to my machine!
    file_path = os.path.expanduser(f'~/School/SentimentAnalysis/YelpScrapper/data/{file_name}')

    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        # Write header only if file is empty
        if file.tell() == 0:
            writer.writeheader()
        # Love but hate the following about scripting languages.
        writer.writerow(obj.to_csv())



def instantiate_from_row(obj_type: Type[T]) -> T:
    
    file: str = "business_test.csv"
    field_names: list[str] = [
                                'id', 'name', 'imgs', 'rating', 
                                'num_ratings', 'offerings', 
                                'price_range', 'location'
                            ]
    is_review = False

    if not issubclass(obj_type, BusinessInfo):
        is_review = True
        file = "reviews_test.csv"
        field_names = ['biz_id', 'username', 'rating', 'text', 'date', 'images']
        

    file_path = os.path.expanduser(f'~/School/SentimentAnalysis/YelpScrapper/data/{file}')

    if is_review:
        with open(file=file_path, mode='r') as f:
            reader = csv.DictReader(f, fieldnames=field_names)

            next(reader) # Skip header 

            for row in reader:
                rev = Review.from_csv(row)
                logger.debug(f"Created review: {rev}")
    else:
        with open(file=file_path, mode='r') as f:
            reader = csv.DictReader(f, fieldnames=field_names)
            
            next(reader)    # Skip header, but _reader class does this already???
            
            for row in reader:
                biz = BusinessInfo.from_csv(row)
                logger.debug(f"Created business obj: {biz}")


def test_csv():
    biz_id = uuid4()
    review: Review = Review(
        id=uuid4(),
        biz_id=biz_id, 
        username="goat", 
        rating=4.5, 
        date="Now", 
        text="This was good chow", 
        images=None
    )
    business: BusinessInfo = BusinessInfo(
        id=biz_id,
        name="Lamb on Leg",
        imgs=None,
        rating=4.0,
        num_ratings=400,
        reviews=[str(review.id)],
        offerings=["Sheep","Lamb"],
        price_range=2,
        location=Location(
            id=uuid4(),
            unit="1014",
            street_addr="99 Fun Time",
            city="despair",
            country="domain"
        )
    )

    logger.info("Beginning to add objects to csv")
    append_csv(business)
    append_csv(review)
    logger.success("Added all objects to csv")

    logger.info("Beginning to create objects from csv")
    instantiate_from_row(BusinessInfo)
    instantiate_from_row(Review)
    logger.success("Instantiated all objects from csv")


def main():
    test_csv()

if __name__ == "__main__":
    main()
import subprocess
import sys
import signal
import csv
import os
import requests
import json

from .types.reviews import Review
from .types.models import ModelType, EmbeddingModel
from .types.API import LLMOutput

from loguru import logger



# def signal_handler(sig, frame, process):
#     logger.info("Kill signal recieved, stopping API")
#     process.terminate()
#     sys.exit(0)

# def launch_api():
#     """Launch fast API service by """
#     logger.debug("Starting fastAPI service...")
#     process = subprocess.Popen(
#         ["fastapi", "dev", "./FastAPI/__main__.py"],
#         stdout=sys.stdout, stderr=sys.stderr, # Redirect output to same terminal
#         text=True,
#         bufsize=1
#     )
#     logger.success("Successfully launched fastApi!")

#     signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, process))
#     signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, process))

#     return process
""" 
    This was causing too many issues wherein FastAPI wouldn't *always* shutdown under the right conditions. 
    If you're in this perdiciment, close / re-open your ide.
"""

FAST_API_URL="http://127.0.0.1:8000/" # Ensure port matches

def select_input_file() -> str:
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Use print instead of logger for cli input. We don't need the extra info for UI
    print("\n---------Please select a file to use---------")

    count = 1
    valid_files: list[str] = []
    for file in os.listdir(f"{package_dir}/data/input"):
        if file.endswith(".csv"):
            print(f"{count} - - - {file}")
            count += 1 # Yes, I could use len(valid_files) but this would be slightly slower.
            valid_files.append(file)
    
    print("\nEnter -1 to escape")
    
    while (1):
        file_selection: str = input("File Selection: ") # Add a proper input loop? 
        
        try:
            file_selection = int(file_selection)
        except ValueError:
            print("Invalid Input.")
            continue
        
        if file_selection == -1:
            raise SystemExit("Terminated via user input")
        if file_selection-1 >= len(valid_files) or file_selection < -1:
            print(f"Invalid input, please select a value between {1} and {len(valid_files)}")
            continue

        return os.path.join(f"{package_dir}/data/input/", valid_files[file_selection-1])

def parse_reviews(file: str, max_reviews: int) -> list[Review]:
    """
        Function for pasrsing amazon CSV and returning list of Reviews.

        ### Args:
            #### max_reviews (int) --- KEEP THIS SMALL IF TESTING. THIS COSTS MONEY
    """

    with open(file=file, newline='', mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)

        column_names = reader.fieldnames
        logger.debug(f"Found field names: {column_names}")
        
        reviews: list[Review] = [] 
        count = 0
        for row in reader:
            if count == max_reviews:
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
        raise SystemExit("No reviews found in file!")

    return reviews

def get_llmOutput(reviews: list[Review]):
    print("\n-----------Please select a model to use-----------")
    for idx, model in enumerate(ModelType):
        print(f"{idx+1}. {model.value}")
    
    model_list = list(ModelType)
    selected_model: ModelType | None = None
    while(1):
        model_selection: str = input("Select a model to use:  ")
        try:
            model_selection = int(model_selection)
        except ValueError:
            print("Invalid input")
            continue
        
        if model_selection == -1:
            raise SystemExit("Exited by user")
        
        if not 0 < model_selection <= len(model_list):
            print("Input out of range")
            continue

        selected_model = model_list[model_selection-1]
        print(f"selected model: {selected_model.value}")
        break
    
    serialized_reviews = [review.model_dump_json() for review in reviews]

    res = requests.get(f"{FAST_API_URL}/feed_model/{selected_model.value}", json=serialized_reviews)
    if res.status_code == 200:
        print("Connected good")
    else:
        logger.error(f"Failed to connect to fast api. Body {json.dumps(res.json())}")



    pass


def main_worker():


    input_file_path = select_input_file()
    logger.debug(f"input file path {input_file_path}")

    """
        IMPORTANT: keep max_reviews SMALL (<= 100) if testing. This costs $ for api calls and embeddings. 
        
        We will allow all reviews for final runs.
    """
    reviews: list[Review] = parse_reviews(file=input_file_path, max_reviews=100)
    logger.debug(f"Found {len(reviews)} reivews.")

    # cleaned_data = clean_data()

    get_llmOutput(reviews=reviews)

if __name__ == "__main__":
    logger.info("Hearsay beginning to yap...")
    
    main_worker()
 
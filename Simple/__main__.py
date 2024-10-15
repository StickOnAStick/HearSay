import subprocess
import sys
import signal
import csv
import os
import requests
import json
from enum import Enum

from .types.reviews import Review
from .types.models import ModelType, EmbeddingModel, MODEL_SYS_PROMPTS
from .types.API import LLMOutput, Keyword

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

FAST_API_URL="http://127.0.0.1:8000" # Ensure port matches


class SYSMODE(Enum):
    GENERATE_NEW: 0
    USE_EXISTING: 1




def main_worker():

    mode = select_mode()
    input_file_path = select_input_file(mode)
    logger.debug(f"input file path {input_file_path}")

    """
        IMPORTANT: keep max_reviews SMALL (<= 10) if testing. This costs $ for api calls and embeddings. 
        
        We will allow all reviews for final runs.
    """
    reviews: list[Review] = parse_reviews(file=input_file_path, max_reviews=3)
    logger.debug(f"Found {len(reviews)} reivews.")
    
    # cleaned_data = clean_data()
    # ...... 

    model, emebdding_model, prompt = select_models()
    max_token_count = get_token_limit(model)
 
    logger.debug(f"Chunk size: {max_token_count}")
    
    # Each "chunk" of reviews has a unique product_id and total_token_count < max_token_count
    chunked_reviews = chunk_reviews(max_size=max_token_count, reviews=reviews)
    
    # Returns the keywords generated for each chunk tied together    
    llmOutput: list[list[LLMOutput, list[Review]]] = get_llmOutput(
        # This output terrible and gross. needs TLC
        chunks=chunked_reviews, 
        selected_model=model, 
        sys_prompt=prompt
    )
    llm_outputs: list[LLMOutput]
    review_lists: list[list[Review]]
    llm_outputs, review_lists = map(list, zip(*llmOutput)) # Makes the code a bit cleaner.

    # Embedd each chunk's keywords 
    # Modifies the values of llmOutput and llm_outputs directly.
    get_embeddings(model=emebdding_model, llmOutputs=llm_outputs) # THIS MODIFIES llmOutput! Python sends a pointer of the array.
    save_output(llmOutput = llmOutput, fileName="Keywords")

    # Aggregate

    # Generate graphs

def select_mode() -> SYSMODE:
    print("\n---------- Operation Selection ----------\n")
    print("1. Upload new data\n2. Use Existing Data")
    while 1:
        selection: str = input("Selection")

        try:
            selection = int(selection)
        except ValueError:
            print("Invalid input")
            continue
        if selection == -1:
            raise SystemExit("Terminated via user")
        if not 0 <= selection <= 1:
            print("Invalid input")
            continue
        
        return SYSMODE.GENERATE_NEW if selection else SYSMODE.USE_EXISTING


def select_input_file(mode: SYSMODE) -> str:
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

def select_models() -> tuple[ModelType, EmbeddingModel, str]:
    print("\n-----------Please select a model to use-----------")
    for idx, model in enumerate(ModelType):
        print(f"{idx+1} - {model.value}")
    

    # Select model to use for test.
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

    print("\n-----------Please select an embedding model-----------")

    model_list = list(EmbeddingModel)
    embedding_model: ModelType | None = None
    for idx, model in enumerate(EmbeddingModel):
        print(f"{idx+1} - {model.value}")

    while(1):
        model_selection: str = input("Select Emebedding Model: ")
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

        embedding_model = model_list[model_selection-1]
        print(f"selected model: {embedding_model.value}")
        break
    

    # Select system prompt to use.
    print("\n-----------Please select a system prompt to use-----------")
    for idx, key in enumerate(MODEL_SYS_PROMPTS.keys()):
        print(f"{idx+1} - {key}")

    prompt_list = list(MODEL_SYS_PROMPTS)
    selected_prompt: str | None = None
    
    while(1):
        prompt_selection: str = input("Select a model to use: ")
        
        try:
            prompt_selection = int(prompt_selection)
        except ValueError:
            print("Invalid input")
        
        if prompt_selection == -1:
            raise SystemExit("Exited by user")
        
        if not 0 < prompt_selection <= len(prompt_list):
            print("Input out of a range")
            continue
        selected_prompt = prompt_list[prompt_selection-1]
        logger.debug(f"Selected prompt: {selected_prompt}")
        break

    return (selected_model, embedding_model, selected_prompt)


def get_token_limit(model: ModelType) -> int:
    logger.debug(f"Senting request for model: {model}")
    chunk_size = requests.get(f"{FAST_API_URL}/token_limit/{model.value}")
    if not chunk_size.status_code == 200:
        logger.exception(chunk_size.json())
        raise SystemExit("Fast API token limit not recieved")
    
    # logger.debug(f"Response: {chunk_size.json()}")
    return chunk_size.json()['token_limit']


def chunk_reviews(max_size: int, reviews: list[Review]) -> list[list[Review]]:
    """
        Chunks reviews based on two metrics: product_id and total token count.

        A queue for processing reviews.
        
        Total token count of each "chunk's" reviews < max_size.
    """
    output: list[list[Review]] = []
    
    # Sort reviews by product id.
    reviews_by_product: dict[str, list[Review]] = {}
    for review in reviews:
        if review.product_id not in reviews_by_product:
            reviews_by_product[review.product_id] = []
        reviews_by_product[review.product_id].append(review)

    for product_id, product_reviews in reviews_by_product.items():
        current_chunk: list[Review] = []
        current_chunk_size: int = 0

        for review in product_reviews:
            review_token_count: int = review.token_count()                

            # If the review itself or adding it will exceed max chunk size, create new chunk
            if review_token_count+current_chunk_size > max_size or review_token_count > max_size:
                output.append(current_chunk) # Place the current chunk in output
                current_chunk = [review] # Create new chunk
                current_chunk_size = review_token_count
            else:
                current_chunk.append(review)
                current_chunk_size += review_token_count

        # Add last chunk        
        output.append(current_chunk)

    return output

def get_llmOutput(selected_model: ModelType, chunks: list[list[Review]], sys_prompt: str) -> list[list[LLMOutput, list[Review]]]:
    """
        Generates list of keywords and the overall predicted rating given a list of product reviews.

        Returns the original product reviews and the response they generated.
    """

    # Reviews will be chunked by the API server.
    # TODO: Add async pool for requests 
    output: list[list[LLMOutput, list[Review]]] = [] 
    for chunk in chunks:
        serialized_reviews = [review.model_dump() for review in chunk]
        logger.debug(f"No. REVIEWS FOR CHUNK: {len(chunk)}")  
        res = requests.get(f"{FAST_API_URL}/feed_model/{selected_model.value}?prompt=default", json=serialized_reviews)
        if res.status_code == 200:
            print("Connected good")
        else:
            logger.error(f"Failed to connect to fast api. Error msg:\n{res.json()['detail']}")
        logger.debug(f"res: {res.json()}")
        
        llmOutput: LLMOutput = LLMOutput(**res.json())
        output.append([llmOutput, chunk])

    return output

def get_embeddings(model: EmbeddingModel, llmOutputs: list[LLMOutput]) -> None:
    """
        Function that updates the embeddings for each keyword

        #### TODO:
        Batching requests to API server. 

        #### FIXME: 
        This is inefficent because we make a copy of all the inputs because of the api request. Starting to regret API'ing this task.
    """

    for idx, llmOutput in enumerate(llmOutputs):

        res = requests.get(f"{FAST_API_URL}/get_embeddings/{model.value}", json=llmOutput.model_dump())
        if res.status_code != 200:
            logger.exception(f"Failed to connect to fast api. Status code: {res.status_code} Response text: {res.text}")
        # logger.debug(f"Embeddings response: {res.json()}")

        # Sanity check
        try:
            response_data = res.json()
        except requests.exceptions.JSONDecodeError:
            logger.exception(f"Failed to decode the JSON response. Status code: {res.status_code} Response text: {res.text}")

        if llmOutput.summary != response_data.get('summary'):
            logger.exception(f"Somehow you recieved the wrong object when trying to embed the keywords. 07")
        
        try:
            keyword_embeddings = response_data.get('keywords', [])
            if len(keyword_embeddings) != len(llmOutput.keywords):
                logger.exception(f"Mismatch between keywords and embeddings count in response for llmOutput at index {idx}")
                continue
            
            for keyword_obj, embedding_data in zip(llmOutput.keywords, keyword_embeddings):
                keyword_obj.embedding = embedding_data.get('embedding')
        except KeyError as e:
            logger.exception(f"Missing expected key in the api response {e}")

        # You need to index this. Otherwise the original data in Main() will not be modified.
        llmOutputs[idx] = llmOutput

def save_output(llmOutput: list[list[LLMOutput, list[Review]]], fileName: str | None = None):
    """
        Function to save results to two csvs: Product and Keywords

        @param fileName: Optional File name param that appends to base csv ex: "{filename}-Products.csv"
    """

    # The LLMOuput type is cumbersome and unfit for production.
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Store the product data in memory to handle udpates
    product_data: dict[str, dict] = {}
    keyword_data: dict[str, dict] = {}

    for llm, reviews in llmOutput:
        reviews: list[Review]
        llm: LLMOutput

        product_id = reviews[0].product_id
        review_ids = [rev.review_id for rev in reviews]
        

        ## PRODUCT CSV DATA
        if product_id in product_data:
            # Update the existing product entry
            product = product_data[product_id]

            # Update the gen_rating (weighted avg)
            prev_gen_rating = float(product['gen_rating'])
            num_appends = int(product['num_appends'])
            new_gen_rating = (prev_gen_rating * num_appends + llm.rating) / (num_appends + 1)
            product['gen_rating'] = new_gen_rating

            # Update the number of appends
            product['num_appends'] = num_appends + 1

            # Update review_ids (without duplicates)
            existing_review_ids = set(product['review_ids'].split(","))
            updated_review_ids = list(existing_review_ids.union(set(review_ids)))
            product['review_ids'] = ','.join(updated_review_ids)
        else:
            # Create new product entry
            product_data[product_id] = {
                'product_id': product_id,
                'review_ids': ",".join(review_ids),
                'gen_rating': llm.rating,
                'num_appends': 1,
                'gen_summary': llm.summary,
                'summary_embedding': llm.summary_embedding or 'null'
            }

        ## KEYWORD CSV DATA  --- USE {product_id}-{keyword} as UNIQUE ID
        for keyword in llm.keywords:
            if f"{product_id}-{keyword.keyword}" in keyword_data:
                existing_record = keyword_data[f"{product_id}-{keyword.keyword}"]
                
                # Update freq
                existing_record['frequency'] += keyword.frequency 

                # Update sentiment (weighted avg)
                prev_sentiment = existing_record['sentiment']
                new_sentiment = (prev_sentiment + keyword.sentiment) / 2 
                existing_record['sentiment'] = new_sentiment

                # Only update embedding if it's currently null
                if existing_record['embedding'] is None:
                    existing_record['embedding'] = keyword.embedding

            else:
                keyword_data[f"{product_id}-{keyword.keyword}"] = {
                    "product_id": product_id,
                    "keyword": keyword.keyword,
                    "frequency": keyword.frequency,
                    'sentiment': keyword.sentiment,
                    'embedding': ",".join(map(str, keyword.embedding)) # store as comma separated list of floats
                }


    with open(f"{package_dir}/data/output/Products.csv", newline="", mode="w") as product_csv:
        field_names = ['product_id', 'review_ids', 'gen_rating', 'num_appends', 'gen_summary', 'summary_embedding']
        product_writer = csv.DictWriter(product_csv, fieldnames=field_names)

        product_writer.writeheader()
        product_writer.writerows(product_data.values())

    with open(f"{package_dir}/data/output/Keywords.csv", newline='', mode="w") as keywords_csv:
        writer = csv.DictWriter(keywords_csv, fieldnames=['product_id'] + list(Keyword.model_fields.keys()) )
        writer.writeheader()
        writer.writerows(keyword_data.values())


if __name__ == "__main__":
    logger.info("Hearsay beginning to yap...")
    
    main_worker()
 
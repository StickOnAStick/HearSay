import subprocess
import sys
import signal
import csv
import os
import requests
import json

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



def main_worker():


    input_file_path = select_input_file()
    logger.debug(f"input file path {input_file_path}")

    """
        IMPORTANT: keep max_reviews SMALL (<= 10) if testing. This costs $ for api calls and embeddings. 
        
        We will allow all reviews for final runs.
    """
    reviews: list[Review] = parse_reviews(file=input_file_path, max_reviews=10)
    logger.debug(f"Found {len(reviews)} reivews.")
    
    # cleaned_data = clean_data()
    # ...... 

    model, emebdding_model, prompt = select_models()
    max_token_count = get_token_limit(model)
 
    logger.debug(f"Chunk size: {max_token_count}")
    
    # Each "chunk" of reviews has a unique product_id and total_token_count < max_token_count
    chunked_reviews = chunk_reviews(max_size=max_token_count, reviews=reviews)
    
    # Returns the keywords generated for each chunk tied together    
    llmOutput: list[tuple[LLMOutput, list[Review]]] = get_llmOutput(
        # This output terrible and gross. needs TLC
        chunks=chunked_reviews, 
        selected_model=model, 
        sys_prompt=prompt
    )

    llm_outputs, review_lists = zip(*llmOutput) # Makes the code a bit cleaner.

    # Embedd each chunk's keywords 
    # Modifies the values of llmOutput and llm_outputs directly.
    get_embeddings(model=emebdding_model, llmOutputs=llm_outputs) # THIS MODIFIES llmOutput! Python sends a pointer of the array.

    save_output(llmOutput = llmOutput)

    # Aggregate

    # Generate graphs
    

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

def get_llmOutput(selected_model: ModelType, chunks: list[list[Review]], sys_prompt: str) -> list[tuple[LLMOutput, list[Review]]]:
    """
        Generates list of keywords and the overall predicted rating given a list of product reviews.

        Returns the original product reviews and the response they generated.
    """

    # Reviews will be chunked by the API server.
    # TODO: Add async pool for requests 
    output: list[tuple[LLMOutput, list[Review]]] = [] 
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
        output.append((llmOutput, chunk))

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
        res = requests.get(f"{FAST_API_URL}/get_embeddings/{model.value}")
        if res.status_code != 200:
            logger.exception(f"Failed to connect to fast api. Error msg:\n{res.json()['detail']}")
        logger.debug(f"Embeddings response: {res.json()}")

        # Sanity check
        response_data = res.json()
        if llmOutput.summary != response_data.get('summary'):
            logger.exception(f"Somehow you recieved the wrong object when trying to embed the keywords. 07")
        
        # You need to index this. Otherwise the original data in Main() will not be modified.
        llmOutputs[idx] = LLMOutput(**response_data) 


def save_output(llmOutput: list[tuple[LLMOutput, Review]]):
    # Someone write me pls.
    package_dir = os.path.dirname(os.path.abspath(__file__))

    with open(f"{package_dir}/data/output/out.csv", newline='', mode="w") as csv_file:
        spamwriter = csv.DictWriter(csv, fieldnames=list(llmOutput[0][0].model_fields.keys()))
        spamwriter.writeheader()

        for llm, review in llmOutput:
            spamwriter.writerow(llm.model_fields)


if __name__ == "__main__":
    logger.info("Hearsay beginning to yap...")
    
    main_worker()
 
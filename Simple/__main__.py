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
from .utils.api_interface import APIInterface
from .constants.constants import FAST_API_URL
from .utils.aggregator import Aggregator
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


def main_worker():


    input_file_path = select_input_file()
    model, emebdding_model, prompt = select_models()

    logger.debug(f"input file path {input_file_path}")
    api_inter = APIInterface(
        file_path=input_file_path,
        embedding_model=emebdding_model,
        prompt=prompt,
        model=model,
        max_reviews=None
    )
    """
        Keep max_reviews small (<= 500) if testing.
    """
    llmOutput: list[LLMOutput] = api_inter.get_llmOutput(filter_product_id=None)
    save_output(llmOutput = llmOutput, fileName="Keywords")

    # Aggregate
    aggregator = Aggregator("Keywords")
    aggregator.aggregate()
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

def save_output(llmOutputs: list[LLMOutput], fileName: str | None = None):
    """
        Function to save results to two csvs: Product and Keywords

        @param fileName: Optional File name param that appends to base csv ex: "{filename}-Products.csv"
    """

    # The LLMOuput type is cumbersome and unfit for production.
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Store the product data in memory to handle udpates
    product_data: dict[str, dict] = {}
    keyword_data: dict[str, dict] = {}

    for llmOut in llmOutputs:

        product_id = llmOut.get_reviews()[0].product_id
        review_ids = [rev.review_id for rev in llmOut.get_reviews()]
        

        ## PRODUCT CSV DATA
        if product_id in product_data:
            # Update the existing product entry
            product = product_data[product_id]

            # Update the gen_rating (weighted avg)
            prev_gen_rating = float(product['gen_rating'])
            num_appends = int(product['num_appends'])
            new_gen_rating = (prev_gen_rating * num_appends + llmOut.rating) / (num_appends + 1)
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
                'gen_rating': llmOut.rating,
                'num_appends': 1,
                'gen_summary': llmOut.summary,
                'summary_embedding': llmOut.summary_embedding or 'null'
            }

        ## KEYWORD CSV DATA  --- USE {product_id}-{keyword} as UNIQUE ID
        for keyword in llmOut.keywords:
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
 
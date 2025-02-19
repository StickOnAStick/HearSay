import csv
import os

from Simple.src.types.reviews import Review
from Simple.src.types.models import ModelType, EmbeddingModel, MODEL_SYS_PROMPTS
from Simple.src.types.API import LLMOutput, Keyword
from Simple.src.client.clientState import ClientState
from Simple.src.utils.api_interface import APIInterface
from Simple.src.utils.aggregator import Aggregator
from Simple.constants.constants import FAST_API_URL # Gross
from loguru import logger

from pathlib import Path

""" 
    This was causing too many issues wherein FastAPI wouldn't *always* shutdown under the right conditions. 
    If you're in this perdiciment, close / re-open your ide.
"""

CLIENT_STATE = ClientState()

class HearSayAPP:
    """
        Singleton of App and necessary state.

        Stores meaningful data used to run and modify the program.

        Responsible for managing the terminal UI.
    """

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._SCRIPT_PATH: Path = Path(__file__)
        self.data_source: Path | None = None
        self.model: ModelType | None = None
        self.embed_model: EmbeddingModel | None = None
        self.prompt: str | None = None
        self.current_reviews: dict[str, list[list[Review]]] | None = None


    def run(self):
        """ Main "game loop" used for navigating UI and running programs. """
        while True: # Lmao
            self.MainMenu()

    def MainMenu(self):
        """ Used for selecting the task to run. Also displays the current state of the application. """
        while True:
            print("\n" + "="*50)
            print("📌  HearSay - Main Menu")
            print("="*50)
            print(f"📂 Data Source: {self.data_source or 'Not Selected'}")
            print(f"🧠 Model: {self.model or 'Not Selected'}")
            print(f"🔎 Embedding Model: {self.embed_model or 'Not Selected'}")
            print(f"✍️  Prompt: {self.prompt or 'Not Set'}")
            print("="*50)
            print("1️⃣  Select Data Source")
            print("2️⃣  Select Model")
            print("3️⃣  Select Prompt")
            print("4️⃣  Extract Keywords and Sentiment")
            print("5️⃣  Train Model")
            print("6️⃣  Display Results")
            print("7️⃣  Exit")
            print("="*50)

            choice = input("Enter choice: ").strip()
            if choice == "1":
                self.DataSourceSelection()
            elif choice == "2":
                self.ModelSelection()
            elif choice == "3":
                self.SelectPrompt()
            elif choice == "4":
                self.ExtractKeywordsAndSentiment()
            elif choice == "5":
                self.TrainModel()
            elif choice == "6":
                self.DisplayResults()
            elif choice == "7":
                logger.info("Exiting HearSay. Goodbye! 👋")
                exit(0)
            else:
                print("❌ Invalid choice. Please enter a number between 1-7.")

    def DataSourceSelection(self):
        """ Allows user to select a dataset type and then a dataset folder within it. """
        print("\n" + "=" * 50)
        print("📂  Select Data Source Type")
        print("=" * 50)

        base_path = Path(__file__).parent / "data" / "input"
        
        if not base_path.exists() or not base_path.is_dir():
            print("❌ The base directory 'data/input' does not exist.")
            return

        # List dataset types (subdirectories inside data/input)
        dataset_types = [d for d in base_path.iterdir() if d.is_dir()]
        
        if not dataset_types:
            print("❌ No dataset types found inside 'data/input'.")
            return
        
        # Display dataset types
        for i, dataset in enumerate(dataset_types, 1):
            print(f"{i}. {dataset.name}")

        # User selects dataset type
        choice = input("Select a dataset type by number: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(dataset_types):
                selected_type = dataset_types[choice - 1]
                logger.info(f"✅ Selected Dataset Type: {selected_type.name}")
            else:
                print("❌ Invalid selection.")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return

        # List available datasets inside the selected type
        print("\n" + "=" * 50)
        print(f"📂  Select a Dataset from '{selected_type.name}'")
        print("=" * 50)

        available_datasets = [d for d in selected_type.iterdir() if d.is_dir()]
        
        if not available_datasets:
            print(f"❌ No datasets found inside '{selected_type.name}'.")
            return

        # Display dataset options
        for i, dataset in enumerate(available_datasets, 1):
            print(f"{i}. {dataset.name}")

        # User selects dataset
        choice = input("Select a dataset by number: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(available_datasets):
                self.data_source = available_datasets[choice - 1]
                logger.info(f"✅ Data Source selected: {self.data_source}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")


    def ModelSelection(self):
        """Used for selecting a model"""
        print("\n" + "="*50)
        print("🧠  Model Selection")
        print("="*50)

        print("Available Models:")
        model_list = list(ModelType)
        for i, model in enumerate(model_list, 1):
            print(f"{i}. {model.name}")

        choice = input("Enter the number of the model: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(model_list):
                self.model = model_list[choice - 1]
                logger.info(f"✅ Model selected: {self.model}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

        print("\nAvailable Embedding Models:")
        embed_list = list(EmbeddingModel)
        for i, embed in enumerate(embed_list, 1):
            print(f"{i}. {embed.name}")

        choice = input("Enter the number of the embedding model: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(embed_list):
                self.embed_model = embed_list[choice - 1]
                logger.info(f"✅ Embedding model selected: {self.embed_model}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

    def SelectPrompt(self):
        """ Allows user to select a system prompt from MODEL_SYS_PROMPTS. """
        print("\n" + "=" * 50)
        print("✍️  Select a System Prompt")
        print("=" * 50)

        if not MODEL_SYS_PROMPTS:
            print("❌ No prompts available.")
            return

        # Display available prompts
        prompt_keys = list(MODEL_SYS_PROMPTS.keys())
        for i, key in enumerate(prompt_keys, 1):
            print(f"{i}. {key}")

        # User selects a prompt
        choice = input("Select a prompt by number: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(prompt_keys):
                self.prompt = MODEL_SYS_PROMPTS[prompt_keys[choice - 1]]
                logger.info(f"✅ Selected Prompt: {prompt_keys[choice - 1]}")
                print(f"📝 Selected Prompt Content:\n{self.prompt}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

    def ExtractKeywordsAndSentiment(self):
        """ Runs external extraction code """
        if not self.data_source:
            print("⚠️  No data source selected. Please select a dataset first.")
            return
        
        logger.info(f"🔍 Extracting Keywords and Sentiment from {self.data_source}...")
        # TODO: Replace with actual extraction function
        # extract_keywords_and_sentiment_function()
        logger.info("✅ Extraction Completed!")

    def DisplayResults(self):
        """
        Displays the results of a selected output file.
        """
        url = "http://localhost:8000/results"  # Replace with actual results page
        logger.info(f"📊 Opening results at {url}")
        #webbrowser.open(url)
        return

    def TrainModel(self):
        """
        Uses selected model and dataset to fine-tune a model.
        """
        if not self.model or not self.data_source:
            print("⚠️  Please select both a model and a dataset before training.")
            return
        
        logger.info(f"🧠 Training Model: {self.model} with dataset: {self.data_source}")
        # TODO: Replace with actual training function
        # train_model_function(self.model, self.data_source)
        logger.info("✅ Training Completed!")
    
    
    


def APP_ENTRY():

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
    save_output(llmOutputs = llmOutput, fileName="Keywords")

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
    
    # Encapsulates Data, Extraction, Analysis, Presentation layers
    HearSayAPP().run()
 
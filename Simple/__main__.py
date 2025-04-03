import csv
import os

from Simple.src.types.models import ModelType, EmbeddingModel, MODEL_SYS_PROMPTS
from Simple.src.types.API import LLMOutput, Keyword
from Simple.src.utils.api_interface import APIInterface
from Simple.src.utils.aggregator import Aggregator
from Simple.src.types.client.clientstate import ClientState, ReadOnlyClientState
from Simple.data.parser_factory import ParserFactory
from Simple.data.parsers import DataParser

from loguru import logger
from pathlib import Path
from collections import deque
from datetime import datetime

import tiktoken
import json


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
        self._SCRIPT_PATH: Path = Path(__file__).parent
        self.global_state: ClientState = ClientState()
        self.API: APIInterface = APIInterface(
            ReadOnlyClientState(self.global_state)
        )

    def run(self):
        """ Main "game loop" used for navigating UI and running programs. """
        with open(self._SCRIPT_PATH / "config.json") as config_file:
            config = json.load(config_file)

        for key, value in config.items():
            val: any = None
            match key:
                case "model":
                    try:
                        val = ModelType[value]
                    except KeyError:
                        raise ValueError(f"Invalid Model Type: {value}")
                case "embed_model":
                    try:
                        val = EmbeddingModel[value]
                    except KeyError:
                        raise ValueError(f"Invalid Embedding Model: {value}")
                case _:
                    val = value

            setattr(self.global_state, f"_{key}", val)

        while True: # Lmao
            self.MainMenu()

    def MainMenu(self):
        """ Used for selecting the task to run. Also displays the current state of the application. """
        while True:
            print("\n" + "="*50)
            print("📌  HearSay - Main Menu")
            print("="*50)
            print(f"📂 Data Source: {self.global_state.data_source or 'Not Selected'}")
            print(f"🧠 Model: {self.global_state.model or 'Not Selected'}")
            print(f"🔎 Embedding Model: {self.global_state.embed_model or 'Not Selected'}")
            print(f"✍️  Prompt: {self.global_state.prompt or 'Not Set'}")
            print(f"📊 Reviews Loaded: {True if self.global_state.reviews else False}")
            print("="*50)
            print("1️⃣  Select Data Source")
            print("2️⃣  Load Existing Keywords")
            print("3️⃣  Select Model")
            print("4️⃣  Select Prompt")
            print("5️⃣  Extract Keywords and Sentiment")
            print("6️⃣  Aggregate Keywords into Topics")
            print("7️⃣  Display Results")
            print("8️⃣  Train Model")
            print("9️⃣  Exit")
            print("="*50)

            choice = input("Enter choice: ").strip()
            
            match choice:
                case "1":
                    self.DataSourceSelection()
                case "2":
                    self.LoadKeywords()
                case "3":
                    self.ModelSelection()
                case "4":
                    self.SelectPrompt()
                case "5":
                    self.ExtractKeywordsAndSentiment()
                case "6":
                    self.Aggregate()
                case "7":
                    self.TrainModel()
                case "8":
                    self.DisplayResults()
                case "9":
                    logger.info("Exiting HearSay. Goodbye! 👋")
                    exit(0)
                case _:
                    print("❌ Invalid choice. Please enter a number between 1-9.")

    def DataSourceSelection(self):
        """ Allows user to select a dataset type and then a dataset folder within it. """
        print("\n" + "="*50)
        print(" Select The number of reviews you want to parse.")
        print("=" * 50)

        choice = input("Enter amount: ").strip()
        try:
            choice_i = int(choice)
            if choice_i <= 0 or not isinstance(choice_i, int):
                print("❌ Please choose a valid positive integer.")
                return
            self.global_state.max_reviews = choice_i
            print(f"Set to parse {self.global_state.max_reviews} reviews")
        except ValueError:
            print("❌ Could not convert the input to an integer.")
            return

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
                if self.global_state.data_source and available_datasets[choice - 1] != self.global_state.data_source:
                    self.global_state.reviews = None
                self.global_state.data_source = available_datasets[choice - 1]
                logger.info(f"✅ Data Source selected: {self.global_state.data_source}")
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
                self.global_state.model = model_list[choice - 1]
                logger.info(f"✅ Model selected: {self.global_state.model}")
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
                self.global_state.embed_model = embed_list[choice - 1]
                logger.info(f"✅ Embedding model selected: {self.global_state.embed_model}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

    def LoadKeywords(self):
        """
        Selects an already parsed keyword data set to load into memory
        
        **Sets:** 
        ```
        ClientState.keyword_source
        ClientState.llm_output
        ```
        """
        print("\n" + "="*50)
        print(" Select The Keyword dataset you want to load.")
        print("=" * 50)

        base_path = Path(__file__).parent / "data" / "output"

        if not base_path.exists() or not base_path.is_dir():
            print("❌ The base directory 'data/output' does not exist.")
            return

        # Pair all keyword CSVs with their product CSV.
        keyword_pairs: dict[Path, dict[str, Path]] = {}
        for file in base_path.iterdir():
            # Discard directories and non-csv files
            if file.is_dir() or not file.parts[-1].endswith(".csv"):
                continue
            
            base_name: str = file.stem
            print(base_name)
            if base_name.endswith("_keywords"):
                key = base_name.removesuffix("_keywords")
                keyword_pairs.setdefault(key, {})["keywords"] = file 
            elif base_name.endswith("_products"):
                key = base_name.removesuffix("_products")
                keyword_pairs.setdefault(key, {})["product"] = file

        # Filter completed datasets only
        valid_pairs = {k: v for k, v in keyword_pairs.items() if "keywords" in v and "product" in v}
        if not valid_pairs:
            logger.warning("❌ No complete datasets found inside 'data/output'.")
            return
        
        # Present options
        keys = list(valid_pairs.keys())
        for i, key in enumerate(keys, 1):
            print(f"{i}: {key}")
        
        # Select dataset
        while True:
            try:
                selection = int(input("\nEnter number of the dataset to load: "))
                if 1 <= selection <= len(keys):
                    break
                print("⚠️ Invalid selection. Please choose a number from the list.")
            except ValueError:
                print("⚠️ Please enter a valid number.")
        
        selected_key = keys[selection - 1]
        self.global_state.keyword_source = valid_pairs[selected_key]['keywords']
        self.global_state.product_source = valid_pairs[selected_key]['product']

        print(f"\n📦 Loading dataset: {selected_key}")

        self._load_keywords()

        print("✅ Dataset loaded into global state.")
       
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
                self.global_state.prompt = prompt_keys[choice - 1]
                logger.info(f"✅ Selected Prompt: {prompt_keys[choice - 1]}")
                print(f"📝 Selected Prompt Content:\n{self.global_state.prompt}")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

    def ExtractKeywordsAndSentiment(self):
        """ Runs external extraction code. Saves to MEMORY NOT DISK!"""
        if not self.global_state.prompt:
            print("⚠️  No data source selected. Please select a dataset first.")
            return
        if not self.global_state.model:
            print("⚠️ No Model selected. Please select a model first.")
            return
        if not self.global_state.data_source:
            self.DataSourceSelection()

        logger.info(f"🔍 Extracting Keywords and Sentiment from {self.global_state.data_source}...")
        parser: DataParser = ParserFactory.get_parser(self.global_state.data_source, self.global_state.max_reviews)
        
        # Extract and chunk the data into usable format (Review... for now)
        batch_size: int = self.API.get_token_limit()
        enc = tiktoken.get_encoding('cl100k_base')
        prompt_tokens: int = len(enc.encode(MODEL_SYS_PROMPTS[self.global_state.prompt]))
        batch_size -= prompt_tokens
        self.global_state.reviews = parser.get_batched_reviews(batch_size, prompt_tokens)
        
        # Call the API to extract the keywords / sentiment
        llmOutput: deque[LLMOutput] = self.API.get_llmOutput(filter_product_id=None)
        # In-Built setter converts the deque to a map of {prod_id: LLMOutput} 
        self.global_state.llm_output = llmOutput

        # Save the Keyword / Sentiment results to a CSV
        print("="*50)
        print("Enter a filename to save to. (Enter to skip and generate automated name)")
        print("="*50)
        choice = input("FileName: ")
        data_type, data_name = self.global_state.data_source.parts[-2:]

        if choice.lower() in ("n", "no", ""):
            choice = f"{data_type}-{data_name}-{int(datetime.time())}"
        
        # append _keywords to the filename
        self.global_state.keyword_source = Path(__file__).parent / "data" / "output" / f"{choice}_keywords.csv" 
        if self._save_keywords(file_name=choice):
            self.global_state.keyword_source = None
            logger.warning("Could not save keywords to a file.")            
        logger.info(f"✅ Saved output to {choice}.csv")

    def Aggregate(self):
        # If LLMOutput isn't loaded, request an input Keywords file
        if not self.global_state.llm_output and not self.global_state.keyword_source:
            self.DataSourceSelection()
            self.ExtractKeywordsAndSentiment()

        # This should be dynamic and managed by state
        aggregator = Aggregator(
            global_state = ReadOnlyClientState(self.global_state),
            ) 
        aggregator.aggregate()
        
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
        if not self.global_state.model or not self.global_state.data_source:
            print("⚠️  Please select both a model and a dataset before training.")
            return
        
        logger.info(f"🧠 Training Model: {self.global_state.model} with dataset: {self.global_state.data_source}")
        # TODO: Replace with actual training function
        # train_model_function(self.model, self.data_source)
        logger.info("✅ Training Completed!")
    
    def _save_keywords(self, file_name: str) -> int:
        """
        Function to save LLMOutput to Keyword and Product CSVs
        :param file_name (str): 
        """
        output_dir = Path(__file__).parent / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        keyword_path = output_dir / f"{file_name}_keywords.csv"
        product_path = output_dir / f"{file_name}_products.csv"
        
        try:

            # Save keywords CSV
            with keyword_path.open('w', newline='', encoding='utf-8') as kf:
                kw_writer = csv.DictWriter(kf, fieldnames=["product_id", "review_id", "keyword", "sentiment", "embedding"])
                kw_writer.writeheader()
                for output in self.global_state.llm_output.values():
                    for kw in output.keywords:
                        kw_writer.writerow(kw.model_dump())

            # Save products CSV (excluding keywords)
            with product_path.open('w', newline='', encoding='utf-8') as pf:
                prod_writer = csv.DictWriter(pf, fieldnames=["product_id", "rating", "rating_count", "rating_sum", "summary", "summary_embedding"])
                prod_writer.writeheader()
                for output in self.global_state.llm_output.values():
                    prod_writer.writerow({
                        "product_id": output.product_id,
                        "rating": output.rating,
                        "rating_count": output.rating_count,
                        "rating_sum": output.rating_sum,
                        "summary": json.dumps(output.summary),
                        "summary_embedding": output.summary_embedding,
                    })
        except PermissionError:
            logger.error("Could not save output. Permission denied.")
            return 1
        except OSError as e:
            logger.error(f"Good luck. OS Error: {e}")
            return 1
        return 0
    
    def _load_keywords(self) -> None:
        """
            Load parsed Keyword and Product data from CSV files into ClientState.llm_output
        """
        output_map: dict[str, LLMOutput] = {}

        with self.global_state.product_source.open(newline='', encoding='utf-8') as pf:
            reader = csv.DictReader(pf)
            for row in reader:
                product_id = row["product_id"]
                if product_id not in output_map:
                    output_map[product_id] = LLMOutput(product_id=product_id, keywords=deque(), summary=[], rating_sum=0.0, rating_count=0)

                out = output_map[product_id]
                out.rating_sum = float(row.get("rating_sum", 0.0))
                out.rating_count = int(row.get("rating_count", 0))
                out.summary = json.loads(row["summary"]) if row.get("summary") else []
                summary_embedding = row.get("summary_embedding")
                out.summary_embedding = json.loads(summary_embedding) if summary_embedding else None
        
        with self.global_state.keyword_source.open(newline='', encoding='utf-8') as kf:
            reader = csv.DictReader(kf)
            for row in reader:
                row["embedding"] = json.loads(row["embedding"]) if row.get("embedding") else None
                kw = Keyword(**row)
                if kw.product_id not in output_map:
                    logger.warning(f"⚠️ Keyword found with no associated product! REV_ID: {kw.review_id} PROD_ID: {kw.product_id}")
                    continue
                output_map[kw.product_id].keywords.append(kw)

        self.global_state.llm_output = output_map

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
    
    # Generate graphs


def save_output(llmOutputs: list[LLMOutput], fileName: str | None = None):
    """
        Function to save results to two csvs: Product and Keywords

        :param (str) fileName: File name param that appends to base csv ex: "{filename}-Products.csv"
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
        writer = csv.DictWriter(keywords_csv, fieldnames=list(Keyword.model_fields.keys()) )
        writer.writeheader()
        writer.writerows(keyword_data.values())


if __name__ == "__main__":
    logger.info("Hearsay beginning to yap...")
    
    # Encapsulates Data, Extraction, Analysis, Presentation layers
    HearSayAPP().run()
 
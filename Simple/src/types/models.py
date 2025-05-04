from enum import Enum

class ModelType(Enum):
    CLAUDE = "claude-3-5-sonnet-20240620"
    GPT3 = "gpt-3.5-turbo"
    GPT4 = "gpt-4o-2024-08-06" 	# This snapshot supporting formatted output.
    GPT4Mini = "gpt-4o-mini" 
    Gemini = "Gemini"

class EmbeddingModel(Enum):
    TEXT_LARGE3 = "text-embedding-3-large"
    TEXT_SMALL3 = "text-embedding-3-small"
    VOYAGE_LARGE2 = "voyage-large-2"
    VOYAGE_LITE2_INSTRUCT = "voyage-lite-02-instruct"

MODEL_TOKEN_LIMITS: dict[ModelType, int] = {
    ModelType.CLAUDE: 2048,
    ModelType.GPT3: 4096,
    ModelType.GPT4: 8192,
    ModelType.GPT4Mini: 8192,
    ModelType.Gemini: 32000
}

MODEL_SYS_PROMPTS: dict[str, str] = {
    "default": """
    You are an AI assistant that extracts key information from customer reviews. Given the following reviews, please:
        1. Identify the main keywords or phrases mentioned. Single word keywords ONLY.
        2. Determine the sentiment associated with each keyword (positive, negative, neutral) as a FLOAT on a scale of +-1.
        3. Count the frequency of each keyword.
        4. Guess the overall rating given the reviews as 0-5 with 0.5 precision.
        5. Generate a concise 3-4 sentence business summary that captures:
        - The overall sentiment during the given time period.
        - Key aspects that customers focused on.
        - Any notable trends or patterns.

        ONLY provide the output in the following JSON format:

        {
            'keywords': [
                {'review_id': 'abc123', 'keyword': 'keyword1', 'sentiment': '1'},
                {'review_id': 'abc123', 'keyword': 'keyword2', 'sentiment': '-0.6'},
                ...
            ],
        }

        Reviews:
    """,
    "none": "",
    "cluster_label_prompt": """
        You are an AI assistant that generates an overarching label to best describe a group of keywords. 
        These keywords are taken from product reviews, business reviews, and social media posts.
        Please return a label which appropriately categorizes the keywords as a topic for a collection of reviews or media post. 

        Keywords:
    """,
}
from pathlib import Path
from collections import deque

from Simple.src.types.reviews import Review
from Simple.src.types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS
from Simple.src.types.API import LLMOutput

from loguru import logger
from dotenv import load_dotenv
import os

class ClientState:
    """
        The real global state which only the Main app should own / modify.
    """
    def __init__(self):
        load_dotenv()
        self._data_source: Path | None = None
        self._keyword_source: Path | None = None
        self._product_source: Path | None = None
        self._aggregate_source: Path | None = None
        self._max_reviews: int | None = None
        self._model: ModelType | None = None
        self._embed_model: EmbeddingModel | None = None
        self._prompt: str | None = None
        self._reviews: dict[str, deque[deque[Review]]] = {} # Map of product id to chunked reviews for the product
        self._llm_output: dict[str, LLMOutput] = {} # Maps product id to parsed products w/keywords
        self._end_point: str = os.getenv("FAST_API_URL")

        if not (self._end_point and isinstance(self._end_point, str)):
            raise RuntimeError("API endpoint not configured or corrupted. Please ensure your Simple/.env file has the FAST_API='http://my_endpoint_root/' variable set")
        else:
            logger.info(f"API Endpoint set to: {self._end_point}")
    
    def __repr__(self) -> str:
        return f"""
                \nData Source: {self._data_source if self._data_source else "None"}
                \nKeyword Source: {self._keyword_source if self._keyword_source else "None"}
                \nProduct Source: {self._product_source if self._product_source else "None"}
                \nAggregate Source: {self.aggregate_source if self._aggregate_source else "None"}
                \nMax Reviews: {self._max_reviews if self._max_reviews else "None"}
                \nModel: {self._model if self._model else "None"}
                \nEmbed Model: {self._embed_model if self._embed_model else "None"}
                \nPrompt: {self._prompt if self.prompt else "None"}"""
    
    @property
    def end_point(self) -> str:
        # No setter for now. We only have one target.
        return self._end_point

    @property
    def keyword_source(self) -> Path | None:
        return self._keyword_source
    
    @keyword_source.setter
    def keyword_source(self, source: Path) -> None:
        self._keyword_source = source
    
    @property
    def product_source(self) -> Path | None:
        return self._product_source
    
    @product_source.setter
    def product_source(self, source: Path) -> None:
        self._product_source = source

    @property
    def aggregate_source(self) -> Path | None:
        return self._aggregate_source

    @aggregate_source.setter
    def aggregate_source(self, source: Path) -> None:
        self._aggregate_source = source

    @property
    def data_source(self) -> Path | None:
        return self._data_source

    @data_source.setter
    def data_source(self, source: Path):
        self._data_source = source

    @property
    def max_reviews(self) -> int | None:
        return self._max_reviews

    @max_reviews.setter
    def max_reviews(self, max_reviews: int):
        if not max_reviews.is_integer():
            logger.warning("Tried to set max reviews to non-integer value!")
            return
        self._max_reviews = max_reviews

    @property
    def model(self) -> ModelType | None:
        return self._model

    @model.setter
    def model(self, model_type: ModelType) -> None:
        if not model_type or not isinstance(model_type, ModelType):
            logger.warning("Invalid model type passed in.")
            return
        self._model = model_type
    
    @property
    def embed_model(self) -> EmbeddingModel | None:
        return self._embed_model

    @embed_model.setter
    def embed_model(self, embed_model: EmbeddingModel) -> None:
        if not embed_model or not isinstance(embed_model, EmbeddingModel):
            logger.warning("Tried to assign invalid embedding model type")
            return
        self._embed_model = embed_model
    
    @property
    def prompt(self) -> str | None:
        return self._prompt
    
    @prompt.setter
    def prompt(self, prompt: str) -> None:
        if prompt not in MODEL_SYS_PROMPTS.keys():
            logger.warning("Tried to set invalid prompt")
            return
        self._prompt = prompt
    
    @property
    def reviews(self) -> dict[str, deque[deque[Review]]] | None:
        return self._reviews
    
    @reviews.setter
    def reviews(self, input: dict[str, deque[deque[Review]]]) -> None:
        # No checks here since we want to be able to null this
        self._reviews = input

    @property
    def llm_output(self) -> dict[str, LLMOutput]:
        return self._llm_output

    @llm_output.setter
    def llm_output(self, llmOutput: deque[LLMOutput] | dict[str: LLMOutput]) -> None:
        if isinstance(llmOutput, dict):
            self._llm_output = llmOutput
        else:
            # Track the number of updates made to a single product
            for out in llmOutput:
                if out.product_id in self._llm_output:
                    logger.debug(f"[AGGREGATE]: appending summary for product: {out.product_id}")
                    self._llm_output[out.product_id].keywords.extend(out.keywords)
                    self._llm_output[out.product_id].summary.extend(out.summary)
                    # Proper running sum average.
                    self._llm_output[out.product_id].rating_sum += out.rating_sum
                    self._llm_output[out.product_id].rating_count += out.rating_count
                else:
                    logger.debug(f"[NEW]: product: {out.product_id}")
                    self._llm_output[out.product_id] = out


class ReadOnlyClientState:
    """
        A Wrapper around ClientState that prevents unauthorized
        mutation of the global state by sub-routines.
    """
    def __init__(self, real_state: ClientState):
        self._real_state = real_state
    
    #
    # 1) Define read-only properties - Annoying as hell to have to redefine these for intellisense.
    #
    @property
    def end_point(self) -> str:
        return self._real_state._end_point

    @property
    def data_source(self) -> Path | None:
        return self._real_state.data_source
    
    @property
    def keyword_source(self) -> Path | None:
        return self._real_state._keyword_source

    @property
    def aggregate_source(self) -> Path | None:
        return self._real_state._aggregate_source

    @property
    def max_reviews(self) -> int | None:
        return self._real_state.max_reviews

    @property
    def model(self) -> ModelType | None:
        return self._real_state.model

    @property
    def embed_model(self) -> EmbeddingModel | None:
        return self._real_state.embed_model
    
    @property
    def prompt(self) -> str | None:
        return self._real_state.prompt
    
    @property
    def reviews(self) -> dict[str, deque[deque[Review]]] | None:
        return self._real_state.reviews

    @property
    def llm_output(self) -> dict[str, LLMOutput]:
        return self._llm_output

    #
    # 2) Disallow all non-internal sets
    #
    def __setattr__(self, name: str, value: object):
        if name == "_real_state":
            # Allow only in __init__
            super().__setattr__(name, value)
        else:
            raise AttributeError("This state is read-only.")

    #
    # 3) Fallback dynamic attribute gets
    #
    def __getattr__(self, name: str):
        # If it is something private, deny
        if name.startswith("_"):
            raise AttributeError(f"Attribute {name} is private or not accessible.")
        return getattr(self._real_state, name)
from pathlib import Path
from Simple.src.types.reviews import Review
from Simple.src.types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS

from loguru import logger

class CientState:
    """
        The real global state which only the Main app should own / modify.
    """
    def __init__(self):
        self._data_source: Path | None = None
        self._max_reviews: int | None = None
        self._model: ModelType | None = None
        self._embed_model: EmbeddingModel | None = None
        self._prompt: str | None = None
        self._current_reviews: dict[str, list[list[Review]]] | None = None

   
    
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
        if prompt not in MODEL_SYS_PROMPTS.values():
            logger.warning("Tried to set invalid prompt")
            return
        self._prompt = prompt
    
    @property
    def current_reviews(self) -> dict[str, list[list[Review]]] | None:
        return self._current_reviews
    
    @current_reviews.setter
    def current_reviews(self, input: dict[str, list[list[Review]]]) -> None:
        # No checks here since we want to be able to null this
        self._current_reviews = input


class ReadOnlyClientState:
    """
        A Wrapper around ClientState that prevents unauthorized
        mutation of the global state by sub-routines.
    """
    def __init__(self, real_state: CientState):
        self._real_state = real_state
    
    def __getattr__(self, name: str):
        """
        Called *only* if 'name' is not found in this object's normal attributes.
        We can forward this to the underlying real_state.
        """
        # If it's something like _internal, raise an error or handle carefully
        if name.startswith('_'):
            raise AttributeError(f"Attribute {name} is private or not accessible.")
        return getattr(self._real_state, name)

    def __setattr__(self, name: str, value: any):
        """
        We only allow setting our own _real_state in __init__. 
        Any other attempt is read-only => raise error.
        """
        if name == "_real_state":
            # Allowed during __init__ only
            super().__setattr__(name, value)
        else:
            raise AttributeError("This state is read-only.")

        

from ..types.models import EmbeddingModel, ModelType, MODEL_SYS_PROMPTS

class APIInterface:
    def __init__(self):
        
        self.model: str | None = None
        self.embedding_model: EmbeddingModel  | None = None

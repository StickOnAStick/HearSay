import tiktoken
from ...types.models import ModelType

def count_gpt_tokens(message: str, model_name: ModelType):
    encoding = tiktoken.encoding_for_model(model_name=model_name.value)
    tokens = encoding.encode(message)

    return len(tokens)

def count_claude_tokens(message: str):
    # Simple aproximation of the actual token count
    tokens = message.split()
    return len(tokens)
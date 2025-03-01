import tiktoken
from tokenizers import Tokenizer


from Simple.src.types.models import ModelType

tokenizer = Tokenizer.from_pretrained("gpt2") # There's a claude version of this. See anthropic docs.

def count_gpt_tokens(message: str, model_name: ModelType):
    encoding = tiktoken.encoding_for_model(model_name=model_name.value)
    tokens = encoding.encode(message)

    return len(tokens)

def count_claude_tokens(message: str):
    # Simple aproximation of the actual token count
    tokens = tokenizer.encode(message)
    return len(tokens.ids)
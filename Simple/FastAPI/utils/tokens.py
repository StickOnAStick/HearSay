import tiktoken


from Simple.src.types.models import ModelType

def count_gpt_tokens(message: str):
    enc = tiktoken.get_encoding('cl100k_base')
    return len(enc.encode(message))

def count_claude_tokens(message: str):
    # Simple aproximation of the actual token count
    enc = tiktoken.get_encoding('cl100k_base')
    return len(enc.encode(message))
import string

def is_english(text: str) -> bool:
    return all(char in string.printable for char in text)

def clean_text(text: str) -> str:
    text = text.replace('<br>', '').replace('\n','').replace('\r','')
    return text
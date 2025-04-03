from Simple.src.processing.string_preprocessing import *

## stemming tests
def test_basic_stemming():
    input_str = "Running quickly and jumping highly"
    expected = "run quick and jump high"
    assert stem_string(input_str) == expected

def test_punctuation_stemming():
    input_str = "Testing. Sentences, with punctuation! Even commas..."
    expected = "test . sentenc , with punctuat ! even comma ..."
    assert stem_string(input_str) == expected

def test_uppercase_stemming():
    input_str = "UPPER CASE becomes Lower"
    expected = "upper case becom lower"
    assert stem_string(input_str) == expected

def test_non_alphabetic_stemming():
    input_str = "hello123 $10.50 @special_tokens"
    expected = "hello123 $ 10.50 @ special_token"
    assert stem_string(input_str) == expected

def test_full_numeric_stemming():
    input_str = "01245 5683 12895"
    expected = "01245 5683 12895"
    assert stem_string(input_str) == expected

def test_french_stemming():
    input_str = "manger des pommes rouges"
    expected = "mang de pomm roug"
    assert stem_string(input_str, language="french") == expected

def test_empty_stemming():
    assert stem_string("") == ""

def test_space_stemming():
    assert stem_string(" ") == ""

def test_one_word_stemming():
    assert stem_string("laughing") == "laugh"
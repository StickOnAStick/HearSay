import nltk
from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer

# Ensure the tokenizer and stopword libraries are downloaded
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

def stem_string(input_string: str, language: str = "english", stem_stopwords: bool = "True") -> str:
    """
    Uses a snowball stemmer to replace each word in the string with its stem, preserving punctuation.
    :param stem_stopwords: Stems stopwords, such as: "a", "the", "is", etc.
    :param language: The language of the provided string.
    :param input_string: The string to stem.
    :return: The stemmed string with original punctuation.
    """
    # edge case detection
    if input_string == "" or input_string is None:
        # Add error logging in future
        return ""

    # setup stemmer and tokenizer
    stemmer_model = SnowballStemmer(language=language, ignore_stopwords=not stem_stopwords)
    tokens = word_tokenize(input_string, language=language)
    stemmed_tokens = []

    # loop through tokens
    for token in tokens:
        if token[0].isalnum() and token[-1].isalnum():  # token appears to be a word or num, not punctuation.
            stemmed_token = stemmer_model.stem(token)
            stemmed_tokens.append(" " + stemmed_token)  # for words, we append a space
        else:
            stemmed_tokens.append(token)    # if punctuation, we don't append a space

    # Join tokens and return string
    stemmed_string = ''.join(stemmed_tokens)
    if stemmed_string[0] == " ":    # if first character is misplaced space, ignore it
        return stemmed_string[1:]
    else:                           # otherwise, return normal
        return stemmed_string

def lemmatize_string_wordnet(input_string : str, language: str = "english") -> str:
    """
    Uses wordnet lemmatizer to replace each word in the string with its lemma - a type of aggregated root.

    A clear example of how this differs from stemming is in the example "better", whose lemma is "good".
    :param language: The language of the provided string.
    :param input_string: The string to lemmatize.
    :return: The lemmatized string.
    """
    # edge case detection
    if input_string == "" or input_string is None:
        # Add error logging in future
        return ""

    # preprocess string
    input_string = input_string.lower() # make it lowercase

    # setup lemmatizer and tokenizer
    lemmatizer_model = WordNetLemmatizer()
    tokens = word_tokenize(input_string, language=language)
    lemmatized_tokens = []

    # loop through tokens
    for token in tokens:
        if token[0].isalnum() and token[-1].isalnum():  # token appears to be a word or num, not punctuation.
            lemma_token = lemmatizer_model.lemmatize(token)
            lemmatized_tokens.append(" " + lemma_token)  # for words, we append a space
        else:
            lemmatized_tokens.append(token)    # if punctuation, we don't append a space

    # Join tokens and return string
    lemmatized_string = ''.join(lemmatized_tokens)
    if lemmatized_string[0] == " ":    # if first character is misplaced space, ignore it
        return lemmatized_string[1:]
    else:                           # otherwise, return normal
        return lemmatized_string


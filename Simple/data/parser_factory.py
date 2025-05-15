from .parsers import YelpParser, DataParser, AmazonParser
from pathlib import Path
import os

class ParserFactory:
    """Singleton factory responsible for creating the correct parser for a given dataset."""
    _parsers = {
        "amazon": AmazonParser,
        "yelp": YelpParser
    }
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_parser(file_path: Path, max_reviews: int) -> DataParser:
        """Determines parser to use based off file path"""

        path_parts = {part.lower() for part in file_path.parts}

        for key in ParserFactory._parsers:
            if key in path_parts:
                return ParserFactory._parsers[key](file_path, max_reviews)

        raise ValueError(f"No matching parser found for path: {file_path}")        

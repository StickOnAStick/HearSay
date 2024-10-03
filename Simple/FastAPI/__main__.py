from fastapi import FastAPI, HTTPException, Response

from ..types.models import ModelType, MODEL_TOKEN_LIMITS, MODEL_SYS_PROMPTS
from ..types.API import LLMOutput
from ..types.reviews import Review
from .types.t_api import TokenLimitResponse

from .utils.tokens import count_claude_tokens, count_gpt_tokens

from openai import OpenAI

from anthropic.types import Message, ContentBlock
import anthropic

from dotenv import load_dotenv
from loguru import logger

import json
import os

load_dotenv()

CLAUDE_KEY = os.getenv("CLAUDE_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_PROJ_ID = os.getenv("OPENAI_PROJ_ID")


assert CLAUDE_KEY is not None and CLAUDE_KEY != "", "FATAL: Could get API key from .env"

claude_client = anthropic.Anthropic(
    api_key=CLAUDE_KEY
)

openAI_client = OpenAI(
    organization=OPENAI_ORG_ID,
    project=OPENAI_PROJ_ID
)


app = FastAPI()


@app.get("/health")
async def check_endpoint():
    return {
        "Status": "OK",
        "code": 200
        }

@app.get("/upload_results")
async def upload_results(business, reviews: list[str]):
    """
        Uploads json to Claude3.5
    """
    pass

@app.get("/token_limit/{model}")
async def get_token_limit(model: str, response_model=TokenLimitResponse):
    try:
        selected_model = ModelType(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="No model selected")

    return {
        "model": selected_model.value,
        "token_limit": MODEL_TOKEN_LIMITS.get(selected_model)
    }

@app.get("/feed_model/{model}/{prompt}", response_model=LLMOutput)
async def feed_model(model: str, prompt: str, reviews: list[Review]):
    try:
        selected_model = ModelType(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="Selected model does not exist!")

    if not reviews:
        raise HTTPException(status_code=400, detail="No reviews provided!")

    if not prompt or prompt == "":
        prompt == "default"

    
    reviews_text: str = "".join([review.text for review in reviews])

    match selected_model:
        case ModelType.CLAUDE:
             
            #Token check
            token_count = count_claude_tokens(MODEL_SYS_PROMPTS[prompt].join(reviews_text))
            if token_count > MODEL_TOKEN_LIMITS[ModelType.CLAUDE]:
                # Check if it will go past max tokens *NOT GUARANTEED 
                raise HTTPException(
                    status_code=400, 
                    detail=f"Input content exceeded token limit!
                    \nSystem Prompt token count: {count_claude_tokens(MODEL_SYS_PROMPTS[prompt])} 
                    \nInput Review Token count: {count_claude_tokens(MODEL_SYS_PROMPTS[prompt])}
                    "
                )

            # Get the LLM response
            message: Message = claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=MODEL_TOKEN_LIMITS[ModelType.CLAUDE],
                system=MODEL_SYS_PROMPTS[prompt],
                messages=[
                    {
                        "role": "user", 
                        "content": reviews_text
                    }
                ],
                temperature=0 # We can play with this later.
            )

            if message.stop_reason == "max_tokens":
                # Catch max_token limits 
                raise HTTPException(status_code=400, detail="Claude: MAX TOKEN REACHED")
            

            if not message.content['text']:
                raise HTTPException(status_code=500, detail="Claude: No assistant response found! Reviews NOT parsed!")
            
            try:
                parsed_dict = json.loads(message.content['text'])
                llm_output = LLMOutput(**parsed_dict) 

                return llm_output
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Recieved Invalid JSON format from claude")
            except ValueError as e:
                logger.error("Failed to parse claude reponse into JSON object!")
                raise HTTPException(status_code=400, detail=f"Validation error when constructing LLMOutput from Claude response! {e}")

        case ModelType.GPT3:
            pass
        case ModelType.GPT4:
            pass
        case ModelType.Gemini:
            pass
   
            
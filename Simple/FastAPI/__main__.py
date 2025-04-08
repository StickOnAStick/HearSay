from fastapi import FastAPI, HTTPException

from Simple.src.types.models import ModelType, EmbeddingModel, MODEL_TOKEN_LIMITS, MODEL_SYS_PROMPTS
from Simple.src.types.API import LLMOutput, Keyword
from Simple.src.types.reviews import Review

from .types.t_api import TokenLimitResponse
from .utils.tokens import count_claude_tokens, count_gpt_tokens

from openai import OpenAI

from anthropic.types import Message
import anthropic

from dotenv import load_dotenv
from loguru import logger

import json
import os

load_dotenv()

CLAUDE_KEY = os.getenv("CLAUDE_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_PROJ_ID = os.getenv("OPENAI_PROJ_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


assert CLAUDE_KEY is not None and CLAUDE_KEY != "", "FATAL: Could get API key from .env"

claude_client = anthropic.Anthropic(
    api_key=CLAUDE_KEY
)

openAI_client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=OPENAI_PROJ_ID
)

logger.debug("FAST API: Starting...")
app = FastAPI()
logger.success("FAST API: Ready and listening")

@app.get("/health")
async def check_endpoint():
    return {
        "Status": "OK",
        "code": 200
        }


@app.get("/token_limit/{model}")
async def get_token_limit(model: ModelType, response_model=TokenLimitResponse):
    try:
        selected_model = ModelType(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="No model selected")

    return {
        "model": selected_model.value,
        "token_limit": MODEL_TOKEN_LIMITS.get(selected_model)
    }

@app.post("/feed_model/{model}", response_model=LLMOutput)
async def feed_model(model: str, reviews: list[Review], prompt: str | None = "default"):
    logger.debug(f"Recived request. Model: {model}, prompt: {prompt} {reviews}")
    try:
        selected_model = ModelType(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="Selected model does not exist!")

    if not reviews:
        raise HTTPException(status_code=400, detail="No reviews provided!")

    formatted_reviews = "\n\n".join(
        f"[REVIEW_ID: {review.review_id}]\n{review.text.strip()}"
        for review in reviews
    )
    logger.debug(formatted_reviews)
    reviews_text_with_prompt: str = MODEL_SYS_PROMPTS[prompt] + "\n\n" + formatted_reviews

    match selected_model:
        case ModelType.CLAUDE:
            #Token check
            token_count = count_claude_tokens(reviews_text_with_prompt)
            logger.debug(f"token_count: {token_count}")
            if token_count > MODEL_TOKEN_LIMITS[ModelType.CLAUDE]:
                # Check if it will go past max tokens *NOT GUARANTEED \

                raise HTTPException(
                    status_code=400, 
                    detail=f"""Input content exceeded token limit of {MODEL_TOKEN_LIMITS[ModelType.CLAUDE]}!
                    \nSystem Prompt token count: {count_claude_tokens(MODEL_SYS_PROMPTS[prompt])} 
                    \nInput Review Token count: {count_claude_tokens(formatted_reviews)}
                    \nTotal: {count_claude_tokens(MODEL_SYS_PROMPTS[prompt] + count_claude_tokens(formatted_reviews))}
                    """
                )

            # Get the LLM response
            message: Message = claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=MODEL_TOKEN_LIMITS[ModelType.CLAUDE],
                system=MODEL_SYS_PROMPTS[prompt],
                messages=[
                    {
                        "role": "user", 
                        "content": formatted_reviews
                    }
                ],
                temperature=0 # We can play with this later.
            )
            logger.debug(f"Recieved anthropic response: {message}")
            if message.stop_reason == "max_tokens":
                # Catch max_token limits 
                raise HTTPException(status_code=400, detail="Claude: MAX TOKEN REACHED")
            
            if not message.content[0].text:
                raise HTTPException(status_code=500, detail="Claude: No assistant response found! Reviews NOT parsed!")
            
            try:
                parsed_dict = json.loads(message.content[0].text)
                #logger.debug(f"Parsed dict: {parsed_dict}")
            
                # Add in the product ID to LLMOutput
                parsed_dict['product_id'] = reviews[0].product_id 
                # Add the product ID to each Keyword of LLMOutput
                for kw in parsed_dict.get("keywords", []):
                    kw["product_id"] = reviews[0].product_id

                llm_output = LLMOutput(**parsed_dict) 
                #logger.debug(f"Created LLMOutput object: {llm_output}")
                return llm_output
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Recieved Invalid JSON format from claude")
            except ValueError as e:
                logger.error("Failed to parse claude reponse into JSON object!")
                raise HTTPException(status_code=400, detail=f"Validation error when constructing LLMOutput from Claude response! {e}")

        case ModelType.GPT3 | ModelType.GPT4 | ModelType.GPT4Mini:
            completion = openAI_client.chat.completions.create(
                model=selected_model.value,
                messages=[
                    {
                        "role": "system", "content": MODEL_SYS_PROMPTS[prompt],
                        "role": "user", "content": formatted_reviews
                    }
                ],
                response_format=LLMOutput,
            )

            if completion.choices[0].finish_reason == "content_filter":
                logger.error("Recieved a content filter exception from OpenAI!")
                raise HTTPException(status_code=503, detail=f"Recieved content filter exception from OpenAI model: {model}")

            if completion.choices[0].finish_reason == "length":
                logger.error("Exceeded max length of OpenAI request!")
                raise HTTPException(status_code=503, detail=f"Exceeded content length of OpenAI model: {model}")
            
            logger.debug(f"Recieved: {completion.choices[0].message.content}")
            


        case ModelType.Gemini:
            logger.warning("Not yet implemented")
            pass


@app.post("/get_cluster_label/{model}")
async def get_cluster_label(model: str, cluster_keywords: list[Keyword]):
    try:
        selected_model = ModelType(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="Selected model does not exist!")
    
    keywords_str = ",".join([kw.keyword for kw in cluster_keywords])
    match selected_model:
        case ModelType.GPT3 | ModelType.GPT4 | ModelType.GPT4Mini:
            completion = openAI_client.chat.completions.create(
                model=selected_model.value,
                messages=[
                    {
                        "role": "system", 
                        "content": MODEL_SYS_PROMPTS["cluster_label_prompt"]
                    },
                    {
                        "role": "user", 
                        "content": f"keywords:\n{keywords_str}"
                    }
                ],
            )
            if completion.choices[0].finish_reason == "content_filter":
                logger.error("Recieved a content filter exception from OpenAI!")
                raise HTTPException(status_code=503, detail=f"Recieved content filter exception from OpenAI model: {model}")

            if completion.choices[0].finish_reason == "length":
                logger.error("Exceeded max length of OpenAI request!")
                raise HTTPException(status_code=503, detail=f"Exceeded content length of OpenAI model: {model}")

            label = completion.choices[0].message.content.strip()
            return {"label": label}

    

@app.post("/get_embeddings/{model}")
async def get_embeddings(model: str, llmOut: LLMOutput) -> LLMOutput:
    
    try:
        selected_model = EmbeddingModel(model)
    except ValueError:
        raise HTTPException(status_code=404, detail="Selected embedding model does not exist!")
    
    if not llmOut:
        raise HTTPException(status_code=500, detail="Failure passing LLMOutput to embedding model")
            

    keywords: list[str] = [kw.keyword for kw in llmOut.keywords]
    
    match selected_model:
        case EmbeddingModel.TEXT_LARGE3 | EmbeddingModel.TEXT_SMALL3:
            # Open Ai's embeddings
            
            embeddings = openAI_client.embeddings.create(
                model=selected_model.value,
                input=keywords,
                dimensions=1536
            )

            if len(embeddings.data) != len(llmOut.keywords):
                raise HTTPException(status_code=500, detail="Mismatch between keywords and embedding array response lengths.")

            logger.debug(f"Recieved {len(embeddings.data)} embeddings of {len(embeddings.data[0].embedding)} dimensions for {len(llmOut.keywords)} keywords")
          
            for keyword_obj, embedding in zip(llmOut.keywords, embeddings.data):
                keyword_obj.embedding = embedding.embedding
            
            return llmOut

        case EmbeddingModel.VOYAGE_LARGE2 | EmbeddingModel.VOYAGE_LITE2_INSTRUCT:
            # Athnropic's embedding 
            raise HTTPException(status_code=404, detail="Voyage embeddings not currently implimented!")


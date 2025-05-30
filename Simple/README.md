# "Premature optimization is the root of all evil"
We're simplifying things now boys. 

## Gist

Use the command-line to select a csv file for parsing. 

This will parse and chunk the csv, sending chunks to Claude, GPT, Gemini API's. 


AI Response will be JSON of keywords, frequency and sentiment. Do this for every review.

Aggregate responses into __topics__ (marg+lemonade = drinks) via vector embeddings, k-means and dynamic grouping.

Display benchmarked results on graphs. 

# Installation and Setup

### __Configure and Set API Keys__

Place a `.env` file at `./Simple/FastAPI/.env`.

Request API keys from Nicholas and you will be provided with unique keys, do not share these with anyone. 

The parameters for the `.env` file are: 

`CLAUDE_KEY`
`OPENAI_ORG_ID`
`OPENAI_PROJ_ID`
`OPENAI_API_KEY`

There's also another `.env` located at `Simple/.env` which should contain:

`FAST_API_URL = "http://127.0.0.1:8000` (unless you've manually changed the fast api port / address)

### __Download the datasets__

Download the amazon reviews dataset [here](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews).

Place the reviews.csv inside `Simple/data/input`

I've also added a bash script located at `Simple/data/input/download_data.bash` which *should* install all the correct datasets.

### __Install Poety__

This project using Poetry to manage dependencies. If you do not have it installed, please install it [here](https://python-poetry.org/docs/) and review the [usage docs](https://python-poetry.org/docs/basic-usage/).

### __Setup Poetry__ 
Setup your poetry virtual enviornment, for reproducibilty we will creat this inside the projects directory using the following commands.

```bash
cd Simple
poetry config virtualenvs.in-project true
poetry install
```
After this you will see a .venv folder be created inside the project's root. 

### __Activate Poetry Venv__
Now that the venv is setup we can activate it using:

__linux__
```bash
source .venv/bin/activate
```

__windows__:
```cmd
.venv\bin\activate
```
Now we are free to install all packages without conflicting dependencies using `poetry install`!

Use the `poetry add` command to install all current existing dependencies or `poetry add myPackage` to extend the current package set. 



# Running:

Start the FastAPI server via `fastapi dev Simple/FastAPI/__main__.py` 

Start the master via `python3 -m Simple`





Documentation specific to our transformer approach.

# Setup

To start development first ensure you have [Poetry package manager](https://python-poetry.org/docs/#installing-with-pipx) installed.

Navigate to the directory with:
``` bash
cd Transformer/Vespera
```

Now set the virtual enviornment to be in the working directory.
``` bash
poetry config virtualenvs.in-project true
```

Now we can install all required dependencies for development using:
```bash
poetry install
```

Lastly, activate the virtual enviornemnt using:
```bash
source .venv/bin/activate
```
and set your vscode interpreter to use this python instance located at:
```bash
Vespera/.venv/bin/python3.12
```
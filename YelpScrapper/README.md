# Installation and Setup

### __Install Poety__

This project using Poetry to manage dependencies. If you do not have it installed, please install it [here](https://python-poetry.org/docs/) and review the [usage docs](https://python-poetry.org/docs/basic-usage/).

### __Setup Poetry__ 
Setup your poetry virtual enviornment, for reproducibilty we will creat this inside the projects directory using the following commands.

```bash
cd ..WebScrappers/YelpScrapper
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
Now we are free to install all packages without conflicting dependencies!

### __VsCode interpreter setup__
If you're using vscode, make sure you change your python enviornment to use the venv; otherwise, intellisense will not be able to match installed packages and show warnings.

You can accompish this by opening a python file and clicking the python version on the bottom right of your screen ex: `3.12.3 64-bit`

From there you can select the interpreter path

### __Lastly:__ 
Use the `poetry add` command to install all current existing dependencies or `poetry add myPackage` to extend the current package set. 

# Running:
To run the scrapper just use `python3 YelpScrapper` or `python3 ../YelpScrapper` if you're inside the directory.

It will prompt you for a query via _stdin console_ and begin running.


# _IMPORTANT_:

__NEVER__ commit the `.venv` folder to git. This is __BAD__, we do __NOT__ want merge conflicts on every push.


# v0.1.0 Note:

Currently I've disabled the functionality to pass in a download destination via the top level `__main.py__`, because of this you will manually need to set the `global_path` variable inside `Selenium/lib/Scrapper/scrapper.py` file.



----------------------------
# Process overview


__1\.__ Navigate to yelp

__2\.__ Enter in "(user defined)" search term.

__3\.__ For each _search result_ __m__ _in pages_ __n__ _(n of m)_ call: [searchResultsPagination](./lib/Scrapper/yelp/scrapper.py) 

__4A.__ Navigate to each search result __m__ on the page __n[i]__ [searchResultPage]() and gather buisness info: 
- __Name__  -- __# review__   --   __rating__ 

__4B.__ For each review __k__ in result __m__ of page __n__:\
if ( k has review_message ):\
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Upload review to training DB




        

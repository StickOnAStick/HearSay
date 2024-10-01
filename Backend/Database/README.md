# Schemas and CSV's

There's a one-to-one mapping between the schema format and the CSV. If you have concerns about the schema format please let me know. 

# Postgres Database

I do not expect you guy's to setup your own psql server locally for this. But it is a convience when dealing with this scale; that being said, CSV is still competely operable especially since it has fast lookups.

### Setup
If you want to install your own psql server you can do so by following the documentation [here](https://www.postgresql.org/download/). __Note__ you will need a recent version of Postgres that supports __vectors__.
Vectors are a recent extension which can be installed in the _Postgres CLI_ using `CREATE EXTENSION IF NOT EXISTS vector;`


#### Note:
Some of the schema variables here are not currently in use for our project. This is because it's taken from a development server of the tangential product "HearSay". 
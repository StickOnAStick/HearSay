Data input needs for have the following structure: 

Data
| - input
|    | - absa
|    |   | - Some dataset
|    | - keywords
|    | - sentiment
|    |   | - amazon
|    |   | - etc

The parser factory will take the last three path variables (/input/{some_dir}/{dataset_name}) and match it to an appropriate parser.


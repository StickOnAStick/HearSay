## Execution


### About

For a given directory defined in the .env, this will parse through every .txt file, parse the review data and upload the results to supabase. 

We use the ```train_buisness``` and ```train_review``` tables available for this purpose. 

### Setup

```.env``` variables: ```FILE_PATH``` ```SUPABASE_ANON``` ```SUPABASE_URL```

- Set the correct filepath to your text files.
- Get the API keys for supabase (Ask me -nickd)
- Ensure data in text files is correct.
- Set the ignore line variable in the text prompt and voila, your data is now uploaded to SupaBase. 
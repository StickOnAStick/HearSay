# CSV formatting


## Product CSV

`product_id` - The product id of a review & it's generated keyword-sentiment

`review_id(s)` - A reference to the original reviews which generated the keywords and sentiment

`gen_rating` - The LLM generated rating based off provided reviews

`num_appends` - ( sum(prev)  / n )

`gen_summary` - The LLM generated summary based off provided reviews

`summary_embedding` - TBD. Will be `null` for now. 

## Keywords CSV

`product_id` - Product where review

`keyword` - Keyword found

`sentiment` - Sentiment

`embedding` - List of floats


## Aggregated CSV

`product_id` 

`gen_keyword`

`embedding`

`avg_sentiment` - Brotha.

`num_occur` - Sum of all frequencies from which label was derived.  

`original_keywords` - Keywords from which the label was derived.





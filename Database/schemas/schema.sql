CREATE TABLE business_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),    -- UUID derived from a hashed from a URL
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),            -- Timestamp of record creation
    last_updated TIMESTAMPTZ,                        -- Timestamp of the last update (last time scrapped)
    overall_rating SMALLINT CHECK (overall_rating >= 0 AND overall_rating <= 10), -- Rating (small integer)
    name VARCHAR(255) NOT NULL,                      -- Name field
    description TEXT,                                -- Array of text values for descriptions
    images TEXT[],                                   -- Array of UUIDs representing images
    source VARCHAR(50) NOT NULL,                     -- Source of the business review (Yelp, Google, Insta, etc..)
    last_page INT DEFAULT 1                          -- Last page viewed, default is 1 (Reviews page 10, 15, etc..)
);

CREATE TABLE business_address (                      -- normalized location
    business_id UUID REFERENCES business_data(id) ON DELETE CASCADE,
    street_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    PRIMARY KEY (business_id)
);

CREATE TABLE business_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES business_data(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    review_time TIMESTAMPTZ,
    user_prof UUID,                                  -- for future use (likely not as this is ILLEGAL)
    rating SMALLINT CHECK (rating >= 0 AND rating <= 10),
    review_text TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,                     -- Source of the review (Yelp, Google, Insta, etc..)
    images TEXT[]                                    --s3 urls
);

CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES business_data(id) ON DELETE CASCADE, -- Should this cascade? Or should we save it for future use?
    keyword VARCHAR(30) NOT NULL,  -- Reasonably long to prevent over flow from words like Pneumonoultramicroscopicsilicovolcanoconiosis
    frequency INTEGER DEFAULT 1,
    sentiment REAL CHECK (sentiment >= -1.2 and sentiment <= 1.2), -- Sentiment score -1.0 (negative) to 1.0 POSITIVE +- 1.2 is SUPER Positive SUPER Negative outliers
    embedding VECTOR(1536), --- OpenAI's text-embedding-3-large model scaled down by half (will still outperform ada-002 even when reduced to 256 according to their own documentation)  
    parent_id UUID REFERENCES keywords(id) ON DELETE SET NULL,  -- Allows for "drilling-down" aggregating keyword to it's roots. DO NOT remove the parent if the child keyword is removed.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
);

CREATE TABLE review_keywords ( -- Table to link keywords to the reviews which contained them. (Associative table)
    review_id UUID REFERENCES business_reviews(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (review_id, keyword_id)
);

CREATE INDEX idx_keywords_embedding ON keywords USING ivfflat (embedding); -- Index for faster vector similarity searches

CREATE INDEX idx_keywords_parent_id ON keywords(parent_id); -- Index for faster recursive calls.

CREATE TABLE business_summaries ( -- AI Generated summary we provide given a businesses keywords & sentiment
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES business_data(id) ON DELETE CASCADE,
    summary TEXT NOT NULL, -- AI Generated summary given current review batch
    embedding VECTOR(1536), -- Vectorized summary for better aggregation.
    sentiment REAL, -- overall sentiment score
    time_period DATERANGE, -- Time period the summary covers (oldest -> newest)
    parent_id UUID REFERENCES business_summaries(id) ON DELETE SET NULL, -- Allows for aggregation of the summaries
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);


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
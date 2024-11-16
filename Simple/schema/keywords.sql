
PRAGMA foregin_keys = ON;

CREATE TABLE KEYWORDS (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    frequency INTEGER NOT NULL,
    sentiment REAL NOT NULL CHECK(sentiment BETWEEN -1.2 AND 1.2),
    embedding BLOB NOT NULL, -- Store vector as blob. SQLITE doesn't support vectors
);

CREATE TABLE LLMOUTPUTS (
    llm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    rating REAL NOT NULL CHECK(rating BETWEEN 0 and 10),
    summary TEXT,
    summary_embedding BLOB,
    FOREIGN KEY (product_id) REFERENCES Reviews (ProductId) ON DELETE CASCADE
);

-- Junction Table to link LLMOutput to extracted Keywords
CREATE TABLE LLM_KEYWORDS_LINK ( 
    llm_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    PRIMARY KEY (llm_id, keyword_id),
    FOREIGN KEY (llm_id) REFERENCES LLMOUTPUTS (llm_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES KEYWORDS (keyword_id) ON DELETE CASCADE
);

-- Junction Table to link LLMOutput to reviews
CREATE TABLE LLM_REVIEWS_LINK (
    llm_id INTEGER NOT NULL,
    review_id INTEGER NOT NULL,
    PRIMARY KEY (llm_id, review_id),
    FOREIGN KEY (llm_id) REFERENCES LLMOUTPUTS (llm_id) on DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES Reviews (Id) on DELETE CASCADE
);


CREATE TABLE CLUSTERS (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    gen_keywrod TEXT NOT NULL,
    embedding BLOB NOT NULL,
    total_sentiment REAL NOT NULL CHECK(total_sentiment BETWEEN 0 AND 10),
    num_occur INTEGER NOT NULL,
    original_keywords
);

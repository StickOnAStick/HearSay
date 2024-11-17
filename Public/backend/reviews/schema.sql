CREATE TABLE IF NOT EXISTS LABELS (
    id INTEGER PRIMARY KEY,
    review_id INTEGER NOT NULL,
    keywords TEXT NOT NULL,
    sentiment REAL NOT NULL CHECK(sentiment BETWEEN -1 and 1),
    FOREIGN KEY (review_id) REFERENCES Reviews (Id)
);

-- Create a new table with modified id field
CREATE TABLE Reviews (
    _id INTEGER PRIMARY KEY,
    ProductId TEXT,
    UserId TEXT,
    ProfileName TEXT,
    HelpfulnessNumerator INTEGER,
    HelpfulnessDenominator INTEGER,
    Score INTEGER,
    Time INTEGER,
    Summary TEXT,
    Text TEXT
);

-- Fill in the new table with modified id field
INSERT INTO _reviews (id_, ProductId, ProfileName, HelpfulnessNumerator, HelpfulnessDenominator, Score, Time, Summary, Text) SELECT Id, ProductId, ProfileName, HelpfulnessNumerator, HelpfulnessDenominator, Score, Time, Summary, Text FROM Reviews;

-- Drop the old table: 
DROP TABLE Reviews;

-- Rename new table
ALTER TABLE _reviews RENAME TO reviews;
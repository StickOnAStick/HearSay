WITH RECURSIVE keyword_hierarchy AS ( -- Query to drill down into the children keyword nodes
    SELECT id, keyword, frequency, sentiment, parent_id
    FROM keywords
    WHERE id = 'parent_keyword_id' -- replace with ID of parent
    UNION ALL
    SELECT k.id, k.keyword, k.frequency, k.sentiment, k.parent_id
    FROM keywords keyword
    INNER JOIN keyword_hierarchy kh ON k.parent_id = kh.id
)
SELECT * FROM keyword_hierarchy;


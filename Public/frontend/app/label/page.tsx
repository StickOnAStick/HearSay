'use client'; // Don't think about shipping invalid states to DB
import React, { useEffect, useState } from 'react';
import PocketBase, { RecordModel } from 'pocketbase';

const pb = new PocketBase(process.env.NEXT_PUBLIC_LOCAL_POCKETBASE_URL);


const LabelPage: React.FC = () => {
    const [keywordInput, setKeywordInput] = useState<string>('');
    const [keywords, setKeywords] = useState<string[]>([]);
    const [sentiment, setSentiment] = useState<number | string>('');
    const [reviews, setReviews] = useState<RecordModel[]>([]);
    const [curReview, setCurReview] = useState<RecordModel | null>(null);

    const handleAddKeyword = () => {
        if (keywordInput.trim() && !keywords.includes(keywordInput.trim())) {
            setKeywords((prev) => [...prev, keywordInput.trim()]);
            setKeywordInput(''); // Clear input after adding
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setKeywordInput(e.target.value);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddKeyword();
        }
    };

    const handleSentimentKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key == 'Enter'){
            e.preventDefault();
            submit();
        }
    };

    const submit = async () => {
        if (!curReview || !keywords || sentiment === '') {
            alert('Please enter keywords and sentiment.');
            return;
        }

        try {
            await pb.collection('LABELS').create({
                review_id: curReview.id,
                keywords: JSON.stringify(keywords), // Convert to array
                sentiment: parseFloat(sentiment as any), // Ensure it's a float
            });

            alert('Label saved!');

            // Move to the next review
            setReviews((prev) => prev.slice(1));
            setCurReview((prev) => (prev?.slice(1)[0] || null));
            setKeywords([]);
            setSentiment('');
        } catch (error) {
            console.error('Error saving label:', error);
            alert('Failed to save label.');
        }
    }

    const removeKeyword = (keywordToRemove: string) => {
        setKeywords((prev) => prev.filter((keyword) => keyword !== keywordToRemove));
    };


    // Fetch reviews that haven't been labeled
    async function getUnlabledReviews() {
        try {
            const reviews = await pb.collection('Reviews').getFullList({
                filter: '!id IN (SELECT review_id FROM labels)'
            })
            console.log("reviews:\n", reviews);
            setReviews(reviews);
            if (reviews.length > 0) {
                setCurReview(reviews[0]);
            }
        } catch (error) {
            console.error("Could not fetch unlabled reviews!", error);
            // do stuff
            throw error;
        }
    }


    useEffect( () => {
        getUnlabledReviews();
    }, []);


    return (
        <div className="min-h-screen flex flex-col items-center justify-center font-[family-name:var(--font-geist-sans)]">
            <h1 className="text-2xl font-bold mb-10">Label the data</h1>
            <div className="flex flex-col gap-4 w-full max-w-4xl px-10">
                <textarea
                    className="bg-[--background] border border-[--foreground] p-2 rounded-lg w-full"
                    rows={5}
                    placeholder={curReview ? 
                        curReview.text : 'Review loading or did not load'
                    }
                >
                </textarea>
                <div className="flex flex-col gap-1">
                    <i>Add keywords one at a time (press Enter to add)</i>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Type a keyword and press Enter"
                            className="w-full bg-[--background] border border-[--foreground] p-2 rounded-lg"
                            value={keywordInput}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                        />
                        <button
                            onClick={handleAddKeyword}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                        >
                            Add
                        </button>
                    </div>
                </div>
                <div>
                    <strong>Keywords:</strong>
                    <div className="flex flex-wrap gap-2 mt-2">
                        {keywords.map((keyword, index) => (
                            <span
                                key={index}
                                className="bg-[--foreground] text-[--background] px-3 py-1 rounded-lg flex items-center gap-2"
                            >
                                {keyword}
                                <button
                                    onClick={() => removeKeyword(keyword)}
                                    className="text-red-500 font-bold hover:text-red-700"
                                >
                                    &times;
                                </button>
                            </span>
                        ))}
                    </div>
                </div>
                <div className='flex flex-col gap-1'>
                    <i>Choose a sentiment float +/-1</i>
                    <input 
                        type="number" 
                        className='w-full bg-background border border-foreground p-2 rounded-lg' 
                        placeholder='+/-1.0'
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSentiment(parseFloat(e.target.value))}
                        onKeyDown={handleSentimentKeyDown}
                    />
                </div>
                <button type='submit' className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600'
                    onClick={submit}
                    onKeyDown={submit}
                >
                    Submit
                </button>
            </div>
        </div>
    );
};

export default LabelPage;

'use client'; // Don't think about shipping invalid states to DB
import React, { useEffect, useState } from 'react';
import PocketBase, { RecordModel } from 'pocketbase';
import Review from '@/types/main';

const pb = new PocketBase(process.env.NEXT_PUBLIC_LOCAL_POCKETBASE_URL);


const LabelPage: React.FC = () => {
    const [keywordInput, setKeywordInput] = useState<string>('');
    const [keywords, setKeywords] = useState<string[]>([]);
    const [sentiment, setSentiment] = useState<number | null>(null);
    const [curReview, setCurReview] = useState<Review | null>(null);
    const [error, setError] = useState<string>('');

    const sentimentOptions = [-1, -0.5, 0, 0.5, 1]

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
        if (!curReview || !keywords || sentiment === undefined) {
            alert('Please enter keywords and sentiment.');
            return;
        }
    
        try {
            const label = await pb.collection('labels').create({
                review_id: curReview.id,
                keywords: keywords,
                sentiment: parseFloat(sentiment as any),
            });
         
            await pb.collection('reviews').update(curReview.id, {
                "labels": [...curReview.labels, label.id]
            })
    
            alert('Label saved!');
    
            setKeywords([]);
            setSentiment(null);
            await getUnlabledReviews(); 

        } catch (error: unknown) {
            console.error('Error saving label:', error);
            // @ts-expect-error Pocketbase error type.
            setError(err.message || "Error fetching unlabeled reviews")
        }
    };

    const removeKeyword = (keywordToRemove: string) => {
        setKeywords((prev) => prev.filter((keyword) => keyword !== keywordToRemove));
    };


    // Fetch reviews that haven't been labeled
    async function getUnlabledReviews() {
        try {
            const result: Review = await pb.collection('reviews').getFirstListItem('labels:length = 0'); // Grab only unlabeled reviews. Don't know why labels=null doesn't work. View 0.30 PB patch notes.
            console.log(result);
            setCurReview(result);

            
        } catch (error) {
            console.error("Could not fetch unlabled reviews!", error);
            // do stuff
            setError("Error fetching unlabeled records!");
            throw error;
        }
    }


    useEffect( () => {
        getUnlabledReviews();
    }, []);


    return (
        <div className="min-h-screen flex flex-col items-center justify-center font-[family-name:var(--font-geist-sans)]">
            <h1 className="text-2xl font-bold mb-10">Label the data</h1>
            <i>If there's an error loading just fetch a new review.</i>
            <button type='submit' className='bg-white text-black rounded p-2 mb-2' onClick={async () => await getUnlabledReviews()}>Fetch Review</button>
            <div className="flex flex-col gap-4 w-full max-w-4xl px-10">
                <div className='bg-[--background] border border-[--foreground] p-2 rounded-lg w-full placeholder:text-white text-white'>{curReview ? curReview.summary : "Loading Summary..."}</div>
                <textarea
                    className="bg-[--background] border border-[--foreground] p-2 rounded-lg w-full placeholder:text-white text-white"
                    rows={10}
                    value={curReview ? 
                        `${curReview.text}` : 'Loading review text...'
                    }
                    disabled
                />
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
                    <div className='flex gap-3'>

                    {
                        sentimentOptions.map((value: number) => {
                            return (
                                <button
                                    key={value} 
                                    className='w-full bg-foreground p-2 rounded text-black'
                                    onClick={() => {setSentiment(value); console.log("Sentiment set to: ", sentiment)}}
                                >   
                                    {value}
                                </button>
                            )
                        })
                    }
                    </div>

                    <input 
                        type="number" 
                        className='w-full bg-background border border-foreground p-2 rounded-lg' 
                        placeholder='+/-1.0'
                        value={sentiment ?? undefined}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSentiment(parseFloat(e.target.value))}
                        onKeyDown={handleSentimentKeyDown}
                    />
                </div>
                <button type='submit' className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600'
                    onClick={submit}
                    onKeyDown={submit}
                >
                    Next Review
                </button>
            </div>
        </div>
    );
};

export default LabelPage;

'use client'; // Don't think about shipping invalid states to DB
import React, { useEffect, useState } from 'react';
import PocketBase from 'pocketbase';
import Review from '@/types/main';
import { Keywords } from '@/types/main';

const pb = new PocketBase(process.env.NEXT_PUBLIC_LOCAL_POCKETBASE_URL);


const LabelPage: React.FC = () => {
    const [keywordInput, setKeywordInput] = useState<string>('');
    const [keywords, setKeywords] = useState<Keywords[]>([]);
    const [sentimentInput, setSentimentInput] = useState<number>(0);
    const [sentiment, setSentiment] = useState<number | null>(null);
    const [curReview, setCurReview] = useState<Review | null>(null);
    const [error, setError] = useState<string>('');

    const sentimentOptions = [-1, -0.5, 0, 0.5, 1]

    const handleAddKeyword = () => {
        if (keywordInput.trim() && !keywords.some(k => k.keyword === keywordInput.trim())) {
            setKeywords((prev: Keywords[]) => [...prev, { keyword: keywordInput.trim(), sentiment: sentimentInput }]);
            setKeywordInput(''); // Clear input after adding
            setSentimentInput(0); // Reset sentiment input
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
        if (e.key === 'Enter') {
            e.preventDefault();
            submit();
        }
    };

    const submit = async () => {
        if (!curReview || !keywords.length || sentiment === undefined || sentiment === null) {
            alert('Please enter keywords and sentiment.');
            return;
        }

        try {
            const label = await pb.collection('labels').create({
                review_id: curReview.id,
                keywords,
                sentiment,
            });

            await pb.collection('reviews').update(curReview.id, {
                labels: [...curReview.labels, label.id],
            });

            alert('Label saved!');

            setKeywords([]);
            setSentiment(null);
            await getUnlabeledReviews();
        } catch (error: unknown) {
            console.error('Error saving label:', error);
            setError("Error saving label.");
        }
    };

    const removeKeyword = (keywordToRemove: string) => {
        setKeywords((prev) => prev.filter(({ keyword }) => keyword !== keywordToRemove));
    };

    async function getUnlabeledReviews() {
        try {
            const result: Review = await pb.collection('reviews').getFirstListItem('labels:length = 0');
            setCurReview(result);
        } catch (error) {
            console.error("Could not fetch unlabeled reviews!", error);
            setError("Error fetching unlabeled records!");
        }
    }

    useEffect(() => {
        getUnlabeledReviews();
    }, []);

    const getColorFromSentiment = (sentiment: number) => {
        if (sentiment === -1) return 'bg-red-500';
        if (sentiment === -0.5) return 'bg-red-300';
        if (sentiment === 0) return 'bg-gray-200';
        if (sentiment === 0.5) return 'bg-green-300';
        if (sentiment === 1) return 'bg-green-500';
        return 'bg-gray-200';
    };


    return (
        <div className="min-h-screen flex flex-col items-center justify-center font-[family-name:var(--font-geist-sans)]">
            <h1 className="text-2xl font-bold mb-10">Label the data</h1>
            {/* <i>If there&apos;s an error loading just fetch a new review.</i>
            <button type='submit' className='bg-white text-black rounded p-2 mb-2' onClick={async () => await getUnlabeledReviews()}>Fetch Review</button> */}

            <h2 className='font-bold text-xl'>Remember!</h2>
            <i className='mb-10'>No keywords <u>is OKAY</u></i>
            <div className="flex flex-col gap-8 w-full max-w-4xl px-6">
                <div className='bg-zinc-900 px-2 py-4 rounded flex flex-col gap-2 border-zinc-800 border'>
                    <i className='text-sm'>Title</i>
                    <div className='bg-[--background] p-2 rounded-lg w-full placeholder:text-white text-white'>
                        {curReview ? curReview.summary : "Loading Summary..."}
                    </div>
                    <i className='text-sm'>Review</i>
                    <textarea
                        className="bg-[--background] p-2 px-3 rounded-lg leading-7 w-full placeholder:text-white text-white"
                        rows={10}
                        value={curReview ? 
                            `${curReview.text}` : 'Loading review text...'
                        }
                        disabled
                    />
                </div>
              
                <div className="flex flex-col gap-3 bg-zinc-900 px-2 py-4 rounded-lg border-zinc-800 border">
                    <i>Add keywords one at a time (press Enter to add)</i>
                    <div className="flex flex-col gap-2">
                        <input
                            type="text"
                            placeholder="Type a keyword and press Enter"
                            className="w-full bg-[--background] p-2 rounded-lg"
                            value={keywordInput}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                        />
                        <label><i>Sentiment Neg/Neut/Pos</i></label>
                        <input
                            type="range"
                            min={-1}
                            max={1}
                            step={0.5}
                            value={sentimentInput}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSentimentInput(parseFloat(e.target.value))}
                        />
                        <button
                            onClick={handleAddKeyword}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                        >
                            Add
                        </button>
                    </div>
                    <div>
                        <p>Keywords:</p>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {keywords.map(({keyword, sentiment}, index) => (
                                <span
                                    key={index}
                                    className={`${getColorFromSentiment(sentiment)} text-[--background] px-3 py-1 rounded-lg flex items-center gap-2`}
                                >
                                    {keyword} ({sentiment})
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
                </div>
               
                {
                    error &&
                    <div className='text-red-600'>{error}</div>
                }
                <div className='flex flex-col gap-1 bg-zinc-900 border-zinc-800 rounded-lg border px-2 py-4'>
                    <i>Overall Sentiment Neg/Neut/Pos</i>
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
                        value={sentiment ?? ''}
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

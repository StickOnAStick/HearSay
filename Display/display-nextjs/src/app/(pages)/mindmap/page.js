'use client';

import 'reactflow/dist/style.css'
import './mindmap.css'
import ReactFlow, { Background, Controls } from 'reactflow';
import { useState, useEffect } from 'react';

export default function MindMap(){
	const [productsData, setProductsData] = useState([]);
	const [keywordsData, setKeywordsData] = useState([]);
	const [aggregatedData, setAggregatedData] = useState([]);
	let KeywordNodes = [];
	let KeywordEdges = [];

	// Products Data Fetch
  	useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/ProductsData');
      const data = await response.json();
      setProductsData(data);
    };
    	fetchData();
  	}, []);

	// Keyword Data Fetch
  	useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/KeywordsData');
      const data = await response.json();
      setKeywordsData(data);
    };
    	fetchData();
  	}, []);

  	// Aggregated Data Fetch
	useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/AggregatedData');
      const data = await response.json();
      setAggregatedData(data);
    };
    	fetchData();
  	}, []);

	// This is not ideal, but without an aggregated_id and these currently being processed as objects this is alright

	// Product Nodes
	for (const prodKey in Object.entries(productsData))
	{
		if(productsData[prodKey].product_id !== ''){
			KeywordNodes.push({id: prodKey+"prod", data: {label: productsData[prodKey].product_id + " (" + productsData[prodKey].gen_rating + ")"}, position: {x: prodKey*200, y: 50}});

			//Aggregated Nodes
			for(const aggKey in Object.entries(aggregatedData))
			{
				// Checking whole aggregate list and comparing for product id
				if(aggregatedData[aggKey].product_id === productsData[prodKey].product_id)
				{
					KeywordNodes.push({id: aggKey+"agg", data: {label: aggregatedData[aggKey].gen_keyword + " (" + aggregatedData[aggKey].avg_sentiment + ")"}, position: {x: aggKey*200, y: 200}});
					KeywordEdges.push({id: aggKey + "aggE", source: prodKey+"prod", target: aggKey+"agg"});

					// And checking whole keywords list under that
					for(const wordKey in Object.entries(keywordsData))
					{
						// Comparing if its the same product and if the original keywords includes the keyword
						if(aggregatedData[aggKey].original_keywords.includes(keywordsData[wordKey].keyword) && keywordsData[wordKey].product_id === productsData[prodKey].product_id)
						{
							KeywordNodes.push({id: wordKey+"word", data: {label: keywordsData[wordKey].keyword+ " (" + keywordsData[wordKey].sentiment + ")"}, position: {x: wordKey*200, y: 500}});
							KeywordEdges.push({id: wordKey+"wordE", source: aggKey+"agg", target: wordKey+"word"});
						}
					}
				}
			}
		}
	}

  	//Return ReactFlow with Test Nodes
  	return (
  		<div className='mind-map'>
  			<h1> Keywords Mindmap </h1>
    		<div style={{ height: '1000px' }}>
      			<ReactFlow 
        			nodes={KeywordNodes} 
        			edges={KeywordEdges}
      			>
        			<Background />
        			<Controls />
      			</ReactFlow>
    		</div>
    	</div>
  );
};
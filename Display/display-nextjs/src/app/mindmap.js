'use client';

import 'reactflow/dist/style.css'
import './main.css'
import ReactFlow, { Background, Controls } from 'reactflow';
import { useState, useEffect } from 'react';

export default function MindMap({ productsData, aggregatedData, keywordsData }){
	// ReactFlow Functionality
	const [captureElementClick, setCaptureElementClick] = useState(false);
	let KeywordNodes = [];
	let KeywordEdges = [];

	// Node Colors
	const positive_aggregate_color = 'darkseagreen';
	const positive_keyword_color = 'lightgreen';

	const neutral_aggregate_color = 'tomato';
	const neutral_keyword_color = 'lightsalmon';

	const negative_aggregate_color = '#CD5C5C';
	const negative_keyword_color = 'lightcoral';

	// Product Node Creation & Placement
	function pushProductNodes()
	{
		// Searches through product list and adds all valid products
		for (const product_key in productsData)
		{
		  const product = productsData[product_key];

		  // Catch invalid products or end of list
		  if(!product || product.product_id == '') continue;

		  // Create Node Data
		  const id = `${product.product_id}product`;
		  const label = `${product.product_id}`;
		  let x = 0, y = 0;

		  switch (product_key % 3){
		  case 0:
		    x = 1600
		    y = (product_key / 3) * 1400;
		    break;
		  case 1:
		    x = 0;
		    y = 700 + 1400 *( (product_key - 1) / 3);
		    break;
		  case 2:
		    x = 3200;
		    y = 700 + 1400 * ((product_key - 2) / 3);
		    break;
		  }

		  // Split into groups to place products neatly separated from one another
		  try{
		    KeywordNodes.push({id: id, data: {label: label}, position: {x: x, y: y}});
		  } catch(error)
		  {
		    console.error("Error: Product node failure");
		  }
		}
	}

	// Aggregate Node Creation & Placement
	function pushAggregateNodes()
	{
		// Cycle through aggregates & create map of aggregate nodes sorted by product_id
		const aggregateProductMap = {}
		for(const key in aggregatedData)
		{
		  const { product_id } = aggregatedData[key];
		  if(!product_id || product_id == '') continue;

		  // Sort into map
		  if(aggregateProductMap[product_id])
		  {
		    aggregateProductMap[product_id].push(key);
		  } else
		  {
		    aggregateProductMap[product_id] = [key];
		  }
		}

		// Cycle through map by product_id

		for(const product_id in aggregateProductMap)
		{
		  // Ensure product_ids are connected to valid nodes
		  const product_node = KeywordNodes.find(node => node.id === `${product_id}product`);
		  if(typeof product_node === "undefined") continue;

		  // Set node_angle and node_index
		  const node_angle = (2 * Math.PI) / aggregateProductMap[product_id].length;
		  let node_index = 0;

		  // Set scale of aggregates to have maximum and minimum distance between them
		  const scale = 300 * Math.min(1.4,(aggregateProductMap[product_id].length / 3))

		  // Add aggregate nodes
		  for(const key_index in aggregateProductMap[product_id])
		  {
		    const key = aggregateProductMap[product_id].at(key_index)
		    const aggregate = aggregatedData[key];
		    const avg_sentiment = Math.round(aggregate.sentiment_sum / aggregate.sentiment_count * 10) / 10
		    // Set Node Color
		    let node_color = '';
		    node_color = avg_sentiment > 0.2
		      ? positive_aggregate_color
		      : aggregate.avg_sentiment < -0.2
		      ? negative_aggregate_color
		      : neutral_aggregate_color

		    // Set Other Data for Aggregate Node
		    const id = `${key}aggregate`;
		    const label = `${aggregate.gen_keyword} (${avg_sentiment})`;

		    const edge_id = `${key}aggregate_e`;
		    const edge_target = `${product_id}product`;
		    const x = Math.cos(node_angle * node_index)*(2*scale) + product_node.position.x;
		    const y = Math.sin(node_angle * node_index)*scale + product_node.position.y + 50;
		    node_index++;

		    // Try-catch to push aggregate node and connect to product node
		    try{
		      KeywordNodes.push({id: id, data: {label: label}, position: {x: x, y: y}, style: {backgroundColor: node_color}});
		      KeywordEdges.push({id: edge_id, source: id, target: edge_target, type: "straight"});
		    } catch(error)
		    {
		      console.error("Error: Aggregate node failure.");
		    }  
		  }
		}
	}

	// Keyword Node Creation & Placement
	function pushKeywordNodes()
	{
		
		// Cycle through keywords and aggregates & create map of keywords sorted by aggregate keys
		const keywordAggregateMap = {};
		for(const aggregate_key in aggregatedData)
		{
		  for(const keyword_key in keywordsData)
		  {
		    const keyword = keywordsData[keyword_key];
		    const aggregate = aggregatedData[aggregate_key]

		    if(!aggregate || aggregate.product_id == '') continue;

		    // If keyword is in aggregate with same product_id, it is added to the aggregate's array
		    if(keyword.product_id === aggregate.product_id && aggregate.child_keywords.includes(keyword.review_id))
		    {
		      if(keywordAggregateMap[aggregate_key])
		      {
		      	if(!keywordAggregateMap[aggregate_key].includes(keyword.review_id))
		      	{
		      		keywordAggregateMap[aggregate_key].push(keyword_key);
		      	}
		      } else
		      {
		        keywordAggregateMap[aggregate_key] = [keyword_key];
		      }
		    }
		  }
		}

		// Adding Nodes for each aggregate collection
		for(const aggregate_key in keywordAggregateMap)
		{
		  // Ensure aggregate node is valid
		  const aggregate_node = KeywordNodes.find(node => node.id === `${aggregate_key}aggregate`);
		  if(typeof aggregate_node === "undefined") continue;

		  // Define node angle and index
		  const node_angle = (2 * Math.PI) / keywordAggregateMap[aggregate_key].length;
		  let node_index = 0;

		  // Add Keyword Nodes
		  for(const key_index in keywordAggregateMap[aggregate_key])
		  {
		    const key = keywordAggregateMap[aggregate_key].at(key_index)
		    const keyword = keywordsData[key];

		    // Set Node Color
		    let node_color = '';
		    node_color = keyword.sentiment > 0.2
		      ? positive_keyword_color
		      : keyword.sentiment < -0.2
		      ? negative_keyword_color
		      : neutral_keyword_color

		    // Set Other Data for Keyword Node
		    const id = `${key}keyword`;
		    const label = `${keyword.keyword} (${keyword.sentiment})`;

		    const edge_id = `${key}keyword_e`;
		    const edge_target = `${aggregate_key}aggregate`;
		    const x = Math.cos(node_angle * node_index)*200 + aggregate_node.position.x;
		    const y = Math.sin(node_angle * node_index)*100 + aggregate_node.position.y;
		    node_index++;

		    // Try-catch to push keyword node and connect to aggregate node
		    try{
		      KeywordNodes.push({id: id, data: {label: label}, position: {x: x, y: y}, style: {backgroundColor: node_color}});
		      KeywordEdges.push({id: edge_id, source: id, target: edge_target, type: "straight"});
		    } catch(error)
		    {
		      console.error("Error: Keyword node failure.");
		    }  
		  }
		}
	}

	// On load fit items to screen - wait until after data has been added
	const handleLoad = (reactFlowInstance) => {
		setTimeout(() => {
		  reactFlowInstance.fitView();
		}, 1000);
	}

	pushProductNodes();
  	pushAggregateNodes();
  	pushKeywordNodes();

	return (
		<div style={{ height: '1000px', width: '1800px' }}>
	        <ReactFlow 
	          nodes={KeywordNodes} 
	          edges={KeywordEdges}
	          onInit={handleLoad}
	          nodeOrigin={[0.5,0.5]}
	          fitViewOptions={{ padding: 0.5}}
	        >
	        	<Background />
	        	<Controls />
	        </ReactFlow>
		</div>
    );
};
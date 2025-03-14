'use client';

import 'reactflow/dist/style.css'
import './main.css'
import ReactFlow, { Background, Controls } from 'reactflow';
import { useState, useEffect } from 'react';

export default function MindMap(){
  // ReactFlow Data & Functionality
  const [productsData, setProductsData] = useState([]);
  const [keywordsData, setKeywordsData] = useState([]);
  const [aggregatedData, setAggregatedData] = useState([]);
  const [captureElementClick, setCaptureElementClick] = useState(false);
  let KeywordNodes = [];
  let KeywordEdges = [];
  // Keyword Colors
  const positive_aggregate_color = 'darkseagreen';
  const positive_keyword_color = 'lightgreen';

  const neutral_aggregate_color = 'tomato';
  const neutral_keyword_color = 'lightsalmon';

  const negative_aggregate_color = '#CD5C5C';
  const negative_keyword_color = 'lightcoral';

  // Products Data Fetch
  function fetchProductData()
  {
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
  }
  
  // Product Node Creation & Placement
  function pushProductNodes()
  {
    // Searches through product list and adds all valid products
    for (const product_key in Object.entries(productsData))
    {
      if(productsData[product_key].product_id !== ''){
        // Split into groups to place products neatly separated from one another
        try{
          switch (product_key % 3)
          {
          case 0:
            KeywordNodes.push({id: product_key+"product", data: {label: productsData[product_key].product_id + " (" + productsData[product_key].gen_rating + ")", summary: productsData[product_key].gen_summary}, position: {x: 900, y: (product_key / 3) * 600}});
            break;
          case 1:
            KeywordNodes.push({id: product_key+"product", data: {label: productsData[product_key].product_id + " (" + productsData[product_key].gen_rating + ")", summary: productsData[product_key].gen_summary}, position: {x: 0, y: 300 + 600*((product_key-1)/3)}});
            break;
          case 2:
            KeywordNodes.push({id: product_key+"product", data: {label: productsData[product_key].product_id + " (" + productsData[product_key].gen_rating + ")", summary: productsData[product_key].gen_summary}, position: {x: 1800, y: 300 + 600*((product_key-2)/3)}});
            break;
          }
        } catch(error)
        {
          console.error("Error: Product node failure");
        }
      }
    }
  }


  // Aggregate Node Creation & Placement
  function pushAggregateNodes()
  {
    let current_product = '';
    let currentAggregates = [];
    for(const agg_key in Object.entries(aggregatedData))
    {
      // For each aggregate, searching through productsData for product_key
      for(const product_key in Object.entries(productsData))
      {
        if(aggregatedData[agg_key].product_id === productsData[product_key].product_id && aggregatedData[agg_key].product_id !== '')
        {
          // Create array of aggregates related to specific product so that they can be displayed together
          if(product_key == current_product)
          {
            currentAggregates.push(agg_key);
          } else
          {
            if(currentAggregates.length != 0)
            {
              // Used to determine the position of the new node, placed in a circle around the product node
              let node_angle = (2 * Math.PI) / currentAggregates.length;
              let node_index = 0;
              const product_node = KeywordNodes.find(node => node.id === current_product + "product");


              // Once we have that array, place all data
              for(const current_agg_key of currentAggregates)
              {
                // Select color based on average sentiment
                let node_color = '';
                if(aggregatedData[current_agg_key].avg_sentiment > 0.2)
                {
                  node_color = positive_aggregate_color;
                } else if(aggregatedData[current_agg_key].avg_sentiment < -0.2)
                {
                  node_color = negative_aggregate_color;
                } else
                {
                  node_color = neutral_aggregate_color;
                }
                // Try-catch to push aggregate node and connect to product node
                try{
                  KeywordNodes.push({id: current_agg_key + "agg", data: {label: aggregatedData[current_agg_key].gen_keyword + " (" + aggregatedData[current_agg_key].avg_sentiment + ")"}, position: {x: Math.cos(node_angle * node_index)*300 + product_node.position.x, y: Math.sin(node_angle * node_index)*300 + product_node.position.y + 50}, style: {backgroundColor: node_color}});
                  KeywordEdges.push({id: current_agg_key + "agg_e", source: current_product + "product", target: current_agg_key + "agg", type: "straight"});
                } catch(error)
                {
                  console.error("Error: Aggregate node failure.");
                }
                node_index++;
              }
            }
            
            current_product = product_key;
            currentAggregates = [agg_key];
          }
        }
      }
    }

    // Run the loop one more time for any leftover data
    if(currentAggregates.length != 0)
    {
      let node_angle = (2 * Math.PI) / currentAggregates.length;
      let node_index = 0;
      const product_node = KeywordNodes.find(node => node.id === current_product + "product");

      for(const current_agg_key of currentAggregates)
      {
        let node_color = '';
        if(aggregatedData[current_agg_key].avg_sentiment > 0.2)
        {
          node_color = positive_aggregate_color;
        } else if(aggregatedData[current_agg_key].avg_sentiment < -0.2)
        {
          node_color = negative_aggregate_color;
        } else
        {
          node_color = neutral_aggregate_color;
        }
        try{
          KeywordNodes.push({id: current_agg_key + "agg", data: {label: aggregatedData[current_agg_key].gen_keyword + " (" + aggregatedData[current_agg_key].avg_sentiment + ")"}, position: {x: Math.cos(node_angle * node_index)*300 + product_node.position.x, y: Math.sin(node_angle * node_index)*300 + product_node.position.y + 50}, style: {backgroundColor: node_color}});
          KeywordEdges.push({id: current_agg_key + "agg_e", source: current_product + "product", target: current_agg_key + "agg", type: "straight"});
        } catch(error)
        {
          console.error("Error: Aggregate node failure.");
        }
        node_index++;
      }
    }
  }


  // Keyword Node Creation & Placement
  function pushKeywordNodes()
  {
    let current_aggregate = '';
    let currentWords = [];
    // For each keyword, search aggregate for matching value
    for(const word_key in Object.entries(keywordsData))
    {
      for(const agg_key in Object.entries(aggregatedData))
      {
        if(aggregatedData[agg_key].product_id == '')
        {
          continue;
        }

        // Comparing if its the same product and if the original keywords includes the keyword
        if(keywordsData[word_key].product_id === aggregatedData[agg_key].product_id  && aggregatedData[agg_key].original_keywords.includes(keywordsData[word_key].keyword))
        {
          // Collecting keywords until we have the aggregate group and then displaying them together
          if(agg_key == current_aggregate)
          {
            currentWords.push(word_key);
          } else
          {
            if(currentWords.length != 0)
            {
              const node_angle = (2 * Math.PI) / currentWords.length;
              // Try catch for finding aggregate node, aggregate node needed to determine position of keywords nodes around it
              const aggregate_node = KeywordNodes.find(node => node.id === current_aggregate + "agg");
              let node_index = 0;
              
              for(const current_word_key of currentWords)
              {
                // Set color based on keyword sentiment
                let node_color = '';
                if(keywordsData[current_word_key].sentiment > 0.2)
                {
                  node_color = positive_keyword_color;
                } else if(keywordsData[current_word_key].sentiment < -0.2)
                {
                  node_color = negative_keyword_color; 
                } else
                {
                  node_color = neutral_keyword_color;
                }
                // Try-catch for Keyword Node creation
                try{
                  KeywordNodes.push({id: current_word_key+"word", data: {label: keywordsData[current_word_key].keyword+ " (" + keywordsData[current_word_key].sentiment + ")"}, position: {x: Math.cos(node_angle * node_index)*200 + aggregate_node.position.x, y: Math.sin(node_angle * node_index)*100 + aggregate_node.position.y}, style: {backgroundColor: node_color}});
                  KeywordEdges.push({id: current_word_key+"word_e", source: current_aggregate+"agg", target: current_word_key+"word", type: "straight"}); 
                } catch(error)
                {
                  console.error("Error: Keyword node failure");
                }
                
                node_index++;
              }
            }
            current_aggregate = agg_key;
            currentWords = [word_key];
          }
        }
      }
    }

    // Extra loop for extra data

    if(currentWords.length != 0)
    {
      const node_angle = (2 * Math.PI) / currentWords.length;
      const aggregate_node = KeywordNodes.find(node => node.id === current_aggregate + "agg");
      let node_index = 0;
      
      for(const current_word_key of currentWords)
      {
        let node_color = '';
        if(keywordsData[current_word_key].sentiment > 0.2)
        {
          node_color = positive_keyword_color;
        } else if(keywordsData[current_word_key].sentiment < -0.2)
        {
          node_color = negative_keyword_color; 
        } else
        {
          node_color = neutral_keyword_color;
        }
        try{
          KeywordNodes.push({id: current_word_key+"word", data: {label: keywordsData[current_word_key].keyword+ " (" + keywordsData[current_word_key].sentiment + ")"}, position: {x: Math.cos(node_angle * node_index)*200 + aggregate_node.position.x, y: Math.sin(node_angle * node_index)*100 + aggregate_node.position.y}, style: {backgroundColor: node_color}});
          KeywordEdges.push({id: current_word_key+"word_e", source: current_aggregate+"agg", target: current_word_key+"word", type: "straight"}); 
        } catch(error)
        {
          console.error("Error: Keyword node failure");
        }
        node_index++;
      }
    }
   }
  

    // Handle node click for review display - show product summaries
    const handleNodeClick = (event, node) => {
      if(node.id.includes("product"))
      {
        alert(node.data.summary);
      }
    }

    // On load fit items to screen - wait until after data has been added
    const handleLoad = (reactFlowInstance) => {
      setTimeout(() => {
        reactFlowInstance.fitView();
      }, 1000);
    }

    fetchProductData();
    pushProductNodes();
    pushAggregateNodes();
    pushKeywordNodes();

    //Return ReactFlow with Nodes
    return (
      <div className='mind-map'>
        <h1> MindMap of Products and Keywords </h1>
        <div style={{ height: '1000px', width: '1800px' }}>
            <ReactFlow 
              nodes={KeywordNodes} 
              edges={KeywordEdges}
              onNodeClick={handleNodeClick}
              onInit={handleLoad}
              nodeOrigin={[0.5,0.5]}
            >
              <Background />
              <Controls />
            </ReactFlow>
        </div>
      </div>
  );
};
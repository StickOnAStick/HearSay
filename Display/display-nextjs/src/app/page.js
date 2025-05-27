import 'reactflow/dist/style.css'
import './main.css'
import MindMap from './mindmap'
import { parseData } from './lib/parseData'

export default async function Page(){

  const defPath = '../../Simple/data/output';

  const productsData = await parseData(`${defPath}/Keywords_products.csv`);
  const aggregatedData = await parseData(`${defPath}/Keywords-agg.csv`);
  const keywordsData = await parseData(`${defPath}/Keywords_keywords.csv`);

  //Return Page HTML with MindMap and Loading
  return (
    <div className='mind-map'>
      <h1> HearSay MindMap </h1>
      <MindMap productsData = {productsData} aggregatedData = {aggregatedData} keywordsData = {keywordsData}/>
    </div>
  );
};
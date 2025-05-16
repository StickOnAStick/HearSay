import 'reactflow/dist/style.css'
import './main.css'
import MindMap from './mindmap'
import { parseData } from './lib/parseData'

export default async function Page(){

  const defPath = '../../Simple/data/output';

  const productsData = await parseData(`${defPath}/EXPODEMO_products.csv`);
  const aggregatedData = await parseData(`${defPath}/EXPODEMO-agg.csv`);
  const keywordsData = await parseData(`${defPath}/EXPODEMO_keywords.csv`);

  //Return Page HTML with MindMap and Loading
  return (
    <div className='mind-map'>
      <h1> MindMap of Products and Keywords </h1>
      <MindMap productsData = {productsData} aggregatedData = {aggregatedData} keywordsData = {keywordsData}/>
    </div>
  );
};
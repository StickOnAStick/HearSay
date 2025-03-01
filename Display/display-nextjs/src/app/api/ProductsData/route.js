import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';
import { NextResponse } from 'next/server';

export function GET(request){

	const productsPath = path.join(process.cwd(), '/src/app/csv/Products.csv');

	try {
		const productsData = fs.readFileSync(productsPath, 'utf-8');
		const parsedProducts = Papa.parse(productsData, {header:true}).data;
		return NextResponse.json( parsedProducts, {status: 200});
	} catch (error) {
		console.error(error);
		return NextResponse.json( {error: "Failed to read Products Data"}, {status: 500});
	}
}
import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';
import { NextResponse } from 'next/server';

export function GET(request){

	const keywordsPath = path.join(process.cwd(), '/src/app/csv/Keywords.csv');

	try {
		const keywordsData = fs.readFileSync(keywordsPath, 'utf-8');
		const parsedKeywords = Papa.parse(keywordsData, {header:true}).data;
		return NextResponse.json( parsedKeywords, {status: 200});
	} catch (error) {
		console.error(error);
		return NextResponse.json( {error: "Failed to read KeywordsData"}, {status: 500});
	}
}
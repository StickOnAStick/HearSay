import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';
import { NextResponse } from 'next/server';

export function GET(request){

	const aggregatePath = path.join(process.cwd(), '/src/app/csv/Aggregated.csv');

	try {
		const aggregatedData = fs.readFileSync(aggregatePath, 'utf-8');
		const parsedAggregate = Papa.parse(aggregatedData, {header:true}).data;
		return NextResponse.json( parsedAggregate, {status: 200});
	} catch (error) {
		console.error(error);
		return NextResponse.json( {error: "Failed to read Aggregated Data"}, {status: 500});
	}
}
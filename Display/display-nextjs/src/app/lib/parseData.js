import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';
import { NextResponse } from 'next/server';

export async function parseData(file_path){

	const aggregatePath = path.join(process.cwd(), file_path);

	try {
		const aggregatedData = fs.readFileSync(aggregatePath, 'utf-8');
		const parsedAggregate = Papa.parse(aggregatedData, {header:true}).data;
		return parsedAggregate;
	} catch (error) {
		console.error(error);
		return 0;
	}
}
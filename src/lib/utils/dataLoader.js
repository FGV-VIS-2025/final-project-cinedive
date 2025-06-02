// src/lib/utils/dataloader.js
import { tsv } from 'd3';
import { base } from '$app/paths';

let cachedMovies = null;

export async function loadMoviesLastMovies() {
	if (cachedMovies) {
		console.log('Using cached movies data');
		return cachedMovies;
	}

	const data = await tsv(`${base}/data/title_oscar.tsv`, row => ({
        ...row,
        averageRating: +row.averageRating,
        numVotes: +row.numVotes,
        oscarNominations: +row.oscarNominations,
        oscarWins: +row.oscarWins,
    }));

	cachedMovies = data;
	console.log('Loaded movies data from TSV file');
	return cachedMovies;
}

let cachedGraph = null;

export async function loadGraph() {
	if (cachedGraph) {
	  console.log('Using cached graph data');
	  return cachedGraph;
	}
  
	const res = await fetch(`${base}/data/graph_for_project_sin_country.json`);
	if (!res.ok) {
	  console.error("❌ No se pudo cargar graph_for_project.json:", res.status);
	  throw new Error("Graph JSON not found");
	}
	const data = await res.json();
	console.log("✅ loadGraph(): JSON cargado, nodos:", data.nodes.length, "enlaces:", data.links.length);
	cachedGraph = data;
	return cachedGraph;
  }
  

let cachedMoviesData = null;

export async function loadMoviesFullData() {
	if (cachedMoviesData) {
		console.log('Using cached movies data:', cachedMoviesData.length, 'rows');
		return cachedMoviesData;
	}

	const data = await tsv(`${base}/data/title_oscar.tsv`, row => ({
		...row,
		startYear: +row.startYear,
		runtimeMinutes: +row.runtimeMinutes,
		averageRating: +row.averageRating,
		numVotes: +row.numVotes,
		oscarNominations: +row.oscarNominations,
		oscarWins: +row.oscarWins,
		genres: row.genres ? row.genres.split(',') : []
	}));

	console.log('Loaded movies data:', data.length, 'rows');
	cachedMoviesData = data;
	return cachedMoviesData;
}
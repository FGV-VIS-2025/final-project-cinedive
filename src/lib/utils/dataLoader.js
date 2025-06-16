// src/lib/utils/dataloader.js
import { tsv, csv } from 'd3';
import { base } from '$app/paths';

let cachedIMDBMovies = null;
export async function getDataForFitas() {
	if (cachedIMDBMovies) {
		console.log('Using cached movies data#1');
		return cachedIMDBMovies;
	}

	const data = await csv(`${base}/data/world_imdb_movies_top_movies_per_year.csv`, row => ({
      id: row.id,
      title: row.title,
      link: row.link,
      year: +row.year,
      duration: row.duration,
      rating_mpa: row.rating_mpa,
      rating_imdb: +row.rating_imdb,
      vote: +row.vote,
      budget: row.budget,
      gross_world_wide: row.gross_world_wide,
      gross_us_canada: row.gross_us_canada,
      gross_opening_weekend: row.gross_opening_weekend,
      director: row.director,
      writer: row.writer,
      star: row.star,
      genre: row.genre ? row.genre.split(',').map(d => d.trim()) : [],
      country_origin: row.country_origin ? row.country_origin.split(',').map(d => d.trim()) : [],
      filming_location: row.filming_location,
      production_company: row.production_company,
      language: row.language,
      win: +row.win,
      nomination: +row.nomination,
      oscar: +row.oscar,
	}));

	cachedIMDBMovies = data;
	return data;
};


let cachedLastMovies = null;
export async function loadMoviesLastMovies() {
	if (cachedLastMovies) {
		console.log('Using cached movies data');
		return cachedLastMovies;
	}

	const data = await tsv(`${base}/data/title_oscar.tsv`, row => ({
        ...row,
        averageRating: +row.averageRating,
        numVotes: +row.numVotes,
        oscarNominations: +row.oscarNominations,
        oscarWins: +row.oscarWins,
    }));

	cachedLastMovies = data;
	console.log('Loaded movies data from TSV file');
	return cachedLastMovies;
}

let cachedGraph = null;
export async function loadGraph() {
	if (cachedGraph) {
	  console.log('loadGraph(): Using cached graph data');
	  return cachedGraph;
	}
  
	const res = await fetch(`${base}/data/graph_full_cleaned.json`);
	if (!res.ok) {
	  console.error("loadGraph(): graph_full_cleaned.json:", res.status);
	  throw new Error("Graph JSON not found");
	}
	const data = await res.json();
	console.log("loadGraph(): JSON loaded, nodes:", data.nodes.length, "edges:", data.links.length);
	
	cachedGraph = data;
	return cachedGraph;
}

let personData = null;
export async function getPersonGraph(params) {
	if (personData) {
	  console.log('getPersonGraph(): Using cached graph data');
	  return personData;
	}
  
	const res = await fetch(`${base}/data/graphic_person.json`);
	if (!res.ok) {
	  console.error("❌ No se pudo cargar graph_for_project.json:", res.status);
	  throw new Error("Graph JSON not found");
	}
	const data = await res.json();
	console.log("getPersonGraph(): JSON loaded, nodes:", data.nodes.length, "links:", data.links.length);
	
	personData = data;
	return personData;
}

let cachedMoviesData = null;
export async function loadMoviesFullData() {
	if (cachedMoviesData) {
		console.log('Using cached movies data:', cachedMoviesData.length, 'rows');
		return cachedMoviesData;
	}

	const data = await tsv(`${base}/data/title_oscar_con_country.tsv`, row => ({
		...row,
		startYear: +row.startYear,
		runtimeMinutes: +row.runtimeMinutes,
		averageRating: +row.averageRating,
		numVotes: +row.numVotes,
		oscarNominations: +row.oscarNominations,
		oscarWins: +row.oscarWins,
		genres: row.genres ? row.genres.split(',') : [],
		country_origin: row.country_origin ? row.country_origin.split(',').map(d => d.trim()) : []
	}));

	console.log('Loaded movies data:', data.length, 'rows');
	cachedMoviesData = data;
	return cachedMoviesData;
}
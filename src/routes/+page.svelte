<!-- routes/+page.svelte -->
<script>
    import { csv } from 'd3';
    import WorldMap from '$lib/WorldMap.svelte';
    import { base } from '$app/paths';
    import { onMount } from 'svelte';
    import worldGeoJson from '$lib/world.json';
    //console.log('geojson:', worldGeoJson);
    let geojson = worldGeoJson
    let data = null;
    

    onMount(async () => {
    data = await csv(`${base}/data/world_imdb_movies_top_movies_per_year.csv`, row => ({
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
  });

    
</script>

<div>
          {#if data}
            <WorldMap geoData={geojson} {data} />
          {/if}
</div>
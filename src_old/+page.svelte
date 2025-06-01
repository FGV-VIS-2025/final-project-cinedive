<!-- routes/+page.svelte -->
<script>
  // Svelte imports
  import { onMount, afterUpdate } from 'svelte';
  import { max, min } from 'd3';
  // charts
  import HBarChart from '$lib/charts/HBarChart.svelte';
  import BubbleChart from '$lib/charts/BubbleChart.svelte';
  import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
  import FilmDetails from '$lib/charts/FilmDetails.svelte';
  // components
  import Slider from '$lib/components/Slider.svelte';
  import FilmSearch from '$lib/components/FilmSearch.svelte';
  // utils
  import { /*loadMoviesFullData,*/ loadMoviesLastMovies } from '$lib/utils/dataLoader';
  import { processBarChartData } from '$lib/utils/dataManipulation.js';

  let fullData = [];
  let filteredData = [];
  let wins_genres = [], wins_values= [];
  let nominations_genres = [], nominations_values = [];

  let flagSum = false;
  let minYear, maxYear, startYear, endYear;

  // Bubble chart and network chart
  let selectedMovie = null;
  let selectedData = null;

  let searchQuery = '';
  let highlightedMovieId = null;

  // Filtro reativo
  $: filteredData = fullData.filter(
    d => d.startYear >= startYear && d.startYear <= endYear
  );

  function updateBarChart() {
    console.log('Updating bar chart with selected years:', startYear, endYear);

    const result1 = processBarChartData(filteredData, startYear, endYear, 'oscarNominations', flagSum);
    nominations_genres = result1.genres;
    nominations_values = result1.values;

    console.log('Genres nominations:', nominations_genres);
    console.log('Nominations:', nominations_values);

    const result2 = processBarChartData(filteredData, startYear, endYear, 'oscarWins', flagSum);
    wins_genres = result2.genres;
    wins_values = result2.values;

    console.log('Genres nominations:', wins_genres);
    console.log('Nominations:', wins_values);
  }

  onMount(async () => {
    // fullData = await loadMoviesFullData();
    fullData = await loadMoviesLastMovies();

    console.log('Loaded data:', fullData);
    console.log('Number of records:', fullData.length);

    // Initialize slider
    minYear = min(fullData, d => d.startYear);
    maxYear = max(fullData, d => d.startYear);
    startYear = minYear;
    endYear = maxYear;

    updateBarChart();
  });

  function handleMovieSelected(event) {
    highlightedMovieId = null;
    selectedMovie = event.detail.id;
    selectedData = event.detail.data;
    console.log(`Selected Movie ID: ${selectedMovie}`);
  }

  function BackInitialView() {
    console.log('Back to Bubble Chart');
    selectedMovie = null;
    selectedData = null;
  }

  function clearSelection() {
    searchQuery = '';
    highlightedMovieId = null;
  }
</script>

<h1 style="text-align: center; color: #ffd700;">Interactive Movie Explorer</h1>
<h3 style="text-align: center; color: #ffd700;">Datasets: IMDB and Oscar database</h3>

{#if !selectedMovie}
  <main class="home-container">

    <label>
      <input type="checkbox" bind:checked={flagSum} on:change={updateBarChart} />
      Count unique movies
    </label>

    <Slider
      min={minYear}
      max={maxYear}
      start={startYear}
      end={endYear}
      on:rangeChanged={(e) => {
        startYear = e.detail.start;
        endYear = e.detail.end;
        updateBarChart();
      }}
    />

    <!-- Cria os bar charts aqui -->
    {#if nominations_genres.length && wins_genres.length}
      <div class="chart-pair-container">
        <div class="chart-container">
          <HBarChart
            data={nominations_values}
            labels={nominations_genres}
            title="Movies by Genre"
            xLabel="Number of Nominations"
            yLabel="Genre"
          />
        </div>
        <div class="chart-container">
          <HBarChart
            data={wins_values}
            labels={wins_genres}
            title="Movies by Genre"
            xLabel="Number of Wins"
            yLabel="Genre"
          />
        </div>
      </div>
    {:else}
      <p>Loading data or no data available.</p>
    {/if}
  

    <h2>Analysis of movies based on ratings and Oscar awards</h2>

    <div class="bubble-container">
      <div class="search-wrapper">
        <FilmSearch
          options={filteredData.filter(d => d.primaryTitle.toLowerCase().includes(searchQuery.toLowerCase()))}
          bind:query={searchQuery}
          on:select={(e) => {
            console.log(`Selected movie: ${e.detail.id}`);
            highlightedMovieId = e.detail.id;
          }}
        />
        <button class="clear-button" on:click={clearSelection}>
          Clear selection
        </button> 
      </div>

      <div class="bubble-legend">
        <!-- Bubble size legend -->
        <svg width="150" height="150">
          <!-- Large circle -->
          <circle cx="75" cy="75" r="40" fill="none" stroke="#333" />
          <text x="75" y="25" text-anchor="middle" stroke="#fff" font-size="12">
            1000000 votes
          </text>
          <!-- Medium circle -->
          <circle cx="75" cy="75" r="15" fill="none" stroke="#333" />
          <text x="75" y="55" text-anchor="middle" stroke="#fff" font-size="12">
            10000 votes
          </text>
          <!-- Small circle -->
          <circle cx="75" cy="75" r="5" fill="none" stroke="#333" />
          <text x="75" y="95" text-anchor="middle" stroke="#fff" font-size="12">
            1000 votes
          </text>
        </svg>
    
        <!-- Bubble color legend -->
        <div class="bubble-color-legend">
          <p><span class="legend-color has-win"></span> Oscar win</p>
          <p><span class="legend-color no-win"></span> No Oscar win</p>
        </div>
      </div>
      

      <BubbleChart 
        fullData={fullData} 
        data={filteredData} 
        highlightedMovieId={highlightedMovieId}
        on:movieSelected={handleMovieSelected} 
      />
    </div>

    <div class="instructions">
      Click on a bubble to explore the network of related movies.
    </div>
  </main>
{:else}
  <h2>Movies Network</h2>
  <p class="network-explanation" style="text-align: center; margin: 0 auto;">
    This visualization shows how the films (circles) are connected to the people who participated (stars), colored according to their role: directors, screenwriters, or actors. The red one is the one u choose
  </p>
  
  <div class="network-view">
    <figure class="graph-container">
      <FilmNetwork movieId={selectedMovie} on:volver={BackInitialView} />
      <figcaption class="network-legend">
        <h2>Nodes</h2>
        <p><span class="legend-circle"></span> Movie (circle)</p>
        <p><span class="legend-star"></span> Person (star)</p>
        <h2>Edges</h2>
        <p><span class="legend-link" style="background:#1f77b4;"></span> Director</p>
        <p><span class="legend-link" style="background:#2ca02c;"></span> Writer</p>
        <p><span class="legend-link" style="background:#ff6600;"></span> Actor</p>
      </figcaption>
    </figure>

    <figure class="film-details">
      <FilmDetails data={selectedData} />
      <figcaption class="details-label">
        <p>Detailed information about the selected film.</p>
      </figcaption>
    </figure>
  </div>
{/if}


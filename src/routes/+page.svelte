<!-- src/routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import FilmSearch from '$lib/charts/FilmSearch.svelte';
  import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
  import { loadMoviesLastMovies } from '$lib/utils/dataLoader.js';
  import Bubble from '$lib/charts/bubble.svelte';
  import Fita from '$lib/components/Fita.svelte';


  //let current = 0;

  let allMovies = [];
  let searchQuery = '';
  let filteredMovies = [];
  let selectedMovie = null;
  let isLoading = true;
  let error = null;

  // Cuando el usuario decide “ver el grafo completo”, activamos esta bandera
  let showGraphView = false;

  // Objeto con detalles de la película seleccionada (tconst, primaryTitle, startYear)
  $: selectedMovieInfo = selectedMovie
    ? allMovies.find(m => m.tconst === selectedMovie)
    : null;

  let observer;

  onMount(() => {
    const steps = document.querySelectorAll('.step');

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const stepNum = +entry.target.getAttribute('data-step');
            currentStep = stepNum;
          }
        });
      },
      {
        threshold: 0.6
      }
    );

    steps.forEach((step) => observer.observe(step));
  });

  onDestroy(() => {
    if (observer) observer.disconnect();
  });

  let currentStep = 0;

  function onMovieSelect(event) {
    selectedMovie = event.detail;
  }

  function handleBack() {
    showGraphView = false;
    currentStep = 1;
  }
</script>

<svelte:head>
  <title>CineDive – Explore the cinematic connections between Oscar-nominated and winning films</title>
  <meta
    name="description"
    content="Visualize the networks of connections between films and explore the history of cinema interactively."
  />
</svelte:head>

<!-- {#if !showGraphView} -->
  <!-- ========================
       MODO BÚSQUEDA / PASOS
     ======================== -->
  <div class="step-container">
    <!-- Intro Section -->
    <div class="step" data-step="0">
      <section class="intro-section">
        <div class="intro-content">
          <h1>Welcome to CineDive!</h1>
          <p class="intro-text">
            Discover the fascinating connections between films through actors, directors, and collaborators.
            An interactive experience exploring the history of cinema.
          </p>
          <div class="scroll-indicator">
            <span>Scroll to start</span>
            <div class="arrow-down"></div>
          </div>
        </div>
      </section>
    </div>

    <!-- Main Content con scrollama -->



    <!-- Step 1: Búsqueda -->
    <div class="step" data-step="1">
      <div class="step-content">
        <h2>Step 1: Search your Film</h2>
        <p class="step-description">
          Enter at least three letters of a movie title to see suggestions.
          Our database includes thousands of movies and their related titles.
        </p>

        {#if isLoading}
          <div class="loading">
            <div class="spinner"></div>
            <p>Loading movies...</p>
          </div>
        {:else if error}
          <div class="error">
            <p>{error}</p>
            <button class="retry-btn" on:click={() => location.reload()}>
              Try again
            </button>
          </div>
        {:else}
          <div class="search-section">
            <FilmSearch
              bind:query={searchQuery}
              options={filteredMovies}
              on:select={onMovieSelect}
              placeholder="Search movie..."
            />

            {#if selectedMovieInfo}
              <div class="selected-movie">
                <h4>Selected film:</h4>
                <div class="movie-card">
                  <strong>{selectedMovieInfo.primaryTitle}</strong>
                  {#if selectedMovieInfo.startYear}
                    <span class="year">({selectedMovieInfo.startYear})</span>
                  {/if}
                </div>
                <button class="reset-btn" on:click={() => { selectedMovie = null; searchQuery = ''; }}>
                  Change selection
                </button>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>

    <!-- Step 2: Instrucción para pasar al grafo -->
    <div class="step" data-step="2">
      <div class="step-content">
        <h2>Step 2: Explore the connections</h2>
        <p class="step-description">
          Once you've chosen a film, you'll see an option to open the full network graph in a new view.
        </p>
        {#if !selectedMovie}
          <div class="warning-message">
            <p>You must first select a movie in Step 1</p>
              Return to Step 1

          </div>
        {/if}

        {#if selectedMovie}
          <div class="open-graph-note">
            <p>
              You selected <strong>{selectedMovieInfo.primaryTitle}</strong>. 
              Click the button below to view the full network graph.
            </p>
            <button class="view-graph-btn" on:click={() => (showGraphView = true)}>
              View Full Graph
            </button>
          </div>
        {/if}
      </div>
    </div>




    <!-- Step 3: Consejos si aún no hay selección -->
    <div class="step" data-step="3">
      <div class="step-content">
        <h2>Step 3: Analyze the Data</h2>
        <p class="step-description">
          Use the filters and explore different connections. Hover on nodes for details.
        </p>
        {#if !selectedMovie}
          <div class="warning-message">
            <p>⚠️ You must first select a movie in Step 1</p>

          </div>
        {/if}

        {#if selectedMovie}
          <div class="analytics-tips">
            <h4>Exploration Tips:</h4>
            <ul>
              <li>Adjust the year range to see temporal trends</li>
              <li>Filter by genres to find specific patterns</li>
              <li>Use rating and votes filters for quality</li>
              <li>Hover over nodes to see details</li>
            </ul>
          </div>
        {/if}
      </div>
    </div>



    <!-- Gráfico Sticky (en modo scroll) solo muestra preview -->
    <div class="scroll__graphic">
      <div class="graphic-content">
        <!-- Si hay película seleccionada, puede mostrarse un preview muy básico -->
        {#if selectedMovie}
          <div class="network-preview">
            <p>Once ready, click “View Full Graph”</p>
          </div>
        {:else}
          <div class="welcome-graphic">
            <p>Select a movie in Step 1 to see a preview</p>
          </div>
        {/if}
      </div>
    </div>


  </div>
<!-- {:else}
   ========================
       MODO GRAFO COMPLETO
     ======================== 
  <div class="full-graph-container">
    <button class="back-full-btn" on:click={handleBack}>
      ← Back to Search
    </button>
    {#if selectedMovie}
      <FilmNetwork movieId={selectedMovie} />
    {/if}
  </div>
{/if} -->

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* ========================
     ESTILOS MODO BÚSQUEDA
   ======================== */


  /* Intro Section */
  .intro-section {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #b4b4b4 0%, #000000 100%);
    color: rgb(255, 222, 78);
    text-align: center;
    position: relative;
  }

  .intro-content h1 {
    font-size: 3.5rem;
    margin-bottom: 1rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  }

  .intro-text {
    font-size: 1.25rem;
    max-width: 600px;
    margin: 0 auto 3rem;
    line-height: 1.6;
    opacity: 0.95;
  }

  .scroll-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    opacity: 0.8;
  }

  .arrow-down {
    width: 20px;
    height: 20px;
    border-right: 2px solid white;
    border-bottom: 2px solid white;
    transform: rotate(45deg);
    animation: bounce 2s infinite;
  }

  @keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: rotate(45deg) translateY(0); }
    40% { transform: rotate(45deg) translateY(-10px); }
    60% { transform: rotate(45deg) translateY(-5px); }
  }

  /* Layout principal */


  .step {
    margin-bottom: 100vh;
    padding: 2rem 0;
  }

  .step-content h2 {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  .step-description {
    font-size: 1.1rem;
    line-height: 1.6;
    color: #666;
    margin-bottom: 2rem;
  }

  /* Search Section */
  .search-section {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }

  .selected-movie {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #667eea;
  }

  .movie-card {
    margin: 0.5rem 0;
    font-size: 1.1rem;
  }

  .year {
    color: #666;
    font-weight: normal;
  }

  .reset-btn,
  .retry-btn,

  .view-graph-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
    margin-top: 0.5rem;
  }

  .reset-btn:hover,
  .retry-btn:hover,

  .view-graph-btn:hover {
    background: #5a6fd8;
  }

  .warning-message {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
  }

  .warning-message p {
    color: #856404;
    margin: 0 0 1rem 0;
    font-weight: 500;
  }

  /* Spinner y error */
  .loading,
  .error {
    text-align: center;
    padding: 2rem;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Step 2: nota para ver grafo completo */
  .open-graph-note {
    background: #e9f2ff;
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid #cfe0ff;
    margin-top: 1rem;
  }

  .open-graph-note p {
    margin: 0 0 1rem 0;
  }

  /* Sticky Preview (no esencial) */
  .scroll__graphic {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border-left: 1px solid #e0e0e0;
  }

  .graphic-content {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .network-preview,
  .welcome-graphic {
    text-align: center;
    color: #666;
  }

  .step-container {
  scroll-snap-type: y mandatory;
  overflow-y: scroll;
  height: 100vh;
  scroll-behavior: smooth;
}

  .step {
    scroll-snap-align: start;
    min-height: 100vh;
    padding: 2rem;
    box-sizing: border-box;
  }

  /* =========================
     ESTILOS MODO GRAFO COMPLETO
   ========================= */





  /* Ajustamos que FilmNetwork ocupe todo el espacio restante */


  /* ========================
     Estilos compartidos / responsive
   ======================== */
  @media (max-width: 1024px) {

    .scroll__graphic {
      position: relative;
      height: 60vh;
    }
    .step {
      margin-bottom: 50vh;
    }
    .intro-content h1 {
      font-size: 2.5rem;
    }
  }

  @media (max-width: 768px) {

    .step-content h2 {
      font-size: 2rem;
    }
    .intro-content h1 {
      font-size: 2rem;
    }
    .intro-text {
      font-size: 1rem;
      padding: 0 1rem;
    }
    .search-section {
      padding: 1rem;
    }
    .open-graph-note {
      padding: 0.75rem;
    }
  }

  @media (max-width: 480px) {
    .intro-content h1 {
      font-size: 1.5rem;
    }
    .step-content h2 {
      font-size: 1.5rem;
    }
    .step-description {
      font-size: 1rem;
    }

    .step {
      padding: 1rem 0;
    }

  }

  
</style>

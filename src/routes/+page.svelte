<!-- src/routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import FilmSearch from '$lib/charts/FilmSearch.svelte';
  import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
  import { loadMoviesLastMovies, getDataForFitas, loadMoviesFullData } from '$lib/utils/dataLoader.js';
  import Bubble from '$lib/charts/bubble.svelte';
  import Fita from '$lib/components/Fita.svelte';
  import Heatmap from '$lib/charts/heatmap.svelte';
  import WorldMap from '$lib/components/WorldMap.svelte';
  import TopMovies from '../lib/charts/TopMovies.svelte';
  import Relogio from '../lib/charts/relogio.svelte';
  import Elenco from '../lib/charts/Elenco.svelte';
  import { currentStep } from '../store/step';
  import { base } from '$app/paths';


  let current = 0;
  let scroller;
  let handleResize;

  let allMovies = [];
  let searchQuery = '';
  let filteredMovies = [];
  let selectedMovie = null;
  let isLoading = true;
  let error = null;

  let showGraphView = false;

  let worldGeoJson;
  let data_for_fitas;
  let GlobalData;
  let heatmapMode = 'exploration';

  onMount(async () => {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 100) {  // Ajusta el valor según el momento que desees
        showFita = true;
      }
    });

    const res = await fetch(`${base}/mapas/World.json`);
    if (res.ok) {
      worldGeoJson = await res.json();
    } else {
      console.error('Error al cargar world.json:', res.status);
    }

    data_for_fitas = await getDataForFitas();
    console.log("Fitas cargadas:", data_for_fitas);

    GlobalData = await loadMoviesFullData();
    console.log("GlobalData cargada:", GlobalData);
  });

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
            console.log('Step intersecting:', stepNum);
            currentStep.set(stepNum);
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

  // Al montar, cargamos la lista de películas y configuramos scrollama
  onMount(async () => {
    if (!browser) return;

    // Carga de películas para el autocomplete
    try {
      const moviesData = await loadMoviesLastMovies();
      allMovies = moviesData
        .map(m => ({
          tconst: m.tconst,
          primaryTitle: m.primaryTitle,
          startYear: m.startYear ? +m.startYear : null
        }))
        .filter(m => m.primaryTitle && m.primaryTitle.trim() !== '');
      filteredMovies = allMovies;
      isLoading = false;
    } catch (err) {
      console.error('Error loading movies:', err);
      error = 'Failed to load movie data. Please refresh the page.';
      isLoading = false;
    }

    // Import dinámico de scrollama (para el modo búsqueda/pasos)
    
  });

  onDestroy(() => {
    if (scroller && typeof scroller.destroy === 'function') {
      scroller.destroy();
    }
  });

  // Filtrado reactivo del autocomplete
  $: if (searchQuery.trim().length < 2) {
    filteredMovies = allMovies;
  } else {
    const q = searchQuery.toLowerCase().trim();
    filteredMovies = allMovies
      .filter(m => m.primaryTitle.toLowerCase().includes(q))
      .slice(0, 100);
  }

  // Cuando el usuario selecciona un ítem del autocomplete:
  function onMovieSelect(event) {
    selectedMovie = event.detail.id; // tconst de la película elegida
    showGraphView = true;            // cambiar a “modo grafo completo”
  }

  // Resetea todo y vuelve al buscador
  function handleBack() {
    showGraphView = false;
    selectedMovie = null;
    searchQuery = '';
  }

  // Scroll a paso específico (para botón “Return to Step 1”)
  function goToStep(stepIndex) {
    current = stepIndex + 1;
    const stepElement = document.querySelector(`.step[data-step="${stepIndex + 1}"]`);
    if (stepElement) {
      stepElement.scrollIntoView({ behavior: 'smooth' });
    }
  }
</script>

<svelte:head>
  <title>CineDive – Explore the cinematic connections between Oscar-nominated and winning films</title>
  <meta
    name="description"
    content="Visualize the networks of connections between films and explore the history of cinema interactively."
  />
</svelte:head>

{#if !showGraphView}
  <!-- ========================
       MODO BÚSQUEDA / PASOS (Scrollytelling)
     ======================== -->
  <div class="step-container">
    <!-- Intro Section -->
    <!-- <div class= "step", data-step="0"> -->
      <section class="intro-section">
        <div class="intro-content">
          <h1>Welcome to CineDive!</h1>
          <p class="intro-text">
            An interactive journey through cinematic history: discover how Oscar-nominated and winning
            films are interwoven via actors, directors, and collaborators.
          </p>
          <div class="scroll-indicator">
            <span>Scroll to start your exploration</span>
            <div class="arrow-down"></div>
          </div>
        </div>
      </section>
  
    <!-- </div> -->
    
    <!-- Fita decorativa en overlay -->
    <div class="overlay">
      <Fita />
    </div> 

    <!-- Contenido principal con pasos scrollytelling -->

    <!-- ===================================
         Step 1: Search your film
         =================================== -->
    <div class="step" data-step="1">
      <div class="step-content">
        <h2>Step 1: Search your Film</h2>
        <!-- Narración Scrollytelling en inglés -->
        <p class="narrative">
          Imagine traveling back to the set where your favorite movie was shot. Every film starts with a spark
          of inspiration, brings together a team of talented individuals, and leaves a lasting mark on popular
          culture. Use the search bar to find that one film that changed everything for you.
        </p>

        {#if isLoading}
          <div class="loading">
            <div class="spinner"></div>
            <p>Loading movie list...</p>
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
              placeholder="Type at least 2 letters..."
            />

            {#if selectedMovieInfo}
              <div class="selected-movie">
                <h4>You have selected:</h4>
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

    <!-- ===================================
         Step 2: Choose your ribbons
         =================================== -->
    <div class="step" data-step="2">
      <div class="step-content">
        <h2>Step 2: Choose your ribbons</h2>
        <!-- Narración Scrollytelling en inglés -->
        <p class="narrative">
          From Hollywood to Bollywood and beyond, every region in the world has its own cinematic fingerprint.
          Explore the world map and select the “ribbons” that pique your curiosity. This way, you’ll embark on
          a geographic journey tracing cinematic influence across the globe.
        </p>
        <div class="horizontal-layout">
          <div class="map-wrapper">
            {#if worldGeoJson && GlobalData}
              <WorldMap geoData={worldGeoJson} data={GlobalData} />
            {/if}
          </div>
          <div class="step-info">
            <p class="step-description">
              Adjust filters and choose the countries that shaped cinematic trends—from golden age classics
              to modern cult favorites.
            </p>
          </div>
        </div>

        {#if selectedMovie}
          <div class="open-graph-note">
            <p>
              You selected <strong>{selectedMovieInfo.primaryTitle}</strong> in the previous step.
              Now, if you want to dive deeper into all its connections, click below to view the full network graph.
            </p>
            <button class="view-graph-btn" on:click={() => (showGraphView = true)}>
              View Full Graph
            </button>
          </div>
        {/if}
      </div>
    </div>

    <!-- ===================================
         Step 3: Oscar Wins vs Nominations Heatmap
         =================================== -->
    <div class="step" data-step="3">
      <div class="step-content">
        <h2>Step 3: Oscar Wins vs Nominations Heatmap</h2>
        <!-- Narración Scrollytelling en inglés -->
        <p class="narrative">
          Over the decades, the Academy Awards have witnessed countless triumphs. This heatmap lets you
          visualize how nominations and wins correlate: each cell groups films with similar numbers of
          nominations and victories, revealing patterns in cinematic recognition.
        </p>

        <Heatmap
          loadMoviesFullData={loadMoviesLastMovies}
          mode={heatmapMode}
        />

        <!-- Controles para cambiar modo de visualización -->
        <div class="mode-controls" style="margin-top: 1rem;">
          <label>
            <input type="radio" bind:group={heatmapMode} value="exploration" />
            Exploration
          </label>
          <label style="margin-left: 1rem;">
            <input type="radio" bind:group={heatmapMode} value="topWins" />
            Top Wins
          </label>
          <label style="margin-left: 1rem;">
            <input type="radio" bind:group={heatmapMode} value="topNominations" />
            Top Nominations
          </label>
        </div>
      </div>
    </div>

    <!-- ===================================
         Step 4: Oscar Wins vs Nominations Heatmap
         =================================== -->
    <div class="step" data-step="4">
      <div class="step-content">
        <h2>Step 4: Oscar Wins vs Nominations Heatmap</h2>
        <!-- Narración Scrollytelling en inglés -->
        <p class="narrative">
          Over the decades, the Academy Awards have witnessed countless triumphs. This heatmap lets you
          visualize how nominations and wins correlate: each cell groups films with similar numbers of
          nominations and victories, revealing patterns in cinematic recognition.
        </p>
        {#if GlobalData}
          <TopMovies data={GlobalData} />
        {/if}
        

      </div>
    </div>

    <!-- ===================================
         Step 5: Oscar Wins vs Nominations Heatmap
         =================================== -->
    <div class="step" data-step="5">
      <div class="step-content">
        <h2>Step 5: Oscar Wins vs Nominations Heatmap</h2>
        <!-- Narración Scrollytelling en inglés -->
        <p class="narrative">
          Over the decades, the Academy Awards have witnessed countless triumphs. This heatmap lets you
          visualize how nominations and wins correlate: each cell groups films with similar numbers of
          nominations and victories, revealing patterns in cinematic recognition.
        </p>

        {#if GlobalData}
          <Relogio data={GlobalData} width={500} />
        {/if}
      </div>
    </div>

    <!-- ===================================
         Step 6: Oscar Wins vs Nominations Heatmap
         =================================== -->
    <div class="step" data-step="6">
      <div class="step-content">
        <h2>Step 6: Gafico apenas de artistas</h2>
        <!-- Narración Scrollytelling en inglés -->
         <Elenco></Elenco>
        <p class="narrative">
          Over the decades, the Academy Awards have witnessed countless triumphs. This heatmap lets you
          visualize how nominations and wins correlate: each cell groups films with similar numbers of
          nominations and victories, revealing patterns in cinematic recognition.
        </p>
      </div>
    </div>

  </div>

{:else}
  <!-- ========================
       MODO GRAFO COMPLETO
     ======================== -->
  <div class="full-graph-container">
    <button class="back-full-btn" on:click={handleBack}>
      ← Back to Search
    </button>
    {#if selectedMovie}
      <FilmNetwork movieId={selectedMovie} />
    {/if}
  </div>
{/if}

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
    background: #ffffff;
    color: rgb(255, 222, 78);
    text-align: center;
    position: relative;
    z-index: 10; 
    margin-bottom: 80px; 
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
  .step-container {
    scroll-snap-type: y mandatory;
    overflow-y: scroll;
    height: 100vh;
    scroll-behavior: smooth;
  }

  .step {
    scroll-snap-align: start;
    scroll-snap-type: y mandatory;
    overflow-y: scroll;
    height: 100vh; /* cada paso ocupa pantalla completa */
    padding: 2rem 0;
    padding-left: 10rem;
    box-sizing: border-box;
  }

  .step-content h2 {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 1rem;
    font-weight: 600;
    margin-left: 3rem;
  }

  .step-description {
    font-size: 1.1rem;
    line-height: 1.6;
    color: #666;
    margin-bottom: 2rem;
  }

  /* Texto narrativo (scrollytelling) */
  .narrative {
    font-size: 1.15rem;
    line-height: 1.7;
    color: #444;
    margin: 1rem 3rem 2rem 3rem;
    max-width: 800px;
  }

  /* Search Section */
  .search-section {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    margin: 0 3rem;
  }

  .selected-movie {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    margin: 0 3rem;
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
  .back-btn,
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
  .back-btn:hover,
  .view-graph-btn:hover {
    background: #5a6fd8;
  }

  .warning-message {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 3rem;
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
    margin: 0 3rem;
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
    margin: 1rem 3rem;
  }

  .open-graph-note p {
    margin: 0 0 1rem 0;
  }

  /* Diseño horizontal para Step 2 */
  .horizontal-layout {
    display: flex;
    flex-direction: row;
    gap: 2rem;
    margin: 0 3rem;
  }

  .map-wrapper {
    flex: 1;
  }

  .step-info {
    flex: 1;
    display: flex;
    align-items: center;
  }

  /* Controles de modo (Heatmap) */
  .mode-controls label {
    font-size: 1rem;
    color: #333;
  }

  /* =========================
     ESTILOS MODO GRAFO COMPLETO
   ========================= */
  .full-graph-container {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: #fafafa;
  }

  .back-full-btn {
    margin: 1rem;
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    align-self: flex-start;
    transition: background-color 0.2s;
  }

  .back-full-btn:hover {
    background: #5a6fd8;
  }

  /* Ajustamos que FilmNetwork ocupe todo el espacio restante */
  .full-graph-container :global(.network-svg) {
    width: 100%;
    height: calc(100vh - 3rem); /* restamos espacio para el botón “Back” */
    display: block;
  }

  /* ========================
     ESTILOS COMPARTIDOS / Responsive
   ======================== */
  @media (max-width: 1024px) {
    .step {
      margin-bottom: 50vh;
    }
    .intro-content h1 {
      font-size: 2.5rem;
    }
    .narrative {
      margin: 1rem 2rem 2rem 2rem;
      font-size: 1rem;
    }
    .search-section,
    .open-graph-note,
    .horizontal-layout {
      margin: 0 2rem;
    }
  }

  @media (max-width: 768px) {
    .step-content h2 {
      font-size: 2rem;
      margin-left: 15rem;
      padding-left: 15rem;
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
      margin: 0 1rem;
    }
    .open-graph-note {
      padding: 0.75rem;
      margin: 0 1rem;
    }
    .narrative {
      margin: 1rem;
      font-size: 0.95rem;
    }
  }

  @media (max-width: 480px) {
    .intro-content h1 {
      font-size: 1.5rem;
    }
    .step-content h2 {
      font-size: 1.5rem;
      margin-left: 15rem;
      padding-left: 15rem;
    }
    .step-description,
    .narrative {
      font-size: 0.9rem;
    }
    .step {
      padding: 1rem 0;
    }
    .back-full-btn {
      font-size: 0.9rem;
      margin: 0.75rem;
    }
  }

  .overlay {
    position: absolute; 
    top: 0;
    left: 0;
    width: 3px;
    background-color: rgba(0,0,0,0); 
    z-index: 1; 
  }
</style>

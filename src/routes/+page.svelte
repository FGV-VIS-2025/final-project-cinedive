<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import FilmSearch from '$lib/charts/FilmSearch.svelte';
  import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
  import { loadMoviesLastMovies } from '$lib/utils/dataLoader.js';
  import Bubble from '$lib/charts/bubble.svelte';
  import Fita from '../lib/components/Fita.svelte';


  let current = 0;
  let scroller;
  let handleResize;

  let allMovies = [];
  let searchQuery = '';
  let filteredMovies = [];
  let selectedMovie = null;
  let isLoading = true;
  let error = null;

  // Cuando seleccionas película, almacenamos su objeto (tconst + primaryTitle + startYear)
  $: selectedMovieInfo = selectedMovie
    ? allMovies.find(m => m.tconst === selectedMovie)
    : null;

  onMount(async () => {
    if (!browser) return;

    // Import dinámico de scrollama para evitar errores en SSR
    const Scrollama = (await import('scrollama')).default;
    scroller = Scrollama()
      .setup({
        step: '.step',
        container: '.scroll__text',
        graphic: '.scroll__graphic',
        offset: 0.5,
        debug: false
      })
      .onStepEnter(({ index }) => {
        current = index + 1; // index arranca en 0; data-step empieza en 1
      });

    // Manejar resize
    handleResize = () => {
      if (scroller && scroller.resize) {
        scroller.resize();
      }
    };
    window.addEventListener('resize', handleResize);

    // Cargar lista de películas
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

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  });

  onDestroy(() => {
    if (scroller && typeof scroller.destroy === 'function') {
      scroller.destroy();
    }
  });

  // Filtrado reactivo
  $: if (searchQuery.trim().length < 3) {
    filteredMovies = allMovies;
  } else {
    const q = searchQuery.toLowerCase().trim();
    filteredMovies = allMovies
      .filter(m => m.primaryTitle.toLowerCase().includes(q))
      .slice(0, 100);
  }

  function onMovieSelect(event) {
    selectedMovie = event.detail.id;
  }

  function resetSelection() {
    selectedMovie = null;
    searchQuery = '';
  }

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
  <meta name="description" content="Visualize the networks of connections between films and explore the history of cinema interactively." />
</svelte:head>

<div class="scroll-container">
  <!-- Intro Section -->
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

  <!-- Main Content -->
  <div class="scroll-layout">
    <!-- Text Content -->
    <div class="scroll__text">
      <!-- Step 1: Search -->
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
                  <button class="reset-btn" on:click={resetSelection}>
                    Change selection
                  </button>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>

      <!-- Step 2: Network Visualization -->
      <div class="step" data-step="2">
        <div class="step-content">
          <h2>Step 2: Explore the connections</h2>
          <p class="step-description">
            Visualize the network of connections around your selected film.
            Each node represents a film or person, and the lines show their collaborations.
          </p>

          {#if !selectedMovie}
            <div class="warning-message">
              <p>You must first select a movie in Step 1</p>
              <button class="back-btn" on:click={() => goToStep(0)}>
                Return to Step 1
              </button>
            </div>
          {/if}

          <div class="network-info">
            <div class="legend">
              <h4>Legend:</h4>
              <div class="legend-items">
                <div class="legend-item">
                  <div class="legend-symbol movie"></div>
                  <span>Movies</span>
                </div>
                <div class="legend-item">
                  <div class="legend-symbol person"></div>
                  <span>People</span>
                </div>
                <div class="legend-item">
                  <div class="legend-line director"></div>
                  <span>Director</span>
                </div>
                <div class="legend-item">
                  <div class="legend-line actor"></div>
                  <span>Actor</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Analytics -->
      <div class="step" data-step="3">
        <div class="step-content">
          <h2>Step 3: Analyze the data</h2>
          <p class="step-description">
            Use the filters to explore different aspects of the connections.
            The bar chart shows the temporal distribution of the films.
          </p>

          {#if !selectedMovie}
            <div class="warning-message">
              <p>⚠️ You must first select a movie in Step 1</p>
              <button class="back-btn" on:click={() => goToStep(0)}>
                Return to Step 1
              </button>
            </div>
          {/if}

          <div class="analytics-tips">
            <h4>Exploration Tips:</h4>
            <ul>
              <li>Adjust the year range to see temporal trends</li>
              <li>Filter by genres to find specific patterns</li>
              <li>Use rating and votes filters for quality</li>
              <li>Hover over nodes to see details</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Sticky Visualization -->
    <div class="scroll__graphic">
      <div class="graphic-content">
        {#if selectedMovie}
          <!-- Si hay película seleccionada, siempre mostramos la red -->
          <div class="network-container">
            <FilmNetwork movieId={selectedMovie} />
          </div>
        {:else}
          <!-- Si NO hay película, seguimos la lógica de pasos -->
          {#if current === 1}
            <!-- Paso 1: pantalla de bienvenida -->
            <div class="welcome-graphic">
              <div class="network-preview">
                <div class="preview-nodes">
                  <div class="preview-node movie"></div>
                  <div class="preview-node person"></div>
                  <div class="preview-node movie"></div>
                </div>
                <div class="preview-connections">
                  <svg width="200" height="100" viewBox="0 0 200 100">
                    <line x1="40" y1="50" x2="100" y2="30" stroke="#666" stroke-width="2" opacity="0.5"/>
                    <line x1="40" y1="50" x2="100" y2="70" stroke="#666" stroke-width="2" opacity="0.5"/>
                    <line x1="160" y1="50" x2="100" y2="30" stroke="#666" stroke-width="2" opacity="0.5"/>
                    <line x1="160" y1="50" x2="100" y2="70" stroke="#666" stroke-width="2" opacity="0.5"/>
                  </svg>
                </div>
              </div>
              <p>Explore cinematic connections</p>
            </div>
          {:else}
            <!-- Paso 2 o Paso 3 (sin película aún): mensaje para elegir -->
            <div class="no-selection">
              <p>Select a movie in Step 1 to see its network of connections</p>
              <button class="back-to-search" on:click={() => goToStep(0)}>
                Back to Search
              </button>
            </div>
          {/if}
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .scroll-container {
    width: 100%;
  }

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

  /* Main Layout */
  .scroll-layout {
    display: grid;
    grid-template-columns: 45% 55%;
    min-height: 100vh;
  }

  .scroll__text {
    padding: 2rem;
    background: #fafafa;
    overflow-y: auto;
  }

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
  .back-btn,
  .back-to-search {
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
  .back-to-search:hover {
    background: #5a6fd8;
  }

  /* Warning Messages */
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

  /* Loading and Error States */
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

  .error p {
    color: #dc3545;
    font-weight: 500;
  }

  /* Legend */
  .legend {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .legend h4 {
    margin: 0 0 1rem 0;
    color: #333;
  }

  .legend-items {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

  .legend-symbol {
    width: 16px;
    height: 16px;
    border-radius: 50%;
  }

  .legend-symbol.movie {
    background: #69b3a2;
  }

  .legend-symbol.person {
    background: #ffffff;
    border: 2px solid #333;
  }

  .legend-line {
    width: 20px;
    height: 3px;
  }

  .legend-line.director {
    background: #1f77b4;
  }

  .legend-line.actor {
    background: #ff6600;
  }

  /* Analytics Tips */
  .analytics-tips {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .analytics-tips h4 {
    margin: 0 0 1rem 0;
    color: #333;
  }

  .analytics-tips ul {
    margin: 0;
    padding-left: 1.5rem;
  }

  .analytics-tips li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
    color: #555;
  }

  /* Sticky Graphic */
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

  /* Welcome Graphic */
  .welcome-graphic {
    text-align: center;
    color: #666;
  }

  .network-preview {
    margin-bottom: 2rem;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .preview-nodes {
    display: flex;
    justify-content: center;
    gap: 4rem;
    margin-bottom: 1rem;
    position: relative;
    z-index: 2;
  }

  .preview-node {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }

  .preview-node.movie {
    background: #69b3a2;
  }

  .preview-node.person {
    background: white;
    border: 3px solid #333;
  }

  .preview-connections {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.8; }
    50% { transform: scale(1.1); opacity: 1; }
  }

  /* Search Graphic */
  .search-graphic {
    text-align: center;
    width: 100%;
  }

  .selected-preview {
    background: #667eea;
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin: 2rem;
  }

  .movie-highlight {
    font-size: 1.5rem;
    margin: 1rem 0;
  }

  .search-prompt {
    color: #666;
  }

  .search-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  /* Network Container */
  .network-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .no-selection {
    text-align: center;
    color: #666;
    padding: 2rem;
  }

  .back-to-search {
    font-size: 1rem;
    padding: 0.75rem 1.5rem;
    margin-top: 1rem;
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .scroll-layout {
      grid-template-columns: 1fr;
    }
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
    .legend-items {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
  }

  @media (max-width: 768px) {
    .scroll__text {
      padding: 1rem;
    }
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
    .selected-preview {
      margin: 1rem;
      padding: 1.5rem;
    }
    .movie-highlight {
      font-size: 1.2rem;
    }
    .preview-nodes {
      gap: 2rem;
    }
    .preview-node {
      width: 30px;
      height: 30px;
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
    .scroll__text {
      padding: 0.5rem;
    }
    .step {
      padding: 1rem 0;
    }
  }
</style>

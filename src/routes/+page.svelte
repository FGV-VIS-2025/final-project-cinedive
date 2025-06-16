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
  import TopMovies from '$lib/charts/TopMovies.svelte';
  import Relogio from '$lib/charts/relogio.svelte';
  import Elenco from '$lib/charts/Elenco.svelte';
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


  let worldGeoJson;
  let data_for_fitas;
  let GlobalData;
  let heatmapMode = 'exploration';

  onMount(async () => {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 100) {  
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
  }

  // Resetea todo y vuelve al buscador
  function handleBack() {
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
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600&display=swap" rel="stylesheet">
</svelte:head>

<div class="step-container">
  <!-- Fita decorativa en overlay -->
  <div class="overlay">
    <Fita />
  </div> 

  <!-- Step 1 -->
  <div class="step" data-step="1">
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
  </div>

  <!-- Step 2: Search your Film -->
  <div class="step" data-step="2">
    <div class="step-content">
      <h2>Search your Film</h2>
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
              <button class="reset-btn" on:click={handleBack}>
                Change selection
              </button>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>

  <!-- Step 3: Network Graph -->
  <div class="step" data-step="3">
    <div class="step-content">
      <h2>Explore Connections</h2>
      <p class="narrative">
        Now that you've picked a film, let's explore its network. Who were the collaborators? Which directors,
        writers, and actors made it iconic? Dive into the connections that shape cinematic history.
      </p>

      {#if selectedMovie}
        <div class="network-graph-wrapper">
          <h3>
            Network of <span style="color: var(--gold);">{selectedMovieInfo.primaryTitle}</span>
          </h3>
          <FilmNetwork movieId={selectedMovie} />
          <button class="reset-btn" on:click={handleBack}>
            ← Change selection
          </button>
        </div>
      {/if}
    </div>
  </div>

  <!-- Step 4: Map -->
  <div class="step" data-step="4">
    <div class="step-content">
      <h2>Choose your ribbons</h2>
      <p class="narrative">
        From Hollywood to Bollywood and beyond, every region in the world has its own cinematic fingerprint.
        Explore the world map and select the “ribbons” that pique your curiosity.
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
    </div>
  </div>

  <!-- Step 5: Heatmap -->
  <div class="step" data-step="5">
    <div class="step-content">
      <h2>Oscar Wins vs Nominations Heatmap</h2>
      <p class="narrative">
        Over the decades, the Academy Awards have witnessed countless triumphs. This heatmap lets you
        visualize how nominations and wins correlate: each cell groups films with similar numbers of
        nominations and victories, revealing patterns in cinematic recognition.
      </p>
      <Heatmap loadMoviesFullData={loadMoviesFullData} mode={heatmapMode} />
      <div class="mode-controls" style="margin-top: 1rem;">
        <label><input type="radio" bind:group={heatmapMode} value="exploration" /> Exploration</label>
        <label style="margin-left: 1rem;"><input type="radio" bind:group={heatmapMode} value="topWins" /> Top Wins</label>
        <label style="margin-left: 1rem;"><input type="radio" bind:group={heatmapMode} value="topNominations" /> Top Nominations</label>
        <label style="margin-left: 1rem;"><input type="radio" bind:group={heatmapMode} value="diagonal" /> Gold Diagonal</label>
      </div>
    </div>
  </div>

  <!-- Step 6: Timeline -->
  <div class="step" data-step="6">
    <div class="step-content">
      <h2>Oscar Timeline</h2>
      <p class="narrative">
        See how Oscar recognition evolved over time and which decades marked major shifts in cinema.
      </p>
      {#if GlobalData}
        <Relogio data={GlobalData} width={500} />
      {/if}
    </div>
  </div>

    <!-- ===================================
         Step 7: Oscar Wins vs Nominations Heatmap
         =================================== -->
  <div class="step" data-step="7">
    <div class="step-content">
      <h2>Grafico apenas de artistas</h2>
      {#if selectedMovie}
        <Elenco selectedMovieId={selectedMovie} />
      {:else}
        <p>Selecione um filme para ver o grafo de artistas.</p>
      {/if}
      <p class="narrative">
        Over the decades, the Academy Awards have witnessed countless triunfos...
      </p>
    </div>
  </div>
</div>

<style>
  :root {
    --bg: #0a0a0a;
    --bg-light: #1a1a1a;
    --bg-medium: #252525;
    --gold: #d4af37;
    --gold-hover: #f5c842;
    --gold-muted: #b8941e;
    --text: #fdfcf8;
    --muted: #a8a8a8;
    --accent-dark: #333333;
    --border: #404040;
    --shadow: rgba(0, 0, 0, 0.8);
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global(html, body) {
    margin: 0;
    padding: 0;
    font-family: 'Source Sans Pro', sans-serif;
    background: linear-gradient(135deg, var(--bg) 0%, #1a1a1a 100%);
    color: var(--text);
    overflow-x: hidden;
    scroll-behavior: smooth;
  }

  .step[data-step="1"] {
    height: 100vh;
    background: 
      radial-gradient(ellipse at center, rgba(212, 175, 55, 0.1) 0%, transparent 70%),
      linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 50%, #0f0f0f 100%);
    color: var(--gold);
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem;
    position: relative;
    overflow: hidden;
  }
  .step[data-step="2"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 30%, rgba(212, 175, 55, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(212, 175, 55, 0.02) 0%, transparent 50%);
    animation: shimmer 20s ease-in-out infinite;
  }


  .intro-section {
    height: 100vh;
    background: 
      radial-gradient(ellipse at center, rgba(212, 175, 55, 0.1) 0%, transparent 70%),
      linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 50%, #0f0f0f 100%);
    color: var(--gold);
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem;
    position: relative;
    overflow: hidden;
  }

  .intro-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 30%, rgba(212, 175, 55, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(212, 175, 55, 0.02) 0%, transparent 50%);
    animation: shimmer 20s ease-in-out infinite;
  }

  @keyframes shimmer {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  .intro-content {
    position: relative;
    z-index: 2;
  }

  .intro-content h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, var(--gold), var(--gold-hover));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.05em;
    text-shadow: 0 4px 20px rgba(212, 175, 55, 0.3);
  }

  .intro-text {
    font-size: clamp(1.1rem, 2.5vw, 1.3rem);
    max-width: 700px;
    margin: 0 auto;
    color: var(--muted);
    line-height: 1.7;
    font-weight: 300;
  }

  .scroll-indicator {
    margin-top: 4rem;
    color: var(--muted);
    font-size: 0.95rem;
    opacity: 0.8;
  }

  .arrow-down {
    width: 24px;
    height: 24px;
    border-right: 3px solid var(--gold);
    border-bottom: 3px solid var(--gold);
    transform: rotate(45deg);
    animation: bounce 2s infinite ease-in-out;
    margin: 1rem auto 0;
    opacity: 0.7;
  }

  @keyframes bounce {
    0%, 20%, 50%, 80%, 100% { 
      transform: rotate(45deg) translateY(0);
      opacity: 0.7;
    }
    40% { 
      transform: rotate(45deg) translateY(-10px);
      opacity: 1;
    }
    60% { 
      transform: rotate(45deg) translateY(-5px);
      opacity: 0.9;
    }
  }

  .step-container {
    scroll-snap-type: y mandatory;
    height: 100vh;
    overflow-y: scroll;
  }

  .step {
    scroll-snap-align: start;
    min-height: 100vh;
    padding: 4rem clamp(1.5rem, 5vw, 4rem);
    background: 
      linear-gradient(135deg, var(--bg) 0%, var(--bg-light) 100%);
    color: var(--text);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .step::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 10% 20%, rgba(212, 175, 55, 0.01) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(212, 175, 55, 0.01) 0%, transparent 40%);
    pointer-events: none;
  }

  .step-content {
    position: relative;
    z-index: 2;
    max-width: 1200px;
    width: 100%;
  }

  .step-content h2 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 4vw, 2.8rem);
    color: var(--gold);
    margin-bottom: 2rem;
    font-weight: 700;
    position: relative;
    display: inline-block;
  }

  .step-content h2::after {
    content: '';
    position: absolute;
    bottom: -0.5rem;
    left: 0;
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, var(--gold), transparent);
    border-radius: 2px;
  }

  .narrative,
  .step-description {
    font-size: clamp(1rem, 2.2vw, 1.2rem);
    color: var(--muted);
    line-height: 1.8;
    max-width: 800px;
    font-weight: 300;
    margin-bottom: 2rem;
  }

  .search-section,
  .selected-movie,
  .open-graph-note {
    background: 
      linear-gradient(135deg, var(--bg-light) 0%, var(--bg-medium) 100%);
    padding: 2.5rem;
    border-radius: 16px;
    border: 1px solid var(--border);
    margin: 2rem 0;
    box-shadow: 
      0 8px 32px var(--shadow),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: var(--transition);
    backdrop-filter: blur(10px);
  }

  .search-section:hover,
  .selected-movie:hover,
  .open-graph-note:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 12px 40px var(--shadow),
      inset 0 1px 0 rgba(255, 255, 255, 0.08);
    border-color: var(--gold-muted);
  }

  .movie-card {
    font-size: 1.15rem;
    padding: 1rem;
    background: rgba(212, 175, 55, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(212, 175, 55, 0.1);
    margin: 1rem 0;
  }

  .year {
    color: var(--gold-muted);
    font-weight: 400;
  }

  .reset-btn,
  .retry-btn,
  .view-graph-btn,
  .back-full-btn {
    background: linear-gradient(135deg, var(--gold), var(--gold-hover));
    color: #000;
    border: none;
    padding: 0.8rem 1.8rem;
    border-radius: 10px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;
    transition: var(--transition);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    position: relative;
    overflow: hidden;
  }

  .reset-btn::before,
  .retry-btn::before,
  .view-graph-btn::before,
  .back-full-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s;
  }

  .reset-btn:hover,
  .retry-btn:hover,
  .view-graph-btn:hover,
  .back-full-btn:hover {
    background: linear-gradient(135deg, var(--gold-hover), #ffd700);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
  }

  .reset-btn:hover::before,
  .retry-btn:hover::before,
  .view-graph-btn:hover::before,
  .back-full-btn:hover::before {
    left: 100%;
  }

  .loading,
  .error {
    text-align: center;
    margin-top: 2rem;
    color: var(--muted);
    padding: 2rem;
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(212, 175, 55, 0.1);
    border-top: 4px solid var(--gold);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .full-graph-container {
    background: var(--bg);
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .full-graph-container :global(.network-svg) {
    width: 100%;
    height: calc(100vh - 3rem);
    display: block;
  }

  .horizontal-layout {
    display: flex;
    gap: 3rem;
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .map-wrapper,
  .step-info {
    flex: 1;
    min-width: 900;
  }

  .map-wrapper {
    background: var(--bg-light);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid var(--border);
  }

  .mode-controls {
    display: flex;
    gap: 1.5rem;
    margin-top: 2rem;
    flex-wrap: wrap;
  }

  .mode-controls label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: var(--transition);
    background: var(--bg-light);
    border: 1px solid var(--border);
  }

  .mode-controls label:hover {
    background: var(--bg-medium);
    border-color: var(--gold-muted);
  }

  .mode-controls input[type="radio"] {
    accent-color: var(--gold);
  }

  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 4px;
    height: 100vh;
    background: linear-gradient(
      to bottom,
      transparent 0%,
      var(--gold) 20%,
      var(--gold-hover) 50%,
      var(--gold) 80%,
      transparent 100%
    );
    z-index: 1000;
    opacity: 0.6;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .step {
      padding: 2rem 1.5rem;
    }

    .search-section,
    .selected-movie,
    .open-graph-note {
      padding: 1.5rem;
      margin: 1rem 0;
    }

    .horizontal-layout {
      flex-direction: column;
      gap: 1.5rem;
    }

    .mode-controls {
      flex-direction: column;
      gap: 1rem;
    }
  }

  @media (max-width: 480px) {
    .intro-content h1 {
      font-size: 2rem;
    }
    
    .step-content h2 {
      font-size: 1.8rem;
    }
    
    .narrative {
      font-size: 1rem;
    }
  }

  /* Focus states for accessibility */
  .reset-btn:focus,
  .retry-btn:focus,
  .view-graph-btn:focus,
  .back-full-btn:focus {
    outline: 2px solid var(--gold);
    outline-offset: 2px;
  }

  /* Smooth transitions for all interactive elements */
  * {
    transition: var(--transition);
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--bg);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--gold-muted);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--gold);
  }
</style>
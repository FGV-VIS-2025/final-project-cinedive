<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import scrollama from 'scrollama';

  import FilmSearch from '$lib/charts/FilmSearch.svelte';
  import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
  import { loadMoviesLastMovies } from '$lib/utils/dataLoader.js';

  let current = 0;
  let scroller;

  let allMovies = [];
  let searchQuery = '';
  let filteredMovies = [];
  let selectedMovie = null;

  onMount(async () => {
    if (!browser) return;

    scroller = scrollama()
      .setup({ step: '.step', offset: 0.5, debug: false })
      .onStepEnter(({ index }) => (current = index));

    window.addEventListener('resize', scroller.resize);

    try {
      const moviesData = await loadMoviesLastMovies();
      allMovies = moviesData.map(m => ({
        tconst: m.tconst,
        primaryTitle: m.primaryTitle,
        startYear: +m.startYear
      }));
      filteredMovies = allMovies;
    } catch (err) {
      console.error('Error cargando películas:', err);
    }
  });

  onDestroy(() => {
    scroller?.destroy?.();
    if (browser) window.removeEventListener('resize', scroller.resize);
  });

  $: if (searchQuery.trim() === '') {
    filteredMovies = allMovies;
  } else {
    const q = searchQuery.toLowerCase();
    filteredMovies = allMovies.filter(m =>
      m.primaryTitle.toLowerCase().includes(q)
    );
  }

  function onMovieSelect(event) {
    selectedMovie = event.detail.id;
  }
</script>

<div class="scroll">
  <div class="step intro" data-step="0">
    <h1>¡Bienvenidos a CineDive!</h1>
    <p>
      En esta experiencia podrás buscar cualquier película y visualizar su red
      de conexiones junto con un bar‐chart interactivo por año.
    </p>
  </div>

  <div class="scroll__text">
    <div class="step" data-step="1">
      <h1>Step 1: Busca tu película</h1>
      <div class="content-box">
        <p>Escribe al menos tres letras para ver sugerencias.</p>
      </div>
      <div class="search-wrapper">
        <FilmSearch
          bind:query={searchQuery}
          options={filteredMovies}
          on:select={onMovieSelect}
        />
      </div>
    </div>

    <div class="step" data-step="2">
      <h1>Step 2: Explora la red y el bar‐chart por año</h1>
      <div class="content-box split">
        <div class="text">
          <p>
            Aquí ves la red de conexiones (profundidad ≤ 2 saltos) alrededor de la
            película seleccionada. Ajusta el rango de años con el slider para filtrar
            tanto la red como el gráfico.
          </p>
        </div>
      </div>
      <div class="network-wrapper">
        {#if selectedMovie}
          <FilmNetwork movieId={selectedMovie} />
        {:else}
          <p class="placeholder-text">Primero selecciona una película en Step 1.</p>
        {/if}
      </div>
    </div>
  </div>

  <div class="scroll__graphic">
    {#if current === 0}
      <p class="placeholder-text">Step 0: Bienvenida.</p>
    {:else if current === 1}
      {#if selectedMovie}
        <p class="placeholder-text">
          Has seleccionado: {selectedMovie}. Baja para ver la red.
        </p>
      {:else}
        <p class="placeholder-text">Step 1: Busca y elige una película.</p>
      {/if}
    {:else if current === 2}
      {#if selectedMovie}
        <p class="placeholder-text">
          Step 2: Desliza el rango de años en el bar‐chart.
        </p>
      {:else}
        <p class="placeholder-text">Selecciona una película antes.</p>
      {/if}
    {/if}
  </div>
</div>

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
  }

  .scroll {
    display: grid;
    width: 100vw;
    grid-template-columns: 40% 60%;
  }

  .step.intro {
    grid-column: 1 / -1;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: hsl(0, 0%, 15%);
    color: hsl(51, 100%, 79%);
    justify-content: center;
    align-items: center;
    text-align: center;
    margin-bottom: 5vh;
  }

  .scroll__text {
    padding: 2rem;
  }
  .scroll__text .step {
    margin-bottom: 80vh;
  }
  .content-box {
    border: 1px solid #ccc;
    padding: 1rem;
    margin: 1rem 0;
  }
  .content-box.split {
    display: flex;
    gap: 1rem;
  }
  .content-box.split .text {
    width: 100%;
  }

  .search-wrapper {
    margin-top: 1rem;
  }

  .network-wrapper {
    margin-top: 1rem;
    border: 1px solid #ccc;
    padding: 0.5rem;
    min-height: 600px;
  }

  .placeholder-text {
    color: #666;
    font-style: italic;
    text-align: center;
  }

  .scroll__graphic {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    background: #f5f5f5;
  }
</style>

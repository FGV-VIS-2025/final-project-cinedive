<script>
    import { onMount, onDestroy } from 'svelte';
    import { browser } from '$app/environment';
    import scrollama from 'scrollama';
  
    import FilmSearch from '$lib/charts/FilmSearch.svelte';
    import FilmNetwork from '$lib/charts/FilmNetwork.svelte';
    import { loadMoviesFullData } from '$lib/utils/dataLoader.js';
  
    let current = 0;
    let scroller;
  
    // Estado para el buscador
    let allMovies = [];
    let searchQuery = "";
    let filteredMovies = [];
    let selectedMovie = null; // Aquí guardaremos el tconst de la peli elegida
  
    onMount(async () => {
      if (!browser) return;
  
      // Inicializar Scrollama
      scroller = scrollama()
        .setup({ step: '.step', offset: 0.5, debug: false })
        .onStepEnter(({ index }) => (current = index));
      window.addEventListener('resize', scroller.resize);
  
      // Cargar lista de películas completas
      try {
        const moviesData = await loadMoviesFullData();
        allMovies = moviesData.map(m => ({
          tconst:       m.tconst,
          primaryTitle: m.primaryTitle,
          startYear:    m.startYear
        }));
        filteredMovies = allMovies;
      } catch(err) {
        console.error("Error cargando lista de películas:", err);
      }
    });
  
    onDestroy(() => {
      scroller?.destroy?.();
      if (browser) window.removeEventListener('resize', scroller.resize);
    });
  
    // Cada vez que cambie searchQuery, filtramos sugerencias
    $: if (searchQuery.trim() === "") {
      filteredMovies = allMovies;
    } else {
      const q = searchQuery.toLowerCase();
      filteredMovies = allMovies.filter(m =>
        m.primaryTitle.toLowerCase().includes(q)
      );
    }
  
    // Manejador cuando el buscador despacha 'select'
    function onMovieSelect(event) {
      selectedMovie = event.detail.id;
    }
  </script>
  
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
      width: 50%;
    }
  
    /* -----------------------------
       Estilos específicos para Step 1
       contenedor de dos columnas
       ----------------------------- */
    .step-1-container {
      display: flex;
      width: 100%;
      height: calc(100vh - 2rem); /* Ajusta según relleno/márgenes */
      gap: 1rem;
    }
  
    .step-1-left {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 1rem;
    }
  
    .step-1-right {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      /* Aquí es donde irá <FilmNetwork/> */
      background: #ffffff;
      border: 1px solid #ccc;
    }
  
    /* Ajuste opcional para que el buscador se vea bien */
    .search-wrapper {
      margin-top: 1rem;
    }
  
    /* Puedes limitar la altura del grafo si lo deseas */
    .film-network-container {
      width: 100%;
      height: 100%;
    }
  </style>
  
  <div class="scroll">
    <!-- Step Intro ocupa ambas columnas -->
    <div class="step intro">
      <h1>¡Bienvenidos a CineDive!</h1>
      <p>Explora aquí cualquier película y visualiza su red de conexiones.</p>
    </div>
  
    <!-- Columna de pasos -->
    <div class="scroll__text">
      <!-- ----------------------
           Step 1: Buscador + Grafo
           ---------------------- -->
      <div class="step" data-step="0">
        <h1>Step 1: Busca tu película</h1>
  
        <!-- Contenedor de dos columnas -->
        <div class="step-1-container">
          <!-- Columna izquierda: texto explicativo + buscador -->
          <div class="step-1-left">
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
  
          <!-- Columna derecha: aquí ira el grafo -->
          <div class="step-1-right">
            {#if selectedMovie}
              <!-- FilmNetwork muestra subgrafo si hay película seleccionada -->
              <div class="film-network-container">
                <FilmNetwork movieId={selectedMovie} />
              </div>
            {:else}
              <p>Selecciona una película para ver su grafo.</p>
            {/if}
          </div>
        </div>
      </div>
  
      <!-- -----------------------
           Step 2: Explicación texto
           ----------------------- -->
      <div class="step" data-step="1">
        <h1>Step 2: Visualiza la red</h1>
        <div class="content-box split">
          <div class="text">
            <p>En este paso, el grafo mostrará la película seleccionada y sus conexiones hasta dos saltos.</p>
            <p>Puedes arrastrar los nodos y ver detalles en el tooltip.</p>
          </div>
        </div>
      </div>
    </div>
  
    <!-- Columna gráfica (puede quedar vacía porque en Step 1 ya está el grafo) -->
    <div class="scroll__graphic">
      {#if current === 0}
        <!-- Al scrollear hasta Step 1, nada adicional; ya el grafo está “sticky” en la propia sección. -->
        <p style="color: #888;">Step 1: usa el buscador a la izquierda.</p>
      {:else if current === 1}
        <!-- En Step 2, podrías repetir el grafo o mostrar algo distinto -->
        {#if selectedMovie}
          <FilmNetwork movieId={selectedMovie} />
        {:else}
          <p>Primero selecciona una película en Step 1.</p>
        {/if}
      {/if}
    </div>
  </div>
  
<!-- routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { max, min } from 'd3';

  // Importações do seu projeto
  import { loadMoviesLastMovies } from '$lib/utils/dataLoader.js';
  import BubbleChart from '$lib/charts/BubbleChart.svelte';
  import FilmDetails from '$lib/charts/FilmDetails.svelte';
  // Se for usar FilmSearch e Slider, importe-os também:
  // import FilmSearch from '$lib/components/FilmSearch.svelte';
  // import Slider from '$lib/components/Slider.svelte';

  let current = 0;
  let scroller;

  // Estados para os dados e o gráfico de bolhas
  let fullData = [];
  let filteredData = [];
  let minYear, maxYear, startYear, endYear; // Para filtragem, se você reimplementar o Slider
  let highlightedMovieId = null;
  let selectedMovie = null; // Para saber se um filme foi selecionado no BubbleChart
  let selectedData = null; // Dados do filme selecionado

  $: if (browser && fullData.length > 0) {
    if (startYear !== undefined && endYear !== undefined) {
      filteredData = fullData.filter(
        d => d.startYear >= startYear && d.startYear <= endYear
      );
    } else {
      filteredData = fullData;
    }
  }

  onMount(async () => {
    if (!browser) return;

    // Carregar Scrollama
    const { default: scrollama } = await import('scrollama');
    scroller = scrollama()
      .setup({ step: '.step', offset: 0.5, debug: false })
      .onStepEnter(({ index }) => (current = index));
    window.addEventListener('resize', scroller.resize);

    // Carregar dados dos filmes
    try {
      fullData = await loadMoviesLastMovies();
      console.log('Loaded data:', fullData);
      if (fullData.length > 0) {
        minYear = min(fullData, d => d.startYear);
        maxYear = max(fullData, d => d.startYear);
        startYear = minYear; // Define um range inicial, ou remova se não usar Slider
        endYear = maxYear;
        // filteredData será atualizado pela declaração reativa $:
      }
    } catch (error) {
      console.error("Failed to load movie data:", error);
    }
  });

  onDestroy(() => {
    scroller?.destroy?.();
    if (browser) window.removeEventListener('resize', scroller.resize);
  });

  function handleMovieSelected(event) {
    // Esta função será chamada quando um filme for selecionado no BubbleChart
    highlightedMovieId = null;
    selectedMovie = event.detail.id;
    selectedData = event.detail.data;
    console.log(`New Project - Selected Movie ID: ${selectedMovie}`, selectedData);
    if (scroller) scroller.goTo(2); // Supondo que o próximo step seja o índice 2
  }

  // Se for usar FilmSearch
  // let searchQuery = '';
  // function clearSearchSelection() {
  //   searchQuery = '';
  //   highlightedMovieId = null;
  // }
</script>

<div class="scroll">
  <div class="step intro">
    <h1>Welcome to CineDive</h1>
    <p>This is the introduction page before starting the steps.</p>
  </div>

  <div class="scroll__text">  

    <div class="step" data-step="0">
      <h1>Step 1</h1>
      <p>Aqui você pode interagir com o gráfico de bolhas. Clique em uma bolha para ver os detalhes</p>
      <div class="content-box">
        <p>steep1</p>
      </div>
    </div>
    
    <div class="step" data-step="1">
      <h1>Step 2</h1>
      <p>Informações sobre um filme especifico</p>
      <div class="content-box">
        <p>steep2</p>
      </div>
    </div>
    
  </div>

  <div class="scroll__graphic">
    {#if current === 0}
        <p>current 0</p>
    {/if}

    {#if current === 1}
      <p>current 1</p>
      {#if filteredData.length > 0}
        <div class="bubble-chart-container">
          <BubbleChart
            {fullData} 
            data={filteredData}
            {highlightedMovieId}
            on:movieSelected={handleMovieSelected}
          />
        </div>
      {:else}
        <p>Carregando dados do gráfico de bolhas...</p>
      {/if}
    {/if}
    
    {#if current === 2}
      <p>current 2</p>

      {#if selectedMovie && selectedData}
        <FilmDetails data={selectedData} />
      {:else}
         <p>Aguardando seleção de filme...</p>
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
    margin-bottom: 100vh; 
    min-height: 50vh;
  }

  .scroll__graphic {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    flex-direction: column; /* Para empilhar legenda e gráfico se necessário */
    align-items: center;
    justify-content: center;
    background-color: #2c2b2b; /* Cor de fundo para a área do gráfico */
  }

  .content-box {
    border: 1px solid #ccc;
    padding: 1rem;
    margin: 1rem 0;
    background-color: #fff;
  }

  .content-box.split {
    display: flex;
    gap: 1rem;
  }
  .content-box.split .text {
    width: 100%; /* Ajustado para ocupar toda a largura no scroll__text */
  }

  /* Estilos para o BubbleChart e suas legendas (adapte do seu projeto antigo) */
  .bubble-chart-container {
    width: 90%;
    height: 80%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .selected-movie-details-graphic {
    padding: 20px;
    text-align: center;
  }

</style>
<script>
  import { onMount } from 'svelte';
  import scrollama from 'scrollama';

  import BubbleChart from '$lib/charts/BubbleChart.svelte';
  import {loadMoviesLastMovies} from '$lib/utils/dataLoader.js';
  
  // Scrollytelling state
  let currentStep = 0;
  let steps = [
    { id: 1, text: 'INTRODUÇÃO AOS DADOS' },
    { id: 2, text: 'VISUALIZAÇÃO BUBBLE CHART' },
    { id: 3, text: 'FILTROS INTERATIVOS' },
    { id: 4, text: 'ANÁLISE DOS RESULTADOS' }
  ];
  
  let scroller;
  let figureElement;
  let stepElements = [];
  
  // Movie data state
  let fullData = [];
  let filteredData = [];
  let minYear = 1990, maxYear = 2023, startYear = 1990, endYear = 2023;
  let searchQuery = '';
  let highlightedMovieId = null;
  let selectedMovie = null;
  let selectedData = null;
  
  // Control variables for interactivity
  let isInteractionEnabled = false;
  
  onMount(async () => {
    // Initialize movie data
    try {
      fullData = await loadMoviesLastMovies();
      
      if (fullData && fullData.length > 0) {
        minYear = Math.min(...fullData.map(d => d.startYear));
        maxYear = Math.max(...fullData.map(d => d.startYear));
        startYear = minYear;
        endYear = maxYear;
      }
    } catch (error) {
      console.error('Error loading data:', error);
      // Fallback data for testing
      fullData = [];
    }
    
    // Setup scrollytelling with delay to ensure DOM is ready
    setTimeout(() => {
      setupScrollytelling();
    }, 100);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (scroller) scroller.destroy();
    };
  });
  
  function setupScrollytelling() {
    scroller = scrollama();
    
    function handleStepEnter(response) {
      currentStep = response.index;
      
      // Enable interaction on steps 1, 2, and 3 (bubble chart and filters)
      isInteractionEnabled = response.index >= 1 && response.index <= 3;
      
      console.log(`Step ${response.index} entered, interaction enabled: ${isInteractionEnabled}`);
    }
    
    function handleStepExit(response) {
      // You can add logic here if needed when leaving steps
    }
        
    window.addEventListener('resize', handleResize);
    handleResize();
    
    scroller
      .setup({
        step: '.step',
        offset: 0.5, // Changed from 0.33 to 0.5 for better trigger
        debug: false // Set to true for debugging
      })
      .onStepEnter(handleStepEnter)
      .onStepExit(handleStepExit);
  }
  
  function handleResize() {
    const stepH = Math.floor(window.innerHeight * 0.75);
    stepElements.forEach(el => {
      if (el) el.style.height = stepH + 'px';
    });
    
    const figureHeight = window.innerHeight * 0.6; // Reduced height
    const figureMarginTop = (window.innerHeight - figureHeight) / 2;
    
    if (figureElement) {
      figureElement.style.height = figureHeight + 'px';
      figureElement.style.top = figureMarginTop + 'px';
      // Ensure figure is interactive
      figureElement.style.pointerEvents = 'auto';
      figureElement.style.zIndex = '10';
    }
    
    if (scroller) scroller.resize();
  }
  
  // Reactive statements
  $: filteredData = fullData.filter(
    d => d.startYear >= startYear && d.startYear <= endYear
  );
  
  // Event handlers for BubbleChart
  function handleMovieSelected(event) {
    if (!isInteractionEnabled) {
      console.log('Interaction disabled at current step');
      return;
    }
    
    selectedMovie = event.detail.id;
    selectedData = event.detail.data;
    highlightedMovieId = event.detail.id;
    console.log(`Selected Movie ID: ${selectedMovie}`, selectedData);
  }
  
  function clearSelection() {
    if (!isInteractionEnabled) return;
    
    searchQuery = '';
    highlightedMovieId = null;
    selectedMovie = null;
    selectedData = null;
    console.log('Selection cleared');
  }
  
  function updateYearRange(start, end) {
    if (!isInteractionEnabled) return;
    
    startYear = parseInt(start);
    endYear = parseInt(end);
    console.log(`Year range updated: ${startYear} - ${endYear}`);
  }
  
  // Dedicated handlers for range inputs
  function handleStartYearChange(event) {
    if (!isInteractionEnabled) return;
    const newStart = parseInt(event.target.value);
    if (newStart <= endYear) {
      startYear = newStart;
    }
  }
  
  function handleEndYearChange(event) {
    if (!isInteractionEnabled) return;
    const newEnd = parseInt(event.target.value);
    if (newEnd >= startYear) {
      endYear = newEnd;
    }
  }
  
  function handleSearchInput(event) {
    if (!isInteractionEnabled) return;
    searchQuery = event.target.value;
    console.log(`Search query: ${searchQuery}`);
  }
  
  // Filter movies based on search query
  $: searchFilteredData = searchQuery.length > 0 
    ? filteredData.filter(d => d.primaryTitle && d.primaryTitle.toLowerCase().includes(searchQuery.toLowerCase()))
    : filteredData;
  
  // Movie item click handler
  function handleMovieItemClick(movie) {
    if (!isInteractionEnabled) return;
    
    selectedMovie = movie.tconst;
    selectedData = movie;
    highlightedMovieId = movie.tconst;
    console.log('Movie item clicked:', movie.primaryTitle);
  }
</script>

<main>
  <section id="intro">
    <h1 class="intro__hed">Interactive Movie Explorer</h1>
    <p class="intro__dek">
      Explore movie ratings, Oscar wins, and interactive visualizations through scrollytelling.
    </p>
  </section>

  <section id="scrolly">
    <article>
      {#each steps as step, i}
        <div 
          class="step" 
          class:is-active={i === currentStep}
          data-step={step.id}
          bind:this={stepElements[i]}
        >
          <p>{step.text}</p>
          
          {#if i === 1}
            <div class="bubble-instructions">
              <p>🎬 Explore movies through an interactive bubble chart</p>
              <p>💡 Bubble size = Number of votes</p>
              <p>🏆 Gold bubbles = Oscar winners</p>
              <p>🖱️ Click on bubbles to select movies</p>
              <p class="interaction-status">
                {isInteractionEnabled ? '✅ Interaction enabled' : '❌ Scroll to enable interaction'}
              </p>
            </div>
          {/if}
          
          {#if i === 2}
            <div class="controls" class:disabled={!isInteractionEnabled}>
              <!-- <label>
                Year Range: {startYear} - {endYear}
              </label> -->
              <div class="range-inputs">
                <div class="range-container">
                  <label for="start-year">Start Year:</label>
                  <input 
                    id="start-year"
                    type="range" 
                    min={minYear} 
                    max={maxYear} 
                    value={startYear}
                    disabled={!isInteractionEnabled}
                    on:input={handleStartYearChange}
                  />
                  <span>{startYear}</span>
                </div>
                <div class="range-container">
                  <label for="end-year">End Year:</label>
                  <input 
                    id="end-year"
                    type="range" 
                    min={minYear} 
                    max={maxYear} 
                    value={endYear}
                    disabled={!isInteractionEnabled}
                    on:input={handleEndYearChange}
                  />
                  <span>{endYear}</span>
                </div>
              </div>
              
              <input 
                type="text" 
                placeholder="Search movies..." 
                value={searchQuery}
                disabled={!isInteractionEnabled}
                on:input={handleSearchInput}
                class="search-input"
              />
              
              <button 
                on:click={clearSelection} 
                disabled={!isInteractionEnabled}
                class="clear-btn"
              >
                Clear Selection
              </button>
              
              {#if selectedMovie && selectedData}
                <div class="selected-info">
                  <strong>Selected:</strong> {selectedData.primaryTitle}<br>
                  <span>Rating: {selectedData.averageRating} | Oscars: {selectedData.oscarWins || 0}</span>
                </div>
              {/if}
              
              <p class="interaction-status">
                {isInteractionEnabled ? '✅ Controls active' : '❌ Scroll to activate controls'}
              </p>
            </div>
          {/if}
          
          {#if i === 3}
            <div class="analysis-text">
              <p>📊 Analysis of {filteredData.length} movies</p>
              <p>🏆 {filteredData.filter(d => d.oscarWins > 0).length} Oscar winners</p>
              <p>⭐ Average rating: {filteredData.length > 0 ? (filteredData.reduce((sum, d) => sum + d.averageRating, 0) / filteredData.length).toFixed(1) : 'N/A'}</p>
            </div>
          {/if}
        </div>
      {/each}
    </article>

    <figure bind:this={figureElement} class="figure-container">
      {#if currentStep === 0}
        <div class="intro-visual">
          <h2>🎬 Movie Database Explorer</h2>
          <p>Discover insights from IMDb and Oscar data</p>
          <div class="stats-preview">
            <div class="stat-item">
              <div class="stat-number">{fullData.length}</div>
              <div class="stat-label">Movies</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{fullData.filter(d => d.oscarWins > 0).length}</div>
              <div class="stat-label">Oscar Winners</div>
            </div>
          </div>
        </div>
        
      {:else if currentStep === 1}
        <div class="chart-container" class:interactive={isInteractionEnabled}>
          <BubbleChart 
            {fullData} 
            data={filteredData} 
            {highlightedMovieId}
            disabled={!isInteractionEnabled}
            on:movieSelected={handleMovieSelected} 
          />
          {#if !isInteractionEnabled}
            <div class="interaction-overlay">
              <p>Scroll down to enable interaction</p>
            </div>
          {/if}
        </div>
        
      {:else if currentStep === 2}
        <div class="filter-visual">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">{filteredData.length}</div>
              <div class="stat-label">Filtered Movies</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{filteredData.filter(d => d.oscarWins > 0).length}</div>
              <div class="stat-label">Oscar Winners</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{filteredData.length > 0 ? ((filteredData.filter(d => d.oscarWins > 0).length / filteredData.length) * 100).toFixed(1) : 0}%</div>
              <div class="stat-label">Win Rate</div>
            </div>
          </div>
          
          {#if searchQuery}
            <div class="search-results">
              <h4>Search Results for "{searchQuery}":</h4>
              <div class="movie-list">
                {#each searchFilteredData.slice(0, 5) as movie}
                  <div 
                    class="movie-item" 
                    class:selected={movie.tconst === selectedMovie}
                    class:clickable={isInteractionEnabled}
                    on:click={() => handleMovieItemClick(movie)}
                    on:keydown={(e) => e.key === 'Enter' && handleMovieItemClick(movie)}
                    tabindex={isInteractionEnabled ? 0 : -1}
                    role="button"
                  >
                    {movie.primaryTitle} ({movie.startYear}) - ⭐{movie.averageRating}
                    {#if movie.oscarWins > 0}🏆{/if}
                  </div>
                {/each}
                {#if searchFilteredData.length > 5}
                  <div class="more-results">...and {searchFilteredData.length - 5} more</div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
        
      {:else if currentStep === 3}
        <div class="conclusion-visual">
          <div class="analysis-grid">
            <div class="analysis-item">
              <h3>Highest Rated</h3>
              <p>{filteredData.length > 0 ? Math.max(...filteredData.map(d => d.averageRating)).toFixed(1) : 'N/A'}</p>
              <span>IMDb Rating</span>
            </div>
            <div class="analysis-item">
              <h3>Most Popular</h3>
              <p>{filteredData.length > 0 ? (Math.max(...filteredData.map(d => d.numVotes)) / 1000000).toFixed(1) : 0}M</p>
              <span>Votes</span>
            </div>
            <div class="analysis-item">
              <h3>Oscar Champion</h3>
              <p>{filteredData.length > 0 ? Math.max(...filteredData.map(d => d.oscarWins || 0)) : 0}</p>
              <span>Most Wins</span>
            </div>
          </div>
          
          {#if selectedData}
            <div class="selected-movie-details">
              <h4>📽️ Selected Movie</h4>
              <h3>{selectedData.primaryTitle}</h3>
              <div class="movie-stats">
                <span>⭐ {selectedData.averageRating}</span>
                <span>🗳️ {(selectedData.numVotes / 1000).toFixed(0)}K votes</span>
                <span>🏆 {selectedData.oscarWins || 0} wins</span>
                <span>📅 {selectedData.startYear}</span>
              </div>
            </div>
          {/if}
        </div>
        
      {:else}
        <div class="default-visual">
          <p>Step {currentStep + 1}</p>
        </div>
      {/if}
    </figure>
  </section>

  <section id="outro">
    <h2>Continue exploring the data...</h2>
    <p>This interactive visualization helps you discover patterns in movie ratings and Oscar success!</p>
  </section>
</main>

<style>
  /* Add basic styles for visual feedback */
  .controls.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
  
  .figure-container {
    pointer-events: auto !important;
    z-index: 10;
  }
  
  .chart-container.interactive {
    pointer-events: auto;
  }
  
  .interaction-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.2em;
    pointer-events: none;
  }
  
  .movie-item.clickable {
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .movie-item.clickable:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }
  
  .movie-item.selected {
    background-color: rgba(255, 215, 0, 0.3);
    border: 2px solid gold;
  }
  
  .interaction-status {
    font-size: 0.9em;
    font-style: italic;
    margin-top: 10px;
    padding: 5px;
    border-radius: 4px;
    background-color: rgba(0, 0, 0, 0.1);
  }
  
  .range-container {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 5px 0;
  }
  
  .range-container label {
    min-width: 80px;
    font-size: 0.9em;
  }
  
  .range-container span {
    min-width: 40px;
    font-weight: bold;
  }
  
  input[type="range"]:disabled,
  input[type="text"]:disabled,
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a1a;
    color: #fff;
  }

  main {
    position: relative;
  }

  #intro {
    padding: 4rem 2rem;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .intro__hed {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #fff;
  }

  .intro__dek {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    max-width: 600px;
    margin: 0 auto;
  }

  #scrolly {
    position: relative;
    display: flex;
    background: #2a2a2a;
    min-height: 100vh;
  }

  #scrolly > * {
    flex: 1;
  }

  article {
    position: relative;
    padding: 0 2rem;
    max-width: 25rem;
  }

  figure {
    position: sticky;
    width: 100%;
    margin: 0;
    background: #1a1a1a;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    margin: 1rem;
    padding: 2rem;
    overflow: hidden; /* Importante para não vazar conteúdo */
  }

  .step {
    margin: 0 auto 3rem auto;
    background: #3a3a3a;
    color: #fff;
    border-radius: 8px;
    transition: all 0.3s ease;
  }

  .step.is-active {
    background: #ffd700;
    color: #1a1a1a;
    transform: scale(1.02);
  }

  .step p {
    text-align: center;
    padding: 2rem 1rem 1rem;
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0;
  }

  .bubble-instructions {
    padding: 0 1rem 2rem;
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .bubble-instructions p {
    margin: 0.5rem 0;
    padding: 0;
    text-align: left;
    font-size: 0.9rem;
    font-weight: normal;
  }

  .controls {
    padding: 0 1rem 2rem;
  }

  .range-inputs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .controls input[type="range"] {
    flex: 1;
  }

  .search-input {
    width: 100%;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    border: none;
    border-radius: 4px;
    background: #2a2a2a;
    color: #fff;
  }

  .clear-btn {
    background: #ff6b6b;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s;
    width: 100%;
  }

  .clear-btn:hover {
    background: #ff5252;
  }

  .selected-info {
    margin-top: 1rem;
    padding: 0.5rem;
    background: rgba(255, 215, 0, 0.1);
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .analysis-text p {
    margin: 0.5rem 0;
    padding: 0;
    text-align: left;
    font-size: 0.9rem;
    font-weight: normal;
  }

  /* Visual Components */
  .intro-visual {
    text-align: center;
    color: #fff;
    width: 100%;
  }

  .intro-visual h2 {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .stats-preview {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-top: 2rem;
  }

  .stat-item {
    text-align: center;
  }

  .stat-number {
    font-size: 3rem;
    font-weight: 900;
    color: #ffd700;
  }

  .stat-label {
    font-size: 1rem;
    color: #ccc;
    margin-top: 0.5rem;
  }

  .chart-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    max-width: 100%;
    max-height: 100%;
    box-sizing: border-box;
  }

  .filter-visual {
    width: 100%;
    text-align: center;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .search-results {
    background: rgba(255, 215, 0, 0.1);
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
  }

  .search-results h4 {
    margin: 0 0 1rem;
    color: #ffd700;
  }

  .movie-list {
    text-align: left;
  }

  .movie-item {
    padding: 0.5rem;
    margin: 0.25rem 0;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .movie-item.selected {
    background: rgba(255, 215, 0, 0.3);
    color: #1a1a1a;
    font-weight: 600;
  }

  .more-results {
    font-style: italic;
    color: #ccc;
    margin-top: 0.5rem;
  }

  .analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .analysis-item {
    text-align: center;
    background: rgba(255, 215, 0, 0.1);
    padding: 1.5rem;
    border-radius: 8px;
  }

  .analysis-item h3 {
    margin: 0 0 0.5rem;
    color: #ffd700;
    font-size: 1rem;
  }

  .analysis-item p {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
  }

  .analysis-item span {
    font-size: 0.8rem;
    color: #ccc;
  }

  .selected-movie-details {
    background: rgba(255, 215, 0, 0.1);
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
  }

  .selected-movie-details h4 {
    margin: 0 0 0.5rem;
    color: #ffd700;
    font-size: 1rem;
  }

  .selected-movie-details h3 {
    margin: 0 0 1rem;
    font-size: 1.5rem;
  }

  .movie-stats {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .movie-stats span {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.8rem;
  }

  .conclusion-visual, .default-visual {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .default-visual p {
    font-size: 8rem;
    font-weight: 900;
    color: #666;
  }

  #outro {
    height: 50vh;
    background: #1a1a1a;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
  }

  #outro h2 {
    color: #ffd700;
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  #outro p {
    color: #ccc;
    font-size: 1.1rem;
    max-width: 600px;
  }
</style>
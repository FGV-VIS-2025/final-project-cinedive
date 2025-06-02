<!-- src/lib/charts/FilmNetwork.svelte -->
<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';
  import { loadGraph, loadMoviesFullData } from '$lib/utils/dataLoader.js';

  let graphData = null;
  let width = 1200;
  let height = 800;
  let svgElement;
  let tooltipElement;
  let barChartElement;
  let containerElement;

  export let movieId;
  const dispatch = createEventDispatcher();

  let loadedGraph = false;
  let simulation = null;
  let isLoading = true;
  let loadError = null;

  // Estado de filtros
  let filters = {
    minYear: 1900,
    maxYear: 2025,
    startYear: 1900,
    endYear: 2025,
    selectedGenres: new Set(),
    ratingMin: 0,
    votesMin: 0,
    oscarsNomMin: 0,
    oscarsWinMin: 0
  };

  let allGenres = [];
  let currentGraph = { nodes: [], links: [] };
  let resizeObserver = null;

  // Carga inicial
  onMount(async () => {
    await initializeData();
    setupResizeObserver();
  });

  onDestroy(() => {
    cleanupSimulation();
    if (resizeObserver) {
      resizeObserver.disconnect();
    }
  });

  async function initializeData() {
    try {
      isLoading = true;
      const [graph, movies] = await Promise.all([loadGraph(), loadMoviesFullData()]);

      // Combinar metadatos
      const movieMap = new Map(movies.map(m => [m.tconst, m]));
      graph.nodes = graph.nodes.map(node => {
        const extra = movieMap.get(node.id);
        return extra ? { ...node, ...extra } : node;
      });
      graphData = graph;

      // Rango de años
      const movieYears = graph.nodes
        .filter(n => n.type === 'movie' && n.year && !isNaN(+n.year))
        .map(n => +n.year);
      if (movieYears.length) {
        const [minY, maxY] = d3.extent(movieYears);
        filters = { ...filters, minYear: minY, maxYear: maxY, startYear: minY, endYear: maxY };
      }

      // Rango rating/votos/oscars
      const movieNodes = graph.nodes.filter(n => n.type === 'movie');
      if (movieNodes.length) {
        const ratings = movieNodes.map(n => +n.averageRating || 0);
        const votes = movieNodes.map(n => +n.numVotes || 0);
        const noms = movieNodes.map(n => +n.oscarNominations || 0);
        const wins = movieNodes.map(n => +n.oscarWins || 0);

        filters = {
          ...filters,
          ratingMin: Math.floor(d3.min(ratings)),
          votesMin: d3.min(votes),
          oscarsNomMin: d3.min(noms),
          oscarsWinMin: d3.min(wins)
        };
      }

      // Géneros únicos
      const genresSet = new Set();
      movieNodes.forEach(n => {
        if (n.genres && Array.isArray(n.genres)) {
          n.genres.forEach(g => genresSet.add(g));
        }
      });
      allGenres = Array.from(genresSet).sort();

      loadedGraph = true;
      isLoading = false;
      // Si ya hay movieId, dispara la visualización inicial
      if (movieId) {
        updateVisualization();
      }
    } catch (err) {
      console.error('Error loading graph data:', err);
      loadError = 'Failed to load network data. Please try again.';
      isLoading = false;
    }
  }

  function setupResizeObserver() {
    if (!containerElement) return;
    resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width: newWidth } = entry.contentRect;
        if (newWidth > 0 && newWidth !== width) {
          width = Math.max(400, newWidth - 40);
          if (loadedGraph && movieId) {
            updateVisualization();
          }
        }
      }
    });
    resizeObserver.observe(containerElement);
  }

  function cleanupSimulation() {
    if (simulation) {
      simulation.stop();
      simulation = null;
    }
  }

  function buildFilteredSubgraph() {
    const rootNode = graphData.nodes.find(d => d.id === movieId);
    if (!rootNode) {
      console.warn(`Root node not found: ${movieId}`);
      return { nodes: [], links: [] };
    }

    // Filtrar componente completo
    const componentId = rootNode.component;
    const componentNodes = graphData.nodes.filter(d => d.component === componentId);
    const componentIds = new Set(componentNodes.map(d => d.id));

    const componentLinks = graphData.links
      .filter(link => {
        const srcId = typeof link.source === 'object' ? link.source.id : link.source;
        const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
        return componentIds.has(srcId) && componentIds.has(tgtId);
      })
      .map(link => ({
        source: typeof link.source === 'object' ? link.source.id : link.source,
        target: typeof link.target === 'object' ? link.target.id : link.target,
        weight: link.weight || 1,
        roles: link.roles || []
      }));

    // Construir adyacencia
    const adjacency = new Map();
    componentNodes.forEach(n => adjacency.set(n.id, []));
    componentLinks.forEach(link => {
      if (adjacency.has(link.source) && adjacency.has(link.target)) {
        adjacency.get(link.source).push(link.target);
        adjacency.get(link.target).push(link.source);
      }
    });

    // BFS a 2 saltos
    const subgraphIds = new Set([movieId]);
    const queue = [{ id: movieId, depth: 0 }];
    while (queue.length > 0) {
      const { id: curr, depth } = queue.shift();
      if (depth >= 2) continue;
      (adjacency.get(curr) || []).forEach(neighborId => {
        if (!subgraphIds.has(neighborId)) {
          subgraphIds.add(neighborId);
          queue.push({ id: neighborId, depth: depth + 1 });
        }
      });
    }

    // Subgrafo inicial
    let subNodes = graphData.nodes.filter(d => subgraphIds.has(d.id));
    let subLinks = componentLinks.filter(link =>
      subgraphIds.has(link.source) && subgraphIds.has(link.target)
    );

    // Filtrar películas que pasan los criterios
    const filteredMovieIds = new Set(
      subNodes
        .filter(n => n.type === 'movie')
        .filter(n => passesFilters(n))
        .map(n => n.id)
    );

    // Filtrar enlaces según películas válidas y conexiones persona–película
    const validLinks = subLinks.filter(link => {
      const srcNode = subNodes.find(n => n.id === link.source);
      const tgtNode = subNodes.find(n => n.id === link.target);
      if (!srcNode || !tgtNode) return false;

      const srcIsMovie = srcNode.type === 'movie';
      const tgtIsMovie = tgtNode.type === 'movie';

      if (srcIsMovie && tgtIsMovie) {
        return filteredMovieIds.has(link.source) && filteredMovieIds.has(link.target);
      }
      if (srcIsMovie) return filteredMovieIds.has(link.source);
      if (tgtIsMovie) return filteredMovieIds.has(link.target);
      return false;
    });

    // Nodos finales
    const finalIds = new Set();
    validLinks.forEach(link => {
      finalIds.add(link.source);
      finalIds.add(link.target);
    });
    const finalNodes = subNodes.filter(n => finalIds.has(n.id));

    return { nodes: finalNodes, links: validLinks };
  }

  function passesFilters(node) {
    const year = node.year ? +node.year : null;
    if (year !== null && (year < filters.startYear || year > filters.endYear)) {
      return false;
    }

    if (filters.selectedGenres.size > 0) {
      if (!node.genres || !Array.isArray(node.genres)) return false;
      const hasGenre = node.genres.some(g => filters.selectedGenres.has(g));
      if (!hasGenre) return false;
    }

    const rating = node.averageRating ? +node.averageRating : 0;
    const votes = node.numVotes ? +node.numVotes : 0;
    const oscarNom = node.oscarNominations ? +node.oscarNominations : 0;
    const oscarWin = node.oscarWins ? +node.oscarWins : 0;

    return (
      rating >= filters.ratingMin &&
      votes >= filters.votesMin &&
      oscarNom >= filters.oscarsNomMin &&
      oscarWin >= filters.oscarsWinMin
    );
  }

  // Dibuja el grafo
  function drawGraph(graph) {
    if (!svgElement || !graph.nodes.length) return;
    cleanupSimulation();

    const svg = d3.select(svgElement);
    svg.selectAll('*').remove();
    svg.attr('width', width)
       .attr('height', height)
       .attr('viewBox', `0 0 ${width} ${height}`);

    const ratings = graph.nodes
      .filter(d => d.averageRating && !isNaN(+d.averageRating))
      .map(d => +d.averageRating);

    const sizeScale = d3.scaleLinear()
      .domain(ratings.length ? d3.extent(ratings) : [0, 10])
      .range([6, 20]);

    const oscarColor = d3.scaleOrdinal()
      .domain([false, true])
      .range(['#69b3a2', '#ffd700']);

    simulation = d3.forceSimulation(graph.nodes)
      .force('link', d3.forceLink(graph.links)
        .id(d => d.id)
        .distance(d => {
          const srcNode = graph.nodes.find(n => n.id === d.source.id || n.id === d.source);
          const tgtNode = graph.nodes.find(n => n.id === d.target.id || n.id === d.target);
          return (srcNode?.type === 'movie' && tgtNode?.type === 'movie') ? 150 : 80;
        }))
      .force('charge', d3.forceManyBody().strength(d =>
        d.type === 'movie' ? -400 : -200
      ))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => {
        const rating = d.averageRating ? +d.averageRating : 5;
        return sizeScale(rating) + 5;
      }));

    const getRoleColor = roles => {
      if (!Array.isArray(roles) || roles.length === 0) return '#999999';
      const str = roles.join(' ').toLowerCase();
      if (str.includes('director')) return '#1f77b4';
      if (str.includes('writer')) return '#2ca02c';
      if (str.includes('actor') || str.includes('actress')) return '#ff7f0e';
      return '#999999';
    };

    // Dibujar enlaces
    const linkGroup = svg.append('g').attr('class', 'links');
    const links = linkGroup.selectAll('line')
      .data(graph.links)
      .join('line')
      .attr('stroke', d => getRoleColor(d.roles))
      .attr('stroke-width', d => Math.sqrt(d.weight || 1) * 2)
      .attr('stroke-opacity', 0.6);

    // Dibujar nodos
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    const nodes = nodeGroup.selectAll('g')
      .data(graph.nodes)
      .join('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    nodes.append('path')
      .attr('d', d => {
        const rating = d.averageRating ? +d.averageRating : 5;
        const size = sizeScale(rating);
        const symbolType = d.type === 'person' ? d3.symbolStar : d3.symbolCircle;
        return d3.symbol().type(symbolType).size(size * size * Math.PI)();
      })
      .attr('fill', d => {
        if (d.type === 'person') return '#ffffff';
        return oscarColor(d.oscarWins && +d.oscarWins > 0);
      })
      .attr('stroke', d => d.id === movieId ? '#ff0000' : d.type === 'person' ? '#333333' : '#666666')
      .attr('stroke-width', d => d.id === movieId ? 3 : 1);

    nodes.filter(d => d.id === movieId || (d.type === 'movie' && d.oscarWins && +d.oscarWins > 0))
      .append('text')
      .text(d => {
        const title = d.title || d.primaryTitle || d.id;
        return title.length > 15 ? title.substring(0, 15) + '...' : title;
      })
      .attr('text-anchor', 'middle')
      .attr('dy', d => {
        const rating = d.averageRating ? +d.averageRating : 5;
        return sizeScale(rating) + 15;
      })
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .attr('font-weight', d => d.id === movieId ? 'bold' : 'normal');

    const tooltip = d3.select(tooltipElement);
    nodes
      .on('mouseover', (event, d) => {
        let content;
        if (d.type === 'person') {
          content = `
            <div class="tooltip-title">Person</div>
            <div>ID: ${d.id}</div>
          `;
        } else {
          const title = d.title || d.primaryTitle || 'Unknown Title';
          const year = d.year || 'N/A';
          const rating = d.averageRating ? (+d.averageRating).toFixed(1) : 'N/A';
          const votes = d.numVotes ? (+d.numVotes).toLocaleString() : 'N/A';
          const genres = d.genres && Array.isArray(d.genres) ? d.genres.join(', ') : 'N/A';
          const oscarNom = d.oscarNominations || 0;
          const oscarWin = d.oscarWins || 0;

          content = `
            <div class="tooltip-title">${title}</div>
            <div>Year: ${year}</div>
            <div>Rating: ${rating}</div>
            <div>Votes: ${votes}</div>
            <div>Genres: ${genres}</div>
            <div>Oscar Nominations: ${oscarNom}</div>
            <div>Oscar Wins: ${oscarWin}</div>
          `;
        }

        tooltip
          .style('display', 'block')
          .html(content)
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 10}px`);
      })
      .on('mouseout', () => {
        tooltip.style('display', 'none');
      })
      .on('click', (event, d) => {
        if (d.type === 'movie' && d.id !== movieId) {
          dispatch('movieSelect', { movieId: d.id });
        }
      });

    simulation.on('tick', () => {
      graph.nodes.forEach(d => {
        const rating = d.averageRating ? +d.averageRating : 5;
        const radius = sizeScale(rating);
        d.x = Math.max(radius, Math.min(width - radius, d.x));
        d.y = Math.max(radius, Math.min(height - radius, d.y));
      });

      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  // Dibuja bar chart
  function drawBarChart(nodes) {
    if (!barChartElement) return;

    const svg = d3.select(barChartElement);
    svg.selectAll('*').remove();

    const movies = nodes
      .filter(n => n.type === 'movie' && n.year && !isNaN(+n.year))
      .map(n => ({ ...n, year: +n.year }));

    if (!movies.length) return;

    const margin = { top: 20, right: 20, bottom: 60, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = 200 - margin.top - margin.bottom;

    const yearCounts = d3.rollup(movies, v => v.length, d => d.year);
    const yearRange = d3.range(filters.startYear, filters.endYear + 1);
    const data = yearRange.map(year => ({
      year,
      count: yearCounts.get(year) || 0
    })).filter(d => d.count > 0);

    if (!data.length) return;

    const xScale = d3.scaleBand()
      .domain(data.map(d => d.year))
      .range([0, chartWidth])
      .padding(0.1);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.count)])
      .range([chartHeight, 0]);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Barras
    g.selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => xScale(d.year))
      .attr('y', d => yScale(d.count))
      .attr('width', xScale.bandwidth())
      .attr('height', d => chartHeight - yScale(d.count))
      .attr('fill', '#69b3a2')
      .attr('rx', 2);

    // Eje X
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.format('d')))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-0.8em')
      .attr('dy', '0.15em')
      .attr('transform', 'rotate(-45)');

    // Eje Y
    g.append('g')
      .call(d3.axisLeft(yScale));

    // Labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (chartHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Number of Movies');

    g.append('text')
      .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Year');
  }

  function handleGenreChange(event) {
    filters.selectedGenres = new Set(
      Array.from(event.target.selectedOptions).map(opt => opt.value)
    );
    // Reasignar para disparar reactividad
    filters = { ...filters };
  }

  function resetFilters() {
    filters = {
      ...filters,
      startYear: filters.minYear,
      endYear: filters.maxYear,
      selectedGenres: new Set(),
      ratingMin: filters.minYear === filters.minYear ? filters.ratingMin : 0,  // conservamos rango
      votesMin: filters.votesMin,
      oscarsNomMin: filters.oscarsNomMin,
      oscarsWinMin: filters.oscarsWinMin
    };
    // Como reasignamos todo el objeto, la reactividad se disparará automáticamente
  }

  function goBack() {
    dispatch('back');
  }

  // Único bloque reactivo que escucha a movieId, loadedGraph y cada propiedad relevante de filters
  $: if (
    loadedGraph &&
    movieId &&
    filters.startYear !== undefined &&
    filters.endYear !== undefined &&
    filters.ratingMin !== undefined &&
    filters.votesMin !== undefined &&
    filters.oscarsNomMin !== undefined &&
    filters.oscarsWinMin !== undefined
  ) {
    updateVisualization();
  }

  function updateVisualization() {
    if (!graphData || !movieId) return;
    const subgraph = buildFilteredSubgraph();
    currentGraph = subgraph;
    drawGraph(subgraph);
    drawBarChart(subgraph.nodes);
  }
</script>

<div class="film-network-container" bind:this={containerElement}>
  {#if isLoading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading network data...</p>
    </div>
  {:else if loadError}
    <div class="error-state">
      <p>⚠️ {loadError}</p>
      <button on:click={() => window.location.reload()}>Retry</button>
    </div>
  {:else}
    <!-- Controls -->
    <div class="controls-panel">
      <div class="control-row">
        <button class="back-btn" on:click={goBack}>
          ← Back to Search
        </button>
        <button class="reset-btn" on:click={resetFilters}>
          Reset Filters
        </button>
      </div>

      <!-- Year Range Slider -->
      <div class="year-filter">
        <label>Years: {filters.startYear} – {filters.endYear}</label>
        <div class="range-slider">
          <input
            type="range"
            min={filters.minYear}
            max={filters.maxYear}
            bind:value={filters.startYear}
            class="slider slider-start"
            on:input={() => {
              if (filters.startYear > filters.endYear) {
                filters.startYear = filters.endYear;
              }
              filters = { ...filters }; // reasignar para disparar reactividad
            }}
          />
          <input
            type="range"
            min={filters.minYear}
            max={filters.maxYear}
            bind:value={filters.endYear}
            class="slider slider-end"
            on:input={() => {
              if (filters.endYear < filters.startYear) {
                filters.endYear = filters.startYear;
              }
              filters = { ...filters }; // reasignar para disparar reactividad
            }}
          />
        </div>
        <small>[{filters.minYear} – {filters.maxYear}]</small>
      </div>

      <!-- Other Filters -->
      <div class="filters-grid">
        <div class="filter-group">
          <label>Min Rating:</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            bind:value={filters.ratingMin}
            on:input={() => { filters = { ...filters }; }}
          />
        </div>
        <div class="filter-group">
          <label>Min Votes:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.votesMin}
            on:input={() => { filters = { ...filters }; }}
          />
        </div>
        <div class="filter-group">
          <label>Min Oscar Nominations:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsNomMin}
            on:input={() => { filters = { ...filters }; }}
          />
        </div>
        <div class="filter-group">
          <label>Min Oscar Wins:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsWinMin}
            on:input={() => { filters = { ...filters }; }}
          />
        </div>
        <div class="filter-group genre-filter">
          <label>Genres:</label>
          <select multiple size="4" on:change={handleGenreChange}>
            {#each allGenres as genre}
              <option value={genre}>{genre}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- Network Visualization -->
    <div class="network-section">
      <div class="network-header">
        <h3>Network Graph</h3>
        <div class="network-stats">
          Showing {currentGraph.nodes.length} nodes, {currentGraph.links.length} connections
        </div>
      </div>
      <div class="graph-container">
        <svg bind:this={svgElement} class="network-svg"></svg>
        <div bind:this={tooltipElement} class="tooltip"></div>
      </div>
    </div>

    <!-- Bar Chart -->
    <div class="chart-section">
      <h3>Movies Distribution by Year</h3>
      <svg bind:this={barChartElement} class="bar-chart" width={width} height="200"></svg>
    </div>
  {/if}
</div>

<style>
  .film-network-container {
    padding: 1rem;
    max-width: 100%;
  }

  /* Loading and Error States */
  .loading-state, .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #69b3a2;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error-state button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  /* Controls */
  .controls-panel {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #dee2e6;
  }

  .control-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .back-btn, .reset-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
  }

  .back-btn {
    background: #6c757d;
    color: white;
  }

  .back-btn:hover {
    background: #5a6268;
  }

  .reset-btn {
    background: #17a2b8;
    color: white;
  }

  .reset-btn:hover {
    background: #138496;
  }

  /* Year Filter */
  .year-filter {
    margin-bottom: 1rem;
  }

  .year-filter label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .range-slider {
    position: relative;
    height: 30px;
    width: 100%;
    max-width: 400px;
  }

  .slider {
    position: absolute;
    width: 100%;
    height: 6px;
    background: transparent;
    outline: none;
    -webkit-appearance: none;
    pointer-events: all;
  }

  .slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #69b3a2;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  .slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #69b3a2;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  .slider::-webkit-slider-runnable-track {
    height: 6px;
    background: #ddd;
    border-radius: 3px;
  }

  .slider::-moz-range-track {
    height: 6px;
    background: #ddd;
    border-radius: 3px;
    border: none;
  }

  .slider-start::-webkit-slider-thumb {
    z-index: 2;
  }

  .slider-end::-webkit-slider-thumb {
    z-index: 1;
  }

  /* Filters Grid */
  .filters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    align-items: start;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .filter-group label {
    font-size: 0.9rem;
    font-weight: 500;
    color: #495057;
  }

  .filter-group input {
    padding: 0.375rem 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .filter-group input:focus {
    outline: none;
    border-color: #69b3a2;
    box-shadow: 0 0 0 2px rgba(105, 179, 162, 0.25);
  }

  .genre-filter select {
    padding: 0.375rem 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 0.9rem;
    min-height: 80px;
  }

  .genre-filter select:focus {
    outline: none;
    border-color: #69b3a2;
    box-shadow: 0 0 0 2px rgba(105, 179, 162, 0.25);
  }

  /* Network Section */
  .network-section {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .network-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #dee2e6;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .network-header h3 {
    margin: 0;
    color: #495057;
    font-size: 1.25rem;
  }

  .network-stats {
    font-size: 0.9rem;
    color: #6c757d;
    background: #f8f9fa;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
  }

  .graph-container {
    position: relative;
    width: 100%;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background: #fafafa;
    overflow: hidden;
  }

  .network-svg {
    display: block;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  }

  /* Chart Section */
  .chart-section {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .chart-section h3 {
    margin: 0 0 1rem 0;
    color: #495057;
    font-size: 1.25rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #dee2e6;
  }

  .bar-chart {
    display: block;
    background: #fafafa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
  }

  /* Tooltip */
  .tooltip {
    position: absolute;
    display: none;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.8rem;
    line-height: 1.4;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    pointer-events: none;
    z-index: 1000;
    max-width: 250px;
  }

  .tooltip-title {
    font-weight: bold;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    color: #69b3a2;
    border-bottom: 1px solid #69b3a2;
    padding-bottom: 0.25rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .film-network-container {
      padding: 0.5rem;
    }

    .controls-panel {
      padding: 0.75rem;
    }

    .filters-grid {
      grid-template-columns: 1fr;
      gap: 0.75rem;
    }

    .control-row {
      flex-direction: column;
      gap: 0.5rem;
    }

    .network-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .network-stats {
      align-self: stretch;
      text-align: center;
    }

    .range-slider {
      max-width: 100%;
    }
  }

  @media (max-width: 480px) {
    .film-network-container {
      padding: 0.25rem;
    }

    .network-section,
    .chart-section,
    .controls-panel {
      border-radius: 4px;
      padding: 0.5rem;
    }

    .network-header h3,
    .chart-section h3 {
      font-size: 1.1rem;
    }

    .tooltip {
      max-width: 200px;
      font-size: 0.75rem;
    }
  }

  /* Node hover */
  :global(.node) {
    cursor: pointer;
    transition: opacity 0.2s ease;
  }

  :global(.node:hover) {
    opacity: 0.8;
  }

  :global(.links line) {
    transition: stroke-opacity 0.2s ease;
  }

  :global(.links line:hover) {
    stroke-opacity: 1 !important;
  }

  /* Fade-in animations */
  .loading-state {
    animation: fadeIn 0.3s ease-in;
  }

  .error-state {
    animation: fadeIn 0.3s ease-in;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Focus outlines */
  .back-btn:focus,
  .reset-btn:focus {
    outline: 2px solid #69b3a2;
    outline-offset: 2px;
  }

  .slider:focus {
    outline: 2px solid #69b3a2;
    outline-offset: 2px;
  }

  /* Custom scrollbar for genre select */
  .genre-filter select::-webkit-scrollbar {
    width: 6px;
  }

  .genre-filter select::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }

  .genre-filter select::-webkit-scrollbar-thumb {
    background: #69b3a2;
    border-radius: 3px;
  }

  .genre-filter select::-webkit-scrollbar-thumb:hover {
    background: #5a9d8a;
  }
</style>

<!-- src/lib/charts/FilmNetwork.svelte -->
<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';
  import { loadGraph, loadMoviesFullData } from '$lib/utils/dataLoader.js';

  let graphData = null;
  let width = 800;
  let height = 600;
  let svgElement;
  let tooltipElement;
  let barChartElement;
  let containerElement;
  let graphContainerElement;

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
    ratingMax: 10,
    votesMin: 0,
    oscarsNomMin: 0,
    oscarsWinMin: 0
  };

  let allGenres = [];
  let currentGraph = { nodes: [], links: [] };
  let resizeObserver = null;

  // Variables para controlar el tamaño consistente de nodos
  let globalSizeScale = null;

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

      // Unimos la información de movies con cada nodo del grafo
      const movieMap = new Map(movies.map(m => [m.tconst, m]));
      graph.nodes = graph.nodes.map(node => {
        const extra = movieMap.get(node.id);
        return extra ? { ...node, ...extra } : node;
      });
      graphData = graph;

      // Determinamos rangos de años basados en nodos de tipo "movie"
      const movieYears = graph.nodes
        .filter(n => n.type === 'movie' && n.year && !isNaN(+n.year))
        .map(n => +n.year);
      if (movieYears.length) {
        const [minY, maxY] = d3.extent(movieYears);
        filters = { ...filters, minYear: minY, maxYear: maxY, startYear: minY, endYear: maxY };
      }

      // Determinamos rangos para todos los filtros
      const movieNodes = graph.nodes.filter(n => n.type === 'movie');
      if (movieNodes.length) {
        const ratings = movieNodes.map(n => +n.averageRating || 0);
        const votes = movieNodes.map(n => +n.numVotes || 0);
        const noms = movieNodes.map(n => +n.oscarNominations || 0);
        const wins = movieNodes.map(n => +n.oscarWins || 0);

        filters = {
          ...filters,
          ratingMin: Math.floor(d3.min(ratings)),
          ratingMax: Math.ceil(d3.max(ratings)),
          votesMin: d3.min(votes),
          oscarsNomMin: d3.min(noms),
          oscarsWinMin: d3.min(wins)
        };
      }

      // Extraemos lista única de géneros
      const genresSet = new Set();
      movieNodes.forEach(n => {
        if (n.genres && Array.isArray(n.genres)) {
          n.genres.forEach(g => genresSet.add(g));
        }
      });
      allGenres = Array.from(genresSet).sort();

      // Creamos escala de tamaño global consistente
      const allRatings = movieNodes
        .filter(n => n.averageRating && !isNaN(+n.averageRating))
        .map(n => +n.averageRating);
      
      globalSizeScale = d3
        .scaleLinear()
        .domain(allRatings.length ? d3.extent(allRatings) : [0, 10])
        .range([8, 24]);

      loadedGraph = true;
      isLoading = false;

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
    if (!graphContainerElement) return;
    resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width: newWidth, height: newHeight } = entry.contentRect;
        if (newWidth > 0 && newHeight > 0) {
          width = Math.max(400, newWidth - 20);
          height = Math.max(300, newHeight - 20);
          if (loadedGraph && movieId) {
            updateVisualization();
          }
        }
      }
    });
    resizeObserver.observe(graphContainerElement);
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

    // Construir lista de adyacencia
    const adjacency = new Map();
    componentNodes.forEach(n => adjacency.set(n.id, []));
    componentLinks.forEach(link => {
      if (adjacency.has(link.source) && adjacency.has(link.target)) {
        adjacency.get(link.source).push(link.target);
        adjacency.get(link.target).push(link.source);
      }
    });

    // BFS a 2 saltos desde movieId
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

    let subNodes = graphData.nodes.filter(d => subgraphIds.has(d.id));
    let subLinks = componentLinks.filter(link =>
      subgraphIds.has(link.source) && subgraphIds.has(link.target)
    );

    // Filtrar películas - EXCEPTO el nodo de origen
    const filteredMovieIds = new Set(
      subNodes
        .filter(n => n.type === 'movie')
        .filter(n => n.id === movieId || passesFilters(n)) // Siempre incluir el nodo de origen
        .map(n => n.id)
    );

    // Filtrar enlaces válidos
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

    // Nodos finales conectados
    const finalIds = new Set();
    validLinks.forEach(link => {
      finalIds.add(link.source);
      finalIds.add(link.target);
    });
    
    // Asegurar que el nodo de origen siempre esté incluido
    finalIds.add(movieId);
    
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
      rating <= filters.ratingMax &&
      votes >= filters.votesMin &&
      oscarNom >= filters.oscarsNomMin &&
      oscarWin >= filters.oscarsWinMin
    );
  }

  function getEffectiveRadius(d) {
    const rating = d.averageRating ? +d.averageRating : 5;
    const baseRadius = globalSizeScale ? globalSizeScale(rating) : 12;
    return d.type === 'person' ? baseRadius * 1.2 : baseRadius;
  }

  function drawGraph(graph) {
    if (!svgElement || !graph.nodes.length) return;
    cleanupSimulation();

    const svg = d3.select(svgElement);
    svg.selectAll('*').remove();
    svg
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`);

    // Definir clip path para contener nodos dentro del SVG
    svg.append('defs')
       .append('clipPath')
       .attr('id', 'graph-clip')
       .append('rect')
       .attr('width', width)
       .attr('height', height);

    // Configurar simulación con fuerzas mejoradas
    simulation = d3
      .forceSimulation(graph.nodes)
      .force(
        'link',
        d3
          .forceLink(graph.links)
          .id(d => d.id)
          .distance(d => {
            const srcNode = graph.nodes.find(n => n.id === (d.source.id || d.source));
            const tgtNode = graph.nodes.find(n => n.id === (d.target.id || d.target));
            return srcNode?.type === 'movie' && tgtNode?.type === 'movie' ? 120 : 80;
          })
          .strength(0.8)
      )
      .force(
        'charge',
        d3.forceManyBody().strength(d => (d.type === 'movie' ? -300 : -150))
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getEffectiveRadius(d) + 8));

    function getRoleColor(roles) {
      if (!Array.isArray(roles) || roles.length === 0) return '#999999';
      const str = roles.join(' ').toLowerCase();
      if (str.includes('director')) return '#1f77b4';
      if (str.includes('writer')) return '#2ca02c';
      if (str.includes('actor') || str.includes('actress')) return '#ff7f0e';
      return '#999999';
    }

    // Dibujar enlaces
    const linkGroup = svg.append('g').attr('class', 'links').attr('clip-path', 'url(#graph-clip)');
    const links = linkGroup
      .selectAll('line')
      .data(graph.links)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', d => getRoleColor(d.roles))
      .attr('stroke-width', d => Math.sqrt(d.weight || 1) * 1.5)
      .attr('stroke-opacity', 0.6);

    // Dibujar nodos
    const nodeGroup = svg.append('g').attr('class', 'nodes').attr('clip-path', 'url(#graph-clip)');
    const nodes = nodeGroup
      .selectAll('g')
      .data(graph.nodes)
      .join('g')
      .attr('class', 'node')
      .call(
        d3
          .drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded)
      );

    // Formas de nodos
    nodes
      .append('path')
      .attr('d', d => {
        const radius = getEffectiveRadius(d);
        const symbolType = d.type === 'person' ? d3.symbolStar : d3.symbolCircle;
        return d3.symbol().type(symbolType).size(radius * radius * Math.PI)();
      })
      .attr('fill', d => {
        if (d.type === 'person') return '#ffffff';
        return d.oscarWins && +d.oscarWins > 0 ? '#ffd700' : '#69b3a2';
      })
      .attr('stroke', d =>
        d.id === movieId
          ? '#ff0000'
          : d.type === 'person'
          ? '#333333'
          : '#666666'
      )
      .attr('stroke-width', d => (d.id === movieId ? 3 : 1.5));

    // Etiquetas para película principal y ganadoras de Oscar
    nodes
      .filter(
        d => d.id === movieId || (d.type === 'movie' && d.oscarWins && +d.oscarWins > 0)
      )
      .append('text')
      .text(d => {
        const title = d.title || d.primaryTitle || d.id;
        return title.length > 15 ? title.substring(0, 15) + '...' : title;
      })
      .attr('text-anchor', 'middle')
      .attr('dy', d => getEffectiveRadius(d) + 18)
      .attr('font-size', '11px')
      .attr('fill', '#333')
      .attr('font-weight', d => (d.id === movieId ? 'bold' : 'normal'))
      .attr('pointer-events', 'none');

    // Configurar tooltip
    const tooltip = d3.select(tooltipElement);

    nodes
    .on('mouseover', (event, d) => {
      if (d.type !== 'movie') return;

      const title = d.title || d.primaryTitle || 'Unknown';
      const year = d.year || 'N/A';
      const rating = d.averageRating ? (+d.averageRating).toFixed(1) : 'N/A';
      const votes = d.numVotes ? (+d.numVotes).toLocaleString() : 'N/A';
      const genres =
        d.genres && Array.isArray(d.genres) ? d.genres.join(', ') : 'N/A';
      const oscarNom = d.oscarNominations != null ? d.oscarNominations : 0;
      const oscarWin = d.oscarWins != null ? d.oscarWins : 0;

      const htmlContent = `
        <div class="title">${title} (${year})</div>
        <div>Rating: ${rating}/10</div>
        <div>Votes: ${votes}</div>
        <div>Genres: ${genres}</div>
        <div>Oscar Nominations: ${oscarNom}</div>
        <div>Oscar Wins: ${oscarWin}</div>
      `;

      // Obtener coordenadas relativas al contenedor del grafo
      const rect = graphContainerElement.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      tooltip
        .html(htmlContent)
        .style('display', 'block')
        .style('left', `${x + 10}px`)    
        .style('top', `${y - 10}px`);  
      })
      .on('mousemove', event => {
        // Obtener coordenadas relativas al contenedor del grafo
        const rect = graphContainerElement.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        tooltip
          .style('left', `${x + 10}px`)    
          .style('top', `${y - 10}px`);   
      })
      .on('mouseout', () => {
        tooltip.style('display', 'none');
    });

    // Actualizar posiciones con restricciones mejoradas
    simulation.on('tick', () => {
      graph.nodes.forEach(d => {
        const r = getEffectiveRadius(d);
        const margin = 20;
        d.x = Math.max(r + margin, Math.min(width - r - margin, d.x));
        d.y = Math.max(r + margin, Math.min(height - r - margin, d.y));
      });

      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  function drawBarChart(nodes) {
    if (!barChartElement) return;

    const svg = d3.select(barChartElement);
    svg.selectAll('*').remove();

    const movies = nodes
      .filter(n => n.type === 'movie' && n.year && !isNaN(+n.year))
      .map(n => ({ ...n, year: +n.year }));

    if (!movies.length) return;

    const margin = { top: 20, right: 30, bottom: 60, left: 50 };
    const chartWidth = 280 - margin.left - margin.right;
    const chartHeight = 200 - margin.top - margin.bottom;

    svg.attr('width', 280).attr('height', 200);

    const yearCounts = d3.rollup(movies, v => v.length, d => d.year);
    const yearRange = d3.range(filters.startYear, filters.endYear + 1);
    const data = yearRange
      .map(year => ({
        year,
        count: yearCounts.get(year) || 0
      }))
      .filter(d => d.count > 0);

    if (!data.length) return;

    const xScale = d3
      .scaleBand()
      .domain(data.map(d => d.year))
      .range([0, chartWidth])
      .padding(0.1);

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(data, d => d.count)])
      .range([chartHeight, 0]);

    const g = svg
      .append('g')
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

    // Ejes con menos ticks para mejor legibilidad
    const tickCount = Math.min(data.length, 6);
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale).tickValues(
        xScale.domain().filter((d, i) => !(i % Math.ceil(data.length / tickCount)))
      ))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-0.8em')
      .attr('dy', '0.15em')
      .attr('transform', 'rotate(-45)')
      .style('font-size', '10px');

    g.append('g').call(d3.axisLeft(yScale).ticks(5));

    // Etiquetas
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - chartHeight / 2)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '11px')
      .text('Movies');

    g.append('text')
      .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('font-size', '11px')
      .text('Year');
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

  function handleGenreChange(event) {
    filters.selectedGenres = new Set(
      Array.from(event.target.selectedOptions).map(opt => opt.value)
    );
    filters = { ...filters };
  }

  function resetFilters() {
    filters = {
      ...filters,
      startYear: filters.minYear,
      endYear: filters.maxYear,
      selectedGenres: new Set(),
      ratingMin: 0,
      ratingMax: 10,
      votesMin: 0,
      oscarsNomMin: 0,
      oscarsWinMin: 0
    };
  }

  $: if (
    loadedGraph &&
    movieId &&
    filters.startYear !== undefined &&
    filters.endYear !== undefined &&
    filters.ratingMin !== undefined &&
    filters.ratingMax !== undefined &&
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
    <div class="main-layout">
      <!-- Panel de controles izquierdo -->
      <div class="controls-panel">
        <div class="panel-header">
          <h3>Filters</h3>
          <button class="reset-btn" on:click={resetFilters}>Reset</button>
        </div>

        <!-- Filtro de años -->
        <div class="filter-section">
          <label class="filter-label">Years: {filters.startYear} – {filters.endYear}</label>
          <div class="range-container">
            <input
              type="range"
              min={filters.minYear}
              max={filters.maxYear}
              bind:value={filters.startYear}
              class="range-input"
              on:input={() => {
                if (filters.startYear > filters.endYear) {
                  filters.startYear = filters.endYear;
                }
                filters = { ...filters };
              }}
            />
            <input
              type="range"
              min={filters.minYear}
              max={filters.maxYear}
              bind:value={filters.endYear}
              class="range-input"
              on:input={() => {
                if (filters.endYear < filters.startYear) {
                  filters.endYear = filters.startYear;
                }
                filters = { ...filters };
              }}
            />
          </div>
          <div class="range-labels">
            <span>{filters.minYear}</span>
            <span>{filters.maxYear}</span>
          </div>
        </div>

        <!-- Rating -->
        <div class="filter-section">
          <label class="filter-label">Rating: {filters.ratingMin} – {filters.ratingMax}</label>
          <div class="range-container">
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              bind:value={filters.ratingMin}
              class="range-input"
              on:input={() => {
                if (filters.ratingMin > filters.ratingMax) {
                  filters.ratingMin = filters.ratingMax;
                }
                filters = { ...filters };
              }}
            />
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              bind:value={filters.ratingMax}
              class="range-input"
              on:input={() => {
                if (filters.ratingMax < filters.ratingMin) {
                  filters.ratingMax = filters.ratingMin;
                }
                filters = { ...filters };
              }}
            />
          </div>
          <div class="range-labels">
            <span>0</span>
            <span>10</span>
          </div>
        </div>

        <!-- Otros filtros -->
        <div class="filter-section">
          <label class="filter-label">Min Votes</label>
          <input
            type="number"
            min="0"
            bind:value={filters.votesMin}
            class="number-input"
            on:input={() => { filters = { ...filters }; }}
          />
        </div>

        <div class="filter-section">
          <label class="filter-label">Min Oscar Nominations</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsNomMin}
            class="number-input"
            on:input={() => { filters = { ...filters }; }}
          />
        </div>

        <div class="filter-section">
          <label class="filter-label">Min Oscar Wins</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsWinMin}
            class="number-input"
            on:input={() => { filters = { ...filters }; }}
          />
        </div>

        <div class="filter-section">
          <label class="filter-label">Genres</label>
          <select multiple size="6" on:change={handleGenreChange} class="genre-select">
            {#each allGenres as genre}
              <option value={genre}>{genre}</option>
            {/each}
          </select>
        </div>

        <!-- Gráfico de barras -->
        <div class="filter-section">
          <label class="filter-label">Year Distribution</label>
          <svg bind:this={barChartElement} class="bar-chart-mini"></svg>
        </div>
      </div>

      <!-- Contenido principal derecho -->
      <div class="main-content">
        <div class="content-header">
          <div class="header-info">
            <h2>Network Graph</h2>
            <div class="stats">
              {currentGraph.nodes.length} nodes • {currentGraph.links.length} connections
            </div>
          </div>
        </div>

        <div class="graph-container" bind:this={graphContainerElement}>
          <svg bind:this={svgElement} class="network-svg"></svg>
          <div bind:this={tooltipElement} class="tooltip"></div>
        </div>

        <!-- Leyenda -->
        <div class="legend">
          <div class="legend-item">
            <div class="legend-symbol circle movie"></div>
            <span>Movie</span>
          </div>
          <div class="legend-item">
            <div class="legend-symbol star person"></div>
            <span>Person</span>
          </div>
          <div class="legend-item">
            <div class="legend-symbol circle oscar"></div>
            <span>Oscar Winner</span>
          </div>
          <div class="legend-item">
            <div class="legend-line director"></div>
            <span>Director</span>
          </div>
          <div class="legend-item">
            <div class="legend-line writer"></div>
            <span>Writer</span>
          </div>
          <div class="legend-item">
            <div class="legend-line actor"></div>
            <span>Actor</span>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .film-network-container {
    width: 100%;
    height: 100vh;
    background: #fafafa;
    color: #222;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, sans-serif;
    overflow: hidden;
  }

  /* Estados de carga y error */
  .loading-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: 20px;
    background: #fafafa;
    color: #222;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-top: 4px solid #555;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .error-state button {
    background: #e0e0e0;
    border: 1px solid #bbb;
    color: #222;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .error-state button:hover {
    background: #d5d5d5;
  }

  /* Layout principal */
  .main-layout {
    display: flex;
    width: 100%;
    height: 100vh;
    gap: 0;
  }

  /* Panel de controles izquierdo */
  .controls-panel {
    width: 320px;
    min-width: 320px;
    background: #ffffff;
    border-right: 1px solid #ddd;
    padding: 20px;
    overflow-y: auto;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #eee;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #222;
  }

  .reset-btn {
    background: #f5f5f5;
    border: 1px solid #ccc;
    color: #222;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .reset-btn:hover {
    background: #e0e0e0;
  }

  /* Secciones de filtros */
  .filter-section {
    margin-bottom: 24px;
    padding: 16px;
    background: #f9f9f9;
    border-radius: 8px;
    border: 1px solid #ddd;
  }

  .filter-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 12px;
    color: #222;
  }

  /* Controles de rango */
  .range-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }

  .range-input {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 6px;
    background: #ddd;
    border-radius: 3px;
    outline: none;
    cursor: pointer;
  }

  .range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    background: #555;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
  }

  .range-input::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }

  .range-input::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: #555;
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }

  .range-labels {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #555;
  }

  /* Inputs numéricos */
  .number-input {
    width: 100%;
    padding: 8px 10px;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 6px;
    color: #222;
    font-size: 14px;
    outline: none;
    transition: all 0.2s ease;
  }

  .number-input:focus {
    border-color: #888;
    box-shadow: 0 0 0 2px rgba(136, 136, 136, 0.2);
  }

  /* Select de géneros */
  .genre-select {
    width: 100%;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 6px;
    color: #222;
    font-size: 14px;
    outline: none;
  }

  .genre-select option {
    background: #fff;
    color: #222;
    padding: 6px;
  }

  .genre-select option:checked {
    background: #eef2ff;
    color: #222;
  }

  /* Gráfico de barras mini */
  .bar-chart-mini {
    width: 100%;
    height: 200px;
    background: #fff;
    border-radius: 6px;
    border: 1px solid #ddd;
  }

  /* Contenido principal */
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    background: #f5f5f5;
  }

  .content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    background: #ffffff;
    border-bottom: 1px solid #ddd;
  }

  .header-info h2 {
    margin: 0 0 4px 0;
    font-size: 24px;
    font-weight: 600;
    color: #222;
  }

  .stats {
    font-size: 14px;
    color: #555;
    font-weight: 400;
  }

  .back-btn {
    background: #f5f5f5;
    border: 1px solid #ccc;
    color: #222;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .back-btn:hover {
    background: #e0e0e0;
  }

  /* Contenedor del grafo */
  .graph-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    background: #ffffff;
    margin: 0;
  }

  .network-svg {
    width: 100%;
    height: 100%;
    background: transparent;
    cursor: grab;
  }

  .network-svg:active {
    cursor: grabbing;
  }

  /* Tooltip */
  .tooltip {
    position: absolute;
    background: rgba(255, 255, 255, 0.95);
    color: #222;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.4;
    pointer-events: none;
    display: none;
    z-index: 1000;
    border: 1px solid #ccc;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    max-width: 250px;
  }

  .tooltip .title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 8px;
    color: #222;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
  }

  /* Leyenda */
  .legend {
    display: flex;
    justify-content: center;
    gap: 24px;
    padding: 16px 24px;
    background: #ffffff;
    border-top: 1px solid #ddd;
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #555;
  }

  .legend-symbol {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1.5px solid #666;
  }

  .legend-symbol.circle.movie {
    background: #69b3a2;
  }

  .legend-symbol.circle.oscar {
    background: #ffd700;
  }

  .legend-symbol.star.person {
    background: #ffffff;
    clip-path: polygon(
      50% 0%,
      61% 35%,
      98% 35%,
      68% 57%,
      79% 91%,
      50% 70%,
      21% 91%,
      32% 57%,
      2% 35%,
      39% 35%
    );
    border-radius: 0;
    border: 1.5px solid #333;
  }

  .legend-line {
    width: 20px;
    height: 2px;
    border-radius: 1px;
  }

  .legend-line.director {
    background: #1f77b4;
  }

  .legend-line.writer {
    background: #2ca02c;
  }

  .legend-line.actor {
    background: #ff7f0e;
  }

  /* Estilos para nodos y enlaces en el SVG */
  .network-svg .node {
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .network-svg .node:hover {
    filter: brightness(1.2) drop-shadow(0 0 6px rgba(0, 0, 0, 0.2));
  }

  .network-svg .link {
    transition: stroke-opacity 0.2s ease;
  }

  .network-svg .link:hover {
    stroke-opacity: 1 !important;
  }

  /* Scrollbar personalizado para el panel de controles */
  .controls-panel::-webkit-scrollbar {
    width: 6px;
  }

  .controls-panel::-webkit-scrollbar-track {
    background: #f0f0f0;
    border-radius: 3px;
  }

  .controls-panel::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
  }

  .controls-panel::-webkit-scrollbar-thumb:hover {
    background: #bbb;
  }

  /* Responsividad */
  @media (max-width: 1024px) {
    .main-layout {
      flex-direction: column;
    }

    .controls-panel {
      width: 100%;
      max-height: 300px;
      overflow-y: auto;
    }

    .legend {
      gap: 16px;
    }
  }

  @media (max-width: 768px) {
    .controls-panel {
      padding: 16px;
    }

    .content-header {
      padding: 16px;
    }

    .content-header h2 {
      font-size: 20px;
    }

    .legend {
      padding: 12px 16px;
      gap: 12px;
    }

    .legend-item {
      font-size: 11px;
    }
  }
</style>

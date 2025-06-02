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

  // 1) Al montar, cargamos datos y configuramos el observer de resize
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

  // 2) Función para cargar grafo y metadatos de películas
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

      // Determinamos rango de rating, votos y Oscars
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

      // Extraemos lista única de géneros
      const genresSet = new Set();
      movieNodes.forEach(n => {
        if (n.genres && Array.isArray(n.genres)) {
          n.genres.forEach(g => genresSet.add(g));
        }
      });
      allGenres = Array.from(genresSet).sort();

      loadedGraph = true;
      isLoading = false;

      // Si ya había un movieId seleccionado, dibujamos de inmediato
      if (movieId) {
        updateVisualization();
      }
    } catch (err) {
      console.error('Error loading graph data:', err);
      loadError = 'Failed to load network data. Please try again.';
      isLoading = false;
    }
  }

  // 3) Observador de cambios de tamaño del contenedor principal
  function setupResizeObserver() {
    if (!containerElement) return;
    resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        const { width: newWidth } = entry.contentRect;
        // Ajustamos width; dejamos al menos 400 px
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

  // 4) Detener y limpiar simulación D3
  function cleanupSimulation() {
    if (simulation) {
      simulation.stop();
      simulation = null;
    }
  }

  // 5) Construye el subgrafo filtrado a partir de movieId y los filtros
  function buildFilteredSubgraph() {
    const rootNode = graphData.nodes.find(d => d.id === movieId);
    if (!rootNode) {
      console.warn(`Root node not found: ${movieId}`);
      return { nodes: [], links: [] };
    }

    // 5.1) Filtrar componente completo (todos los nodos con mismo componente)
    const componentId = rootNode.component;
    const componentNodes = graphData.nodes.filter(d => d.component === componentId);
    const componentIds = new Set(componentNodes.map(d => d.id));

    // 5.2) Filtrar enlaces que conecten dentro de ese componente
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

    // 5.3) Construir lista de adyacencia
    const adjacency = new Map();
    componentNodes.forEach(n => adjacency.set(n.id, []));
    componentLinks.forEach(link => {
      if (adjacency.has(link.source) && adjacency.has(link.target)) {
        adjacency.get(link.source).push(link.target);
        adjacency.get(link.target).push(link.source);
      }
    });

    // 5.4) Recorrido BFS a 2 saltos desde movieId
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

    // 5.5) Nodos y enlaces iniciales del subgrafo
    let subNodes = graphData.nodes.filter(d => subgraphIds.has(d.id));
    let subLinks = componentLinks.filter(link =>
      subgraphIds.has(link.source) && subgraphIds.has(link.target)
    );

    // 5.6) Filtrar películas que no pasen los criterios
    const filteredMovieIds = new Set(
      subNodes
        .filter(n => n.type === 'movie')
        .filter(n => passesFilters(n))
        .map(n => n.id)
    );

    // 5.7) Filtrar enlaces válidos: 
    //   - Si ambos lados son "movie", ambos deben pasar filtros
    //   - Si uno solo es movie, ese debe pasar filtro
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

    // 5.8) Construir lista final de nodos (solo aquellos conectados por validLinks)
    const finalIds = new Set();
    validLinks.forEach(link => {
      finalIds.add(link.source);
      finalIds.add(link.target);
    });
    const finalNodes = subNodes.filter(n => finalIds.has(n.id));

    return { nodes: finalNodes, links: validLinks };
  }

  // 6) Verifica si un nodo de tipo "movie" pasa los filtros actuales
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

  // 7) Función que dibuja el grafo (nodos + enlaces + tooltip)
  function drawGraph(graph) {
    if (!svgElement || !graph.nodes.length) return;
    cleanupSimulation();

    // Seleccionamos y limpiamos el SVG
    const svg = d3.select(svgElement);
    svg.selectAll('*').remove();
    svg
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`);

    // 7.1) Escala de tamaño basada en “averageRating”
    const ratings = graph.nodes
      .filter(d => d.averageRating && !isNaN(+d.averageRating))
      .map(d => +d.averageRating);

    const sizeScale = d3
      .scaleLinear()
      .domain(ratings.length ? d3.extent(ratings) : [0, 10])
      .range([6, 20]);
      // Estos valores (6 a 20) representan el “radio base” de cada nodo

    // 7.2) Función para devolver el “radio efectivo” (radio base * factor)
    function getEffectiveRadius(d) {
      const rating = d.averageRating ? +d.averageRating : 5;
      const baseRadius = sizeScale(rating);
      return baseRadius * 1.2; 
      // Multiplicamos por 1.2 para cubrir los “picos” de la estrella
    }

    // 7.3) Configuramos la simulación de fuerzas
    simulation = d3
      .forceSimulation(graph.nodes)
      .force(
        'link',
        d3
          .forceLink(graph.links)
          .id(d => d.id)
          .distance(d => {
            // Distancia mayor si ambos nodos son películas
            const srcNode = graph.nodes.find(n => n.id === (d.source.id || d.source));
            const tgtNode = graph.nodes.find(n => n.id === (d.target.id || d.target));
            return srcNode?.type === 'movie' && tgtNode?.type === 'movie' ? 150 : 80;
          })
      )
      .force(
        'charge',
        d3.forceManyBody().strength(d => (d.type === 'movie' ? -400 : -200))
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getEffectiveRadius(d) + 5));

    // 7.4) Función para asignar color a cada enlace según roles
    function getRoleColor(roles) {
      if (!Array.isArray(roles) || roles.length === 0) return '#999999';
      const str = roles.join(' ').toLowerCase();
      if (str.includes('director')) return '#1f77b4';
      if (str.includes('writer')) return '#2ca02c';
      if (str.includes('actor') || str.includes('actress')) return '#ff7f0e';
      return '#999999';
    }

    // 7.5) Dibujar enlaces (<line>)
    const linkGroup = svg.append('g').attr('class', 'links');
    const links = linkGroup
      .selectAll('line')
      .data(graph.links)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', d => getRoleColor(d.roles))
      .attr('stroke-width', d => Math.sqrt(d.weight || 1) * 2)
      .attr('stroke-opacity', 0.6);

    // 7.6) Dibujar nodos (<g> → <path> + opcional <text>)
    const nodeGroup = svg.append('g').attr('class', 'nodes');
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

    // 7.7) Cada nodo es un <path> que puede ser estrella o círculo
    nodes
      .append('path')
      .attr('d', d => {
        const radius = getEffectiveRadius(d);
        const symbolType = d.type === 'person' ? d3.symbolStar : d3.symbolCircle;
        // Para obtener área ≈ π·r², usamos size = r²·π
        return d3.symbol().type(symbolType).size(radius * radius * Math.PI)();
      })
      .attr('fill', d => {
        if (d.type === 'person') return '#ffffff';
        // Películas ganadoras de Oscar van doradas, el resto verdes
        return d.oscarWins && +d.oscarWins > 0 ? '#ffd700' : '#69b3a2';
      })
      .attr('stroke', d =>
        d.id === movieId
          ? '#ff0000'
          : d.type === 'person'
          ? '#333333'
          : '#666666'
      )
      .attr('stroke-width', d => (d.id === movieId ? 3 : 1));

    // 7.8) Agregar texto para el nodo raíz o películas con Oscar
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
      .attr('dy', d => getEffectiveRadius(d) + 15)
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .attr('font-weight', d => (d.id === movieId ? 'bold' : 'normal'));

    // 7.9) Configurar tooltip
    
    // 7.9) Configurar tooltip para películas
    const tooltip = d3.select(tooltipElement);

    nodes
      .on('mouseover', (event, d) => {
        // Solo mostrar tooltip si es nodo de tipo 'movie'
        if (d.type !== 'movie') return;

        // Obtener datos de la película
        const title = d.title || d.primaryTitle || 'Unknown';
        const year = d.year || 'N/A';
        const rating = d.averageRating ? (+d.averageRating).toFixed(1) : 'N/A';
        const votes = d.numVotes ? (+d.numVotes).toLocaleString() : 'N/A';
        const genres =
          d.genres && Array.isArray(d.genres) ? d.genres.join(', ') : 'N/A';
        const oscarNom = d.oscarNominations != null ? d.oscarNominations : 0;
        const oscarWin = d.oscarWins != null ? d.oscarWins : 0;

        // Construir el contenido HTML del tooltip
        const htmlContent = `
          <div class="title">${title} (${year})</div>
          <div>Rating: ${rating}</div>
          <div>Votes: ${votes}</div>
          <div>Genres: ${genres}</div>
          <div>Oscar Nominations: ${oscarNom}</div>
          <div>Oscar Wins: ${oscarWin}</div>
        `;

        tooltip
          .html(htmlContent)
          .style('display', 'block')
          .style('left', `${event.pageX + 12}px`)
          .style('top', `${event.pageY - 12}px`);
      })
      .on('mousemove', event => {
        // Seguir al cursor mientras se mueve
        tooltip
          .style('left', `${event.pageX + 12}px`)
          .style('top', `${event.pageY - 12}px`);
      })
      .on('mouseout', () => {
        // Ocultar cuando se salga del nodo
        tooltip.style('display', 'none');
      });


    // 7.10) Clamp con margen extra en Y para evitar desbordar por abajo
    const offsetY = 20; // Reserva 20px adicionales debajo de cada nodo (para texto, márgenes, etc.)

    simulation.on('tick', () => {
      graph.nodes.forEach(d => {
        const r = getEffectiveRadius(d);
        // Clamp en X (igual que antes)
        d.x = Math.max(r, Math.min(width - r, d.x));
        // Clamp en Y teniendo en cuenta offset inferior
        d.y = Math.max(r, Math.min(height - (r + offsetY), d.y));
      });

      // Actualizamos posiciones de enlaces
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      // Actualizamos posiciones de nodos
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

  // 8) Función que dibuja el diagrama de barras (histograma de años)
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
    g.append('g').call(d3.axisLeft(yScale));

    // Labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - chartHeight / 2)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Number of Movies');

    g.append('text')
      .attr(
        'transform',
        `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 10})`
      )
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Year');
  }

  // Funciones auxiliares de filtros y volver atrás
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
      ratingMin: filters.ratingMin,
      votesMin: filters.votesMin,
      oscarsNomMin: filters.oscarsNomMin,
      oscarsWinMin: filters.oscarsWinMin
    };
    filters = { ...filters };
  }

  function goBack() {
    dispatch('back');
  }

  // 9) Reactivo: cuando cambian movieId o filtros, volvemos a dibujar
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
    <!-- Controles de filtros -->
    <div class="controls-panel">
      <div class="control-row">
        <button class="back-btn" on:click={goBack}>
          ← Back to Search
        </button>
        <button class="reset-btn" on:click={resetFilters}>
          Reset Filters
        </button>
      </div>

      <!-- Filtro de rango de años -->
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
              filters = { ...filters };
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
              filters = { ...filters };
            }}
          />
        </div>
        <small>[{filters.minYear} – {filters.maxYear}]</small>
      </div>

      <!-- Resto de filtros -->
      <div class="filters-grid">
        <div class="filter-group">
          <label>Min Rating:</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            bind:value={filters.ratingMin}
            on:input={() => {
              filters = { ...filters };
            }}
          />
        </div>
        <div class="filter-group">
          <label>Min Votes:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.votesMin}
            on:input={() => {
              filters = { ...filters };
            }}
          />
        </div>
        <div class="filter-group">
          <label>Min Oscar Nominations:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsNomMin}
            on:input={() => {
              filters = { ...filters };
            }}
          />
        </div>
        <div class="filter-group">
          <label>Min Oscar Wins:</label>
          <input
            type="number"
            min="0"
            bind:value={filters.oscarsWinMin}
            on:input={() => {
              filters = { ...filters };
            }}
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

    <!-- Sección de grafo -->
    <div class="network-section">
      <div class="network-header">
        <h3>Network Graph</h3>
        <div class="network-stats">
          Showing {currentGraph.nodes.length} nodes, {currentGraph.links.length} connections
        </div>
      </div>
      <div class="graph-container">
        <svg bind:this={svgElement} class="network-svg"></svg>
      
        <!-- Tooltip para mostrar datos de la película -->
        <div bind:this={tooltipElement} class="tooltip"></div>
      </div>
      
    </div>

    <!-- Sección de histograma -->
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

  /* Estados de carga y error */
  .loading-state,
  .error-state {
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

  /* Panel de controles */
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

  .back-btn,
  .reset-btn {
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

  .back-btn:hover { background: #5a6268; }

  .reset-btn {
    background: #17a2b8;
    color: white;
  }

  .reset-btn:hover { background: #138496; }

  /* Filtro de años */
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

  .slider-start::-webkit-slider-thumb { z-index: 2; }
  .slider-end::-webkit-slider-thumb   { z-index: 1; }

  /* Grid de filtros */
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
    box-shadow: 0 0 0 2px rgba(105,179,162,0.25);
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
    box-shadow: 0 0 0 2px rgba(105,179,162,0.25);
  }

  /* Sección del grafo */
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
    overflow: hidden; /* ya tenías esto para recortar los nodos */
    width: 100%;
    /* resto de estilos… */
  }


  .network-svg {
    display: block;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  }

  /* Sección del histograma */
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
  /* Estilos básicos del tooltip */
  .tooltip {
    position: absolute;
    pointer-events: none;      /* para que no intercepte el cursor */
    display: none;             /* oculto por defecto */
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    line-height: 1.2;
    max-width: 220px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    z-index: 1000;
  }

  /* Título dentro del tooltip */
  .tooltip .title {
    font-weight: bold;
    margin-bottom: 0.25rem;
    font-size: 0.9rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    padding-bottom: 0.2rem;
    margin-bottom: 0.4rem;
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

  /* Efectos hover en nodos y enlaces */
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

  /* Animación fadeIn para estados de carga/error */
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

  /* Focus outline accesible */
  .back-btn:focus,
  .reset-btn:focus {
    outline: 2px solid #69b3a2;
    outline-offset: 2px;
  }

  .slider:focus {
    outline: 2px solid #69b3a2;
    outline-offset: 2px;
  }

  /* Scrollbar personalizado para <select multiple> de géneros */
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

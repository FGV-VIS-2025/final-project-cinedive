<!-- src/lib/charts/FilmNetwork.svelte -->
<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';
  import { loadGraph, loadMoviesFullData } from '$lib/utils/dataLoader.js';

  export let movieId;
  const dispatch = createEventDispatcher();

  let graphData = null;
  let svgElement;
  let svgBarChart;
  let tooltipElement;
  let simulation;

  // Dimensiones
  const width = 1200;
  const height = 600;
  const heightBar = 150;
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };

  // Filtros (temporalmente simplificados)
  // Para depuración, desactivamos el filtro de roles/rating:
  // let selectedRoles = new Set(['actor', 'director', 'writer']);
  let selectedRoles = null; // null significa "no filtrar por roles"
  let yearExtent = [1900, 2025];
  let minYear = 1900;
  let maxYear = 2025;
  // let minRating = 0;
  let minRating = 0; // mantenemos en 0 para que no excluya nada

  let nodesToDraw = [];
  let linksToDraw = [];
  let globalLinks = [];

  onMount(async () => {
    try {
      const [graph, movies] = await Promise.all([
        loadGraph(),
        loadMoviesFullData()
      ]);

      // Fusionar metadatos en nodos de tipo "movie"
      const movieMap = new Map(movies.map(m => [m.tconst, m]));
      graph.nodes = graph.nodes.map(node => {
        const extra = movieMap.get(node.id);
        return extra ? { ...node, ...extra } : node;
      });

      graphData = graph;
      buildGlobalLinks();

      // Calcular año extremo para los sliders (aunque de momento no los usamos)
      const allMovieYears = graphData.nodes
        .filter(n => n.type === 'movie' && typeof n.year === 'number')
        .map(n => +n.year);
      if (allMovieYears.length) {
        yearExtent = d3.extent(allMovieYears);
        minYear = yearExtent[0];
        maxYear = yearExtent[1];
      }

      if (movieId) {
        updateSubgraph();
        drawGraph();
        drawBarChart();
      }
    } catch (err) {
      console.error('FilmNetwork: error cargando datos →', err);
    }
  });

  onDestroy(() => {
    simulation?.stop();
  });

  // Cuando cualquiera de estas variables cambie, recalcular subgrafo y redibujar
  $: if (movieId && graphData) {
    updateSubgraph();
    drawGraph();
    drawBarChart();
  }

  function buildGlobalLinks() {
    globalLinks = graphData.links.map(link => {
      const s = typeof link.source === 'object' ? link.source.id : link.source;
      const t = typeof link.target === 'object' ? link.target.id : link.target;
      // Para depuración, permitimos roles nulos:
      const rolesArr = Array.isArray(link.roles) ? link.roles : [link.roles];
      return {
        source: s,
        target: t,
        roles: rolesArr
      };
    });
  }

  function updateSubgraph() {
    const root = graphData.nodes.find(n => n.id === movieId);
    if (!root) {
      nodesToDraw = [];
      linksToDraw = [];
      return;
    }

    // 1) Filtrar nodos por componente
    const compId = root.component;
    const nodesInComp = graphData.nodes.filter(n => n.component === compId);

    // 2) Filtrar películas por año y rating (dejamos rating=0 para no filtrar nada)
    const yearFiltered = nodesInComp.filter(n => {
      if (n.id === movieId) return true;
      if (n.type === 'movie') {
        return (
          n.year >= minYear &&
          n.year <= maxYear &&
          (n.averageRating || 0) >= minRating
        );
      }
      return true; // Si no es movie (p.ej. es persona), lo mantenemos
    });
    const idSetYear = new Set(yearFiltered.map(n => n.id));

    // 3) Filtrar enlaces que conecten nodos dentro de idSetYear
    let filteredLinks = globalLinks.filter(l => {
      if (!idSetYear.has(l.source) || !idSetYear.has(l.target)) return false;
      // Si quisieras filtrar por roles, descomenta este bloque:
      // if (selectedRoles) {
      //   return l.roles.some(r => selectedRoles.has(r));
      // }
      return true; // No filtramos por roles en esta depuración
    });

    // 4) Construir vecindad
    const adjacency = new Map(yearFiltered.map(n => [n.id, []]));
    filteredLinks.forEach(l => {
      adjacency.get(l.source).push(l.target);
      adjacency.get(l.target).push(l.source);
    });

    // 5) BFS a profundidad 2
    const visited = new Set([movieId]);
    const queue = [{ id: movieId, depth: 0 }];
    while (queue.length) {
      const { id: curr, depth } = queue.shift();
      if (depth >= 2) continue;
      (adjacency.get(curr) || []).forEach(neigh => {
        if (!visited.has(neigh)) {
          visited.add(neigh);
          queue.push({ id: neigh, depth: depth + 1 });
        }
      });
    }

    // 6) Guardar nodos y enlaces finales
    nodesToDraw = yearFiltered.filter(n => visited.has(n.id));
    linksToDraw = filteredLinks.filter(
      l => visited.has(l.source) && visited.has(l.target)
    );

    // ===> Para depuración, imprime cuántos nodos/enlaces quedan:
    console.log(
      'updateSubgraph → nodosToDraw:',
      nodesToDraw.length,
      'linksToDraw:',
      linksToDraw.length
    );
    // Incluso puedes loguear los primeros ids para verlos:
    console.log('IDs nodosToDraw:', Array.from(nodesToDraw.map(x => x.id)).slice(0, 10));
  }

  function drawGraph() {
    if (!svgElement) return;
    d3.select(svgElement).selectAll('*').remove();

    const svg = d3
      .select(svgElement)
      .attr('width', width)
      .attr('height', height)
      .style('border', '1px solid #ccc')
      .style('background', '#fafafa');

    // 7) Si no hay vecinos, dibujar al menos el nodo raíz
    if (nodesToDraw.length === 1 && linksToDraw.length === 0) {
      const rootNode = nodesToDraw[0];
      const x = width / 2;
      const y = height / 2;
      const radius = 20;

      svg
        .append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', radius)
        .attr('fill', rootNode.type === 'movie' ? '#ffd700' : '#fff')
        .attr('stroke', 'red')
        .attr('stroke-width', 3);

      return;
    }

    // 8) Escala de tamaño por averageRating
    const sizeScale = d3
      .scaleLinear()
      .domain([
        d3.min(nodesToDraw, d => +d.averageRating || 0),
        d3.max(nodesToDraw, d => +d.averageRating || 1)
      ])
      .range([5, 20]);

    // Color de nodos movie según oscarWins
    const colorScale = d3
      .scaleOrdinal()
      .domain([0, 1])
      .range(['#aaa', '#ffd700']);

    // Color de enlaces por rol (temporalmente ignoramos roles si selectedRoles es null)
    const roleColor = rolesArr => {
      if (!selectedRoles) return '#999';
      if (rolesArr.includes('director')) return '#1f77b4';
      if (rolesArr.includes('writer')) return '#2ca02c';
      if (rolesArr.includes('actor')) return '#ff6600';
      return '#999';
    };

    const rolesMap = new Map();
    nodesToDraw.forEach(n => rolesMap.set(n.id, new Set()));
    linksToDraw.forEach(l => {
      [l.source, l.target].forEach(id => {
        if (!rolesMap.has(id)) rolesMap.set(id, new Set());
        l.roles.forEach(r => rolesMap.get(id).add(r));
      });
    });

    // Generador de símbolos: estrella si type==='person', círculo si type==='movie'
    const symbolGen = d3
      .symbol()
      .type(d => (d.type === 'person' ? d3.symbolStar : d3.symbolCircle))
      .size(d => {
        if (d.type === 'person') return 100;
        const r = isNaN(d.averageRating) ? 8 : sizeScale(d.averageRating);
        return Math.PI * r * r;
      });

    // Configurar la simulación
    simulation?.stop();
    simulation = d3
      .forceSimulation(nodesToDraw)
      .force('link', d3.forceLink(linksToDraw).id(d => d.id).distance(80).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'collide',
        d3.forceCollide(d => {
          if (d.type === 'person') return 10;
          return isNaN(d.averageRating)
            ? 10
            : Math.sqrt(sizeScale(d.averageRating)) + 5;
        })
      );

    // Dibujar enlaces
    const linkSel = svg
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksToDraw)
      .join('line')
      .attr('stroke', d => roleColor(d.roles))
      .attr('stroke-width', 2)
      .attr('opacity', 0.7);

    // Dibujar nodos
    const nodeSel = svg
      .append('g')
      .attr('class', 'nodes')
      .selectAll('path')
      .data(nodesToDraw)
      .join('path')
      .attr('d', d => symbolGen(d))
      .attr('fill', d =>
        d.type === 'person' ? 'white' : colorScale(d.oscarWins > 0 ? 1 : 0)
      )
      .attr('stroke', d => (d.id === movieId ? 'red' : '#555'))
      .attr('stroke-width', d => (d.id === movieId ? 3 : 1))
      .call(drag(simulation));

    // Tooltips
    const tooltip = d3.select(tooltipElement);
    nodeSel
      .on('mouseover', (event, d) => {
        let html;
        if (d.type === 'person') {
          const roles = Array.from(rolesMap.get(d.id) || []);
          html = `<strong>Persona</strong><br/>
                  ID: ${d.id}<br/>
                  Roles: ${roles.length ? roles.join(', ') : 'Ninguno'}`;
        } else {
          const title = d.primaryTitle || d.title || 'Sin título';
          const wins = d.oscarWins > 0 ? 'Sí' : 'No';
          const rating = d.averageRating || 'N/A';
          const genres = Array.isArray(d.genres) ? d.genres.join(', ') : d.genres || 'N/A';
          const directors = Array.isArray(d.directors)
            ? d.directors.join(', ')
            : d.directors || 'N/A';
          html = `<strong>${title}</strong><br/>
                  Ganó Oscar: ${wins}<br/>
                  Rating: ${rating}<br/>
                  Género(s): ${genres}<br/>
                  Director(es): ${directors}`;
        }
        tooltip
          .style('display', 'block')
          .html(html)
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY + 10}px`);
      })
      .on('mouseout', () => {
        tooltip.style('display', 'none');
      });

    // Simulación: tick para actualizar posiciones
    simulation.on('tick', () => {
      nodesToDraw.forEach(d => {
        const r =
          d.type === 'person'
            ? 5
            : isNaN(d.averageRating)
            ? 5
            : sizeScale(d.averageRating);
        d.x = Math.max(r, Math.min(width - r, d.x));
        d.y = Math.max(r, Math.min(height - r, d.y));
      });

      linkSel
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodeSel.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  function drawBarChart() {
    if (!svgBarChart) return;
    d3.select(svgBarChart).selectAll('*').remove();

    const svg = d3
      .select(svgBarChart)
      .attr('width', width)
      .attr('height', heightBar)
      .style('border', '1px solid #ccc')
      .style('background', '#fafafa');

    // Sólo películas
    const movieNodes = nodesToDraw.filter(n => n.type === 'movie');
    const counts = d3.rollups(
      movieNodes,
      v => v.length,
      d => d.year
    );
    const countsMap = new Map(counts);

    const allYears = d3.range(minYear, maxYear + 1);
    const data = allYears.map(y => ({
      year: y,
      count: countsMap.get(y) || 0
    }));

    const x = d3
      .scaleBand()
      .domain(data.map(d => d.year))
      .range([margin.left, width - margin.right])
      .padding(0.1);

    const yMax = d3.max(data, d => d.count) || 1;
    const y = d3
      .scaleLinear()
      .domain([0, yMax])
      .nice()
      .range([heightBar - margin.bottom, margin.top]);

    const xAxis = g =>
      g
        .attr('transform', `translate(0,${heightBar - margin.bottom})`)
        .call(
          d3
            .axisBottom(x)
            .tickValues(x.domain().filter((_, i) => i % 5 === 0))
            .tickFormat(d3.format('d'))
        )
        .selectAll('text')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end');

    const yAxis = g =>
      g.attr('transform', `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(4));

    svg.append('g').call(xAxis);
    svg.append('g').call(yAxis);

    svg
      .append('g')
      .selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => x(d.year))
      .attr('y', d => y(d.count))
      .attr('width', x.bandwidth())
      .attr('height', d => y(0) - y(d.count))
      .attr('fill', '#6baed6')
      .append('title')
      .text(d => `${d.year}: ${d.count} películas`);

    // Después de pintar el bar-chart, inicializamos brush
    initBrush();
  }

  function initBrush() {
    if (!svgBarChart) return;
    d3.select(svgBarChart).selectAll('.brush').remove();

    const svg = d3.select(svgBarChart);
    const xScale = d3
      .scaleLinear()
      .domain([yearExtent[0], yearExtent[1]])
      .range([margin.left, width - margin.right]);

    const brush = d3
      .brushX()
      .extent([
        [margin.left, margin.top],
        [width - margin.right, heightBar - margin.bottom]
      ])
      .on('end', event => {
        if (!event.selection) return;
        const [x0, x1] = event.selection;
        const y0 = Math.round(xScale.invert(x0));
        const y1 = Math.round(xScale.invert(x1));
        minYear = Math.max(yearExtent[0], Math.min(y0, y1));
        maxYear = Math.min(yearExtent[1], Math.max(y0, y1));
        d3.select(svgBarChart).selectAll('.brush').remove();
      });

    svg
      .append('g')
      .attr('class', 'brush')
      .call(brush)
      .call(brush.move, xScale.range());
  }

  function onMinYearChange(e) {
    const v = +e.target.value;
    if (v <= maxYear) minYear = v;
  }

  function onMaxYearChange(e) {
    const v = +e.target.value;
    if (v >= minYear) maxYear = v;
  }

  function onMinRatingChange(e) {
    const v = +e.target.value;
    minRating = v;
  }

  function toggleRole(role) {
    if (!selectedRoles) return;
    if (selectedRoles.has(role)) selectedRoles.delete(role);
    else selectedRoles.add(role);
    selectedRoles = new Set(selectedRoles);
  }

  function drag(sim) {
    return d3
      .drag()
      .on('start', event => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', event => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on('end', event => {
        if (!event.active) sim.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      });
  }

  function volver() {
    dispatch('volver');
  }
</script>

<style>
  .container {
    display: grid;
    grid-template-columns: 280px auto;
    gap: 1rem;
    height: 100%;
  }
  .controls-panel {
    padding: 1rem;
    border: 1px solid #ccc;
    background: #f9f9f9;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .controls-panel label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    cursor: pointer;
  }
  .controls-panel input[type='checkbox'],
  .controls-panel input[type='range'] {
    cursor: pointer;
  }
  .slider-wrapper {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  .slider-wrapper input[type='range'] {
    flex: 1;
  }
  .graph-panel {
    position: relative;
  }
  svg {
    display: block;
  }
  .tooltip-network {
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: #fff;
    padding: 0.5rem;
    border-radius: 4px;
    display: none;
    pointer-events: none;
    font-size: 0.9rem;
    z-index: 10;
  }
  .button-back {
    margin-bottom: 1rem;
    background-color: #695a03;
    padding: 0.5rem 1rem;
    border: none;
    cursor: pointer;
    border-radius: 5px;
    color: white;
    font-weight: bold;
  }
  .placeholder-text {
    color: #666;
    font-style: italic;
    text-align: center;
    margin: 2rem;
  }
</style>

{#if !movieId}
  <p class="placeholder-text">Selecciona primero una película en Step 1.</p>
{:else}
  <div class="container">
    <!-- Panel de filtros -->
    <div class="controls-panel">
      <button class="button-back" on:click={volver}>← Volver</button>

      <div>
        <strong>Roles:</strong>
        <label>
          <input
            type="checkbox"
            disabled
          />
          Actor
        </label>
        <label>
          <input
            type="checkbox"
            disabled
          />
          Director
        </label>
        <label>
          <input
            type="checkbox"
            disabled
          />
          Writer
        </label>
        <small style="color: #999;">(Filtrado temporalmente desactivado)</small>
      </div>

      <div class="slider-wrapper">
        <label for="minYear">Año mín.:</label>
        <input
          id="minYear"
          type="range"
          min={yearExtent[0]}
          max={yearExtent[1]}
          step="1"
          bind:value={minYear}
          on:input={onMinYearChange}
        />
        <span>{minYear}</span>
      </div>

      <div class="slider-wrapper">
        <label for="maxYear">Año máx.:</label>
        <input
          id="maxYear"
          type="range"
          min={yearExtent[0]}
          max={yearExtent[1]}
          step="1"
          bind:value={maxYear}
          on:input={onMaxYearChange}
        />
        <span>{maxYear}</span>
      </div>

      <div class="slider-wrapper">
        <label for="minRating">Rating mín.:</label>
        <input
          id="minRating"
          type="range"
          min="0"
          max="10"
          step="0.1"
          bind:value={minRating}
          on:input={onMinRatingChange}
        />
        <span>{minRating.toFixed(1)}</span>
      </div>
      <small style="color: #999;">
        (Rating mínimo: solo las películas con rating ≥ este valor)
      </small>
    </div>

    <!-- Panel de grafo + bar-chart -->
    <div class="graph-panel">
      <svg bind:this={svgElement} width={width} height={height}></svg>
      <svg
        bind:this={svgBarChart}
        width={width}
        height={heightBar}
        style="margin-top: 0.5rem;"
      ></svg>
      <div bind:this={tooltipElement} class="tooltip-network"></div>
    </div>
  </div>
{/if}

<!-- src/lib/charts/FilmNetwork.svelte -->
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import * as d3 from 'd3';
  import { loadGraph, loadMoviesFullData } from '$lib/utils/dataLoader.js';

  let graphData = null;
  let width = 1200;
  let height = 800;
  let svgElement;
  let tooltipElement;

  export let movieId;
  const dispatch = createEventDispatcher();

  onMount(async () => {
    const graph = await loadGraph();
    const movies = await loadMoviesFullData();

    const movieMap = new Map(movies.map(movie => [movie.tconst, movie]));

    graph.nodes = graph.nodes.map(node => {
      const movieData = movieMap.get(node.id);
      return movieData ? { ...node, ...movieData } : node;
    });

    graphData = graph;

    if (movieId) {
      drawFromMovieId(movieId);
    }
  });

  $: if (movieId && graphData) {
    drawFromMovieId(movieId);
  }

  function drawFromMovieId(movieId) {
    const node = graphData.nodes.find(d => d.id === movieId);
    if (!node) return;

    const componentId = node.component;
    const nodesInComponent = graphData.nodes.filter(d => d.component === componentId);
    const nodeIdsInComponent = new Set(nodesInComponent.map(d => d.id));

    const linksAll = graphData.links
      .filter(d =>
        nodeIdsInComponent.has(typeof d.source === 'object' ? d.source.id : d.source) &&
        nodeIdsInComponent.has(typeof d.target === 'object' ? d.target.id : d.target)
      )
      .map(d => ({
        source: typeof d.source === 'object' ? d.source.id : d.source,
        target: typeof d.target === 'object' ? d.target.id : d.target,
        weight: d.weight,
        roles:  d.roles
      }));

      
    const adjacency = new Map(nodesInComponent.map(n => [n.id, []]));
    linksAll.forEach(l => {
      adjacency.get(l.source).push(l.target);
      adjacency.get(l.target).push(l.source);
    });

    const resultNodes = new Set([movieId]);
    const queue = [{ id: movieId, depth: 0 }];

    while (queue.length > 0) {
      const { id: current, depth } = queue.shift();
      if (depth >= 2) continue;          

      for (const neighbor of adjacency.get(current)) {
        if (!resultNodes.has(neighbor)) {
          resultNodes.add(neighbor);
          queue.push({ id: neighbor, depth: depth + 1 });
        }
      }
    }

    const nodes = graphData.nodes.filter(d => resultNodes.has(d.id));
    const finalLinks = linksAll.filter(l =>
      resultNodes.has(l.source) && resultNodes.has(l.target)
    );

    drawGraph({ nodes, links: finalLinks });
  }


  function drawGraph(graph) {
  // Limpio SVG
  d3.select(svgElement).selectAll('*').remove();

  const svg = d3.select(svgElement)
    .attr('width', width)
    .attr('height', height);

  // Escalas
  const sizeScale = d3.scaleLinear()
    .domain([
      d3.min(graph.nodes, d => +d.averageRating || 0),
      d3.max(graph.nodes, d => +d.averageRating || 1)
    ])
    .range([5, 20]);

  const colorScale = d3.scaleOrdinal()
    .domain([0, 1])
    .range(['#aaa', '#ffd700']);

  const roleColor = role => {
    if (role.includes("director")) return "#1f77b4";
    if (role.includes("writer"))   return "#2ca02c";
    if (role.includes("actor"))    return "#ff6600";
    return "#999";
  };

  // Mapa de roles para tooltips de persona
  const rolesMap = new Map();
  graph.links.forEach(l => {
    [l.source, l.target].forEach(id => {
      if (!rolesMap.has(id)) rolesMap.set(id, new Set());
      l.roles.forEach(r => rolesMap.get(id).add(r));
    });
  });


  const symbol = d3.symbol()
    .size(d => {
      const r = isNaN(d.averageRating) ? 11 : sizeScale(d.averageRating);
      return Math.PI * r * r;
    });

  const simulation = d3.forceSimulation(graph.nodes)
    .force('link', d3.forceLink(graph.links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2));

  const link = svg.append('g')
    .selectAll('line')
    .data(graph.links)
    .join('line')
    .attr('stroke', d => roleColor(d.roles || []))
    .attr('stroke-width', 4);

  const node = svg.append('g')
    .selectAll('path')
    .data(graph.nodes)
    .join('path')
    .attr('d', d =>
      symbol.type(d.bipartite === 'person' ? d3.symbolStar : d3.symbolCircle)(d)
    )
    .attr('fill', d =>
      d.bipartite === 'person'
        ? 'white'
        : colorScale(d.oscarWins > 0 ? 1 : 0)
    )
    .attr('stroke', d => d.id === movieId ? 'red' : null)
    .attr('stroke-width', d => d.id === movieId ? 6 : 0)
    .call(drag(simulation));

  const tooltip = d3.select(tooltipElement);
  node.on('mouseover', (event, d) => {
    let html;
    if (d.bipartite === 'person') {
      const roles = Array.from(rolesMap.get(d.id) || []);
      html = `<strong>Persona</strong><br/>
              ID: ${d.id}<br/>
              Roles: ${roles.length ? roles.join(', ') : 'Ninguno'}`;
    } else {
      html = `<strong>${d.primaryTitle || d.title || 'Untitled'}</strong><br/>
          Won Oscar: ${d.oscarWins > 0 ? 'Yes' : 'No'}<br/>
          Rating: ${d.averageRating || 'N/A'}<br/>
          Genre: ${d.genres || 'N/A'}<br/>
          Director(s): ${d.directors || 'N/A'}`;
    }
    tooltip
      .style('display', 'block')
      .html(html)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY + 10}px`);
  }).on('mouseout', () => tooltip.style('display', 'none'));

  
  simulation.on('tick', () => {
    // 1) Limitar nodos al área del SVG
    graph.nodes.forEach(d => {
      // radio equivalente al tamaño del símbolo
      const r = isNaN(d.averageRating)
        ? 3
        : sizeScale(d.averageRating);
      d.x = Math.max(r, Math.min(width  - r, d.x));
      d.y = Math.max(r, Math.min(height - r, d.y));
    });

    // 2) Actualizar líneas
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    // 3) Actualizar nodos (paths) con translate
    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });
  }



  function drag(simulation) {
    return d3.drag()
      .on('start', event => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', event => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on('end', event => {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      });
  }

  function volver() {
    dispatch('volver');
  }
</script>

<button on:click={volver} 
  style="margin: 1rem 0; 
  background-color: #695a03; 
  padding: 0.5rem 1rem; 
  border: none; 
  cursor: pointer; 
  border-radius: 5px;">
  Back
</button>

<svg bind:this={svgElement} class="film-network"></svg>

<div bind:this={tooltipElement} class="tooltip-network"></div>

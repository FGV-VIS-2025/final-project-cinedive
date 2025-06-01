<script>
  import { onMount } from "svelte";
  import * as d3 from "d3";

  
  let svg;                             // Referencia al <svg>
  let width = 800;                     // Ajusta según contenedor
  let height = 600;
  
  let allNodes = [];                   // Lista completa de nodos
  let allLinks = [];                   // Lista completa de enlaces
  let filteredNodes = [];              // Nodos filtrados por año y colapsados/expand
  let filteredLinks = [];              // Enlaces filtrados por año

  let minYear = 0, maxYear = 0;
  let selectedStart, selectedEnd;      // Valores del time bar

  let genreCenters = {};               // Coordenadas (x,y) para cada género
  let allGenres = [];                  // Lista de géneros únicos

  let simulation;                      // La forceSimulation de D3

  // ------------------------------

  onMount(async () => {
    
    const res = await fetch("static/data/graph_for_project.json");
    const data = await res.json();
    allNodes = data.nodes;
    allLinks = data.links;

    
    const movieYears = allNodes
      .filter(d => d.type === "movie" && d.year != null)
      .map(d => d.year);
    minYear = d3.min(movieYears);
    maxYear = d3.max(movieYears);

    
    selectedStart = minYear;
    selectedEnd = maxYear;
    

    allNodes.forEach(node => {
      if (node.type === "movie") {
        
        node.mainGenre = (node.genres && node.genres.length > 0)
          ? node.genres[0]
          : "Unknown";
      }
    });

    
    const genreSet = new Set(
      allNodes
        .filter(d => d.type === "movie")
        .map(d => d.mainGenre)
    );
    allGenres = Array.from(genreSet);

    
    const radius = Math.min(width, height) / 3;
    const centerX = width / 2;
    const centerY = height / 2;
    allGenres.forEach((g, i) => {
      const angle = (i / allGenres.length) * 2 * Math.PI;
      genreCenters[g] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    
    filtrarPorAño();
  });

  
  function filtrarPorAño() {
    
    if (selectedStart > selectedEnd) {
      [selectedStart, selectedEnd] = [selectedEnd, selectedStart];
    }

    
    const movieIdsEnRango = new Set(
      allNodes
        .filter(d => d.type === "movie" 
                     && d.year != null 
                     && d.year >= selectedStart 
                     && d.year <= selectedEnd)
        .map(d => d.id)
    );

    
    const linksEnRango = allLinks.filter(link => 
      movieIdsEnRango.has(link.target) &&
      link.year != null 
      && link.year >= selectedStart 
      && link.year <= selectedEnd
    );

    
    const personIdsEnRango = new Set(
      linksEnRango.map(link => link.source)
    );

    
    filteredNodes = allNodes.filter(node => {
      if (node.type === "movie") {
        return movieIdsEnRango.has(node.id);
      } else {
        return personIdsEnRango.has(node.id);
      }
    });

    
    filteredLinks = linksEnRango;

    
    redrawForceGraph();
  }

  

  function forceCluster(strength = 0.1) {
    function force(alpha) {
      for (const d of filteredNodes) {
        if (d.type === "movie") {
          const c = genreCenters[d.mainGenre];
          if (c) {
            d.vx += (c.x - d.x) * strength * alpha;
            d.vy += (c.y - d.y) * strength * alpha;
          }
        }
      }
    }
    force.strength = function(_) {
      return arguments.length ? ((strength = +_), force) : strength;
    };
    return force;
  }

  

  function redrawForceGraph() {
    
    d3.select(svg).selectAll("*").remove();

    
    const colorMovie = "#ff8c00";
    const colorPerson = "#1f77b4";

    
    simulation = d3.forceSimulation(filteredNodes)
      .force("link", d3.forceLink(filteredLinks)
        .id(d => d.id)
        .distance(d => (d.source.type === "movie" && d.target.type === "person") ? 60 : 30)
      )
      .force("charge", d3.forceManyBody().strength(-50))
      .force("cluster", forceCluster(0.15))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .on("tick", ticked);

      
    const link = d3.select(svg)
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(filteredLinks)
      .enter()
      .append("line")
        .attr("stroke", "#aaa")
        .attr("stroke-width", 1);

        
    const node = d3.select(svg)
      .append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(filteredNodes)
      .enter()
      .append("circle")
        .attr("r", d => d.type === "movie" ? 8 : 5)
        .attr("fill", d => d.type === "movie" ? colorMovie : colorPerson)
        .call(drag(simulation));

    node.append("title")
      .text(d => d.type === "movie" 
                  ? `${d.title} (${d.year})` 
                  : d.id);

                  
    function ticked() {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    }
  }

  // ------------------------------
  
  function drag(sim) {
    return d3.drag()
      .on("start", (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }
</script>

<style>
  
  .time-bar {
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .time-bar input[type="range"] {
    width: 150px;
  }
  svg {
    border: 1px solid #ddd;
    background: #fafafa;
  }
</style>


<div class="time-bar">
  <label>
    Desde: 
    <input
      type="range"
      min={minYear}
      max={maxYear}
      bind:value={selectedStart}
      on:input={filtrarPorAño}
    />
  </label>

  <label>
    Hasta: 
    <input
      type="range"
      min={minYear}
      max={maxYear}
      bind:value={selectedEnd}
      on:input={filtrarPorAño}
    />
  </label>

  <span>{selectedStart} – {selectedEnd}</span>
</div>

<svg bind:this={svg} width={width} height={height}></svg>

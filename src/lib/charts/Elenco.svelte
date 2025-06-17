<script>
  import { onMount } from 'svelte';
  import { getPersonGraph } from '$lib/utils/dataLoader.js';
  import MultiSelect from '$lib/components/MultiSelect.svelte';
  import { pessoasSelecionadas } from '../../store/people';
  import * as d3 from 'd3';

  export let selectedMovieTitle = null;

  let data = null;
  let subgraphPeople = [];
  let availablePeople = [];

  let svgEl;
  let tooltipDiv;

  const paleta = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
  ];

  $: colorscale = d3.scaleOrdinal().domain(selectedPeople).range(paleta);

  onMount(async () => {
    data = await getPersonGraph();
    buildSubgraphPeople();
  });

  $: if (data && selectedMovieTitle) {
    buildSubgraphPeople();
  }

  function buildSubgraphPeople() {
    if (!data || !selectedMovieTitle) {
      subgraphPeople = [];
      availablePeople = [];
      pessoasSelecionadas.clear();
      return;
    }
    const linksDoFilme = data.links.filter(
      l => l.filmes && l.filmes.includes(selectedMovieTitle)
    );
    const ids = new Set();
    linksDoFilme.forEach(l => {
      ids.add(l.source);
      ids.add(l.target);
    });
    subgraphPeople = data.nodes.filter(n => ids.has(n.id));
    availablePeople = subgraphPeople.map(p => p.name);
    pessoasSelecionadas.clear();
  }

  
  $: selectedPeople = Array.from($pessoasSelecionadas).filter(p => availablePeople.includes(p));

  
  function drag(simulation) {
    return d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }

  // ---- Grafo ----
  $: if (data && selectedMovieTitle && selectedPeople.length > 0 && svgEl && tooltipDiv) {
   
    const selectedNodes = data.nodes.filter(n => selectedPeople.includes(n.name));
    const selectedIds = new Set(selectedNodes.map(n => n.id));

    const links = data.links.filter(
      l => selectedIds.has(l.source) || selectedIds.has(l.target)
    );

    const connectedIds = new Set([...selectedIds]);
    links.forEach(l => {
      connectedIds.add(l.source);
      connectedIds.add(l.target);
    });
    const nodes = data.nodes.filter(n => connectedIds.has(n.id));

    //dibujo 
    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl);
    const width = +svg.attr("width");
    const height = +svg.attr("height");

    const nodeById = new Map(nodes.map(n => [n.id, n]));
    const resolvedLinks = links
      .map(l => ({
        ...l,
        source: nodeById.get(l.source),
        target: nodeById.get(l.target)
      }))
      .filter(l => l.source && l.target);

    // ---- Tooltip HTML overlay ----
    const tip = d3.select(tooltipDiv)
      .style("position", "fixed")
      .style("pointer-events", "none")
      .style("background", "#222")
      .style("color", "#fff")
      .style("padding", "6px 12px")
      .style("border-radius", "8px")
      .style("font-size", "13px")
      .style("opacity", 0)
      .style("z-index", 10000)
      .style("box-shadow", "0 3px 16px rgba(0,0,0,0.35)");

    // Links (tooltip)
    svg.append("g")
      .attr("stroke", "#aaa")
      .selectAll("line")
      .data(resolvedLinks)
      .join("line")
      .attr("stroke-width", 2)
      .on("mouseover", function (event, d) {
        const filmes = d.filmes?.join(', ') || '';
        tip.html(
          `<div><strong>${d.source.name}</strong> &rarr; <strong>${d.target.name}</strong></div>` +
          (filmes ? `<div style="font-size:11px;margin-top:2px;">Filmes: ${filmes}</div>` : '')
        )
        .style("left", (event.clientX + 12) + "px")
        .style("top", (event.clientY - 12) + "px")
        .style("opacity", 1);
      })
      .on("mousemove", function (event) {
        tip
        .style("left", (event.clientX + 12) + "px")
        .style("top", (event.clientY - 12) + "px");
      })
      .on("mouseout", function () {
        tip.style("opacity", 0);
      });

      
    svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", 10)
      .attr("fill", d => selectedPeople.includes(d.name) ? colorscale(d.name) : "#888")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .call(drag(d3.forceSimulation())) // se reasigna abajo igual, no problema
      .on("mouseover", function (event, d) {
        tip.html(
          `<div><strong>${d.name}</strong></div>
           <div style="font-size:11px">${d.type ? d.type : ""}</div>
           <div style="font-size:11px">${d.country ? d.country : ""}</div>`
        )
        .style("left", (event.clientX + 12) + "px")
        .style("top", (event.clientY - 12) + "px")
        .style("opacity", 1);
      })
      .on("mousemove", function (event) {
        tip
        .style("left", (event.clientX + 12) + "px")
        .style("top", (event.clientY - 12) + "px");
      })
      .on("mouseout", function () {
        tip.style("opacity", 0);
      })
      .on("click", (event, d) => {
        pessoasSelecionadas.toggle(d.name);
      });

    svg.append("g")
      .selectAll("text")
      .data(nodes.filter(d => selectedPeople.includes(d.name)))
      .join("text")
      .text(d => d.name)
      .attr("font-size", "11px")
      .attr("dy", "-1.2em")
      .attr("text-anchor", "middle")
      .attr("fill", "#fff");


    // ---- Fuerzas ----
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(resolvedLinks).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2));

      
    svg.selectAll("circle").call(drag(simulation));

    simulation.on("tick", () => {
      nodes.forEach(d => {
        d.x = Math.max(16, Math.min(width - 16, d.x));
        d.y = Math.max(16, Math.min(height - 16, d.y));
      });
      svg.selectAll("line")
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      svg.selectAll("circle")
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
      svg.selectAll("text")
        .attr("x", d => d.x)
        .attr("y", d => d.y - 12);
    });
  }

  let svgTL;

  $: if (data && $pessoasSelecionadas.size > 0 && svgTL) {
  const svg = d3.select(svgTL);
  svg.selectAll("*").remove(); // limpa antes de desenhar

  const selectedSet = $pessoasSelecionadas;

  const width = +svg.attr("width");
  const height = +svg.attr("height");

  const peoples = data.nodes.filter(d => selectedSet.has(d.name));
  let size_i = 0;
  for (let i = 0; i < peoples.length; i++) {
    const person = peoples[i];
    size_i = i;
    if (person.years && person.years.length > 0) {
      for (let j = 0; j < person.years.length; j++) {
        const year = parseInt(person.years[j]);
        if (!isNaN(year)) {
          svg.append("rect")
            .attr("x", 20 * i + 35)  // ajuste aqui se estiver fora da tela
            .attr("y", (year - 1925)*10 +2)
            .attr("width", 20) 
            .attr("height", 10) 
            .attr("fill", colorscale(person.name));
        }
      }
    }
  }
  for (let k = 1925; k < 2025; k++){
    svg.append("text")
    .text(`${k}`)
    .attr("x", 5)
    .attr("y", (k - 1925) * 10 + 12) 
    .attr("font-size", "12px")
    .attr("fill", "#cc8");
  }}
</script>

{#if data && selectedMovieTitle && subgraphPeople.length > 0}
  <div class="container">
    <div class="multiselect-panel">
      <h2>People of the movie</h2>
      <MultiSelect options={availablePeople} />
      <p>Selected people:</p>
      <ul>
        {#each selectedPeople as person}
          <li style="color: {colorscale(person)}">{person}</li>
        {/each}
      </ul>
      <div class="timeline">
          <svg bind:this={svgTL} width={800} height={1010}></svg>
      </div>
      {#if selectedPeople.length === 0}
        <p style="color: #aaa; margin-top: 1em;">Selecione pessoas para visualizar o grafo.</p>
      {/if}
    </div>
    {#if selectedPeople.length > 0}
      <div class="graph-panel" style="position:relative;">
        <svg bind:this={svgEl} width={800} height={600}></svg>
        <div bind:this={tooltipDiv} class="tooltip"></div>
      </div>
    {/if}
    
  </div>
{:else if (data && selectedMovieTitle)}
  <p>Este filme não tem pessoas associadas.</p>
{:else}
  <p>Carregando dados...</p>
{/if}

<style>
  .container {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }
  .multiselect-panel {
    width: 300px;
    flex-shrink: 0;
  }
  .graph-panel {
    flex-grow: 1;
    position: relative;
  }
  .tooltip {
    position: fixed;
    pointer-events: none;
    z-index: 1000;
    transition: opacity 0.13s;
  }
  .timeline {
    max-height: 50vh;          /* altura limitada */
    overflow-y: auto;           /* scroll vertical */
    scrollbar-width: none;      /* Firefox */
    -ms-overflow-style: none;
  }
</style>

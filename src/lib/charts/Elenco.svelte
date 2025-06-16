<script>
  import { onMount } from 'svelte';
  import { getPersonGraph } from '$lib/utils/dataLoader.js';
  import MultiSelect from '$lib/components/MultiSelect.svelte';
  import { pessoasSelecionadas } from '../../store/people';
  import * as d3 from 'd3';

  export let selectedMovieId = null;

  let svgEl;
  let data = null;
  let pessoasDoFilme = [];
  let availablePeople = [];

  // Carga inicial
  onMount(async () => {
    data = await getPersonGraph();
    filtrarPorFilme();
  });

  // Refiltar cada vez que cambia la peli o los datos
  $: if (data && selectedMovieId) {
    filtrarPorFilme();
  }

  function filtrarPorFilme() {
    if (!data || !selectedMovieId) {
      pessoasDoFilme = [];
      availablePeople = [];
      return;
    }
    // Opción 1: Si las personas tienen campo movies (más eficiente)
    if (data.nodes.some(n => n.type === "person" && Array.isArray(n.movies))) {
      pessoasDoFilme = data.nodes.filter(
        p => p.type === "person" && p.movies && p.movies.includes(selectedMovieId)
      );
    } else {
      // Opción 2: Filtra por links
      pessoasDoFilme = data.nodes.filter(
        p => p.type === "person" &&
          data.links.some(
            l =>
              (l.source === selectedMovieId && l.target === p.id) ||
              (l.target === selectedMovieId && l.source === p.id)
          )
      );
    }
    availablePeople = pessoasDoFilme.map(p => p.name);
    pessoasSelecionadas.clear();
  }

  // Personas seleccionadas (solo de este filme)
  $: selectedPeople = Array.from($pessoasSelecionadas).filter(p => availablePeople.includes(p));

  // Paleta para D3
  const paleta = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
  ];
  $: colorscale = d3.scaleOrdinal()
    .domain(selectedPeople)
    .range(paleta);

  // Grafo D3
  $: if (data && selectedMovieId && svgEl) {
    // Nodo de la película
    const movieNode = data.nodes.find(n => n.id === selectedMovieId);
    // Links directos entre peli y personas del filme
    const links = data.links.filter(
      l =>
        (l.source === selectedMovieId && pessoasDoFilme.some(p => p.id === l.target)) ||
        (l.target === selectedMovieId && pessoasDoFilme.some(p => p.id === l.source))
    );
    // Nodos: la peli y solo las personas asociadas
    const nodes = movieNode ? [movieNode, ...pessoasDoFilme] : [...pessoasDoFilme];

    // Limpia SVG
    d3.select(svgEl).selectAll('*').remove();
    const svg = d3.select(svgEl);
    const width = +svg.attr("width");
    const height = +svg.attr("height");

    const nodeById = new Map(nodes.map(n => [n.id, n]));
    const resolvedLinks = links.map(l => ({
      ...l,
      source: nodeById.get(l.source),
      target: nodeById.get(l.target)
    }));

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(resolvedLinks).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Links
    svg.append("g")
      .attr("stroke", "#aaa")
      .selectAll("line")
      .data(resolvedLinks)
      .join("line")
      .attr("stroke-width", 2);

    // Nodes
    svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", d => d.type === "movie" ? 18 : 10)
      .attr("fill", d =>
        d.type === "movie" ? "#d4af37" : (selectedPeople.includes(d.name) ? colorscale(d.name) : "#888")
      )
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .on("click", (event, d) => {
        if (d.type === "person") pessoasSelecionadas.toggle(d.name);
      });

    // Etiquetas
    svg.append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text(d => d.type === "movie" ? d.title ?? d.name : d.name)
      .attr("font-size", d => d.type === "movie" ? "16px" : "11px")
      .attr("font-weight", d => d.type === "movie" ? "bold" : "normal")
      .attr("dy", "-1.2em")
      .attr("text-anchor", "middle");

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
        .attr("y", d => d.y - (d.type === "movie" ? 20 : 12));
    });
  }
</script>

{#if data && selectedMovieId && pessoasDoFilme.length > 0}
  <div class="container">
    <div class="graph-panel">
      <svg bind:this={svgEl} width={800} height={600}></svg>
    </div>
    <div class="multiselect-panel">
      <h2>Pessoas do filme</h2>
      <MultiSelect options={availablePeople} />
      <p>Pessoas selecionadas:</p>
      <ul>
        {#each selectedPeople as person}
          <li style="color: {colorscale(person)}">{person}</li>
        {/each}
      </ul>
    </div>
  </div>
{:else if (data && selectedMovieId)}
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
  }
</style>

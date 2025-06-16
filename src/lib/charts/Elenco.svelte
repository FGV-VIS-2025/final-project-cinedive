<script>
  import { onMount } from 'svelte';
  import { getPersonGraph } from '$lib/utils/dataLoader.js';
  import MultiSelect from '$lib/components/MultiSelect.svelte';  // Importe o componente
  import { pessoasSelecionadas } from '../../store/people';  // Importe o store para controle de pessoas selecionadas
  import { derived } from 'svelte/store';
  import * as d3 from 'd3'; //comentario para pull request

  let svgEl;
  let data = null;
  let availablePeople;

  // Carregar os dados ao montar
  onMount(async () => {
    data = await getPersonGraph();
    if (data?.nodes) {
      availablePeople = [...new Set(data.nodes.map(person => person.name).filter(Boolean))];
      console.log(availablePeople)
    }
  });

  // Lista de pessoas selecionadas já existe no store `pessoasSelecionadas`
  $: selectedPeople = Array.from($pessoasSelecionadas);


  $: if (data && $pessoasSelecionadas.size > 0 && svgEl) {
    const selectedSet = $pessoasSelecionadas;

    const selectedNodeIds = data.nodes
      .filter(n => selectedSet.has(n.name))
      .map(n => n.id);

    const links = data.links.filter(
      l => selectedNodeIds.includes(l.source) || selectedNodeIds.includes(l.target)
    );

    const connectedIds = new Set();
    links.forEach(link => {
      connectedIds.add(link.source);
      connectedIds.add(link.target);
    });

    const allRelevantIds = new Set([...selectedNodeIds, ...connectedIds]);

    const nodes = data.nodes.filter(n => allRelevantIds.has(n.id));


    // Limpa SVG
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
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("x", d3.forceX(width / 2).strength(0.02))
    .force("y", d3.forceY(height / 2).strength(0.02));

    const tooltipGroup = svg.append("g")
    .style("display", "none");

    const tooltipBackground = tooltipGroup.append("rect")
    .attr("fill", "black")
    .attr("rx", 4)
    .attr("ry", 4)
    .attr("opacity", 0.8);

    const tooltipText = tooltipGroup.append("text")
    .attr("fill", "white")
    .attr("font-size", "12px")
    .attr("x", 5)
    .attr("y", 15);

    const link = svg.append("g")
        .attr("stroke", "#aaa")
        .selectAll("line")
        .data(resolvedLinks)
        .join("line")
        .attr("stroke-width", d => {
            return (Array.isArray(d.filmes) ? d.filmes.length : 1)
        }
        )
        .on("mouseover", (event, d) => {
            tooltipText.text(`${d.source.name} → ${d.target.name }`);
            const textBBox = tooltipText.node().getBBox();

            tooltipBackground
            .attr("width", textBBox.width + 10)
            .attr("height", textBBox.height + 6);

            tooltipGroup.style("display", "block");
        })
        .on("mousemove", (event) => {
            const [x, y] = d3.pointer(event);

            tooltipGroup.attr("transform", `translate(${x + 10}, ${y - 20})`);
        })
        .on("mouseout", () => {
            tooltipGroup.style("display", "none");
        });

    const node = svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 0)
        .selectAll("circle")
        .data(nodes)
        .join("circle")
        .attr("r", 8)
        .attr("fill", d => selectedSet.has(d.id) ? "gold" : "#888")
        .call(drag(simulation))
        .on("click", (event, d) => {
            pessoasSelecionadas.toggle(d.name);
        });

    const label = svg.append("g")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .text(d => d.name)
        .attr("font-size", "10px")
        .attr("dy", "-0.9em");

    simulation.on("tick", () => {
        nodes.forEach(d => {
            d.x = Math.max(8, Math.min(width - 8, d.x));
            d.y = Math.max(8, Math.min(height - 8, d.y));
        });

        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
        });

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
  }

    

</script>

<!-- Usando o MultiSelect no HTML -->
{#if data && availablePeople.length > 0}
  <div class="container">
    <!-- Painel da multiseleção -->
    <div class="multiselect-panel">
      <h2>Selecione as pessoas</h2>
      <MultiSelect options={availablePeople} />

      <!-- Lista de selecionados -->
      <p>Pessoas selecionadas:</p>
      <ul>
        {#each selectedPeople as person}
          <li>{person}</li>
        {/each}
      </ul>
    </div>

    <!-- Painel do grafo -->
    <div class="graph-panel">
      <svg bind:this={svgEl} width={800} height={600}></svg>
    </div>
  </div>
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
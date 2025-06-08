<script>
  import { onMount, afterUpdate } from 'svelte';
  import * as d3 from 'd3';

  export let data = [];
  export let width = 500;

  let svgEl;

  function draw() {
    if (!data || data.length === 0) return;

    const cleaned = data.filter(d => !isNaN(d.numVotes) && !isNaN(d.runtimeMinutes));

    const height = width;
    const margin = 40;
    const radius = (width - 2 * margin) / 2;
    const centerX = width / 2;
    const centerY = height / 2;

    const angle = d3.scaleLinear()
      .domain(d3.extent(cleaned, d => +d.runtimeMinutes))
      .range([0, 2 * Math.PI]);

    const r = d3.scaleSqrt() // sqrt para espalhar melhor os valores
      .domain([0, d3.max(cleaned, d => +d.numVotes)])
      .range([10, radius]);

    const svg = d3.select(svgEl)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove();

    const g = svg.append("g")
      .attr("transform", `translate(${centerX}, ${centerY})`);

    // Eixos circulares (raio)
    const gr = g.append("g").attr("class", "r axis");
    const rTicks = r.ticks(5);
    gr.selectAll("circle")
      .data(rTicks)
      .join("circle")
      .attr("r", d => r(d))
      .attr("fill", "none")
      .attr("stroke", "#ccc");

    gr.selectAll("text")
      .data(rTicks)
      .join("text")
      .attr("y", d => -r(d))
      .attr("dy", "-0.35em")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text(d => d);

    // Eixos angulares (linhas radiais para tempo)
    const aTicks = angle.ticks(8);
    const ga = g.append("g").attr("class", "angle axis");
    ga.selectAll("line")
      .data(aTicks)
      .join("line")
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", d => Math.cos(angle(d) - Math.PI / 2) * radius)
      .attr("y2", d => Math.sin(angle(d) - Math.PI / 2) * radius)
      .attr("stroke", "#ccc");

    ga.selectAll("text")
      .data(aTicks)
      .join("text")
      .attr("x", d => Math.cos(angle(d) - Math.PI / 2) * (radius + 10))
      .attr("y", d => Math.sin(angle(d) - Math.PI / 2) * (radius + 10))
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .text(d => d);

    // Pontos
    g.selectAll("circle.dot")
      .data(cleaned)
      .join("circle")
      .attr("class", "dot")
      .attr("cx", d => Math.cos(angle(d.runtimeMinutes) - Math.PI / 2) * r(d.numVotes))
      .attr("cy", d => Math.sin(angle(d.runtimeMinutes) - Math.PI / 2) * r(d.numVotes))
      .attr("r", 3)
      .attr("fill", "#69b3a2")
      .attr("opacity", 0.7);
  }

  onMount(draw);
  afterUpdate(draw);
</script>

<svg bind:this={svgEl}></svg>

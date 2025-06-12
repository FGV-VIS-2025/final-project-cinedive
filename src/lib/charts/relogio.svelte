<script>
  import { onMount, afterUpdate } from 'svelte';
  import * as d3 from 'd3';
  import { hexbin as d3Hexbin } from 'd3-hexbin';

  export let data = [];
  export let width = 500;

  let svgEl;

  // criando função de select feature
  const featureOptions = [
    "startYear",
    "runtimeMinutes",
    "averageRating",
    "numVotes",
  ];

  let angleFeature = "runtimeMinutes";
  let radiusFeature = "numVotes";

function polarToCartesian(theta, r) {
  return [
    Math.cos(theta - Math.PI / 2) * r,
    Math.sin(theta - Math.PI / 2) * r
  ];
}
  

  function draw() {
    if (!data || data.length === 0) return;

    const cleaned = data.filter(d => !isNaN(d[radiusFeature]) && !isNaN(d[angleFeature]));

    const height = width;
    const margin = 40;
    const radius = (width - 2 * margin) / 2;
    const centerX = width / 2;
    const centerY = height / 2;

    const angle = d3.scaleLinear()
      .domain(d3.extent(cleaned, d => +d[angleFeature]))
      .range([0, 2 * Math.PI]);

    const r = d3.scaleSqrt() // sqrt para espalhar melhor os valores
      .domain([0, d3.max(cleaned, d => +d[radiusFeature])])
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

    const points = cleaned.map(d => {
      const a = angle(+d[angleFeature]);
      const rad = r(+d[radiusFeature]);
      const [x, y] = polarToCartesian(a, rad);
      return { x, y };
    });

    const hexbin = d3Hexbin()
      .x(d => d.x)
      .y(d => d.y)
      .radius(10) // ajuste conforme necessário
      .extent([[-radius, -radius], [radius, radius]]);

    const bins = hexbin(points);

    const color = d3.scaleSequential(d3.interpolateYlGnBu)
      .domain([0, d3.max(bins, b => b.length)]);


    g.append("g")
      .attr("class", "density")
      .selectAll("path")
      .data(bins)
      .join("path")
      .attr("d", d => `M${d.x},${d.y}${hexbin.hexagon()}`)
      .attr("fill", d => color(d.length))
      .attr("stroke", "none")
      .attr("opacity", 0.6);

    // Pontos
    g.selectAll("circle.dot")
      .data(cleaned)
      .join("circle")
      .attr("class", "dot")
      .attr("cx", d => Math.cos(angle(d[angleFeature]) - Math.PI / 2) * r(d[radiusFeature]))
      .attr("cy", d => Math.sin(angle(d[angleFeature]) - Math.PI / 2) * r(d[radiusFeature]))
      .attr("r", 3)
      .attr("fill", "#69b3a2")
      .attr("opacity", 0.7);
  }

  onMount(draw);
  afterUpdate(draw);
</script>

<!-- Seletor de Features -->
<div style="margin-bottom: 1rem;">
  <label>
    Ângulo:
    <select bind:value={angleFeature}>
      {#each featureOptions as feature}
        <option value={feature}>{feature}</option>
      {/each}
    </select>
  </label>

  <label style="margin-left: 1rem;">
    Raio:
    <select bind:value={radiusFeature}>
      {#each featureOptions as feature}
        <option value={feature}>{feature}</option>
      {/each}
    </select>
  </label>
</div>

<svg bind:this={svgEl}></svg>

<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data = [];
  export let width = 800;

  let svgEl;

  onMount(() => {
    if (!data || data.length === 0) return;

    const top10 = [...data]
      .filter(d => !isNaN(d.numVotes))
      .sort((a, b) => d3.descending(a.numVotes, b.numVotes))
      .slice(0, 10);

    const height = top10.length * 40 + 60;
    const margin = { top: 30, right: 20, bottom: 40, left: 200 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    svg.selectAll('*').remove(); // limpa antes de desenhar

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
      .domain([0, d3.max(top10, d => d.numVotes)])
      .range([0, innerWidth])
      .nice();

    const y = d3.scaleBand()
      .domain(top10.map(d => d.primaryTitle))
      .range([0, innerHeight])
      .padding(0.1);

    // Eixo X
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x));

    // Eixo Y
    g.append('g')
      .call(d3.axisLeft(y).tickSize(0))
      .selectAll('text')
      .style('font-size', '12px');

    // Barras
    g.selectAll('rect')
      .data(top10)
      .join('rect')
      .attr('y', d => y(d.primaryTitle))
      .attr('height', y.bandwidth())
      .attr('x', 0)
      .attr('width', d => x(d.numVotes))
      .attr('fill', '#69b3a2');

    // Texto nos finais das barras
    g.selectAll('text.bar-label')
      .data(top10)
      .join('text')
      .attr('class', 'bar-label')
      .attr('x', d => x(d.numVotes) + 4)
      .attr('y', d => y(d.primaryTitle) + y.bandwidth() / 2 + 4)
      .text(d => d.numVotes)
      .style('fill', '#fff')
      .style('font-size', '11px');
  });
</script>

<svg bind:this={svgEl}></svg>

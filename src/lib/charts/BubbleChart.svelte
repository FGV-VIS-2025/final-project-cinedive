<!-- src/lib/charts/BubbleChart.svelte -->
<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import * as d3 from 'd3';

  export let fullData = [];
  export let data = [];

  export let highlightedMovieId = null;

  const dispatch = createEventDispatcher();

  // Constantes
  const M  = { top: 20, right: 40, bottom: 50, left: 60 };
  const W  = 1000;
  const H  = 700;
  const IW = W - M.left - M.right;
  const IH = H - M.top  - M.bottom;

  // Escalas
  const xScale  = d3.scaleLinear().range([0, IW]);
  const radiusScale  = d3.scaleSqrt().range([3, 20]);
  const colorScale  = d3.scaleOrdinal().domain([0, 1]).range(['#aaa', '#ffd700']);

  // Variáveis de DOM
  let svgEl, tipEl, g, xAxis;

  const layout = new Map();
  let layoutReady = false;

  // Desenho estático (eixo, rótulos, etc.)
  let mounted = false;
  onMount(() => {
    mounted = true;
    const svg = d3.select(svgEl).attr('viewBox', `0 0 ${W} ${H}`);

    g      = svg.append('g').attr('transform', `translate(${M.left},${M.top})`);
    xAxis  = g.append('g').attr('class', 'x-axis')
               .attr('transform', `translate(0,${IH})`);

    g.append('text')
      .attr('class', 'x-label')
      .attr('x', IW / 2)
      .attr('y', IH + 40)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ffd700')
      .text('Average Rating (IMDb)');
  });

  $: if (fullData.length && !layoutReady && mounted) {
    computeLayout(fullData);    // RODA UMA VEZ
    layoutReady = true;
  }

  $: if (layoutReady && data.length) {
    drawChart(data);                 // Só redesenha
  }

  $: if (layoutReady && data.length && highlightedMovieId !== undefined) {
    drawChart(data); // força redesenho quando highlightedMovieId muda
  }

  function computeLayout(all) {
    // Domínios tirados do universo completo (fixos)
    xScale.domain(d3.extent(all, d => +d.averageRating)).nice();
    radiusScale.domain(d3.extent(all, d => +d.numVotes));

    const sim = d3.forceSimulation(all)
      .force('x', d3.forceX(d => xScale(+d.averageRating)).strength(1))
      .force('y', d3.forceY(IH / 2).strength(0.05))
      .force('collide', d3.forceCollide(d => radiusScale(+d.numVotes) + 1))
      .stop();

    sim.tick(500);

    // Guarda posição e raio no cache
    all.forEach(d => layout.set(d.tconst, {
      x: d.x,
      y: d.y,
      r: radiusScale(+d.numVotes)
    }));
  }

  function drawChart(crr) {
    if (!g || !xAxis) {
      console.warn("Tentou desenhar antes do DOM estar montado.");
      return;
    }

    xAxis.call(d3.axisBottom(xScale));

    const selection = g.selectAll('circle')
      .data(crr, d => d.tconst)
      .join(
        enter => enter.append('circle')
          .attr('class', d => `bubble ${d.tconst === highlightedMovieId ? 'highlighted' : ''}`)
          .attr('stroke', '#333')
          .attr('stroke-width', .5)
          .attr('fill', d => colorScale(d.oscarWins > 0 ? 1 : 0))
          .attr('r', 0)
          .style('opacity', d => highlightedMovieId ? (d.tconst === highlightedMovieId ? 1 : 0.2) : 0.85)
          .on('mouseover', handleOver)
          .on('mouseout', () => d3.select(tipEl).style('display','none'))
          .on('click', (e,d) => dispatch('movieSelected', { id: d.tconst, data: d }))
          .call(sel => sel.transition().duration(250)
            .attr('r', d => layout.get(d.tconst).r)),
        update => update
          .attr('class', d => `bubble ${d.tconst === highlightedMovieId ? 'highlighted' : ''}`)
          .attr('fill', d => colorScale(d.oscarWins > 0 ? 1 : 0))
          .style('opacity', d => highlightedMovieId ? (d.tconst === highlightedMovieId ? 1 : 0.2) : 0.85),
        exit => exit.transition().duration(250).attr('r', 0).remove()
      );

    selection
      .attr('cx', d => layout.get(d.tconst).x)
      .attr('cy', d => layout.get(d.tconst).y);

    if (highlightedMovieId) {
      g.selectAll('circle')
        .filter(d => d.tconst === highlightedMovieId)
        .each(function() { this.parentNode.appendChild(this); });
    }
  }

  // Tooltip
  function handleOver(event, d) {
    d3.select(tipEl)
      .style('display', 'block')
      .html(`<strong>${d.primaryTitle}</strong>`)
      .style('left', `${event.pageX + 10}px`)
      .style('top',  `${event.pageY + 10}px`);
  }
</script>

<div class="chart-container">
  <svg bind:this={svgEl} class="bubble-chart"></svg>
  <div bind:this={tipEl} class="tooltip-bubble" style="position:absolute;display:none;"></div>
</div>

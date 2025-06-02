<!-- src/lib/charts/BarChart.svelte -->
<script>
    import { onMount, afterUpdate } from 'svelte';
    import * as d3 from 'd3';
    import '$lib/styles/barchart.css';

    export let data = [];
    export let labels = [];
    
    const chartConfig = {
        width: 550,
        height: 380,
        margin: { top: 25, right: 20, bottom: 80, left: 45 }
    };

    const { width, height, margin } = chartConfig;
    const innerWidth  = width  - margin.left - margin.right;
    const innerHeight = height - margin.top  - margin.bottom;
    
    let tooltip;

    let barsGroup, xAxisGroup, yAxisGroup;
    let xScale = d3.scaleBand().range([0, innerWidth]).padding(0.1);
    let yScale = d3.scaleLinear().range([innerHeight, 0]);

    function drawChart() {
        console.log('drawChart() em barchart.svelte');
        if (!labels.length || !data.length || !barsGroup){
            console.log('Erro: labels ou data vazios ou barsGroup não definido.');
            return;
        }

        const tooltipG = d3.select(tooltip);

        xScale.domain(labels);
        yScale.domain([0, d3.max(data, d => d) + 20]);
        
        const bars = d3.select(barsGroup).selectAll('rect').data(data);

        bars.exit()
            .transition().duration(600)
            .attr('y', innerHeight)
            .attr('height', 0)
            .remove();
            
        const barsEnter = bars.enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', (_, i) => xScale(labels[i]))
            .attr('y', innerHeight)
            .attr('width', xScale.bandwidth())
            .attr('height', 0);
        
        const allBars = barsEnter.merge(bars);

        allBars.
            on('mouseover', (event, d) => {
                tooltipG
                .style('display', 'block')
                .html(`Value: <strong>${d}</strong>`);
            })
            .on('mousemove', (event) => {
                tooltipG
                .style('left', `${event.pageX + 10}px`)
                .style('top',  `${event.pageY - 28}px`);
            })
            .on('mouseout', () => {
                tooltipG.style('display', 'none');
            });

        allBars
            .transition().duration(600)
                .attr('x', (_, i) => xScale(labels[i]))
                .attr('y', d => yScale(d))
                .attr('width', xScale.bandwidth())
                .attr('height', d => innerHeight - yScale(d));
        
        d3.select(xAxisGroup)
            .transition().duration(600)
            .call(d3.axisBottom(xScale))
            .selectAll('text')
                .attr('transform', 'rotate(-45)')
                .style('text-anchor', 'end')
                .attr('dx', '-0.5em')
                .attr('dy', '0.25em');

        d3.select(yAxisGroup)
            .transition().duration(600)
            .call(d3.axisLeft(yScale));
    }

    onMount(() => {
        drawChart();
    });

    afterUpdate(drawChart);
</script>

<div bind:this={tooltip} class="tooltip"></div>

<svg {width} {height}>
    <g
      bind:this={barsGroup}
      transform={`translate(${margin.left},${margin.top})`}
    ></g>
    
    <g
      bind:this={xAxisGroup}
      class="x-axis"
      transform={`translate(${margin.left},${margin.top + innerHeight})`}
    ></g>

    <g
      bind:this={yAxisGroup}
      class="y-axis"
      transform={`translate(${margin.left},${margin.top})`}
    ></g>
</svg>
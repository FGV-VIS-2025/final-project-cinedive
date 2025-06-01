<!-- src/lib/charts/HBarChart.svelte -->
<script>
    import { onMount, afterUpdate } from 'svelte';
    import * as d3 from 'd3';

    export let data = [];
    export let labels = [];
    export let title   = '';
    export let xLabel  = '';
    export let yLabel  = '';

    const chartConfig = {
        width: 550,
        height: 380,
        margin: { top: 25, right: 20, bottom: 60, left: 100 }
    };

    const { width, height, margin } = chartConfig;
    const innerWidth  = width  - margin.left - margin.right;
    const innerHeight = height - margin.top  - margin.bottom;

    let tooltipEl;
    let barsGroup, xAxisGroup, yAxisGroup;
    let yScale = d3.scaleBand().range([0, innerHeight]).padding(0.1);
    let xScale = d3.scaleLinear().range([0, innerWidth]);

    function drawChart() {
        if (!labels.length || !data.length || !barsGroup) return;

        const tooltip = d3.select(tooltipEl);

        yScale.domain(labels);
        xScale.domain([0, d3.max(data, d => d) + 100]);

        const bars = d3.select(barsGroup).selectAll('rect').data(data);

        bars.exit()
            .transition().duration(600)
            .attr('x', 0)
            .attr('width', 0)
            .remove();

        const barsEnter = bars.enter()
            .append('rect')
            .attr('class', 'bar-hbar')
            .attr('x', 0)
            .attr('y', (_, i) => yScale(labels[i]))
            .attr('width', 0)
            .attr('height', yScale.bandwidth());

        const allBars = barsEnter.merge(bars);

        allBars
            .on('mouseover', (event, d) => {
                tooltip
                    .style('display', 'block')
                    .html(`Value: <strong>${d}</strong>`);
            })
            .on('mousemove', (event) => {
                tooltip
                    .style('left', `${event.pageX + 10}px`)
                    .style('top', `${event.pageY - 28}px`);
            })
            .on('mouseout', () => {
                tooltip.style('display', 'none');
            });

        allBars
            .transition().duration(600)
            .attr('x', 0)
            .attr('y', (_, i) => yScale(labels[i]))
            .attr('width', d => xScale(d))
            .attr('height', yScale.bandwidth());

        d3.select(xAxisGroup)
            .transition().duration(600)
            .call(d3.axisBottom(xScale));

        d3.select(yAxisGroup)
            .transition().duration(600)
            .call(d3.axisLeft(yScale));
    }

    onMount(drawChart);
    afterUpdate(drawChart);
</script>

<div bind:this={tooltipEl} class="tooltip-hbar"></div>

<svg {width} {height} class="hbar-chart">
    <text
        class="chart-title"
        x={width / 2}
        y={margin.top / 2}
    >{title}</text>

    <text
        class="axis-label axis-label-x"
        x={margin.left + innerWidth / 2}
        y={margin.top + innerHeight + margin.bottom - 10}
    >{xLabel}</text>

    <text
        class="axis-label axis-label-y"
        x={-(margin.top + innerHeight / 2)}
        y={margin.left / 2 - 30}
        transform="rotate(-90)"
    >{yLabel}</text>

    <g bind:this={barsGroup} transform={`translate(${margin.left},${margin.top})`}></g>
    <g bind:this={xAxisGroup} class="x-axis" transform={`translate(${margin.left},${margin.top + innerHeight})`}></g>
    <g bind:this={yAxisGroup} class="y-axis" transform={`translate(${margin.left},${margin.top})`}></g>
</svg>

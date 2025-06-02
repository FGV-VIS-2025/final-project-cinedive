<script>
	import { onMount, tick } from 'svelte';
	import * as d3 from 'd3';

	export let loadMoviesFullData;

	let container;
	let data = [];
	let heatmapData = [];
	let loading = true;
	let selectedMovies = []; // Armazena filmes da célula clicada

	// Configurações do heatmap
	const margin = { top: 60, right: 100, bottom: 80, left: 80 };
	const width = 800 - margin.left - margin.right;
	const height = 600 - margin.top - margin.bottom;

	// Escala de cor (logarítmica)
	const colorScale = d3.scaleSequential(d3.interpolateYlOrRd);

	onMount(async () => {
		try {
			data = await loadMoviesFullData();
			loading = false;
			await tick(); // Aguarda o DOM atualizar após carregar os dados

			processData();
			createHeatmap();
		} catch (error) {
			console.error('Erro ao carregar dados:', error);
			loading = false;
		}
	});

	function processData() {
		// Filtra dados válidos e agrupa por «nominations-wins», guardando arrays de filmes
		const validData = data.filter(d =>
			d.oscarNominations >= 0 &&
			d.oscarWins >= 0 &&
			!isNaN(d.oscarNominations) &&
			!isNaN(d.oscarWins)
		);

		// Map<string, { movies: Array<obj>, count: number }>
		const groupedMap = new Map();

		validData.forEach(d => {
			const key = `${d.oscarNominations}-${d.oscarWins}`;
			if (!groupedMap.has(key)) {
				groupedMap.set(key, { movies: [], count: 0 });
			}
			const entry = groupedMap.get(key);
			entry.movies.push(d);
			entry.count = entry.movies.length;
		});

		// Determina valores máximos para escalas
		const maxNominations = d3.max(validData, d => d.oscarNominations) || 14;
		const maxWins = d3.max(validData, d => d.oscarWins) || 10;

		// Converte para array de objetos para o heatmap, incluindo lista de filmes
		heatmapData = [];
		for (let nominations = 0; nominations <= maxNominations; nominations++) {
			for (let wins = 0; wins <= Math.min(maxWins, nominations); wins++) {
				const key = `${nominations}-${wins}`;
				if (groupedMap.has(key)) {
					const entry = groupedMap.get(key);
					heatmapData.push({
						nominations,
						wins,
						count: entry.count,
						movies: entry.movies // array de objetos de filmes
					});
				}
			}
		}

		// Configura a escala de cor em base logarítmica (mínimo de 1)
		const maxCount = d3.max(heatmapData, d => d.count) || 1;
		colorScale.domain([Math.log(1), Math.log(maxCount)]);
	}

	function createHeatmap() {
		if (!heatmapData.length) return;

		// Limpa o container antes de desenhar
		d3.select(container).selectAll('*').remove();

		// Cria SVG
		const svg = d3.select(container)
			.append('svg')
			.attr('width', width + margin.left + margin.right)
			.attr('height', height + margin.top + margin.bottom);

		const g = svg.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`);

		// Escalas para eixos
		const nominations = [...new Set(heatmapData.map(d => d.nominations))].sort((a, b) => a - b);
		const wins = [...new Set(heatmapData.map(d => d.wins))].sort((a, b) => a - b);

		const xScale = d3.scaleBand()
			.domain(nominations)
			.range([0, width])
			.padding(0.1);

		const yScale = d3.scaleBand()
			.domain(wins.reverse()) // inverte para números menores estarem embaixo
			.range([0, height])
			.padding(0.1);

		// Remove tooltips anteriores
		d3.selectAll('.heatmap-tooltip').remove();

		// Tooltip (apenas exibição de contagem: indicações/vitórias/quantidade)
		const tooltip = d3.select('body').append('div')
			.attr('class', 'heatmap-tooltip')
			.style('opacity', 0)
			.style('position', 'absolute')
			.style('background', 'rgba(0, 0, 0, 0.8)')
			.style('color', 'white')
			.style('padding', '8px')
			.style('border-radius', '4px')
			.style('font-size', '12px')
			.style('pointer-events', 'none')
			.style('z-index', '1000');

		// Desenha as células
		const cells = g.selectAll('.cell')
			.data(heatmapData)
			.enter().append('rect')
			.attr('class', 'cell')
			.attr('x', d => xScale(d.nominations) ?? 0)
			.attr('y', d => yScale(d.wins) ?? 0)
			.attr('width', xScale.bandwidth())
			.attr('height', yScale.bandwidth())
			.attr('fill', d => colorScale(Math.log(d.count)))
			.attr('stroke', '#fff')
			.attr('stroke-width', 1)
			.style('cursor', 'pointer');

		// Interações: hover para tooltip e clique para lista de filmes
		cells
			.on('mouseover', function(event, d) {
				d3.select(this).attr('stroke', '#333').attr('stroke-width', 2);
				tooltip.transition().duration(200).style('opacity', .9);
				tooltip.html(`
					<strong>Indicações:</strong> ${d.nominations}<br/>
					<strong>Vitórias:</strong> ${d.wins}<br/>
					<strong>Filmes:</strong> ${d.count}
				`)
					.style('left', (event.pageX + 10) + 'px')
					.style('top', (event.pageY - 28) + 'px');
			})
			.on('mouseout', function() {
				d3.select(this).attr('stroke', '#fff').attr('stroke-width', 1);
				tooltip.transition().duration(500).style('opacity', 0);
			})
			.on('click', function(event, d) {
        // 1) Remove 'selected' de todas as células (volta ao estado padrão)
        d3.selectAll('.cell')
          .classed('selected', false)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1);

        // 2) Marca somente a célula clicada
        d3.select(this)
          .classed('selected', true)
          .attr('stroke', '#000')
          .attr('stroke-width', 3);

				// 3) Atualiza a lista de filmes
				selectedMovies = d.movies.slice().sort((a, b) => b.startYear - a.startYear);
			});

		// Eixo X (Indicações)
		const xAxis = d3.axisBottom(xScale);
		g.append('g')
			.attr('transform', `translate(0,${height})`)
			.call(xAxis)
			.selectAll('text')
			.style('font-size', '12px');

		// Eixo Y (Vitórias)
		const yAxis = d3.axisLeft(yScale);
		g.append('g')
			.call(yAxis)
			.selectAll('text')
			.style('font-size', '12px');

		// Rótulos dos eixos
		g.append('text')
			.attr('transform', `translate(${width/2}, ${height + 50})`)
			.style('text-anchor', 'middle')
			.style('font-size', '14px')
			.style('font-weight', 'bold')
			.text('Número de Indicações ao Oscar');

		g.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('y', -50)
			.attr('x', -height/2)
			.style('text-anchor', 'middle')
			.style('font-size', '14px')
			.style('font-weight', 'bold')
			.text('Número de Vitórias no Oscar');

		// Título geral
		svg.append('text')
			.attr('x', (width + margin.left + margin.right) / 2)
			.attr('y', 30)
			.attr('text-anchor', 'middle')
			.style('font-size', '18px')
			.style('font-weight', 'bold')
			.text('Heatmap: Vitórias vs Indicações ao Oscar');

		// Legenda do heatmap
		const legendWidth = 25;
		const legendHeight = 250;
		const maxCount = d3.max(heatmapData, d => d.count);

		const chartCenterY = margin.top + height / 2;
		const legendY = chartCenterY - legendHeight / 2;

		const legend = svg.append('g')
			.attr('transform', `translate(${width + margin.left + 20}, ${legendY})`);

		const defs = svg.append('defs');
		const gradient = defs.append('linearGradient')
			.attr('id', 'legend-gradient')
			.attr('x1', '0%')
			.attr('y1', '100%')
			.attr('x2', '0%')
			.attr('y2', '0%');

		const steps = 5;
		for (let i = 0; i <= steps; i++) {
			const valorLog = Math.log(1) + (i / steps) * (Math.log(maxCount) - Math.log(1));
			gradient.append('stop')
				.attr('offset', `${(i / steps) * 100}%`)
				.attr('stop-color', colorScale(valorLog));
		}

		legend.append('rect')
			.attr('width', legendWidth)
			.attr('height', legendHeight)
			.style('fill', 'url(#legend-gradient)')
			.attr('stroke', '#ccc');

		const legendScale = d3.scaleLog()
			.domain([1, maxCount])
			.range([legendHeight, 0]);

		const legendAxis = d3.axisRight(legendScale)
			.ticks(5, "~s");

		legend.append('g')
			.attr('transform', `translate(${legendWidth}, 0)`)
			.call(legendAxis)
			.selectAll('text')
			.style('font-size', '10px');

		legend.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('y', -10)
			.attr('x', -legendHeight/2)
			.style('text-anchor', 'middle')
			.style('font-size', '12px')
			.text('Nº Filmes');
	}
</script>

<div class="heatmap-container">
	{#if loading}
		<div class="loading">
			<p>Carregando dados...</p>
		</div>
	{:else}
		<!-- Contêiner possui display flex: à esquerda o heatmap, à direita a lista de filmes -->
		<div class="heatmap-flex">
			<!-- Heatmap -->
			<div bind:this={container} class="heatmap"></div>

			<!-- Painel de lista de filmes -->
			<div class="movie-list-panel">
				<h3>Filmes na célula selecionada</h3>
				{#if selectedMovies.length === 0}
					<p>Nenhuma célula selecionada.</p>
				{:else}
					<ul>
						{#each selectedMovies as movie}
							<li>
								<strong>{movie.primaryTitle} ({movie.startYear})</strong>
                <br>Nominations: {movie.oscarNominations}, Wins: {movie.oscarWins}
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>

		<!-- Informações gerais abaixo -->
		<div class="info">
			<p><strong>Total de filmes analisados:</strong> {data.length}</p>
			<p><strong>Filmes com indicações/vitórias:</strong> {heatmapData.reduce((sum, d) => sum + d.count, 0)}</p>
			<p><strong>Pontos no heatmap:</strong> {heatmapData.length}</p>
			{#if heatmapData.length > 0}
				<p><strong>Máximo de indicações:</strong> {Math.max(...heatmapData.map(d => d.nominations))}</p>
				<p><strong>Máximo de vitórias:</strong> {Math.max(...heatmapData.map(d => d.wins))}</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.heatmap-container {
		width: 75%;
		padding: 20px;
		background: #a1a1a1;
		border-radius: 8px;
	}

	.loading {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 400px;
		font-size: 16px;
		color: #666;
	}

	/* Flex para dispor heatmap e lista lado a lado */
	.heatmap-flex {
		display: flex;
		flex-direction: row;
		gap: 1px;
	}

	.heatmap {
		flex: 1;
		overflow-x: auto;
	}

	.movie-list-panel {
		width: 300px;
		max-height: 600px;
		overflow-y: auto;
		padding: 10px;
		background: #fff;
		border: 1px solid #ddd;
		border-radius: 6px;
	}

	.movie-list-panel h3 {
		margin-top: 0;
		font-size: 16px;
		border-bottom: 1px solid #ccc;
		padding-bottom: 4px;
	}

	.movie-list-panel ul {
		list-style: disc;
		padding-left: 20px;
		margin: 10px 0;
	}

	.movie-list-panel li {
		margin: 4px 0;
		font-size: 14px;
		color: #333;
	}

	.info {
		margin-top: 20px;
		padding: 15px;
		background: white;
		border-radius: 6px;
		border-left: 4px solid #ff6b35;
	}

	.info p {
		margin: 5px 0;
		font-size: 14px;
		color: #333;
	}

	:global(.cell:hover) {
		stroke: #333 !important;
		stroke-width: 2px !important;
	}

	:global(.heatmap-tooltip) {
		z-index: 1000;
	}

  :global(.cell.selected) {
    stroke: #000 !important;
    stroke-width: 3px !important;
  }
</style>

<script>
	import { onMount, tick } from 'svelte';
	import * as d3 from 'd3';

	export let loadMoviesFullData;

	let container;
	let data = [];
	let heatmapData = [];
	let loading = true;

	// Configurações do heatmap
	const margin = { top: 60, right: 100, bottom: 80, left: 80 };
	const width = 800 - margin.left - margin.right;
	const height = 600 - margin.top - margin.bottom;

	// Escalas de cor
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
		console.log('Processando dados...', data.length, 'filmes');
		
		// Filtra dados válidos e agrupa
		const validData = data.filter(d => 
			d.oscarNominations >= 0 && d.oscarWins >= 0 && 
			!isNaN(d.oscarNominations) && !isNaN(d.oscarWins)
		);
		
		console.log('Dados válidos:', validData.length);

		// Agrupa os dados por combinação de nominations e wins
		const grouped = new Map();
		validData.forEach(d => {
			const key = `${d.oscarNominations}-${d.oscarWins}`;
			grouped.set(key, (grouped.get(key) || 0) + 1);
		});

		console.log('Grupos criados:', grouped.size);

		// Encontra os valores máximos
		const maxNominations = d3.max(validData, d => d.oscarNominations) || 14;
		const maxWins = d3.max(validData, d => d.oscarWins) || 10;
		
		console.log('Max nominations:', maxNominations, 'Max wins:', maxWins);

		// Converte para array de objetos para o heatmap
		heatmapData = [];
		for (let nominations = 0; nominations <= maxNominations; nominations++) {
			for (let wins = 0; wins <= Math.min(maxWins, nominations); wins++) { // wins não pode ser maior que nominations
				const key = `${nominations}-${wins}`;
				const count = grouped.get(key) || 0;
				if (count > 0) {
					heatmapData.push({
						nominations,
						wins,
						count
					});
				}
			}
		}

		console.log('Heatmap data:', heatmapData.length, 'pontos');
		console.log('Sample data:', heatmapData.slice(0, 5));

		// Configura a escala de cor
		const maxCount = d3.max(heatmapData, d => d.count) || 1;
		colorScale.domain([Math.log(1), Math.log(maxCount)]);

		console.log('Max count para cor:', maxCount);
	}

	function createHeatmap() {
		console.log('Criando heatmap com', heatmapData.length, 'pontos');
		
		if (heatmapData.length === 0) {
			console.log('Nenhum dado para exibir no heatmap');
			return;
		}

		// Limpa o container
		d3.select(container).selectAll('*').remove();

		// Cria o SVG
		const svg = d3.select(container)
			.append('svg')
			.attr('width', width + margin.left + margin.right)
			.attr('height', height + margin.top + margin.bottom);
		if (!svg.node()) {
			console.error('Erro ao criar SVG');
			return;
		}
		const g = svg.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`);

		// Encontra os valores únicos para as escalas
		const nominations = [...new Set(heatmapData.map(d => d.nominations))].sort((a, b) => a - b);
		const wins = [...new Set(heatmapData.map(d => d.wins))].sort((a, b) => a - b);
		
		console.log('Valores únicos - Nominations:', nominations);
		console.log('Valores únicos - Wins:', wins);

		// Escalas usando os valores reais dos dados
		const xScale = d3.scaleBand()
			.domain(nominations)
			.range([0, width])
			.padding(0.1);

		const yScale = d3.scaleBand()
			.domain(wins.reverse()) // Inverte para que valores menores fiquem embaixo
			.range([0, height])
			.padding(0.1);

		console.log('Largura da banda X:', xScale.bandwidth());
		console.log('Largura da banda Y:', yScale.bandwidth());

		// Teste de posicionamento com valores que existem nos dados
		const firstNomination = heatmapData[0].nominations;
		const firstWin = heatmapData[0].wins;
		console.log('Primeira entrada:', heatmapData[0]);
		console.log(`Posição X para ${firstNomination}:`, xScale(firstNomination));
		console.log(`Posição Y para ${firstWin}:`, yScale(firstWin));

		// Remove tooltips anteriores
		d3.selectAll('.heatmap-tooltip').remove();
		
		// Tooltip
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

		// Células do heatmap
		const cells = g.selectAll('.cell')
			.data(heatmapData)
			.enter().append('rect')
			.attr('class', 'cell')
			.attr('x', d => {
				const x = xScale(d.nominations);
				if (x === undefined) {
					console.error(`Posição X undefined para nominations=${d.nominations}`);
					return 0;
				}
				return x;
			})
			.attr('y', d => {
				const y = yScale(d.wins);
				if (y === undefined) {
					console.error(`Posição Y undefined para wins=${d.wins}`);
					return 0;
				}
				return y;
			})
			.attr('width', xScale.bandwidth())
			.attr('height', yScale.bandwidth())
			.attr('fill', d => colorScale(Math.log(d.count)))
			.attr('stroke', '#fff')
			.attr('stroke-width', 1)
			.style('cursor', 'pointer');

		console.log('Células criadas:', cells.size());
		
		// Verifica se as células foram realmente criadas
		cells.each(function(d, i) {
			if (i < 3) { // Log das primeiras 3 células
				const rect = d3.select(this);
				console.log(`Célula ${i}:`, {
					data: d,
					x: rect.attr('x'),
					y: rect.attr('y'),
					width: rect.attr('width'),
					height: rect.attr('height'),
					fill: rect.attr('fill')
				});
			}
		});

		// Event handlers para tooltip
		cells.on('mouseover', function(event, d) {
				d3.select(this).attr('stroke', '#333').attr('stroke-width', 2);
				tooltip.transition()
					.duration(200)
					.style('opacity', .9);
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
				tooltip.transition()
					.duration(500)
					.style('opacity', 0);
			});

		// Eixo X (Indicações)
		const xAxis = d3.axisBottom(xScale);

		g.append('g')
			.attr('transform', `translate(0,${height})`)
			.call(xAxis)
			.selectAll('text')
			.style('font-size', '12px');

		// Eixo Y (Vitórias) - precisa usar a mesma escala
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

		// Título
		svg.append('text')
			.attr('x', (width + margin.left + margin.right) / 2)
			.attr('y', 30)
			.attr('text-anchor', 'middle')
			.style('font-size', '18px')
			.style('font-weight', 'bold')
			.text('Heatmap: Vitórias vs Indicações ao Oscar');

		// Legenda
		const legendWidth = 25;
		const legendHeight = 250;
		const maxCount = d3.max(heatmapData, d => d.count);
		
		const chartCenterY = margin.top + height / 2;
		const legendY = chartCenterY - legendHeight / 2;
		
		const legend = svg.append('g')
			.attr('transform', `translate(${width + margin.left + 20}, ${legendY})`);

		// Gradiente para a legenda
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

		// Labels da legenda
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
		<div bind:this={container} class="heatmap"></div>
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
		width: 100%;
		padding: 20px;
		background: #fafafa;
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

	.heatmap {
		width: 100%;
		overflow-x: auto;
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

	:global(.tooltip) {
		z-index: 1000;
	}
</style>
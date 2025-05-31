<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';
  import { fitas } from '../store/fitas.js';
  import { get } from 'svelte/store';

  export let width = 800;
  export let height = 450;
  export let geoData;
  export let data;
  //let fitas = new Set();

  // definindo variaveis globais
  let svgEl;
  let projection;
  let pathGenerator;
  let currentZoom = 1;
  let g;

  // preparando dados

  const bubbleData = d3.rollups(
    data,
    group => ({
      nominations: d3.sum(group, d => d.nomination || 0),
      wins: d3.sum(group, d => d.oscar || 0),
      rating: d3.mean(group, d => d.rating_imdb)
    }),
    d => d.country_origin[0] // ajuste conforme o nome da coluna que indica o país sovereignt
  ).map(([country, values]) => ({
    country,
    ...values
  }));

  const countryMap = new Map(
    bubbleData.map(d => [d.country, {
      nominations: d.nominations,
      wins: d.wins,
      rating: d.rating
    }])
  );

  // Agrupa por continente
  const continentGroups = {};
  for (const feature of geoData.features) {
    const name = feature.properties.name;
    const continent = feature.properties.continent;
    const values = countryMap.get(name);
    if (!values) continue;

    if (!continentGroups[continent]) {
      continentGroups[continent] = {
        totalNominations: 0,
        totalWins: 0,
        totalRating: 0,
        count: 0,
        centroids: []
      };
    }

    const centroid = d3.geoCentroid(feature);
    continentGroups[continent].totalNominations += values.nominations;
    continentGroups[continent].totalWins += values.wins;
    continentGroups[continent].totalRating += values.rating;
    continentGroups[continent].count += 1;
    continentGroups[continent].centroids.push(centroid);
  }

  const continentBubbles = Object.entries(continentGroups).map(([continent, { totalNominations, totalWins, totalRating, count, centroids }]) => {
  const avgLon = d3.mean(centroids, d => d[0]);
  const avgLat = d3.mean(centroids, d => d[1]);
  return {
    continent,
    value: totalRating,
    circle01: totalWins,
    circle02: totalNominations,
    coordinates: [avgLon, avgLat]
  };
  });



  async function draw() {
    if (!geoData || !geoData.features || !data) return;
    await tick(); // garante que svgEl está montado

    const svg = d3.select(svgEl);
    svg.selectAll("*").remove(); // limpa antes de redesenhar

    projection = d3.geoMercator().fitSize([width, height], geoData);
    pathGenerator = d3.geoPath().projection(projection);

    g = svg.append("g");

    g.selectAll("path")
      .data(geoData.features)
      .enter()
      .append("path")
      .attr("d", d => pathGenerator(d) || "")
      .attr("fill", "lightblue")
      .attr("stroke", "#333");

    

    
    

    // Escala de raio para as bolhas
    const radiusScale = d3.scaleSqrt()
      .domain([0, d3.max(bubbleData, d => d.nominations)])
      .range([0, 20]);

    

    
    // Desenha as bolhas
    // g.selectAll("circle")
    //   .data(bubbleData)
    //   .enter()
    //   .append("circle")
    //   .attr("cx", d => {
    //     const centroid = countryCentroids.get(d.country);
    //     return centroid ? centroid[0] : -9999; // esconde se não encontrado
    //   })
    //   .attr("cy", d => {
    //     const centroid = countryCentroids.get(d.country);
    //     return centroid ? centroid[1] : -9999;
    //   })
    //   .attr("r", d => radiusScale(d.nominations))
    //   .attr("fill", "steelblue")
    //   .attr("opacity", 0.7)
    //   .attr("stroke", "#222");


    const zoom = d3.zoom()
      .scaleExtent([1, 8]) // escala mínima e máxima
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
        currentZoom = event.transform.k;
        updateView();
      });

    svg.call(zoom);

    updateView()
  }

  function drawCountries () {
    g.selectAll("rect").remove();
    g.selectAll("circle").remove();
    g.selectAll("circle1").remove();
    const ratio = 1.82;



    const sizeScalecircle = d3.scaleSqrt()
      .domain([d3.min(bubbleData, d => d.wins), d3.max(bubbleData, d => d.nominations)]) 
      .range([0, 4]);

    const sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(bubbleData, d => d.rating)]) 
      .range([0, 8]);

    // Calcula os centroides dos países do GeoJSON
    const countryCentroids = new Map(
      geoData.features.map(f => [f.properties.sovereignt, pathGenerator.centroid(f)])
    );

    const preparedData2 = bubbleData
      .map(d => {
      const rawCentroid = countryCentroids.get(d.country);
      if (!rawCentroid) {
        console.warn("❌ Centroid não encontrado para:", d.country);
        return null;
      }
      const [x, y] = rawCentroid;
      if (!x | !y) {
        return null
      }
      const height = sizeScale(d.rating);
      const width = height * ratio;
      return { ...d, x, y, width, height };
    }).filter(d => d !== null);

    console.log("preparedData2", preparedData2);

    const radiusScale = d3.scaleSqrt()
      .domain([0, d3.max(bubbleData, d => d.nominations)])
      .range([0, 20]);

     // Desenha as bolhas
    // g.selectAll("circle")
    //   .data(preparedData2)
    //   .enter()
    //   .append("circle")
    //   .attr("cx", d => {
    //     const centroid = countryCentroids.get(d.country);
    //     return centroid ? centroid[0] : -9999; // esconde se não encontrado
    //   })
    //   .attr("cy", d => {
    //     const centroid = countryCentroids.get(d.country);
    //     return centroid ? centroid[1] : -9999;
    //   })
    //   .attr("r", d => radiusScale(d.nominations))
    //   .attr("fill", "steelblue")
    //   .attr("opacity", 0.7)
    //   .attr("stroke", "#222");

    
    g.selectAll("rect")
      .data(preparedData2)
      .enter()
      .append("rect")
      .attr("x", d => d.x - d.width / 2)
      .attr("y", d => d.y - d.height / 2)
      .attr("width", d => d.width)
      .attr("height", d => d.height)
      .attr("fill", "steelblue")
      .attr("opacity", 0.7)
      .attr("stroke", d => get(fitas).has(d.country) ? "gold" : "steelblue")
      .on("click", (event, d) => {
        fitas.toggle(d.country);  // seu método da store que adiciona/remove reativamente
        drawCountries(); // redesenha para atualizar a cor
        console.log("fitas:", get(fitas)); // pega snapshot atual
      });

    g.selectAll("circle")
      .data(preparedData2)
      .enter()
      .append("circle")
      .attr("cx", d => d.x - d.width/4)
      .attr("cy", d => d.y + d.height/14)
      .attr("r", d => sizeScalecircle(d.wins))
      .attr("fill", "orange")
      .attr("opacity", 0.7)
      .attr("stroke", "#222");

    g.selectAll("circle1")
    .data(preparedData2)
    .enter()
    .append("circle")
    .attr("cx", d => d.x + d.width/4)
    .attr("cy", d => d.y + d.height/14)
    .attr("r", d => sizeScalecircle(d.nominations))
    .attr("fill", "green")
    .attr("opacity", 0.7)
    .attr("stroke", "#222");

    

  }

  function drawContinents () {
    g.selectAll("rect").remove();
    g.selectAll("circle").remove();
    g.selectAll("circle1").remove();
    const ratio = 1.82;

    const sizeScalecircle = d3.scaleSqrt()
      .domain([d3.min(continentBubbles, d => d.circle01), d3.max(continentBubbles, d => d.circle02)]) 
      .range([2, 10]);

    const sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(continentBubbles, d => d.value)]) 
      .range([10, 46]);

    // Calcula os centroides dos países do GeoJSON
    const countryCentroids = new Map(
      geoData.features.map(f => [f.properties.sovereignt, pathGenerator.centroid(f)])
    );

    const preparedData = continentBubbles.map(d => {
      const [x, y] = projection(d.coordinates); // centróide
      const height = sizeScale(d.value);
      const width = height * ratio;
      return { ...d, x, y, fx: x, fy: y, width, height };
    });


    g.selectAll("rect")
      .data(preparedData)
      .enter()
      .append("rect")
      .attr("x", d => d.x - d.width / 2)
      .attr("y", d => d.y - d.height / 2)
      .attr("width", d => d.width)
      .attr("height", d => d.height)
      .attr("fill", "steelblue")
      .attr("opacity", 0.7)
      .attr("stroke", d => {
        const countriesInContinent = geoData.features
          .filter(f => f.properties.continent === d.continent)
          .map(f => f.properties.name);

        const allSelected = countriesInContinent.every(c => get(fitas).has(c));
        return allSelected ? "gold" : "steelblue";
      })
      .on("click", (event, d) => {

        const countriesInContinent = geoData.features
          .filter(f => f.properties.continent === d.continent)
          .map(f => f.properties.name);

        const allSelected = countriesInContinent.every(c => get(fitas).has(c));

        if (allSelected) {
          countriesInContinent.forEach(c => fitas.delete(c));  // se esses métodos existirem na store
        } else {
          countriesInContinent.forEach(c => fitas.add(c));
        }

        drawContinents();
        console.log("fitas:", get(fitas));
      });

    g.selectAll("circle")
    .data(preparedData)
    .enter()
    .append("circle")
    .attr("cx", d => d.x - d.width/4)
    .attr("cy", d => d.y + d.height/14)
    .attr("r", d => sizeScalecircle(d.circle01))
    .attr("fill", "orange")
    .attr("opacity", 0.7)
    .attr("stroke", "#222");

    g.selectAll("circle1")
    .data(preparedData)
    .enter()
    .append("circle")
    .attr("cx", d => d.x + d.width/4)
    .attr("cy", d => d.y + d.height/14)
    .attr("r", d => sizeScalecircle(d.circle02))
    .attr("fill", "green")
    .attr("opacity", 0.7)
    .attr("stroke", "#222");

    console.log("Mapa com bolhas desenhado");

    console.log("✅ Mapa desenhado");

  }

  function updateView() {
    if (currentZoom >= 4) {
      drawCountries();
    } else {
      drawContinents();
    }
  }

  // Redesenha no mount ou se geoData mudar
  onMount(draw);
  $: geoData && data && draw();
</script>

<svg bind:this={svgEl} {width} {height} />

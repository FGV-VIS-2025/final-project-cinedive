<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';
  import { fitas } from '../../store/fitas';
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
  let currentTransform = d3.zoomIdentity;
  let g;
  let gMap;

  const colorContries = "#3a3a35"
  const colorFitas = "#606878"
  const colorWins = "#FAD432"
  const colorNominates = "#005000"

  // preparando dados

  const bubbleData = d3.rollups(
    data,
    group => ({
      nominations: d3.sum(group, d => d.oscarNominations || 0),
      wins: d3.sum(group, d => d.oscarWins || 0),
      rating: d3.mean(group, d => d.averageRating)
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
    wins: totalWins,
    nominations: totalNominations,
    coordinates: [avgLon, avgLat]
  };
  });

  function pontoTangenciaMenorY(x, y, r, a, b) {
    const dx = a - x;
    const dy = b - y;
    const d2 = dx * dx + dy * dy;
    const d = Math.sqrt(d2);

    if (d <= r) {
      console.log("nhaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaooooooooooo")
      throw new Error("O ponto P está dentro ou na borda do círculo");
    }

    const rx = (r * r * dx) / d2;
    const ry = (r * r * dy) / d2;
    const h = r * Math.sqrt(d2 - r * r) / d2;

    const perpX = -dy;
    const perpY = dx;

    const t1x = x + rx + h * perpX;
    const t1y = y + ry + h * perpY;
    const t2x = x + rx - h * perpX;
    const t2y = y + ry - h * perpY;

    return t1y > t2y ? [t1x, t1y] : [t2x, t2y];
  }



  async function draw() {
    if (!geoData || !geoData.features || !data) return;
    await tick(); // garante que svgEl está montado

    const svg = d3.select(svgEl);
    svg.selectAll("*").remove(); // limpa antes de redesenhar

    projection = d3.geoMercator().fitSize([width, height], geoData);
    pathGenerator = d3.geoPath().projection(projection);

    g = svg.append("g");
    gMap = g.append("g")
      .attr("class", "map");

    gMap.selectAll("path")
      .data(geoData.features)
      .enter()
      .append("path")
      .attr("d", d => pathGenerator(d) || "")
      .attr("fill", colorContries);

    

    
    

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
      .scaleExtent([1, 30]) // escala mínima e máxima
      .on("zoom", (event) => {
        currentTransform = event.transform;
        gMap.attr("transform", event.transform);
        currentZoom = event.transform.k;
        updateView();
      });

    svg.call(zoom);

    updateView()
  }

  function drawFitas (data, nivel) {
    g.selectAll("rect").remove();
    g.selectAll("circle").remove();
    g.selectAll("line").remove();

    const ratio = 1.82;
    
    const sizeScalecircle = d3.scaleSqrt()
      .domain([0, d3.max([d3.max(continentBubbles, d => d.nominations - d.wins), d3.max(continentBubbles, d => d.wins)])]) 
      .range([5, 10]);
      
    const svg = d3.select(svgEl);
    svg.select("defs").remove();
    const defs = svg.append("defs");
    const mask = defs.append("mask")
      .attr("id", "myMask");

    mask.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "white");

    const circles1 = mask.selectAll("circle.first")
      .data(data)
      .enter()
      .append("circle")
      .attr("class", "first")
      .attr("cx", d => {
        const [x, _] = currentTransform.apply([d.x, d.y]);
        return x - d.width / 4;
      })
      .attr("cy", d => {
        const [_, y] = currentTransform.apply([d.x, d.y]);
        return y + d.height / 14;
      })
      .attr("r", d => sizeScalecircle(0)) // usa valor real, não zero
      .attr("fill", "black");

    mask.selectAll("circle.second")
    .data(data)
    .join(
      enter => enter.append("circle")
        .attr("class", "second")
        .attr("fill", "black")
        .call(enter => enter
          .attr("cx", d => currentTransform.apply([d.x, d.y])[0] + d.width / 4)
          .attr("cy", d => currentTransform.apply([d.x, d.y])[1] + d.height / 14)
          .attr("r", d => sizeScalecircle(0))
        ),
      update => update
        .call(update => update
          .attr("cx", d => currentTransform.apply([d.x, d.y])[0] + d.width / 4)
          .attr("cy", d => currentTransform.apply([d.x, d.y])[1] + d.height / 14)
          .attr("r", d => sizeScalecircle(0))
        ),
      exit => exit.remove()
    );

    g.selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", d => {
        const [x, _] = currentTransform.apply([d.x, d.y]);
        return x - d.width / 2;
      })
      .attr("y", d => {
        const [_, y] = currentTransform.apply([d.x, d.y]);
        return y - d.height / 2;
      })
      .attr("width", d => d.width)
      .attr("height", d => d.height)
      .attr("fill", colorFitas)
      .attr("mask", "url(#myMask)")
      .attr("opacity", 0.9)
      .attr("stroke", nivel === "continent" ?  
      d => {
        const countriesInContinent = geoData.features
          .filter(f => f.properties.continent === d.continent)
          .map(f => f.properties.name);

        const allSelected = countriesInContinent.every(c => get(fitas).has(c));
        return allSelected ? "gold" : null;
      } :
      d => get(fitas).has(d.country) ? "gold" : null
      )
      .on("click", nivel === "continent" ? 
      (event, d) => {

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
      } :
      (event, d) => {
        fitas.toggle(d.country);  // seu método da store que adiciona/remove reativamente
        drawCountries(); // redesenha para atualizar a cor
        console.log("fitas:", get(fitas)); // pega snapshot atual
      }
      );

    g.selectAll("circle.left")
    .data(data)
    .enter()
    .append("circle")
    .attr("cx", d => {
      const [x, _] = currentTransform.apply([d.x, d.y]);
      return x - d.width/4;
    })
    .attr("cy", d => {
      const [_, y] = currentTransform.apply([d.x, d.y]);
      return y + d.height/14;
    })
    .attr("r", d => sizeScalecircle(d.wins))
    .attr("fill", colorWins)
    .attr("opacity", 0.7)
    .attr("stroke", colorWins)
    .attr("mask", "url(#myMask)")
    .each(d => {
      const [x, y] = currentTransform.apply([d.x, d.y]);
      const [a, b] = pontoTangenciaMenorY(x - d.width/4, y + d.height/14, sizeScalecircle(d.wins), x-d.width/2, y - d.height/3);

      g.append("line")
      .attr("class", "yellow")
      .attr("x1", a)
      .attr("y1", b)
      .attr("x2", x - d.width/2)
      .attr("y2", y - d.height/3)
      .attr("stroke", colorWins);

      g.append("line")
      .attr("class", "yellow")
      .attr("x1", x)
      .attr("y1", y - d.height/3)
      .attr("x2", x - d.width/2)
      .attr("y2", y - d.height/3)
      .attr("stroke", colorWins);
      
    });

    g.selectAll("circle.right")
    .data(data)
    .enter()
    .append("circle")
    .attr("cx", d => {
      const [x, _] = currentTransform.apply([d.x, d.y]);
      return x + d.width/4;
    })
    .attr("cy", d => {
      const [_, y] = currentTransform.apply([d.x, d.y]);
      return y + d.height/14;
    })
    .attr("r", d => sizeScalecircle(d.nominations - d.wins))
    .attr("fill", colorNominates)
    .attr("opacity", 0.7)
    .attr("stroke", colorNominates)
    .attr("mask", "url(#myMask)")
    .each(d => {
      const [x, y] = currentTransform.apply([d.x, d.y]);
      const [a, b] = pontoTangenciaMenorY(x + d.width/4, y + d.height/14, sizeScalecircle(d.nominations - d.wins), x+d.width/2, y - d.height/3);

      g.append("line")
      .attr("class", "green")
      .attr("x1", a)
      .attr("y1", b)
      .attr("x2", x + d.width/2)
      .attr("y2", y - d.height/3)
      .attr("stroke", colorNominates);

      g.append("line")
      .attr("class", "green")
      .attr("x1", x)
      .attr("y1", y - d.height/3)
      .attr("x2", x + d.width/2)
      .attr("y2", y - d.height/3)
      .attr("stroke", colorNominates);
      
    });

    g.selectAll("text.continent-label").remove(); // Remove textos anteriores

    g.selectAll("text.continent-label")
      .data(data)
      .enter()
      .append("text")
      .attr("class", "continent-label")
      .attr("x", d => {
        const [x, _] = currentTransform.apply([d.x, d.y]);
        return x;
      })
      .attr("y", d => {
        const [_, y] = currentTransform.apply([d.x, d.y]);
        return y - 5; // ligeiro ajuste vertical
      })
      .text(d => d[nivel])
      .attr("text-anchor", "middle")
      .attr("font-size", d => Math.max(d.height * 0.25))
      .attr("fill", "black")
      .attr("pointer-events", "none") // evita que interfira nos cliques nos retângulos
      .each(function(d) {
        const fontSize = Math.max(8, d.height * 0.2);
        const maxWidth = d.width * 0.9; // margem de segurança
        const words = d[nivel].split(/\s+/); // divide por espaço
        const lineHeight = fontSize * 1.1;
        let line = [];
        let lines = [];
        const tempText = d3.select(this);

        for (let word of words) {
          line.push(word);
          tempText.text(line.join(" "));
          if (tempText.node().getComputedTextLength() > maxWidth) {
            line.pop();
            lines.push(line.join(" "));
            line = [word];
          }
        }
        if (line.length) lines.push(line.join(" "));

        tempText.text(null); // limpa o texto antes de adicionar tspans

        lines.forEach((textLine, i) => {
          tempText.append("tspan")
            .text(textLine)
            .attr("x", d => {
              const [x, _] = currentTransform.apply([d.x, d.y]);
              return x;
            })
            .attr("dy", i === 0 ? 0 : lineHeight)
            .attr("text-anchor", "middle")
        });

        const [x, y] = currentTransform.apply([d.x, d.y]);

        const textX = tempText.node().getComputedTextLength()
        const textY = y - d.height / 4  ;

        // adiciona rect atrás da linha de texto
        d3.select(this.parentNode)
          .insert("rect", "text")
          .attr("x", x - textX / 2 - 4)
          .attr("y", textY - Math.max(d.height * 0.25) * 0.9)
          .attr("width", textX + 8)
          .attr("height", Math.max(d.height * 0.25) * 1.2)
          .attr("fill", "#aaa")
          .attr("rx", 3);

        // centraliza verticalmente ajustando y inicial
        tempText.attr("y", d => {
          const [_, y] = currentTransform.apply([d.x, d.y]);
          return y - d.height/4//- (lines.length - 1) * lineHeight / 2;
        });
      });

  }

  function drawCountries () {

    const ratio = 1.82;


    const sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(bubbleData, d => d.nominations)]) 
      .range([24, 50]);

    // Calcula os centroides dos países do GeoJSON
    const countryCentroids = new Map(
      geoData.features.map(f => [f.properties.sovereignt, pathGenerator.centroid(f)])
    );

    let preparedData2 = bubbleData
      .map(d => {
        const rawCentroid = countryCentroids.get(d.country);
        if (!rawCentroid) return null;
        const [x, y] = rawCentroid;
        const height = sizeScale(d.nominations);
        const width = height * ratio;
        const radius = Math.sqrt(width * width + height * height) / 2;
        return { ...d, x, y, width, height, radius };
      })
      .filter(d => d !== null);

    // Simulação de colisão
    const simulation = d3.forceSimulation(preparedData2)
      .force("x", d3.forceX(d => d.x ).strength(0.9))
      .force("y", d3.forceY(d => d.y ).strength(0.9))
      .force("collision", d3.forceCollide(d => d.radius / currentZoom + 1)) // padding extra de 1px
      .stop();

    // Roda a simulação por alguns ticks
    for (let i = 0; i < 10; ++i) simulation.tick();

    preparedData2 = [...preparedData2]; // força reatividade

    drawFitas(preparedData2, "country")


    

  }

  function drawContinents () {

    const ratio = 1.82;


    const sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(continentBubbles, d => d.nominations)]) 
      .range([40, 80]);

    // Calcula os centroides dos países do GeoJSON
    const countryCentroids = new Map(
      geoData.features.map(f => [f.properties.sovereignt, pathGenerator.centroid(f)])
    );

    const preparedData = continentBubbles.map(d => {
      const [x, y] = projection(d.coordinates); // centróide
      const height = sizeScale(d.nominations);
      const width = height * ratio;
      return { ...d, x, y, fx: x, fy: y, width, height };
    });

    drawFitas(preparedData, "continent");

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
  $: if (geoData && data) {
    draw();
  }
</script>

<svg bind:this={svgEl} {width} {height} />
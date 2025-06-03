<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';
  import {currentStep} from '../../store/step'
  import { derived } from 'svelte/store';
  import { get } from 'svelte/store';

  export let howmany = 3;
  export let width = 220;
  export let height = 1000;

  let svgEl;
  let current = 0;

  // subscribe para atualizar variável local `current`
  $: current = $currentStep;
  const line = d3.line();

  const startpx = 0;
  const startpy = 50;
  const startx = 25;
  const starty = 140;
  const colorfita = "#1a1a2e";
  const colorframe = "#16213e";
  const projectorColor = "#2c2c54";
  const projectorAccent = "#40407a";
  const highlightColor = "#ffd700";
  const filmHoleColor = "#0f3460";

  function drawSvg(step) {
    const a = step
    
    const svg = d3.select(svgEl)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove()

    // Definir gradientes y filtros
    const defs = svg.append("defs");

    // Gradiente para el proyector
    const projectorGradient = defs.append("linearGradient")
      .attr("id", "projectorGradient")
      .attr("x1", "0%")
      .attr("y1", "0%")
      .attr("x2", "100%")
      .attr("y2", "100%");

    projectorGradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#40407a")
      .attr("stop-opacity", 1);

    projectorGradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#2c2c54")
      .attr("stop-opacity", 1);

    // Gradiente para la película
    const filmGradient = defs.append("linearGradient")
      .attr("id", "filmGradient")
      .attr("x1", "0%")
      .attr("y1", "0%")
      .attr("x2", "100%")
      .attr("y2", "0%");

    filmGradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#0f3460")
      .attr("stop-opacity", 1);

    filmGradient.append("stop")
      .attr("offset", "50%")
      .attr("stop-color", "#1a1a2e")
      .attr("stop-opacity", 1);

    filmGradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#0f3460")
      .attr("stop-opacity", 1);

    // Filtro de sombra
    const dropShadow = defs.append("filter")
      .attr("id", "dropshadow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");

    dropShadow.append("feGaussianBlur")
      .attr("in", "SourceAlpha")
      .attr("stdDeviation", "3");

    dropShadow.append("feOffset")
      .attr("dx", "2")
      .attr("dy", "4")
      .attr("result", "offset");

    dropShadow.append("feComponentTransfer")
      .append("feFuncA")
      .attr("type", "linear")
      .attr("slope", "0.3");

    const feMerge = dropShadow.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "offset");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Máscara para los agujeros de la película
    const mask = defs.append("mask")
      .attr("id", "hole-mask");

    mask.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "white");

    // Agujeros de la película
    for (let i = 1; i*22 < howmany * 40 + 4; i++){
        mask.append("rect")
            .attr("x", startx + 12)
            .attr("y", starty + i*22 - 10)
            .attr("width", 12)
            .attr("height", 10)
            .attr("rx", 2)
            .attr("fill", "black");

        mask.append("rect")
            .attr("x", startx + 116)
            .attr("y", starty + i*22 - 10)
            .attr("width", 12)
            .attr("height", 10)
            .attr("rx", 2)
            .attr("fill", "black");
    }

    // Dibujando el cuerpo principal del proyector
    svg.append("rect")
      .attr("class", "projector-body")
      .attr("x", 15)
      .attr("y", 55)
      .attr("width", 165)
      .attr("height", 75)
      .attr("rx", 12)
      .attr("ry", 12)
      .attr("fill", "url(#projectorGradient)")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 2)
      .attr("filter", "url(#dropshadow)");

    // Lente del proyector
    svg.append("path")
      .attr("class", "projector-lens")
      .attr("d", line([
          [165, 85],
          [165, 105],
          [205, 155],
          [205, 25],
          [165, 85]
      ]))
      .attr("fill", "url(#projectorGradient)")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 2)
      .attr("filter", "url(#dropshadow)");

    // Bobinas del proyector
    svg.append("circle")
      .attr("class", "projector-reel")
      .attr("cx", 25)
      .attr("cy", 55)
      .attr("r", 32)
      .attr("fill", "url(#projectorGradient)")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 2)
      .attr("filter", "url(#dropshadow)");

    svg.append("circle")
      .attr("class", "projector-reel")
      .attr("cx", 95)
      .attr("cy", 40)
      .attr("r", 32)
      .attr("fill", "url(#projectorGradient)")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 2)
      .attr("filter", "url(#dropshadow)");

    // Detalles de las bobinas
    svg.append("circle")
      .attr("cx", 25)
      .attr("cy", 55)
      .attr("r", 15)
      .attr("fill", "none")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 1)
      .attr("opacity", 0.7);

    svg.append("circle")
      .attr("cx", 95)
      .attr("cy", 40)
      .attr("r", 15)
      .attr("fill", "none")
      .attr("stroke", projectorAccent)
      .attr("stroke-width", 1)
      .attr("opacity", 0.7);

    // Película principal
    svg.append("rect")
      .attr("class", "film-strip")
      .attr("x", startx)
      .attr("y", starty)
      .attr("width", 140)
      .attr("height", howmany * 40 + 4)
      .attr("rx", 3)
      .attr("fill", "url(#filmGradient)")
      .attr("stroke", "#0f3460")
      .attr("stroke-width", 2)
      .attr("mask", "url(#hole-mask)")
      .attr("filter", "url(#dropshadow)");

    // Frames de la película
    for (let i = 0; i < howmany; i++){
        const isActive = i === get(currentStep) -1;
        
        svg.append("rect")
            .attr("class", "frame")
            .attr("x", startx + 28)
            .attr("y", starty + 4 + 40*i)
            .attr("width", 84)
            .attr("height", 36)
            .attr("rx", 3)
            .attr("fill", isActive ? "#2c3e50" : colorframe)
            .attr("stroke", isActive ? highlightColor : "#34495e")
            .attr("stroke-width", isActive ? 3 : 1)
            .style("cursor", "pointer")
            .style("transition", "all 0.3s ease")
            .on("mouseover", function() {
                if (!isActive) {
                    d3.select(this)
                        .attr("fill", "#34495e")
                        .attr("stroke", "#7f8c8d");
                }
            })
            .on("mouseout", function() {
                if (!isActive) {
                    d3.select(this)
                        .attr("fill", colorframe)
                        .attr("stroke", "#34495e");
                }
            })
            .on("click", () => {
              const steps = d3.selectAll('.step').nodes();
              steps[i+1]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

        // Añadir número de frame
        if (isActive) {
            svg.append("text")
                .attr("x", startx + 70)
                .attr("y", starty + 24 + 40*i)
                .attr("text-anchor", "middle")
                .attr("fill", highlightColor)
                .attr("font-family", "Arial, sans-serif")
                .attr("font-size", "12px")
                .attr("font-weight", "bold")
                .text(i + 1);
        }
    }

    // Agujeros de perfil de la película con mejor estilo
    for (let i = 1; i * 22 < howmany * 40 + 4; i++) {
      svg.append("rect")
        .attr("x", startx + 12)
        .attr("y", starty + i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("rx", 2)
        .attr("fill", filmHoleColor)
        .attr("stroke", "#0f3460")
        .attr("stroke-width", 1);

      svg.append("rect")
        .attr("x", startx + 116)
        .attr("y", starty + i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("rx", 2)
        .attr("fill", filmHoleColor)
        .attr("stroke", "#0f3460")
        .attr("stroke-width", 1);
    }

    // Efectos de luz del proyector
    const lightBeam = svg.append("g")
      .attr("class", "light-beam")
      .attr("opacity", 0.3);

    lightBeam.append("polygon")
      .attr("points", "180,85 180,95 220,140 220,40")
      .attr("fill", "url(#lightGradient)");

    // Gradiente para el haz de luz
    const lightGradient = defs.append("linearGradient")
      .attr("id", "lightGradient")
      .attr("x1", "0%")
      .attr("y1", "0%")
      .attr("x2", "100%")
      .attr("y2", "0%");

    lightGradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#ffd700")
      .attr("stop-opacity", 0.8);

    lightGradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#ffffff")
      .attr("stop-opacity", 0.1);
  };

  onMount(() => {
    drawSvg();
  });

  $: drawSvg($currentStep);
</script>

<svg bind:this={svgEl} {width} {height} {howmany}/>
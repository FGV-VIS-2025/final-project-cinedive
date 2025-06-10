<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';
  import {currentStep} from '../../store/step'
  import { derived } from 'svelte/store';
  import { get } from 'svelte/store';

  export let howmany = 6;
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
              steps[i]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

    
  };

  onMount(() => {
    drawSvg();
  });

  $: drawSvg($currentStep);
</script>

<svg bind:this={svgEl} {width} {height} {howmany}/>
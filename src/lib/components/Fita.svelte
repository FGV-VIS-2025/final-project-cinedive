<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';
  import {currentStep} from '../../store/step'
  import { derived } from 'svelte/store';
  import { get } from 'svelte/store';


  export let howmany = 3;
  export let width = 200;
  export let height = 1000;



  let svgEl;
  let current = 0;

  // subscribe para atualizar variável local `current`
  $: current = $currentStep;
  const line = d3.line();

  const camera = [

  ]
  const startpx = 0;
  const startpy = 50;
  const startx = 20;
  const starty = 130;
  const colorfita = "#802040"
  const colorframe = "#807040"




  function drawSvg(step) {
    
    const svg = d3.select(svgEl)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove()

    // desenhando o projetor

    svg.append("rect")
      .attr("class", "projector")
      .attr("x", 10)
      .attr("y", 50)        // posição Y
      .attr("width", 160)   // largura
      .attr("height", 80)  // altura
      .attr("rx", 10) // raio horizontal
      .attr("ry", 10)
      .attr("fill", "black");

    svg.append("path")
      .attr("class", "projector")
      .attr("d", line([
          [160, 80],
          [160, 100],
          [200, 150],
          [200, 30],
          [160, 80]
      ]))
      .attr("fill", "black")

    svg.append("circle")
      .attr("class", "projector")
      .attr("cx", 20)
      .attr("cy", 50)
      .attr("r", 35)
      .attr("fill", "black")

    svg.append("circle")
      .attr("class", "projector")
      .attr("cx", 90)
      .attr("cy", 35)
      .attr("r", 35)
      .attr("fill", "black")


    const defs = svg.append("defs");

    const mask = defs.append("mask")
      .attr("id", "hole-mask");

    // Área visível (branca)
    mask.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "white");

    // Buraco (preto)
    for (let i = 1; i*22 <  howmany * 40 + 4; i++){
        mask.append("rect")
            .attr("x", startx + 12)
            .attr("y", starty + i*22 - 10)
            .attr("width", 12)
            .attr("height", 10)
            .attr("fill", "black")
            .attr("stroke", "black");

        mask.append("rect")
            .attr("x", startx + 116)
            .attr("y", starty + i*22 - 10)
            .attr("width", 12)
            .attr("height", 10)
            .attr("fill", "black")
            .attr("stroke", "black");
    }
    

    // Adiciona um retângulo
    svg.append("rect")
      .attr("x", startx)        // posição X
      .attr("y", starty)        // posição Y
      .attr("width", 140)   // largura
      .attr("height", howmany * 40 + 4)  // altura
      .attr("fill", colorfita)
      .attr("stroke", "black")
      .attr("stroke-width", 1)
      .attr("mask", "url(#hole-mask)");

    for (let i = 0; i < howmany; i++){
        svg.append("rect")
            .attr("class", "frame")
            .attr("x", startx + 28)
            .attr("y", starty + 4 + 40*i)        // posição Y
            .attr("width", 84)   // largura
            .attr("height", 36)  // altura
            .attr("fill", colorframe)
            .attr("stroke", i === get(currentStep) ? "#aa9900" : null)
            .on("click", () => {
              const steps = d3.selectAll('.step').nodes();
              steps[i]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
    }

    for (let i = 1; i * 22 < howmany * 40 + 4; i++) {
      svg.append("rect")
        .attr("x", startx + 12)
        .attr("y", starty + i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("fill", "none")
        .attr("stroke", "black")
        .attr("stroke-width", 1);

      svg.append("rect")
        .attr("x", startx + 116)
        .attr("y", starty + i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("fill", "none")
        .attr("stroke", "black")
        .attr("stroke-width", 1);
    }
  };

  onMount(() => {
    drawSvg(); // chama uma vez com valor inicial de `current`
  });

  $: drawSvg($currentStep);




</script>

<svg bind:this={svgEl} {width} {height} {howmany}/>
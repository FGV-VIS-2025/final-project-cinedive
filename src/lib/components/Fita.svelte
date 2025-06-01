<script>
  import { onMount, tick } from 'svelte';
  import * as d3 from 'd3';

  export let howmany = 10;
  export let width = 800;
  export let height = 450;


  let svgEl;

  const startx = 0;
  const starty = 0;
  const colorfita = "#802040"
  const colorframe = "#807040"


  onMount(() => {
    const svg = d3.select(svgEl)
      .attr("width", width)
      .attr("height", height);

    const defs = svg.append("defs");

    const mask = defs.append("mask")
      .attr("id", "hole-mask");

    // Área visível (branca)
    mask.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "white");

    // Buraco (preto)
    for (let i = 0; i*22 <  howmany * 40 + 4; i++){
        mask.append("rect")
            .attr("x", 12)
            .attr("y", i*22 - 10)
            .attr("width", 12)
            .attr("height", 10)
            .attr("fill", "black")
            .attr("stroke", "black");

        mask.append("rect")
            .attr("x", 116)
            .attr("y", i*22 - 10)
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
            .attr("fill", colorframe);
    }

    for (let i = 0; i * 22 < howmany * 40 + 4; i++) {
      svg.append("rect")
        .attr("x", 12)
        .attr("y", i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("fill", "none")
        .attr("stroke", "black")
        .attr("stroke-width", 1);

      svg.append("rect")
        .attr("x", 116)
        .attr("y", i * 22 - 10)
        .attr("width", 12)
        .attr("height", 10)
        .attr("fill", "none")
        .attr("stroke", "black")
        .attr("stroke-width", 1);
    }
  });




</script>

<svg bind:this={svgEl} {width} {height} {howmany}/>
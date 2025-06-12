<script>
  import { onMount } from 'svelte';
  import noUiSlider from 'nouislider';
  import 'nouislider/dist/nouislider.css';

  export let min = 1900;
  export let max = 2025;
  export let startYear = 2000;
  export let endYear = 2020;
  export let onChange = () => {};

  let sliderElement;

  onMount(() => {
    const slider = noUiSlider.create(sliderElement, {
      start: [startYear, endYear],
      connect: true,
      range: {
        min,
        max
      },
      step: 1,
      tooltips: true,
      format: {
        to: value => Math.round(value),
        from: value => Number(value)
      }
    });

    slider.on('update', (values) => {
      const [newStart, newEnd] = values.map(Number);
      startYear = newStart;
      endYear = newEnd;
      onChange({ startYear, endYear });
    });
  });
</script>

<div bind:this={sliderElement} class="slider-container" />

<style>
  .slider-container {
    margin: 1rem 0;
  }
</style>

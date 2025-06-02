<!-- src/lib/components/Slider.svelte -->
<script>
    import { onMount, afterUpdate } from 'svelte';
    import noUiSlider from 'nouislider';
    import { createEventDispatcher } from 'svelte';

    export let min = 2000;
    export let max = 2025;
    export let start = min;
    export let end = max;

    const dispatch = createEventDispatcher();
    let sliderElement;

    function createSlider() {
        if (!sliderElement) return;

        if (sliderElement.noUiSlider) {
        sliderElement.noUiSlider.destroy();
        }

        noUiSlider.create(sliderElement, {
        start: [start, end],
        connect: true,
        step: 1,
        range: { min, max },
        tooltips: [true, true],
        format: {
            to: Math.round,
            from: Number
        }
        });

        sliderElement.noUiSlider.on('update', ([low, high]) => {
        dispatch('rangeChanged', { start: low, end: high });
        });
    }

    onMount(createSlider);
    afterUpdate(createSlider);
</script>
  
<div bind:this={sliderElement} class="year-slider"></div> 
  
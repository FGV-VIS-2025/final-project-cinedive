<script>
    import { onMount, createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();
  
    onMount(() => {
      // Selecciona todos los pasos después de que el DOM esté montado
      const stepEls = Array.from(document.querySelectorAll('.step'));
  
      const observer = new IntersectionObserver(
        entries => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              const idx = stepEls.indexOf(entry.target);
              dispatch('stepchange', idx);
            }
          }
        },
        { threshold: 0.5 }
      );
  
      stepEls.forEach(el => observer.observe(el));
  
      return () => observer.disconnect();
    });
  </script>
  
  <style>
    .step {
      margin: 0 auto 100vh;
      max-width: 600px;
    }
  </style>
  
  {#each Array(5) as _, i}
    <div class="step">
      <h2>Paso {i + 1}</h2>
      <p>Texto explicativo para el paso {i + 1}…</p>
    </div>
  {/each}
  
<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import Bubble from '$lib/components/bubble.svelte';

  let current = 0;
  let scroller;

  onMount(async () => {
    if (!browser) return;
    const { default: scrollama } = await import('scrollama');
    scroller = scrollama()
      .setup({ step: '.step', offset: 0.5, debug: false })
      .onStepEnter(({ index }) => (current = index));
    window.addEventListener('resize', scroller.resize);
  });

  onDestroy(() => {
    scroller?.destroy?.();
    if (browser) window.removeEventListener('resize', scroller.resize);
  });
</script>

<div class="scroll">
  <!-- INTRO ocupa ambas columnas -->
  <div class="step intro">
    <h1 class="titulo-grande">¡Bienvenidos a CineDive!</h1>
    <p>Esta es la página de introducción antes de comenzar con los pasos.</p>
    
  </div>

  <!-- Columna de pasos -->
  <div class="scroll__text">
    <div class="step" data-step="0">
      <h1>Step 1</h1>
      <div class="content-box"></div>
    </div>
    <div class="step" data-step="1">
      <h1>Step 2</h1>
      <div class="content-box ">
        <div class="text">
          <p>Aquí va tu texto explicativo del paso 2…</p>
        </div>
      </div>
    </div>
    <div class="step" data-step="2">
      <h1>Step 3</h1>
      <div class="content-box split">
        <div class="text">
          <p>Aquí va tu texto explicativo del paso 2…</p>
        </div>
    </div>
    
  </div>
</div>
  <!-- Columna gráfica -->
  <div class="scroll__graphic">
    {#if current === 1}
      <Bubble />
    {/if}
  </div>
</div>

<style>
  /* GRID de dos columnas */
  :global(html, body) {
    margin: 0;
    padding: 0;
    overflow-x: hidden; /* opcional, para evitar scroll horizontal */
  }

  .scroll {
    display: grid;
    width: 100vw;
    grid-template-columns: 40% 60%;
  }

  /* Intro ocupa columnas 1 y 2 */
  .step.intro {
    grid-column: 1 / -1;
    height: 100vh;               /* pantalla completa */
    display: flex;
    flex-direction: column;
    background-color: hsl(0, 0%, 0%);  
    color: hsl(51, 100%, 79%);
    justify-content: center;
    align-items: center;
    text-align: center;
    margin-bottom: 5vh;  
  }

  .scroll__text {
    /* nada que cambiar aquí */
    padding: 2rem;
  }

  .scroll__text .step {
    margin-bottom: 80vh; /* aqui es el tamanho  */
  }

  .titulo-grande {
    font-size: 4rem;    /* el tamaño que quieras */
    /* puedes usar también px, em, %, etc. */
  }

  .scroll__graphic {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }  

  .content-box {
    border: 1px solid #ccc;
    padding: 1rem;
    margin: 1rem 0;
  }

  .content-box.split {
    display: flex;
    gap: 1rem;
  }
  .content-box.split .text {
    width: 50%;
  }
</style>

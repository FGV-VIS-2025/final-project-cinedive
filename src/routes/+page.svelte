<script>
    import { onMount, onDestroy } from 'svelte';
    import scrollama from 'scrollama';
  
    // Tus componentes
    import Bubble from '../lib/components/bubble.svelte';

  
    let current = 0;
    let scroller;
  
    onMount(() => {
      scroller = scrollama();
      scroller
        .setup({ step: '.step', offset: 0.5, debug: false })
        .onStepEnter(({ index }) => {
          current = index;
        });
  
      window.addEventListener('resize', scroller.resize);
    });
  
    onDestroy(() => {
      if (scroller && scroller.destroy) scroller.destroy();
      window.removeEventListener('resize', scroller.resize);
    });
  </script>
  
  <div class="scroll">
    <!-- Columna de pasos -->
    <div class="scroll__text">
      <!-- STEP 1 -->
      <div class="step" data-step="0">
        <h1>Step 1</h1>
        <div class="content-box">
          <h2>Título</h2>
          <p class="dots">. . . . . . . . . . . . . . .</p>
        </div>
      </div>
  
      <!-- STEP 2 -->
      <div class="step" data-step="1">
        <h1>Step 2</h1>
        <div class="content-box split">
          <div class="text">
            <p>Aquí va tu texto explicativo del paso 2…</p>
          </div>
          <!-- el gráfico solo aparece en la otra columna, ver más abajo -->
        </div>
        <p class="dots">. . . . . . . . . . . . . . .</p>
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
    /* Layout de dos columnas */
    .scroll {
      display: flex;
    }
    .scroll__text {
      width: 40%;
      padding: 2rem;
    }
    .scroll__graphic {
      width: 60%;
      position: sticky;
      top: 0;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  
    /* Cada paso ocupa una pantalla para forzar scroll */
    .step {
      margin-bottom: 100vh;
    }
  
    /* Tu “cajón” de contenido */
    .content-box {
      border: 1px solid #ccc;
      padding: 1rem;
      margin: 1rem 0;
    }
  
    /* Paso 2: dividir en texto + espacio para gráfico (vacío) */
    .content-box.split {
      display: flex;
      gap: 1rem;
    }
    .content-box.split .text {
      width: 50%;
    }
  
    /* Los “puntitos” de página */
    .dots {
      text-align: center;
      color: #999;
    }
  </style>
  
<script>
  import Fita from '../lib/components/Fita.svelte';
  import Bubble from '$lib/components/bubble.svelte';

  let steps = [0, 1, 2];
</script>

<div class="container">
  <section class="step intro">
    <h1>¡Bienvenidos a CineDive!</h1>
    <p>Intro antes de los pasos.</p>
  </section>

  <section class="step">
    <h1>Step 1</h1>
    <Fita />
  </section>

  <section class="step">
    <h1>Step 2</h1>
    <p>Aquí va tu texto explicativo del paso 2…</p>
    <Bubble />
  </section>

  <!-- ... outros steps ... -->
</div>

<style>
  .container {
    scroll-snap-type: y mandatory;
    overflow-y: scroll;
    height: 100vh;
  }

  .step {
    scroll-snap-align: start;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    padding: 2rem;
    box-sizing: border-box;
  }

  .intro {
    background-color: hsl(0, 0%, 15%);
    color: hsl(51, 100%, 79%);
  }
</style>
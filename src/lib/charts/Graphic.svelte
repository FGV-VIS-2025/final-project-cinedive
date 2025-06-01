<script>
    export let activeStep = 0;

    const positions = [20, 30, 40, 50, 60].map(x => ({ x, y: 95 }));
</script>
<style>
    .graphic {
  position: sticky;
  top: 0;
  height: 100vh;             /* toda la altura de la ventana */
  display: flex;
  align-items: flex-end;     /* pega el contenido abajo */
  justify-content: center;   /* centra horizontalmente */
  padding-bottom: 1rem;      /* opcional: un pequeño margen al fondo */
}
    svg {
      width: 25%;  /* controla aquí el ancho final */
      height: auto;
    }
</style>
  
<div class="graphic">
    <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMax meet"
    >
        {#each positions as pos, j}
            <circle
                cx={pos.x}
                cy={pos.y}
                r={2}                         
                fill="currentColor"
                style="opacity: {j <= activeStep ? 1 : 0.2}"
            />
        {/each}
        </svg>
</div>
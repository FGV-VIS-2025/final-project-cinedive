<!-- src/lib/charts/FilmDetails.svelte -->
<script>
  export let data;
</script>

{#if data}
  <div class="film-details-card">
    <h2>{data.primaryTitle}</h2>
    <p><strong>Gênero:</strong> {data.genres}</p>
    <p><strong>Avaliação média:</strong> {data.averageRating}</p>
    <p><strong>Direção:</strong> {data.directors}</p>
    <p><strong>Indicações ao Oscar:</strong> {data.oscarNominations}</p>
    <p><strong>Vitórias no Oscar:</strong> {data.oscarWins}</p>
    <p><strong>Ano de lançamento:</strong> {data.startYear}</p>
  </div>
{/if}

<!-- src/lib/charts/FilmSearch.svelte -->
<script>
    import { createEventDispatcher } from 'svelte';
  
    export let options = [];   // Array de { tconst, primaryTitle, startYear }
    export let query   = '';
  
    const dispatch = createEventDispatcher();
    let showList = false;
    let selectedIndex = -1;
  
    $: if (showList && selectedIndex >= 0) {
      const btn = document.querySelector(`button[data-idx="${selectedIndex}"]`);
      btn?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  
    function select(opt) {
      dispatch('select', { id: opt.tconst });
      showList = false;
    }
  
    function handleKey(e) {
      if (!showList) return;
      if (e.key === 'ArrowDown') {
        selectedIndex = (selectedIndex + 1) % options.length;
        e.preventDefault();
      } else if (e.key === 'ArrowUp') {
        selectedIndex = (selectedIndex - 1 + options.length) % options.length;
        e.preventDefault();
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        select(options[selectedIndex]);
        e.preventDefault();
      } else if (e.key === 'Escape') {
        showList = false;
        e.preventDefault();
      }
    }
  </script>
  
  <style>
    .dropdown       { position: relative; width: 300px; }
    .results        { position: absolute; background:#1e1e1e; border:1px solid #695a03;
                      width:100%; max-height:200px; overflow-y:auto; z-index:100; }
    .results button { width:100%; text-align:left; padding:.5rem; background:none; border:none;
                      color:inherit; cursor:pointer; }
    .results button:hover,
    .results button.selected { background:#ffd700; color:black; }
  </style>
  
  <div class="dropdown">
    <input
      type="text"
      placeholder="Search for a movie"
      bind:value={query}
      on:input={() => { showList = true; selectedIndex = -1; }}
      on:focus={() => showList = true}
      on:keydown={handleKey}
    />
  
    {#if showList && options.length > 0}
      <div class="results">
        {#each options as opt, i (opt.tconst)}
          <button
            type="button"
            data-idx={i}
            class:selected={i === selectedIndex}
            on:mousedown={() => select(opt)}
          >
            {opt.primaryTitle} ({opt.startYear})
          </button>
        {/each}
      </div>
    {/if}
  </div>
  
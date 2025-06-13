<script>
  import { onMount } from 'svelte';
  import { pessoasSelecionadas } from '../../store/people';
  import { get } from 'svelte/store';

  export let options = [];
  export let label = '';

  let searchQuery = '';
  let isOpen = false;
  let containerRef;

  let filteredOptions = options;

  const updateFiltered = () => {
    filteredOptions = options.filter(option =>
      option.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const toggle = (option) => {
    pessoasSelecionadas.toggle(option);
  };

  const allSelected = () => {
    return get(pessoasSelecionadas).size === options.length;
  };

  const handleSelectAll = () => {
    if (allSelected()) {
      pessoasSelecionadas.clear();
    } else {
      options.forEach(opt => pessoasSelecionadas.add(opt));
    }
  };

  const handleClickOutside = (event) => {
    if (!containerRef.contains(event.target)) {
      isOpen = false;
    }
  };

  onMount(() => {
    updateFiltered();
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  });

  $: updateFiltered(); // reexecuta ao alterar searchQuery ou options
</script>

<style>
  .dropdown {
    position: absolute;
    top: calc(100% + 5px);
    left: 0;
    width: 300px;
    background-color: #111;
    border: 1px solid #333;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    margin-top: 5px;
    max-height: 300px;
    overflow-y: auto;
    padding: 10px;
  }
  input[type="text"] {
    margin-bottom: 10px;
    padding: 5px;
    width: 100%;
  }
</style>

<div bind:this={containerRef} style="position: relative;">
  {#if label}
    <p><strong>{label}</strong></p>
  {/if}

  <input
    type="text"
    placeholder="Search some species"
    bind:value={searchQuery}
    on:focus={() => isOpen = true}
  />

  {#if isOpen}
    <div class="dropdown">
      <div style="margin-bottom: 10px;">
        <label>
          <input type="checkbox" checked={allSelected()} on:change={handleSelectAll} />
          {' '}Select All
        </label>
      </div>

      {#if filteredOptions.length > 0}
        <ul style="list-style: none; padding: 0; margin: 0;">
          {#each filteredOptions as option}
            <li>
              <label>
                <input
                  type="checkbox"
                  checked={get(pessoasSelecionadas).has(option)}
                  on:change={() => toggle(option)}
                />
                {' '}{option}
              </label>
            </li>
          {/each}
        </ul>
      {:else}
        <p style="font-style: italic; color: #777;">No options found</p>
      {/if}
    </div>
  {/if}
</div>

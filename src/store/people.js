// src/store/pessoasSelecionadas.js
import { writable } from 'svelte/store';

function createPessoasSelecionadasStore() {
  const { subscribe, set, update } = writable(new Set());

  return {
    subscribe,
    add: (pessoa) => update(set => {
      const newSet = new Set(set);
      newSet.add(pessoa);
      return newSet;
    }),
    delete: (pessoa) => update(set => {
      const newSet = new Set(set);
      newSet.delete(pessoa);
      return newSet;
    }),
    clear: () => set(new Set()),
    has: (pessoa) => {
      let value;
      const unsubscribe = subscribe(set => (value = set.has(pessoa)));
      unsubscribe();
      return value;
    },
    toggle: (pessoa) => update(set => {
      const newSet = new Set(set);
      if (newSet.has(pessoa)) {
        newSet.delete(pessoa);
      } else {
        newSet.add(pessoa);
      }
      return newSet;
    })
  };
}

export const pessoasSelecionadas = createPessoasSelecionadasStore();

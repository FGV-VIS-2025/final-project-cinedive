// src/store/fitas.js
import { writable } from 'svelte/store';

function createFitasStore() {
  const { subscribe, set, update } = writable(new Set());

  return {
    subscribe,
    add: (item) => update(set => {
      const newSet = new Set(set);
      newSet.add(item);
      return newSet;
    }),
    delete: (item) => update(set => {
      const newSet = new Set(set);
      newSet.delete(item);
      return newSet;
    }),
    clear: () => set(new Set()),
    has: (item) => {
      let value;
      const unsubscribe = subscribe(set => (value = set.has(item)));
      unsubscribe();
      return value;
    },
    toggle: (item) => update(set => {
      const newSet = new Set(set);
      if (newSet.has(item)) {
        newSet.delete(item);
      } else {
        newSet.add(item);
      }
      return newSet;
    })
  };
}

export const fitas = writable(new Set());
<script setup>
import HiveScene from '../components/HiveScene.vue'
import VApp from './VApp.vue'
import VMorph from './VMorph.vue'
import VNight from './VNight.vue'

const VARIANTS = [
  { id: 'A', name: 'Texto que se transforma', note: 'La nota escrita a lo rápido se convierte letra a letra en el texto limpio de la página (TextMorph de elastic-ui). Solo tipografía.', comp: VMorph },
  { id: 'B', name: 'Día y noche', note: 'Por el día caen notas y sube el contador, cae la noche, la colmena las lee, y por la mañana la página está lista.', comp: VNight },
  { id: 'C', name: 'La app de verdad', note: 'El árbol de páginas de la clase: por la mañana aparece una página nueva marcada «Nueva» y se abre.', comp: VApp },
  { id: 'D', name: 'Notas de dos personas y el apunte conjunto', note: 'Notas de Ana y Leo, más y no del todo bien puestas; al lado, el apunte conjunto, redondeado y cuidado, que aparece entero y se va escribiendo.', comp: HiveScene },
]
</script>

<template>
  <main class="mx-auto flex w-[min(100%-2rem,64rem)] flex-col gap-14 py-14">
    <h1 class="m-0 text-3xl font-semibold tracking-tight">Primer capítulo: variantes</h1>
    <section v-for="v in VARIANTS" :key="v.id" class="flex flex-col gap-5">
      <div>
        <p class="m-0 text-xl font-semibold">{{ v.id }} · {{ v.name }}</p>
        <p class="m-0 mt-1 text-fg-secondary">{{ v.note }}</p>
      </div>
      <component :is="v.comp" />
    </section>
  </main>
</template>

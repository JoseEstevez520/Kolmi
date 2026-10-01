<script setup>
import { Diagram } from 'elastic-ui'
import { ArrowDown, BookOpen, Clock, Filter, Globe, Lock, MessageSquarePlus } from '@lucide/vue'

// Cómo funciona Notas de clase: la nota entra, se guarda en privado en el
// servidor, un cron despierta a los agentes, el portero la limpia y decide
// dónde va, y los agentes de apuntes y web la publican. El violeta del agente
// es el mismo de las páginas de IA. Ámbar para lo privado, verde para lo que
// ya es público.
const VIOLETA = '#7c3aed'
const GRIS = '#64748b'

const PASOS = [
  {
    icono: MessageSquarePlus,
    titulo: 'La nota',
    texto: 'Se escribe en un chat o en la web. Texto libre, sin formato ni campos.',
    color: GRIS,
  },
  {
    icono: Lock,
    titulo: 'Guardada en privado',
    texto: 'En un servidor propio, fuera del repo. La nota en crudo no se publica nunca.',
    color: 'var(--color-warning)',
    etiqueta: 'privado',
  },
  {
    icono: Clock,
    titulo: 'El cron',
    texto: 'Una vez al día despierta al equipo de agentes.',
    color: GRIS,
  },
  {
    icono: Filter,
    titulo: 'El portero',
    texto: 'Junta las notas del mismo tema, quita nombres y datos, descarta lo que no aporta y decide dónde va cada una.',
    color: VIOLETA,
  },
  {
    icono: BookOpen,
    titulo: 'Apuntes y web',
    texto: 'Redactan la nota con el estilo de casa y la publican en la página que toca.',
    color: VIOLETA,
  },
  {
    icono: Globe,
    titulo: 'Publicado',
    texto: 'Al publicarse, la web se reconstruye sola.',
    color: 'var(--color-success)',
    etiqueta: 'público',
  },
]
</script>

<template>
  <Diagram
    class="rounded-[var(--radius-xl)] bg-bg-subtle p-5 sm:p-6"
    label="El recorrido de una nota: se escribe, se guarda en privado en el servidor, un cron despierta a los agentes, el portero la limpia y decide dónde va, y los agentes de apuntes y web la publican. Lo privado nunca llega a lo público sin pasar por el portero."
  >
    <ol class="mx-auto flex max-w-md flex-col items-stretch">
      <li v-for="(paso, i) in PASOS" :key="paso.titulo">
        <div class="diagram-area diagram-in gap-1.5" :style="{ '--diagram-color': paso.color }">
          <span class="flex flex-wrap items-center gap-2 text-sm font-semibold">
            <component :is="paso.icono" class="size-4 shrink-0" :stroke-width="1.5" aria-hidden="true" />
            {{ paso.titulo }}
            <span v-if="paso.etiqueta" class="text-xs font-normal" :style="{ color: paso.color }">
              {{ paso.etiqueta }}
            </span>
          </span>
          <span class="text-sm text-fg-secondary">{{ paso.texto }}</span>
        </div>
        <div v-if="i < PASOS.length - 1" class="flex justify-center py-1.5 text-fg-faint">
          <ArrowDown class="size-4" :stroke-width="1.5" aria-hidden="true" />
        </div>
      </li>
    </ol>
  </Diagram>
</template>

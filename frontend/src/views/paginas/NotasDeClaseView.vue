<script setup>
import DiagramaNotasDeClase from '../../visuales/DiagramaNotasDeClase.vue'
import PlantillaPagina from '../../components/PlantillaPagina.vue'

// extra/herramientas/notas-de-clase/README.md
</script>

<template>
  <PlantillaPagina
    titulo="Notas de clase"
    entradilla="Cualquiera deja notas en crudo y un equipo de agentes las convierte en apuntes y páginas de la web. Idea de clase colaborativa, sin código todavía."
  >
    <p>
      Aportar al repo pide saber git y Vue, y la mayoría no lo hace aunque tenga algo que contar.
      Aquí solo hay que dejar la nota.
    </p>

    <h2 id="como-funciona">Cómo funciona</h2>
    <p>Fíjate en la frontera: lo que entra está en privado, y solo lo que pasa por el portero llega a lo público.</p>
    <DiagramaNotasDeClase />
    <p><strong>La nota en crudo no llega a los otros dos agentes: el portero la limpia antes.</strong></p>

    <h2 id="el-equipo">El equipo</h2>
    <p>
      Son los mismos papeles de <RouterLink to="/extra/ia/equipo">Un equipo de agentes</RouterLink>,
      repartidos así:
    </p>
    <table>
      <thead>
        <tr><th>Agente</th><th>Qué hace</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Portero</td>
          <td>conoce los cursos: anonimiza, junta duplicados, descarta y decide dónde va cada nota</td>
        </tr>
        <tr>
          <td>Apuntes</td>
          <td>redacta la nota con el estilo de casa</td>
        </tr>
        <tr>
          <td>Web</td>
          <td>la convierte en página o actualiza la que toca</td>
        </tr>
      </tbody>
    </table>

    <h2 id="en-privado">Por qué en privado</h2>
    <p>
      Un borrador puede llevar nombres o datos de compañeros, y lo que se publica una vez ya está
      copiado: clones, cachés, historial de git. Por eso la nota en crudo se queda en el servidor y
      lo único que sale es la síntesis, sin nombres. El portero es la puerta por la que pasa, no el
      que limpia después.
    </p>

    <h2 id="como-se-montaria">Cómo se montaría</h2>
    <p>La infraestructura son dos piezas:</p>
    <ul>
      <li>
        <strong>El VPS</strong>: la app web, el job diario y, más adelante, el chat. Opcionalmente,
        también OpenCode en modo servidor.
      </li>
      <li>
        <strong>Supabase</strong> (en la nube, gratis): login y base de datos con las notas, las
        páginas y sus versiones. Si algún día quieres, se autoaloja en el VPS.
      </li>
    </ul>
    <p>
      Los agentes se montan con el SDK de OpenAI. Se empieza con un script simple y se pasa a
      LangGraph (un framework para flujos de agentes con varios pasos) si hacen falta bucles o
      aprobación.
    </p>

    <h3 id="fase-1">Fase 1: notas y pasada diaria</h3>
    <p>
      Los alumnos inician sesión y dejan notas; no tocan las páginas. Un cron (el programador de
      tareas del servidor) lanza una vez al día el flujo de agentes: coge las notas pendientes, las
      agrupa por tema y las clasifica, redacta y revisa. De cada página se guarda la versión
      anterior, para poder volver atrás.
    </p>
    <p>Cuesta céntimos al día.</p>

    <h3 id="fase-2">Fase 2: chat con los apuntes (RAG)</h3>
    <p>
      Un chatbot que responde preguntando a los apuntes, no a lo que recuerde el modelo. RAG es
      eso: buscar primero los trozos que hablan del tema y responder solo con ellos.
    </p>
    <ul>
      <li>
        <strong>Guardar</strong>: con pgvector (una extensión de Postgres que guarda vectores) en
        Supabase, una tabla de fragmentos con etiquetas, metadatos y embeddings (los números que
        representan el significado de cada fragmento).
      </li>
      <li><strong>Indexar</strong>: al final de la pasada diaria, solo las páginas que han cambiado.</li>
      <li>
        <strong>Responder</strong>: en cada pregunta se buscan los fragmentos parecidos y el LLM
        responde solo con ellos, citando la página.
      </li>
    </ul>

    <h2 id="decidir">Lo que hay que decidir</h2>
    <ul>
      <li>Por dónde entran las notas: bot de chat o web.</li>
      <li>Cuánto tiempo se guarda la nota en crudo una vez publicada su síntesis.</li>
    </ul>

    <h2 id="estado">Estado</h2>
    <p>Sin código todavía. Es el diseño, por si alguien se anima a empezarlo.</p>
  </PlantillaPagina>
</template>

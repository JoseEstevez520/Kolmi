# La idea

Los alumnos de una clase dejan notas en crudo y un equipo de agentes las convierte en
apuntes y páginas. Sin código todavía: esto es el diseño.

## El problema

Publicar un apunte a mano pide saber git y Vue, y la mayoría no lo hace aunque tenga algo
que contar. La idea es que solo tengan que dejar la nota.

## Cómo funciona

1. La nota se escribe donde sea cómodo (un bot de chat o una caja en la web), en texto libre
   y sin formato.
2. Se guarda **en privado**, en un servidor propio, fuera del repo. La nota en crudo no se
   publica nunca.
3. Un cron despierta al equipo de agentes una vez al día.
4. El **portero** las revisa: junta las que hablan de lo mismo, quita nombres y datos de
   compañeros, descarta lo que no aporta, y decide si entra y en qué módulo. Si eso ya está
   en los apuntes, corrige; si no, añade.
5. Los agentes de apuntes redactan lo que pasa el portero, y el de la web lo publica. La web
   se reconstruye sola.

## El equipo

Son los mismos papeles de un equipo de agentes, repartidos así:

| Agente | Qué hace |
|---|---|
| Portero | conoce los cursos: anonimiza, junta duplicados, descarta y decide dónde va cada nota |
| Apuntes | redacta la nota con el estilo de casa |
| Web | la convierte en página o actualiza la que toca |

El portero va primero: la nota en crudo no llega a los otros dos.

## Por qué en privado

Un borrador puede llevar nombres o datos de compañeros, y lo que se publica una vez ya está
copiado: clones, cachés, historial de git. Por eso la nota en crudo se queda en el servidor y
lo único que sale es la síntesis, sin nombres. El portero es la puerta por la que pasa, no el
que limpia después.

## Cómo se montaría

La infraestructura son dos piezas:

- **El VPS**: la app web, el job diario y, más adelante, el chat. Opcionalmente, también
  OpenCode en modo servidor.
- **Supabase** (en la nube, gratis): login y base de datos con las notas, las páginas y sus
  versiones. Si algún día quieres, se autoaloja en el VPS.

Los agentes se montan con el SDK de OpenAI. Se empieza con un script simple y se pasa a
LangGraph (un framework para flujos de agentes con varios pasos) si hacen falta bucles o
aprobación.

La parte de cuentas, login y registro tiene su propia especificación:
[Autenticación y usuarios](autenticacion.md).

### Fase 1: notas y pasada diaria

Los alumnos inician sesión y dejan notas; no tocan las páginas. Un cron (el programador de
tareas del servidor) lanza una vez al día el flujo de agentes: coge las notas pendientes, las
agrupa por tema y las clasifica, redacta y revisa. De cada página se guarda la versión
anterior, para poder volver atrás.

Cuesta céntimos al día.

### Fase 2: chat con los apuntes (RAG)

Un chatbot que responde preguntando a los apuntes, no a lo que recuerde el modelo. RAG es
eso: buscar primero los trozos que hablan del tema y responder solo con ellos.

- **Guardar**: con pgvector (una extensión de Postgres que guarda vectores) en Supabase, una
  tabla de fragmentos con etiquetas, metadatos y embeddings (los números que representan el
  significado de cada fragmento).
- **Indexar**: al final de la pasada diaria, solo las páginas que han cambiado.
- **Responder**: en cada pregunta se buscan los fragmentos parecidos y el LLM responde solo
  con ellos, citando la página.

## Lo que hay que decidir

- Por dónde entran las notas: bot de chat o web.
- Cuánto tiempo se guarda la nota en crudo una vez publicada su síntesis.

## Estado

Sin código todavía. Es el diseño, por si alguien se anima a empezarlo.

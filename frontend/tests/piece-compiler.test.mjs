import assert from 'node:assert/strict'
import test from 'node:test'
import { checkPiece } from '../scripts/check-piece.mjs'

test('compiles an interactive Vue component without running it', () => {
  assert.deepEqual(checkPiece('<template><button @click="n++">{{ n }}</button></template><script>import { ref } from "vue"; export default { setup() { return {n: ref(0)} } }</script>'), [])
})
test('reports syntax errors that structural regexes cannot detect', () => {
  assert.ok(checkPiece('<template><div>{{ n }}</div></template><script>export default { setup() { const = ; } }</script>').length)
  assert.ok(checkPiece('<template><div></span></template>').length)
})

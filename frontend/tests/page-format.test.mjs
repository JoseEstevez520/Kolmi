import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { createParser } from '@openuidev/vue-lang'
import { library } from '../src/lib/openui/prompt.js'

const cases = JSON.parse(readFileSync(new URL('../../shared/page-format-cases.json', import.meta.url)))
const parser = createParser(library.toJSONSchema(), 'Page')
function shape(value) {
  if (Array.isArray(value)) return value.map(shape)
  if (value?.type === 'element') return { typeName: value.typeName, props: shape(value.props) }
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, shape(v)]))
  return value
}
for (const item of cases) {
  test(item.id, () => {
    const result = parser.parse(item.source)
    const valid = result.root?.typeName === 'Page' && !result.meta.incomplete
      && result.root.props.blocks.length > 0 && !result.meta.errors.length && !result.meta.unresolved.length
    assert.equal(valid, item.valid, JSON.stringify(result.meta))
    if (item.valid) assert.deepEqual(shape(result.root), item.shape)
  })
}

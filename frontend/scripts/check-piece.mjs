// Development bench only: compile without executing the untrusted component.
import { readFileSync } from 'node:fs'
import { parse, compileScript, compileStyle, compileTemplate } from 'vue/compiler-sfc'

export function checkPiece(source) {
  const problems = []
  try {
    const { descriptor, errors } = parse(source, { filename: 'artifact.vue' })
    problems.push(...errors)
    if (!descriptor.template) problems.push('A template is required')
    if (descriptor.script || descriptor.scriptSetup) compileScript(descriptor, { id: 'artifact' })
    if (descriptor.template) problems.push(...compileTemplate({
      source: descriptor.template.content, filename: 'artifact.vue', id: 'artifact',
    }).errors)
    for (const style of descriptor.styles) problems.push(...compileStyle({
      source: style.content, filename: 'artifact.vue', id: 'artifact', scoped: style.scoped,
    }).errors)
  } catch (error) {
    problems.push(error)
  }
  return problems.map(error => typeof error === 'string' ? error : error.message)
}

if (process.argv[1]?.endsWith('check-piece.mjs')) {
  process.stdout.write(JSON.stringify({ problems: checkPiece(readFileSync(0, 'utf8')) }) + '\n')
}

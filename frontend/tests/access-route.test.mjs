import { test } from 'node:test'
import assert from 'node:assert/strict'
import { decideRoute } from '../src/lib/accessRoute.js'

const login = (redirect) => ({ name: 'login', meta: {}, query: { redirect } })
const current = { role: 'student', status: 'active' }
test('an active session resumes OAuth consent instead of going home', () => {
  const path = '/oauth/consent?authorization_id=request-id'
  assert.equal(decideRoute(login(path), current, true), path)
  assert.deepEqual(decideRoute(login('https://other.example'), current, true), { name: 'home' })
  assert.deepEqual(decideRoute(login('//other.example'), current, true), { name: 'home' })
})
test('blocked users cannot resume a consent route', () => {
  const consent = { name: 'oauth-consent', fullPath: '/oauth/consent?authorization_id=id', meta: {} }
  assert.deepEqual(decideRoute(consent, { ...current, status: 'blocked' }, true), { name: 'waiting' })
  assert.deepEqual(decideRoute(consent, null, false), { name: 'login', query: { redirect: consent.fullPath } })
})

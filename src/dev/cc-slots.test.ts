import { verifiedCcDocument } from '../../scripts/local-cc-slots'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { describe, expect, it } from 'vitest'
import { ccPackage, ccTrialProblem, CC_SLOTS_ID } from './cc-slots'
import type { LinkState } from '../engine/elekloader/octatrack-link'
const base = 'a'.repeat(64)
const ready: LinkState = { status: 'ready', active: 'b'.repeat(64), identity: { base, model: 'MKII', canSubmit: true, capabilities: { abi: 8, features: 3, maxSites: 128, maxCopies: 128 } } }
const review = base + ':' + ready.active

describe('local CC trial review', () => {
  it('requires a connected, capable base and an inventory tied to the running set', () => {
    expect(ccTrialProblem(ready, [], review)).toBeUndefined()
    expect(ccTrialProblem({ status: 'idle' }, [], review)).toBeTruthy()
    expect(ccTrialProblem({ ...ready, identity: { ...ready.identity!, capabilities: undefined } }, [], review)).toBeTruthy()
    expect(ccTrialProblem(ready, undefined, review)).toBeTruthy()
    expect(ccTrialProblem({ ...ready, active: 'c'.repeat(64) }, [], review)).toBeTruthy()
    expect(ccTrialProblem(ready, [{ module: CC_SLOTS_ID, handle: 1, layout: 1, name: 'CC' }], review)).toContain('already installed')
  })
  it('refuses damaged or substituted local packages', () => {
    expect(() => ccPackage({ version: '0.0.4-experimental', sha256: 'a'.repeat(64), hex: '00'.repeat(100) })).toThrow('identity')
    expect(() => ccPackage({ version: 'wrong', sha256: '', hex: '' })).toThrow('Invalid')
  })
})

it('does not offer edited native source as the verified local trial', () => {
  const data = new Uint8Array([1, 2, 3]), digest = sha(data)
  expect(verifiedCcDocument(data, { version: 'test', sha256: digest }).sha256).toBe(digest)
  expect(() => verifiedCcDocument(new Uint8Array([1, 2, 4]), { version: 'test', sha256: digest })).toThrow('source changed')
})

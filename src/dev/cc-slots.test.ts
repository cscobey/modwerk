import { verifiedCcDocument } from '../../scripts/local-cc-slots'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { describe, expect, it } from 'vitest'
import { ccPackage, ccTrialProblem, ccPersistenceProblem, parseCcInstallRecord, CC_SLOTS_ID, type CcInstallRecord } from './cc-slots'
import type { LinkState } from '../engine/elekloader/octatrack-link'
const base = 'c1ae2ee92a829e06aa9398d35981b8228efdd34c578c9583ef36fba8f5bc637f'
const ready: LinkState = { status: 'ready', active: 'b'.repeat(64), identity: { base, model: 'MKII', canSubmit: true, capabilities: { abi: 8, features: 3, maxSites: 128, maxCopies: 128 } } }
const review = base + ':' + ready.active

describe('local CC trial review', () => {
  it('requires a connected, capable base and an inventory tied to the running set', () => {
    expect(ccTrialProblem(ready, [], review)).toBeUndefined()
    expect(ccTrialProblem({ ...ready, identity: { ...ready.identity!, capabilities: { ...ready.identity!.capabilities!, abi: 7 } } }, [], review)).toContain('capabilities')
    expect(ccTrialProblem({ status: 'idle' }, [], review)).toBeTruthy()
    expect(ccTrialProblem({ ...ready, identity: { ...ready.identity!, capabilities: undefined } }, [], review)).toBeTruthy()
    expect(ccTrialProblem(ready, undefined, review)).toBeTruthy()
    expect(ccTrialProblem({ ...ready, active: 'c'.repeat(64) }, [], review)).toBeTruthy()
    expect(ccTrialProblem(ready, [{ module: CC_SLOTS_ID, handle: 1, layout: 1, name: 'CC' }], review)).toBeUndefined()
    expect(ccTrialProblem(ready, [], review, 'remove')).toContain('not installed')
  })
  it('refuses damaged or substituted local packages', () => {
    expect(() => ccPackage({ version: '0.0.18-experimental', sha256: 'a'.repeat(64), hex: '00'.repeat(100) })).toThrow('identity')
    expect(() => ccPackage({ version: 'wrong', sha256: '', hex: '' })).toThrow('Invalid')
  })
})

it('accepts the larger initialized-project package and bounds it by the reviewed size', () => {
  const data=new Uint8Array(33434),view=new DataView(data.buffer)
  view.setUint32(0,0x4d57524d);view.setUint16(4,8);view.setUint32(28,parseInt(CC_SLOTS_ID,16))
  const document={version:'0.0.18-experimental',sha256:sha(data),hex:Buffer.from(data).toString('hex')}
  expect(ccPackage(document)).toEqual(data)
  expect(()=>ccPackage({...document,hex:document.hex+'00'})).toThrow('Invalid')
})

it('does not offer edited native source as the verified local trial', () => {
  const data = new Uint8Array([1, 2, 3]), digest = sha(data)
  expect(verifiedCcDocument(data, { version: 'test', sha256: digest }).sha256).toBe(digest)
  expect(() => verifiedCcDocument(new Uint8Array([1, 2, 4]), { version: 'test', sha256: digest })).toThrow('source changed')
})

it('retains a restart receipt across refresh while refusing another base or an incomplete saved set', () => {
  const receipt: CcInstallRecord = { schema: 1, base, packageSha256: 'c'.repeat(64), action: 'install', saved: true, restored: false, expected: [{ module: CC_SLOTS_ID, layout: 1 }] }
  const restored = parseCcInstallRecord(JSON.stringify(receipt))!
  expect(restored).toEqual(receipt)
  expect(parseCcInstallRecord('{broken')).toBeUndefined()
  expect(parseCcInstallRecord(JSON.stringify({ ...receipt, saved: false, restored: true }))).toBeUndefined()
  const modules = [{ module: CC_SLOTS_ID, layout: 1, handle: 1, name: 'CC' }]
  const health = { saved: 1, savedCount: 1, live: 1 }
  expect(ccPersistenceProblem(restored, ready, modules, health, true)).toBeUndefined()
  expect(ccPersistenceProblem(restored, { ...ready, identity: { ...ready.identity!, base: 'd'.repeat(64) } }, modules, health, true)).toContain('same Modwerk base')
  expect(ccPersistenceProblem(restored, ready, modules, { ...health, savedCount: 0 }, true)).toContain('complete saved module set')
  expect(ccPersistenceProblem(restored, ready, modules, { ...health, saved: 7 }, true)).toContain('Startup restoration is not confirmed')
})

it.each([[23,25],[24,24]])('refuses naming-test packages when base capacity is sites=%s copies=%s', (maxSites,maxCopies) => {
  const state={...ready,identity:{...ready.identity!,capabilities:{abi:8,features:3,maxSites,maxCopies}}}
  expect(ccTrialProblem(state,[],review)).toContain('capabilities')
})

it('distinguishes an unreadable module list from a real mismatch and names both reviewed and observed layouts', () => {
  const receipt:CcInstallRecord={schema:1,base,packageSha256:'c'.repeat(64),action:'install',saved:false,restored:false,expected:[{module:CC_SLOTS_ID,layout:1}]}
  expect(ccPersistenceProblem(receipt,ready,undefined,undefined,false)).toContain('could not be read')
  const mismatch=ccPersistenceProblem(receipt,ready,[{module:CC_SLOTS_ID,layout:2,handle:1,name:'CC'}],{saved:7,savedCount:1,live:1},false)
  expect(mismatch).toContain(`Expected: ${CC_SLOTS_ID} (layout 1)`)
  expect(mismatch).toContain(`Read back: ${CC_SLOTS_ID} (layout 2)`)
  expect(mismatch).toContain('Persistence is not confirmed')
})

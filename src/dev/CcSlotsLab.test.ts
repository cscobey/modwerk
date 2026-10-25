// @vitest-environment jsdom
import { act, createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import CcSlotsLab from './CcSlotsLab'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { CC_SLOTS_ID, CC_INSTALL_KEY } from './cc-slots'
import type { OctatrackLink, LinkState } from '../engine/elekloader/octatrack-link'
import type { MissingModule, SelftestRecord } from '../engine/elekloader/upload-usb'

let dispose: (() => Promise<void>) | undefined
const button = (container: HTMLElement, text: string) => [...container.querySelectorAll('button')].find(b => b.textContent === text)!
beforeEach(() => { vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true); localStorage.clear() })
afterEach(async () => { await dispose?.(); vi.unstubAllGlobals(); vi.restoreAllMocks() })
async function setup(installed = false) {
  const data = new Uint8Array(72), view = new DataView(data.buffer)
  view.setUint32(0, 0x4d57524d); view.setUint16(4, 8); view.setUint32(28, parseInt(CC_SLOTS_ID, 16))
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ version: '0.0.11-experimental', sha256: sha(data), hex: Array.from(data,b=>b.toString(16).padStart(2,'0')).join('') }) })))
  const other: MissingModule = { name: 'Existing module', module: '12345678', layout: 3, handle: 1 }
  const cc: MissingModule = { name: 'MIDI CC Slots', module: CC_SLOTS_ID, layout: 1, handle: 2 }
  let modules = installed ? [other,cc] : [other]
  let state: LinkState = { status: 'ready', active: 'b'.repeat(64), identity: { canSubmit: true, base: 'a'.repeat(64), model: 'MKII', capabilities: { abi: 8, features: 3, maxSites: 128, maxCopies: 128 } } }
  const listeners = new Set<() => void>()
  const set = (next: LinkState) => { state = next; listeners.forEach(fn=>fn()) }
  const control = { saved: 7, missingOther: false, testReported: true }
  const selftest = vi.fn(async (report: (reading: SelftestRecord) => void) => {
    if (control.testReported) report({ state: 2 } as SelftestRecord)
    return null
  })
  const update = vi.fn(async (_name: string, changes: {module:string;data:Uint8Array}[], check:()=>Promise<unknown>) => {
    const failure = await check()
    if (failure) { set({ ...state, status: 'ready', notice: {tone:'error',text:String(failure)} }); return }
    modules = changes[0].data.length === 32 ? [other] : [other,cc]
    set({ ...state, active: 'c'.repeat(64), status: 'trial', tested: true })
  })
  const keep = vi.fn(async () => set({ ...state, status: 'ready', notice: {tone:'success',text:'Kept.'} }))
  const undo = vi.fn(async () => set({ ...state, status: 'ready' }))
  const link = { start: () => () => {}, getState: () => state, subscribe: (fn:()=>void) => { listeners.add(fn);return()=>listeners.delete(fn) }, update, selftest, keep, undo,
    inventory: async () => control.missingOther ? modules.filter(m=>m.module!==other.module) : modules,
    health: async () => control.saved < 0 ? undefined : { saved: control.saved, savedCount: modules.length, live: modules.length },
  } as unknown as OctatrackLink
  const container = document.createElement('div'); document.body.append(container)
  const root = createRoot(container); dispose = async () => { await act(() => root.unmount()); container.remove() }
  await act(() => root.render(createElement(CcSlotsLab, { link })))
  async function click(text: string) { await act(async () => button(container,text).click()) }
  return { container, click, update, keep, undo, selftest, data, control }
}
it('prepares without sending; Keep stays an explicit action after the tested one-module trial', async () => {
  const t=await setup()
  expect(t.update).not.toHaveBeenCalled(); expect(t.keep).not.toHaveBeenCalled()
  expect(button(t.container,'Start temporary USB trial').disabled).toBe(true)
  await t.click('Build draft and read installed modules')
  expect(t.container.textContent).toContain('Existing module'); expect(t.update).not.toHaveBeenCalled()
  await t.click('Start temporary USB trial')
  expect(t.update).toHaveBeenCalledOnce(); expect(t.keep).not.toHaveBeenCalled()
  expect(t.update.mock.calls[0][1]).toEqual([{ module:'midi-cc-slots',data:t.data }])
  expect(t.selftest).toHaveBeenCalledOnce()
  await t.click('Keep installed')
  expect(t.keep).toHaveBeenCalledOnce(); expect(t.container.textContent).toContain('Card save confirmed')
  const record=JSON.parse(localStorage.getItem(CC_INSTALL_KEY)!)
  expect(record.saved).toBe(true);expect(record.restored).toBe(false)
  expect(record.expected).toContainEqual({module:'12345678',layout:3})
  await t.click('Check after restart')
  expect(t.container.textContent).toContain('Startup restoration is not confirmed')
  t.control.saved=1
  await t.click('Check after restart')
  expect(t.container.textContent).toContain('Startup restoration confirmed by the base')
})
it.each([8,-1])('does not claim persistence when card save status is %s', async saved => {
  const t=await setup();await t.click('Build draft and read installed modules');await t.click('Start temporary USB trial')
  t.control.saved=saved;await t.click('Keep installed')
  expect(JSON.parse(localStorage.getItem(CC_INSTALL_KEY)!).saved).toBe(false)
  expect(button(t.container,'Check after restart').disabled).toBe(true)
  expect(t.container.textContent).not.toContain('Card save confirmed for')
  t.control.saved=7;await t.click('Check card save')
  expect(JSON.parse(localStorage.getItem(CC_INSTALL_KEY)!).saved).toBe(true)
})
it('removes only MIDI CC Slots, then keeps removal while preserving the companion', async () => {
  const t=await setup(true);await t.click('Build draft and read installed modules')
  await t.click('Try removing MIDI CC Slots')
  expect(t.keep).not.toHaveBeenCalled()
  const changes=t.update.mock.calls[0][1]
  expect(changes).toHaveLength(1);expect(changes[0].module).toBe('midi-cc-slots');expect(changes[0].data.length).toBe(32)
  await t.click('Keep removal')
  const record=JSON.parse(localStorage.getItem(CC_INSTALL_KEY)!)
  expect(record.action).toBe('remove');expect(record.expected).toEqual([{module:'12345678',layout:3}])
})
it('refuses a persistence claim if a companion module disappears', async () => {
  const t=await setup();await t.click('Build draft and read installed modules');await t.click('Start temporary USB trial')
  t.control.missingOther=true;await t.click('Keep installed')
  expect(JSON.parse(localStorage.getItem(CC_INSTALL_KEY)!).saved).toBe(false)
  expect(t.container.textContent).toContain('installed module set differs')
})
it('Undo remains available and never keeps the trial', async () => {
  const t=await setup();await t.click('Build draft and read installed modules');await t.click('Start temporary USB trial');await t.click('Undo trial')
  expect(t.undo).toHaveBeenCalledOnce();expect(t.keep).not.toHaveBeenCalled();expect(localStorage.getItem(CC_INSTALL_KEY)).toBeNull()
})
it('does not offer Keep when a legacy base passes without reporting a completed self-test', async () => {
  const t=await setup();t.control.testReported=false
  await t.click('Build draft and read installed modules');await t.click('Start temporary USB trial')
  expect(t.container.textContent).toContain('did not report a completed self-test')
  expect(button(t.container,'Keep installed')).toBeUndefined()
  expect(t.keep).not.toHaveBeenCalled()
})

it('explicitly trials an updated same-ID draft with project profile saving guidance', async () => {
  const t=await setup(true)
  expect(t.container.textContent).toContain('0.0.11-experimental')
  expect(t.container.textContent).toContain('MIDI PROFILE SAVED')
  expect(t.container.textContent).toContain('overrides only that bank')
  expect(t.container.textContent).toContain('Hold FUNC and push D at INIT')
  expect(t.container.textContent).toContain('NO cancels at a safe boundary')
  expect(t.container.textContent).not.toContain('Type APPLY')
  expect(t.container.textContent).toContain('Existing MIDI3_*.DAT and MIDI2_*.DAT profiles')
  await t.click('Build draft and read installed modules')
  expect(t.update).not.toHaveBeenCalled()
  await t.click('Try updated module')
  expect(t.update.mock.calls[0][1]).toEqual([{module:'midi-cc-slots',data:t.data}])
  expect(t.keep).not.toHaveBeenCalled()
  await t.click('Undo trial')
  expect(t.undo).toHaveBeenCalledOnce()
})

// @vitest-environment jsdom
import { act, createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import CcSlotsLab from './CcSlotsLab'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { CC_SLOTS_ID } from './cc-slots'
import type { OctatrackLink, LinkState } from '../engine/elekloader/octatrack-link'

let dispose: (() => Promise<void>) | undefined
const button = (container: HTMLElement, text: string) => [...container.querySelectorAll('button')].find(b => b.textContent === text)!
afterEach(async () => { await dispose?.(); vi.unstubAllGlobals(); vi.restoreAllMocks() })
it('compiles and reviews without sending, then sends only the draft on an explicit trial click', async () => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true)
  const data = new Uint8Array(72), view = new DataView(data.buffer)
  view.setUint32(0, 0x4d57524d); view.setUint16(4, 7); view.setUint32(28, parseInt(CC_SLOTS_ID, 16))
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ version: '0.0.4-experimental', sha256: sha(data), hex: Array.from(data,b=>b.toString(16).padStart(2,'0')).join('') }) })))
  const state: LinkState = { status: 'ready', active: 'b'.repeat(64), identity: { canSubmit: true, base: 'a'.repeat(64), model: 'MKII', capabilities: { abi: 8, features: 3, maxSites: 128, maxCopies: 128 } } }
  const update = vi.fn(async () => {}), selftest = vi.fn(async () => null)
  const link = { start: () => () => {}, getState: () => state, subscribe: () => () => {}, update, selftest, inventory: async () => [{ name: 'Existing module', module: '12345678', layout: 1, handle: 1 }] } as unknown as OctatrackLink
  const container = document.createElement('div'); document.body.append(container)
  const root = createRoot(container); dispose = async () => { await act(() => root.unmount()); container.remove() }
  await act(() => root.render(createElement(CcSlotsLab, { link })))
  expect(update).not.toHaveBeenCalled()
  expect(button(container, 'Start temporary USB trial').disabled).toBe(true)
  await act(async () => button(container, 'Build draft and read installed modules').click())
  expect(update).not.toHaveBeenCalled()
  expect(container.textContent).toContain('Existing module')
  expect(button(container, 'Start temporary USB trial').disabled).toBe(false)
  await act(async () => button(container, 'Start temporary USB trial').click())
  expect(update).toHaveBeenCalledOnce()
  const [label, changes, check] = update.mock.calls[0] as unknown as [string, {module:string;data:Uint8Array}[], () => Promise<unknown>]
  expect(label).toContain('local draft')
  expect(changes).toEqual([{ module: 'midi-cc-slots', data }])
  await check(); expect(selftest).toHaveBeenCalledOnce()
  expect(container.textContent).not.toContain('Keep trial')
})

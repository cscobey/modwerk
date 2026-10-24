import { sha } from '../../vendor/elekloader/kit/src/bytes.ts'
import type { LinkState } from '../engine/elekloader/octatrack-link'
import type { MissingModule } from '../engine/elekloader/upload-usb'

export const CC_SLOTS_ID = sha(new TextEncoder().encode('midi-cc-slots')).slice(0, 8)
export interface LocalCcPackage { version: string; sha256: string; hex: string }
export function ccPackage(document: LocalCcPackage): Uint8Array {
  if (document.version !== '0.0.4-experimental' || !/^[0-9a-f]{64}$/.test(document.sha256) || !/^(?:[0-9a-f]{2})+$/.test(document.hex) || document.hex.length > 32768) throw new Error('Invalid local CC package.')
  const data = Uint8Array.from(document.hex.match(/../g)!, byte => parseInt(byte, 16)), view = new DataView(data.buffer)
  if (data.length < 72 || view.getUint32(0) !== 0x4d57524d || view.getUint16(4) !== 7 || view.getUint32(28).toString(16).padStart(8, '0') !== CC_SLOTS_ID || sha(data) !== document.sha256) throw new Error('The local CC package failed its identity check.')
  return data
}
export function ccTrialProblem(state: LinkState, inventory: readonly MissingModule[] | undefined, reviewed: string | undefined, action: 'install' | 'remove' = 'install'): string | undefined {
  if (state.status !== 'ready' || !state.identity?.canSubmit) return 'Connect to a Modwerk base that supports module trials.'
  const caps = state.identity.capabilities
  if (!caps || caps.abi < 7 || (caps.features & 3) !== 3 || caps.maxSites < 16 || caps.maxCopies < 8) return 'This base does not report the capabilities this draft needs.'
  if (!reviewed || reviewed !== state.identity.base + ':' + state.active || !inventory) return 'Read the installed modules before starting the trial.'
  if (action === 'remove' && !inventory.some(module => module.module === CC_SLOTS_ID)) return 'MIDI CC Slots is not installed on this unit.'
  return undefined
}

export interface CcInstallRecord {
  schema: 1; base: string; packageSha256: string; action: 'install' | 'remove'; saved: boolean; restored: boolean
  expected: { module: string; layout: number }[]
}
export const CC_INSTALL_KEY = 'modwerk-local-cc-install-v1'
export function parseCcInstallRecord(value: string | null): CcInstallRecord | undefined {
  try {
    const r = JSON.parse(value ?? '') as CcInstallRecord
    if (r.schema !== 1 || !/^[0-9a-f]{64}$/.test(r.base) || !/^[0-9a-f]{64}$/.test(r.packageSha256) || !['install','remove'].includes(r.action) || typeof r.saved !== 'boolean' || typeof r.restored !== 'boolean' || !Array.isArray(r.expected) || r.expected.length > 128 || r.expected.some(m => !/^[0-9a-f]{8}$/.test(m.module) || !Number.isInteger(m.layout) || m.layout < 1 || m.layout > 65535) || new Set(r.expected.map(m => m.module)).size !== r.expected.length) return undefined
    if ((r.restored && !r.saved) || r.expected.some(m => m.module === CC_SLOTS_ID) !== (r.action === 'install')) return undefined
    return r
  } catch { return undefined }
}
export function ccExpectedModules(inventory: readonly MissingModule[], action: CcInstallRecord['action']) {
  const expected = inventory.filter(m => m.module !== CC_SLOTS_ID).map(({ module, layout }) => ({ module, layout }))
  if (action === 'install') expected.push({ module: CC_SLOTS_ID, layout: 1 })
  return expected
}
export function ccPersistenceProblem(record: CcInstallRecord, state: LinkState, inventory: readonly MissingModule[] | undefined, reading: { saved: number; savedCount: number; live: number } | undefined, restart: boolean) {
  if (state.status !== 'ready' || !state.identity || state.identity.base !== record.base) return 'Connect to the same Modwerk base used for this install.'
  if (!inventory || inventory.length !== record.expected.length || record.expected.some(want => !inventory.some(m => m.module === want.module && m.layout === want.layout))) return 'The installed module set differs from the reviewed set. Persistence is not confirmed.'
  if (!reading || reading.savedCount !== record.expected.length || reading.live !== record.expected.length) return 'The base has not confirmed the complete saved module set. Do not switch off yet.'
  if (reading.saved !== (restart ? 1 : 7)) return restart ? 'Startup restoration is not confirmed. Power-cycle only after a confirmed card save, reconnect, then check again.' : 'The card save is not confirmed. Keep the Octatrack on, check the card, then try Check card save again.'
  return undefined
}

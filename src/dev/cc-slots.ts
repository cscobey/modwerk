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
export function ccTrialProblem(state: LinkState, inventory: readonly MissingModule[] | undefined, reviewed: string | undefined): string | undefined {
  if (state.status !== 'ready' || !state.identity?.canSubmit) return 'Connect to a Modwerk base that supports module trials.'
  const caps = state.identity.capabilities
  if (!caps || caps.abi < 7 || (caps.features & 3) !== 3 || caps.maxSites < 16 || caps.maxCopies < 8) return 'This base does not report the capabilities this draft needs.'
  if (!reviewed || reviewed !== state.identity.base + ':' + state.active || !inventory) return 'Read the installed modules before starting the trial.'
  if (inventory.some(module => module.module === CC_SLOTS_ID)) return 'MIDI CC Slots is already installed. Undo or remove that copy before testing this draft.'
  return undefined
}

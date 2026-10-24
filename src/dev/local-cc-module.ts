// Opt-in development catalogue overlay. Never a published catalogue or bundled firmware asset.
import document from '../../sdk/drafts/midi-cc-slots/local-module.json'
import pin from '../../sdk/drafts/midi-cc-slots/local-build.json'

export const LOCAL_CC_ENABLED = import.meta.env?.DEV === true && import.meta.env.MODE !== 'test' && import.meta.env.VITE_LOCAL_CC_SLOTS === '1'
export const LOCAL_CC_ID = 'midi-cc-slots'
if (LOCAL_CC_ENABLED && (document.id !== LOCAL_CC_ID || document.version !== pin.version)) throw new Error('The local Midi Mode 2 listing does not match its verified package version.')
export const isLocalCcModule = (id: string) => LOCAL_CC_ENABLED && id === LOCAL_CC_ID
export const localCcDocuments = LOCAL_CC_ENABLED ? [document] : []
export const localCcPackages = LOCAL_CC_ENABLED ? [{ id: LOCAL_CC_ID, name: 'Midi Mode 2', version: pin.version, path: '__local/midi-cc-slots/package.mwrm', sha256: pin.sha256, bytes: 1914, abi: 7, features: 3, sites: 16, copies: 8 }] : []

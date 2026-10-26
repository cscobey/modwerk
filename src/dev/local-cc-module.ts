// SPDX-License-Identifier: GPL-3.0-or-later OR Elastic-2.0
// Copyright (c) 2026 Jannik Aßfalg (repeat98)
// Copyright (c) 2026 Cooper Scobey
// Opt-in development catalogue overlay. Never a published catalogue or bundled firmware asset.
import document from '../../sdk/drafts/midi-cc-slots/local-module.json' with { type: 'json' }
import pin from '../../sdk/drafts/midi-cc-slots/local-build.json' with { type: 'json' }
import card from '../../sdk/drafts/midi-cc-slots/local-card-build.json' with {type:'json'}
import compiled from '../engine/assets/module-build.json' with {type:'json'}

export const LOCAL_CC_ENABLED = import.meta.env?.DEV === true && import.meta.env.MODE !== 'test' && import.meta.env.VITE_LOCAL_CC_SLOTS === '1'
export const LOCAL_CC_ID = 'midi-cc-slots'
if (LOCAL_CC_ENABLED && (document.id !== LOCAL_CC_ID || document.version !== pin.version)) throw new Error('The local Midi Mode 2 listing does not match its verified package version.')
export const isLocalCcModule = (id: string) => LOCAL_CC_ENABLED && id === LOCAL_CC_ID
export const localCcDocuments = LOCAL_CC_ENABLED ? [document] : []
export const localCcPackages = LOCAL_CC_ENABLED ? [{ id: LOCAL_CC_ID, name: 'Midi Mode 2', version: pin.version, path: '__local/midi-cc-slots/package.mwrm', sha256: pin.sha256, bytes: pin.bytes, abi: pin.abi, features: pin.features, sites: pin.sites, copies: pin.copies, fills: pin.fills }] : []

// Keep the local walkthrough short; remaining CC pages stay under More screenshots.
export const localCcMediaGuide = LOCAL_CC_ENABLED ? { version: document.version, screenshots: document.media.map((item,index) => ({ path:item.path,caption:item.caption,alt:item.alt,additional:index>=5 })) } : undefined

// A recorded local combination is tied to the exact published companion build.
export function localCcCardBaselineProblem(actual: {sourceTreeSha256: string; moduleVersions: Readonly<Record<string,string>>}=compiled): string {
  return actual.sourceTreeSha256!==card.nativeSourceTreeSha256 || Object.entries(card.nativeModuleVersions).some(([id,version])=>actual.moduleVersions[id]!==version)
    ? 'The published module build changed. Recheck the local Midi Mode 2 card combinations before building.' : ''
}

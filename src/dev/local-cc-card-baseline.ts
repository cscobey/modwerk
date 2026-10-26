// SPDX-License-Identifier: GPL-3.0-or-later
import card from '../../sdk/drafts/midi-cc-slots/local-card-build.json' with {type:'json'}
import compiled from '../engine/assets/module-build.json' with {type:'json'}
// A recorded local combination is tied to the exact published companion build.
export function localCcCardBaselineProblem(actual: {sourceTreeSha256: string; moduleVersions: Readonly<Record<string,string>>}=compiled): string {
  return actual.sourceTreeSha256!==card.nativeSourceTreeSha256 || Object.entries(card.nativeModuleVersions).some(([id,version])=>actual.moduleVersions[id]!==version)
    ? 'The published module build changed. Recheck the local Midi Mode 2 card combinations before building.' : ''
}

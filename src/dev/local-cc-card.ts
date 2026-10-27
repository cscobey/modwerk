// SPDX-License-Identifier: GPL-3.0-or-later
import { LOCAL_CC_ENABLED } from './local-cc-module.ts'
import { localCcCardBaselineProblem } from './local-cc-card-baseline.ts'
import pin from '../../sdk/drafts/midi-cc-slots/local-card-build.json' with {type:'json'}
import { loggerHash } from '../engine/core-logger.ts'
import type { ResidentCard } from '../engine/resident-card.ts'
export const localCardPin=pin
let cached: Promise<ResidentCard> | undefined
export function localCcCard(): Promise<ResidentCard> {
  return cached ??= load().catch(error=>{cached=undefined;throw error})
}
async function load(): Promise<ResidentCard> {
  if(!LOCAL_CC_ENABLED) throw new Error('Local card packaging is disabled.')
  const baseline=localCcCardBaselineProblem()
  if(baseline)throw new Error(baseline)
  const response=await fetch('/__local/midi-cc-slots/card.json')
  if(!response.ok) throw new Error('The local card package did not compile. Check the local development tools.')
  const data=new Uint8Array(await response.arrayBuffer())
  if(await loggerHash(data)!==pin.sha256) throw new Error('The local card package differs from the reviewed build.')
  const pkg=JSON.parse(new TextDecoder().decode(data)) as ResidentCard
  if(pkg.version!==pin.version || pkg.implementationSha256!==pin.implementationSha256 || pkg.objectSha256!==pin.objectSha256) throw new Error('The local card identity does not match.')
  return pkg
}

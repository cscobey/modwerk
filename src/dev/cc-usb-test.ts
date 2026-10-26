// SPDX-License-Identifier: GPL-3.0-or-later
import original from '../../sdk/drafts/midi-cc-slots/local-build.json' with { type: 'json' }
import test from '../../sdk/drafts/midi-cc-slots/local-usb-test.json' with { type: 'json' }
import { sha } from '../../vendor/elekloader/kit/src/bytes.ts'
import { decodeCardSeed } from '../engine/elekloader/card-seed.ts'
import type { SavedSetSnapshot } from '../engine/elekloader/upload-wire.ts'
import type { MissingModule } from '../engine/elekloader/upload-usb.ts'
export { original, test }
export type Revision = 'original' | 'test'
export interface PackageRow { module: string; sha256: string }
export const TEST_RECORD_KEY = 'modwerk-midi-usb-test-v1'
const ID='f36a496d'
export const revisionPin=(revision:Revision)=>revision==='test'?test:{...original,title:test.originalTitle}
/** Label-only package revision: no compiler, image, relocation, hook, site or project-format changes. */
export function makeUsbTestPackage(data:Uint8Array) {
  if(data.length!==original.bytes||sha(data)!==original.sha256)throw new Error('The original package differs from the reviewed 0.0.13 build.')
  const result=data.slice();result.fill(0,50,66);result.set(new TextEncoder().encode(test.title),50)
  if(sha(result)!==test.sha256)throw new Error('The test revision differs from its reviewed hash.')
  return result
}
export function verifiedTestDocument(document:{version:string;sha256:string;hex:string},revision:Revision) {
  const pin=revisionPin(revision)
  if(document.version!==pin.version||document.sha256!==pin.sha256||document.hex.length!==pin.bytes*2||!/^[0-9a-f]+$/.test(document.hex))throw new Error('Wrong USB test package identity.')
  const data=Uint8Array.from(document.hex.match(/../g)!,s=>parseInt(s,16))
  if(sha(data)!==pin.sha256)throw new Error('Damaged USB test package.')
  return data
}
/** Same MWS1 identity as runtime_journal_set_digest, including every companion's original package hash. */
export function packageSetDigest(rows:readonly PackageRow[]) {
  if(!rows.length||rows.length>128||rows.some(r=>! /^[0-9a-f]{8}$/.test(r.module)||r.module==='00000000'||! /^[0-9a-f]{64}$/.test(r.sha256))||new Set(rows.map(r=>r.module)).size!==rows.length)throw new Error('Invalid reviewed module set.')
  const data=new Uint8Array(8+rows.length*36),v=new DataView(data.buffer)
  data.set(new TextEncoder().encode('MWS1'));v.setUint32(4,rows.length)
  ;[...rows].sort((a,b)=>a.module.localeCompare(b.module)).forEach((r,i)=>{const at=8+36*i;v.setUint32(at,parseInt(r.module,16));data.set(Uint8Array.from(r.sha256.match(/../g)!,s=>parseInt(s,16)),at+4)})
  return sha(data)
}
export function replaceRevision(rows:readonly PackageRow[],revision:Revision) {
  if(!rows.some(r=>r.module===ID))throw new Error('Midi Mode 2 is missing.')
  return rows.map(r=>r.module===ID?{module:ID,sha256:revisionPin(revision).sha256}:{...r})
}
export function inventoryProblem(rows:readonly PackageRow[],modules:readonly MissingModule[],revision:Revision) {
  if(modules.length!==rows.length||rows.some(r=>!modules.some(m=>m.module===r.module)))return 'The installed companion/module list changed.'
  if(modules.find(m=>m.module===ID)?.name!==revisionPin(revision).title)return 'The device did not report the expected MIDI revision name.'
}
/** Use both read-only snapshots. Padding after the logical body is unspecified after ordinary Keep. */
export function readSavedPackages(snapshots:readonly SavedSetSnapshot[]|undefined,base:string) {
  if(!snapshots||snapshots.length!==2||new Set(snapshots.map(s=>s.slot)).size!==2)throw new Error('Both saved module files must be readable for this test.')
  const candidates=snapshots.map(s=>{
    if(s.status!=='ready'||s.fileBase!==base||sha(s.data)!==s.sha256||s.data.length!==s.length||s.data.length<84)throw new Error('A saved module file is unavailable or belongs to another base.')
    const data=s.data.slice(),used=new DataView(data.buffer).getUint32(16)
    if(used<84||used>data.length)throw new Error('Invalid saved module file length.')
    data.fill(0,used)
    return {...decodeCardSeed(data,base),slot:s.slot}
  }).sort((a,b)=>b.generation-a.generation||a.slot-b.slot)
  if(candidates[0].generation===candidates[1].generation&&shaRows(candidates[0].packages)!==shaRows(candidates[1].packages))throw new Error('Equal saved-file generations disagree.')
  return candidates[0].packages.map(p=>({module:new DataView(p.buffer,p.byteOffset,p.length).getUint32(28).toString(16).padStart(8,'0'),sha256:sha(p)}))
}
function shaRows(packages:Uint8Array[]) {return packageSetDigest(packages.map(p=>({module:new DataView(p.buffer,p.byteOffset,p.length).getUint32(28).toString(16).padStart(8,'0'),sha256:sha(p)})))}
export function revisionOf(rows:readonly PackageRow[]):Revision {
  const hash=rows.find(r=>r.module===ID)?.sha256
  if(hash===original.sha256)return 'original'
  if(hash===test.sha256)return 'test'
  throw new Error('The installed MIDI package is neither reviewed test revision. No update was started.')
}
export interface TestReceipt {schema:1;base:string;revision:Revision;rows:PackageRow[];saved:boolean;restored:boolean;undoVerified:boolean}
export function parseTestReceipt(value:string|null):TestReceipt|undefined {
  try {const r=JSON.parse(value??'') as TestReceipt
    if(r.schema!==1||r.base!==test.base||!['original','test'].includes(r.revision)||typeof r.saved!=='boolean'||typeof r.restored!=='boolean'||typeof r.undoVerified!=='boolean'||r.restored&&!r.saved)return
    packageSetDigest(r.rows);if(revisionOf(r.rows)!==r.revision)return
    return r
  }catch{return}
}

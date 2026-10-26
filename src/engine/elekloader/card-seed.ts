// SPDX-License-Identifier: GPL-3.0-or-later
// MWST v1, the existing modset.c on-card format. Packages stay unrelocated;
// the unchanged base performs normal prepare/publish at boot, as after Keep.
import {sha} from '../../../vendor/elekloader/kit/src/bytes.ts'
export const SAVED_SET_CAPACITY=768*1024+4096
const HEADER=84,align=(n:number,a:number)=>Math.ceil(n/a)*a
function moduleId(data: Uint8Array) {
  if(data.length<68)throw new Error('Incomplete installer module.')
  const v=new DataView(data.buffer,data.byteOffset,data.byteLength)
  if(v.getUint32(0)!==0x4d57524d || v.getUint16(4)<6 || v.getUint16(4)>10 || !v.getUint32(28) || !v.getUint32(8))throw new Error('Invalid installer module.')
  return v.getUint32(28)
}
export function encodeCardSeed(base:string,packages:readonly Uint8Array[],generation:number):Uint8Array {
  if(!/^[0-9a-f]{64}$/.test(base)||!packages.length||packages.length>128||!Number.isInteger(generation)||generation<1||generation>0xffffffff)throw new Error('Invalid installer saved-set identity.')
  const ids=packages.map(moduleId)
  if(new Set(ids).size!==ids.length)throw new Error('Repeated installer module.')
  const used=HEADER+packages.reduce((n,p)=>n+8+align(p.length,4),0),length=align(used,512)
  if(length>SAVED_SET_CAPACITY)throw new Error('Installer saved set exceeds the base capacity.')
  const data=new Uint8Array(length),v=new DataView(data.buffer)
  v.setUint32(0,0x4d575354);v.setUint32(4,1);v.setUint32(8,generation);v.setUint32(12,packages.length);v.setUint32(16,used)
  data.set(Uint8Array.from(base.match(/../g)!,s=>parseInt(s,16)),20)
  let at=HEADER
  packages.forEach((pkg,i)=>{v.setUint32(at,ids[i]);v.setUint32(at+4,pkg.length);data.set(pkg,at+8);at+=8+align(pkg.length,4)})
  data.set(Uint8Array.from(sha(data.subarray(HEADER,used)).match(/../g)!,s=>parseInt(s,16)),52)
  return data
}
export function decodeCardSeed(data:Uint8Array,base:string) {
  const v=new DataView(data.buffer,data.byteOffset,data.byteLength)
  if(data.length<HEADER||data.length>SAVED_SET_CAPACITY||data.length%512||v.getUint32(0)!==0x4d575354||v.getUint32(4)!==1)throw new Error('Invalid installer saved set.')
  const used=v.getUint32(16),count=v.getUint32(12)
  const hex=(b:Uint8Array)=>Array.from(b,n=>n.toString(16).padStart(2,'0')).join('')
  if(!v.getUint32(8)||!count||count>128||used<HEADER||used>data.length||align(used,512)!==data.length||hex(data.subarray(20,52))!==base||sha(data.subarray(HEADER,used))!==hex(data.subarray(52,84))||data.subarray(used).some(Boolean))throw new Error('Installer saved-set identity or checksum mismatch.')
  let at=HEADER;const packages:Uint8Array[]=[],ids=new Set<number>()
  while(at<used) {
    if(at+8>used)throw new Error('Truncated installer module record.')
    const id=v.getUint32(at),length=v.getUint32(at+4),end=at+8+align(length,4)
    if(end>used||ids.has(id))throw new Error('Invalid installer module extent.')
    const pkg=data.slice(at+8,at+8+length)
    if(moduleId(pkg)!==id||data.subarray(at+8+length,end).some(Boolean))throw new Error('Invalid installer module identity.')
    ids.add(id);packages.push(pkg);at=end
  }
  if(packages.length!==count)throw new Error('Installer module count mismatch.')
  return {generation:v.getUint32(8),packages}
}

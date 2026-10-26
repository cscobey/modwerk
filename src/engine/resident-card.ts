// SPDX-License-Identifier: GPL-3.0-or-later
// Stock-free resident objects use the existing ColdFire linker, arena and boot
// copier. No second core boot hook or arena reservation may be installed.
import { parseColdFireObject } from './coldfire-elf.ts'
import type { CfLinkInput, CfRuntimeLink } from './coldfire-link.ts'
import { loggerHash } from './core-logger.ts'
import { OS_LOAD_ADDRESS, type OsWrite } from './os-patches.ts'
export type ResidentCard = {
  schema: number; kind: string; moduleId: string; version: string; firmwareLabel: string
  implementationSha256: string; coreCommit: string; busSourceSha256: string
  object: string; objectSha256: string; imageSymbol: string
  copies: { offset: number; address: number; length: number; sha256: string }[]
  sites: {addr: string; len: number; stock_sha256: string; new: string; relocs: [number,string,string,number][]}[]
  busSites: { address: number; length: number; sha256: string; target: string }[]
}
const hex = (value: string) => {
  if (!/^(?:[0-9a-f]{2})+$/.test(value)) throw new Error('Invalid resident card bytes.')
  return Uint8Array.from(value.match(/../g)!, b=>parseInt(b,16))
}
export async function residentCardObject(pkg: ResidentCard, original: Uint8Array): Promise<CfLinkInput> {
  if(pkg.schema!==1 || pkg.kind!=='resident-card-object' || !/^[a-z0-9-]+$/.test(pkg.moduleId)) throw new Error('Invalid resident card package.')
  const bytes=hex(pkg.object)
  if(await loggerHash(bytes)!==pkg.objectSha256) throw new Error('Resident card object checksum mismatch.')
  const object=parseColdFireObject(bytes),image=object.symbols.find(s=>s.name===pkg.imageSymbol)
  if(!image || !image.section || image.section>=object.sections.length) throw new Error('Missing resident image symbol.')
  const section=object.sections[image.section]
  const ranges: [number,number][]=[]
  for(const copy of pkg.copies) {
    const at=image.value+copy.offset,source=copy.address-OS_LOAD_ADDRESS
    if(!Number.isSafeInteger(copy.offset) || copy.offset<0 || !Number.isSafeInteger(at) || !Number.isSafeInteger(source) || !Number.isSafeInteger(copy.length) || copy.length<1 || at<0 || at+copy.length>section.data.length || source<0 || source+copy.length>original.length || ranges.some(([a,b])=>at<b&&a<at+copy.length) || section.data.slice(at,at+copy.length).some(Boolean) || object.relocations.some(r=>r.section===image.section&&r.offset<at+copy.length&&at<r.offset+4)) throw new Error('Invalid resident stock copy.')
    const data=original.slice(source,source+copy.length)
    if(await loggerHash(data)!==copy.sha256) throw new Error('Resident stock copy guard mismatch.')
    section.data.set(data,at);ranges.push([at,at+copy.length])
  }
  return {label:'resident-'+pkg.moduleId,object}
}
export function residentCardWrites(pkg: ResidentCard,runtime: CfRuntimeLink): OsWrite[] {
  const symbol=(name: string)=>{
    const value=runtime.symbols.get(name)
    if(value===undefined || !runtime.sections.some(s=>value>=s.address&&value<s.address+s.size)) throw new Error('Missing resident card symbol: '+name)
    return value
  }
  const image=symbol(pkg.imageSymbol)
  return [
    ...pkg.busSites.map(site=>{
      const bytes=new Uint8Array(site.length),v=new DataView(bytes.buffer)
      if(site.length!==6) throw new Error('Unsupported resident bus site.')
      v.setUint16(0,0x4eb9);v.setUint32(2,symbol(site.target))
      return {address:site.address,guardLength:site.length,guardSha256:site.sha256,bytes,note:'resident event bus '+pkg.moduleId}
    }),
    ...pkg.sites.map(site=>{
      const bytes=hex(site.new),v=new DataView(bytes.buffer)
      if(bytes.length!==site.len) throw new Error('Invalid resident site extent.')
      for(const [at,kind,target,addend] of site.relocs) {
        if(kind!=='abs32'||target!=='sec:.run'||!Number.isInteger(at)||at<0||at+4>bytes.length||!Number.isInteger(addend)||addend<0) throw new Error('Unsupported resident site relocation.')
        v.setUint32(at,image+addend)
      }
      return {address:Number(site.addr),guardLength:site.len,guardSha256:site.stock_sha256,bytes,note:'resident '+pkg.moduleId}
    }),
  ]
}

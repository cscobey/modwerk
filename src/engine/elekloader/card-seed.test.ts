import {it,expect} from 'vitest'
import {encodeCardSeed,decodeCardSeed} from './card-seed'
import {storedZip} from '../stored-zip'
import {members,read} from '../../../vendor/elekloader/kit/src/zip'
const base='a'.repeat(64)
function pkg(id:number){const b=new Uint8Array(80),v=new DataView(b.buffer);v.setUint32(0,0x4d57524d);v.setUint16(4,8);v.setUint32(8,4);v.setUint32(28,id);return b}
it('writes sector-aligned saved sets with independent generations and exact original packages',()=>{
 const packages=[pkg(7),pkg(8)],a=encodeCardSeed(base,packages,1),b=encodeCardSeed(base,packages,2)
 expect(a.length%512).toBe(0);expect(a).not.toEqual(b)
 expect(decodeCardSeed(a,base)).toEqual({generation:1,packages});expect(decodeCardSeed(b,base)).toEqual({generation:2,packages})
 expect(()=>decodeCardSeed(a,'b'.repeat(64))).toThrow('identity')
 for(const at of [4,12,52,100,a.length-1]){const bad=a.slice();bad[at]^=1;expect(()=>decodeCardSeed(bad,base)).toThrow()}
 expect(()=>encodeCardSeed(base,[pkg(7),pkg(7)],1)).toThrow('Repeated')
 expect(()=>encodeCardSeed(base,[],1)).toThrow();expect(()=>encodeCardSeed(base,[pkg(7)],0)).toThrow()
})
it('creates a deterministic archive readable by the unchanged kit, with CRC and safe root names',async()=>{
 const data=encodeCardSeed(base,[pkg(7)],1),files=new Map([['MODWERK0.SET',data],['INSTALL.txt',new TextEncoder().encode('Install instructions')]])
 const zip=storedZip(files),entries=members(zip)
 expect(zip).toEqual(storedZip(files));expect(entries.map(e=>e.filename)).toEqual([...files.keys()])
 for(const e of entries)expect(await read(zip,e)).toEqual(files.get(e.filename))
 const bad=zip.slice();bad[30+entries[0].filename.length+100]^=1
 await expect(read(bad,entries[0])).rejects.toThrow('CRC')
 expect(()=>storedZip(new Map([['../card.bin',data]]))).toThrow('member')
})

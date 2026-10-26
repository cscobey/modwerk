import { expect,it } from 'vitest'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { encodeCardSeed } from '../engine/elekloader/card-seed'
import type { SavedSetSnapshot } from '../engine/elekloader/upload-wire'
import { packageSetDigest,readSavedPackages,replaceRevision,revisionOf,verifiedTestDocument,inventoryProblem,parseTestReceipt,makeUsbTestPackage,original,test } from './cc-usb-test'
function pkg(id:number){const b=new Uint8Array(80),v=new DataView(b.buffer);v.setUint32(0,0x4d57524d);v.setUint16(4,8);v.setUint32(8,4);v.setUint32(28,id);return b}
function snapshot(slot:0|1,generation:number,packages:Uint8Array[]):SavedSetSnapshot {const data=encodeCardSeed(test.base,packages,generation);return {slot,status:'ready',token:1,length:data.length,fileBase:test.base,sha256:sha(data),data}}
it('matches the C MWS1 sorted id/hash encoding and rejects duplicate/invalid rows',()=>{
 const rows=[{module:'f36a496d',sha256:original.sha256},{module:'12345678',sha256:'a'.repeat(64)}]
 const bytes=new Uint8Array(80);bytes.set([77,87,83,49,0,0,0,2,0x12,0x34,0x56,0x78]);bytes.fill(0xaa,12,44);bytes.set([0xf3,0x6a,0x49,0x6d],44);bytes.set(Uint8Array.from(original.sha256.match(/../g)!,s=>parseInt(s,16)),48)
 expect(packageSetDigest(rows)).toBe(sha(bytes));expect(packageSetDigest([...rows].reverse())).toBe(sha(bytes))
 expect(()=>packageSetDigest([rows[0],rows[0]])).toThrow();expect(()=>packageSetDigest([{module:'0',sha256:'a'}])).toThrow()
 const changed=replaceRevision(rows,'test');expect(changed[1]).toEqual(rows[1]);expect(revisionOf(changed)).toBe('test');expect(replaceRevision(changed,'original')).toEqual(rows)
 expect(()=>revisionOf([{module:'f36a496d',sha256:'0'.repeat(64)}])).toThrow('neither')
})
it('selects the newest saved set, validates both and tolerates ordinary Keep tail padding',()=>{
 const older=snapshot(0,1,[pkg(7)]),newer=snapshot(1,2,[pkg(7),pkg(8)])
 expect(readSavedPackages([older,newer],test.base)).toHaveLength(2)
 if(newer.status!=='ready')throw Error();newer.data[newer.data.length-1]=99;newer.sha256=sha(newer.data)
 expect(readSavedPackages([older,newer],test.base)).toHaveLength(2)
 expect(()=>readSavedPackages([older],test.base)).toThrow('Both')
 expect(()=>readSavedPackages([older,{...newer,fileBase:'a'.repeat(64)}],test.base)).toThrow('another base')
 newer.data[100]^=1;newer.sha256=sha(newer.data)
 expect(()=>readSavedPackages([older,newer],test.base)).toThrow('checksum')
 expect(()=>readSavedPackages([older,snapshot(1,1,[pkg(8)])],test.base)).toThrow('disagree')
})
it('pins both test documents and refuses substituted or corrupted payloads and arbitrary baseline derivation',()=>{
 expect(()=>verifiedTestDocument({version:test.version,sha256:test.sha256,hex:'00'.repeat(test.bytes)},'test')).toThrow('Damaged')
 expect(()=>verifiedTestDocument({version:original.version,sha256:test.sha256,hex:'00'.repeat(test.bytes)},'test')).toThrow('identity')
 expect(()=>makeUsbTestPackage(new Uint8Array(original.bytes))).toThrow('original package')
})
it('requires the complete companion inventory, visible revision, and a bounded valid saved receipt',()=>{
 const rows=[{module:'f36a496d',sha256:original.sha256},{module:'12345678',sha256:'a'.repeat(64)}],modules=rows.map(r=>({...r,name:r.module==='f36a496d'?test.originalTitle:'Companion',layout:1,handle:1}))
 expect(inventoryProblem(rows,modules,'original')).toBeUndefined();expect(inventoryProblem(rows,modules.slice(0,1),'original')).toContain('list changed');expect(inventoryProblem(rows,modules,'test')).toContain('revision name')
 const receipt={schema:1,base:test.base,rows,revision:'original',saved:true,restored:false,undoVerified:true}
 expect(parseTestReceipt(JSON.stringify(receipt))).toEqual(receipt)
 for(const invalid of [{...receipt,base:'a'.repeat(64)},{...receipt,saved:false,restored:true},{...receipt,revision:'test'},{...receipt,rows:[]},{...receipt,rows:[...rows,...rows]}])expect(parseTestReceipt(JSON.stringify(invalid))).toBeUndefined()
})

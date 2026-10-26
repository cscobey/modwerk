import {it,expect,vi} from 'vitest'
import {residentCardObject,residentCardWrites,type ResidentCard} from './resident-card'
import {loggerHash} from './core-logger'
import {parseColdFireObject,type CfObject} from './coldfire-elf'
import {OS_LOAD_ADDRESS,applyGuardedOsWrites} from './os-patches'
vi.mock('./coldfire-elf',()=>({parseColdFireObject:vi.fn()}))
const base=0x40a955e0
async function fixture(){
 const original=Uint8Array.from({length:64},(_,i)=>i),object: CfObject={flags:0,sections:[{index:0,name:'',type:0,flags:0,size:0,alignment:1,entrySize:0,data:new Uint8Array()},{index:1,name:'.text',type:1,flags:6,size:64,alignment:16,entrySize:0,data:new Uint8Array(64)}],symbols:[{index:0,name:'image',value:16,size:0,binding:1,type:0,section:1}],relocations:[]}
 vi.mocked(parseColdFireObject).mockImplementation(()=>structuredClone(object))
 const pkg: ResidentCard={schema:1,kind:'resident-card-object',moduleId:'synthetic',version:'test',firmwareLabel:'TEST',implementationSha256:'a'.repeat(64),coreCommit:'b'.repeat(40),busSourceSha256:'c'.repeat(64),object:'010203',objectSha256:await loggerHash(new Uint8Array([1,2,3])),imageSymbol:'image',copies:[{offset:4,address:OS_LOAD_ADDRESS+8,length:4,sha256:await loggerHash(original.slice(8,12))}],busSites:[{address:OS_LOAD_ADDRESS,length:6,sha256:await loggerHash(original.slice(0,6)),target:'bus'}],sites:[{addr:'0x'+(OS_LOAD_ADDRESS+20).toString(16),len:6,stock_sha256:await loggerHash(original.slice(20,26)),new:'4ef900000000',relocs:[[2,'abs32','sec:.run',4]]}]}
 const runtime={bytes:new Uint8Array(64),symbols:new Map([['image',base+16],['bus',base]]),placements:new Map(),sections:[{name:'.text',address:base,size:64}],memoryEnd:base+64}
 return {pkg,original,object,runtime}
}
it('reconstructs checked stock locally and relocates sites through the existing linker symbols',async()=>{
 const {pkg,original,runtime}=await fixture(),before=original.slice(),unit=await residentCardObject(pkg,original)
 expect(unit.label).toBe('resident-synthetic');expect(unit.object.sections[1].data.slice(20,24)).toEqual(original.slice(8,12));expect(original).toEqual(before)
 const writes=residentCardWrites(pkg,runtime),patched=await applyGuardedOsWrites(original,writes)
 expect(new DataView(patched.buffer).getUint32(22)).toBe(base+20)
 expect(new DataView(patched.buffer).getUint16(0)).toBe(0x4eb9)
 expect(original).toEqual(before)
 await expect(applyGuardedOsWrites(original,[...writes,writes[0]])).rejects.toThrow('overlapping')
})
it('refuses changed objects, nonzero placeholders, overlapping copies and wrong stock before linking',async()=>{
 const {pkg,original,object}=await fixture()
 await expect(residentCardObject({...pkg,object:'010204'},original)).rejects.toThrow('checksum')
 const bad=original.slice();bad[8]^=1
 await expect(residentCardObject(pkg,bad)).rejects.toThrow('guard')
 await expect(residentCardObject({...pkg,copies:[...pkg.copies,...pkg.copies]},original)).rejects.toThrow('copy')
 await expect(residentCardObject({...pkg,copies:[{...pkg.copies[0],offset:-4}]},original)).rejects.toThrow('copy')
 object.sections[1].data[20]=1
 vi.mocked(parseColdFireObject).mockReturnValue(object)
 await expect(residentCardObject(pkg,original)).rejects.toThrow('copy')
})
it('refuses missing symbols and unsupported site relocations',async()=>{
 const {pkg,runtime}=await fixture()
 expect(()=>residentCardWrites(pkg,{...runtime,symbols:new Map()})).toThrow('symbol')
 pkg.sites[0].relocs[0][0]=4
 expect(()=>residentCardWrites(pkg,runtime)).toThrow('relocation')
})

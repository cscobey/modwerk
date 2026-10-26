// SPDX-License-Identifier: GPL-3.0-or-later
// A bounded, uncompressed ZIP for locally generated installers (BIN is already packed).
export function storedZip(files:ReadonlyMap<string,Uint8Array>):Uint8Array {
  if(!files.size||files.size>128)throw new Error('Invalid installer archive size.')
  const parts:Uint8Array[]=[],central:Uint8Array[]=[];let offset=0
  const crc=(data:Uint8Array)=>{let n=0xffffffff;for(const b of data){n^=b;for(let k=0;k<8;k++)n=(n>>>1)^((n&1)?0xedb88320:0)}return(n^0xffffffff)>>>0}
  for(const [path,data] of files){
    if(!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(path)||path.includes('..')||data.length>16*1024*1024)throw new Error('Invalid installer archive member.')
    const name=new TextEncoder().encode(path),sum=crc(data),local=new DataView(new ArrayBuffer(30)),entry=new DataView(new ArrayBuffer(46))
    local.setUint32(0,0x04034b50,true);local.setUint16(4,20,true);local.setUint16(12,33,true)
    local.setUint32(14,sum,true);local.setUint32(18,data.length,true);local.setUint32(22,data.length,true);local.setUint16(26,name.length,true)
    entry.setUint32(0,0x02014b50,true);entry.setUint16(4,20,true);entry.setUint16(6,20,true);entry.setUint16(14,33,true)
    entry.setUint32(16,sum,true);entry.setUint32(20,data.length,true);entry.setUint32(24,data.length,true);entry.setUint16(28,name.length,true);entry.setUint32(42,offset,true)
    parts.push(new Uint8Array(local.buffer),name,data);central.push(new Uint8Array(entry.buffer),name);offset+=30+name.length+data.length
    if(offset>32*1024*1024)throw new Error('Installer archive exceeds its limit.')
  }
  const size=central.reduce((n,p)=>n+p.length,0),end=new DataView(new ArrayBuffer(22))
  end.setUint32(0,0x06054b50,true);end.setUint16(8,files.size,true);end.setUint16(10,files.size,true);end.setUint32(12,size,true);end.setUint32(16,offset,true)
  const all=[...parts,...central,new Uint8Array(end.buffer)],output=new Uint8Array(offset+size+22);let at=0
  for(const part of all){output.set(part,at);at+=part.length}return output
}

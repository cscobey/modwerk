// SPDX-License-Identifier: GPL-3.0-or-later
import {isLocalCcModule,LOCAL_CC_ENABLED} from './local-cc-module.ts'
import midiLicense from '../../sdk/drafts/midi-cc-slots/LICENSE?raw'
import {assetUrl} from '../hosting.ts'
import pin from '../../sdk/drafts/midi-cc-slots/local-usb-installer.json' with {type:'json'}
import {checkSelection} from '../catalog/compatibility.ts'
import {localCcCardBaselineProblem} from './local-cc-card-baseline.ts'
import {CURRENT_BASE,prepareModuleSet,fetchPackage} from '../engine/elekloader/module-set.ts'
import {encodeCardSeed,decodeCardSeed} from '../engine/elekloader/card-seed.ts'
import {buildBase,type BaseFill} from '../engine/elekloader/octatrack-base.ts'
import {storedZip} from '../engine/stored-zip.ts'
import {sha} from '../../vendor/elekloader/kit/src/bytes.ts'
export const INSTALLER_CAPABILITIES=pin.capabilities
export async function buildLocalCcInstaller(stock:Uint8Array,moduleIds:readonly string[],packageText:string,fills:readonly BaseFill[]) {
  if(!LOCAL_CC_ENABLED||!moduleIds.some(isLocalCcModule))throw new Error('Local USB card installer is disabled.')
  const baseline=localCcCardBaselineProblem();if(baseline)throw new Error(baseline)
  const compatibility=checkSelection(moduleIds)
  if(!compatibility.checked||compatibility.issues.length)throw new Error(compatibility.issues.join(' ')||'Installer selection is unreviewed.')
  if(CURRENT_BASE!==pin.base)throw new Error('The published USB base changed; recheck this installer.')
  const target={name:'Midi Mode 2 USB installer',moduleIds:[...moduleIds],removedStockFx:[]}
  // Same manifest checks, base requirements, package validation and hashes as USB Sync.
  const set=await prepareModuleSet(target,{moduleIds:[],removedStockFx:[]},fetchPackage,INSTALLER_CAPABILITIES,CURRENT_BASE)
  let facts:Parameters<NonNullable<Parameters<typeof buildBase>[3]>>[0]|undefined
  const base=await buildBase(stock,packageText,fills,result=>{facts=result})
  if(base.base!==CURRENT_BASE||!facts)throw new Error('The installer base differs from the published base.')
  const packages=set.changes.map(c=>c.data)
  for(const pkg of packages){const id=new DataView(pkg.buffer,pkg.byteOffset,pkg.byteLength).getUint32(28).toString(16).padStart(8,'0');if((pin.packages as Record<string,string>)[id]!==sha(pkg))throw new Error('Installer module changed since review: '+id)}
  const zero=encodeCardSeed(base.base,packages,1),one=encodeCardSeed(base.base,packages,2)
  decodeCardSeed(zero,base.base);decodeCardSeed(one,base.base)
  const files=new Map<string,Uint8Array>([['Modwerk-USB-base.bin',base.bin],['MODWERK0.SET',zero],['MODWERK1.SET',one]])
  const notices=await fetch(assetUrl('licenses/THIRD_PARTY_NOTICES.txt'))
  if(!notices.ok)throw new Error('Installer copyright notices did not load.')
  files.set('THIRD_PARTY_NOTICES.txt',new Uint8Array(await notices.arrayBuffer()))
  files.set('Midi-Mode-2-LICENSE.txt',new TextEncoder().encode(midiLicense))
  const receipt={format:'modwerk-usb-card-installer-v1',version:'0.0.16-experimental',base:base.base,baseSha256:base.sha256,moduleIds:[...moduleIds],modules:packages.map(p=>({id:new DataView(p.buffer,p.byteOffset,p.byteLength).getUint32(28).toString(16).padStart(8,'0'),bytes:p.length,sha256:sha(p)})),files:Object.fromEntries([...files].map(([n,b])=>[n,{bytes:b.length,sha256:sha(b)}])),hardware:'not tested'}
  files.set('installer-receipt.json',new TextEncoder().encode(JSON.stringify(receipt,null,2)+'\n'))
  files.set('INSTALL.txt',new TextEncoder().encode(`Modwerk USB-capable card installer — private test\n\nThis installs the unchanged current Modwerk USB base and the complete selected module set. It is a ZIP containing three card files, not one combined firmware BIN.\n\n1. Back up your entire CF card and keep your known firmware available. Use a backed-up test project.\n2. Enter USB DISK MODE. Back up existing MODWERK0.SET and MODWERK1.SET off the card, then replace BOTH with the two included files. This replaces the kept module set with exactly the selected set. Do not merge with old files or retain one old generation.\n3. Copy Modwerk-USB-base.bin to the card root. Keep other firmware BIN files away from the root during this test.\n4. Safely eject, exit disk mode, then PROJECT > SYSTEM > OS UPGRADE and confirm. Keep power connected until complete.\n5. Boot normally without holding FUNC. Wait for MODULES LOADED. The OS label is ELEKLOADER; the full base identity is ${base.base}.\n6. Connect from Your Octatrack in the local app. Confirm the exact base and all selected modules, then run self-test. Do not Keep a partial or failed restoration.\n7. Check MIDI names/channels/CC controls and each companion. Save, power-cycle, reconnect and verify restoration.\n8. Test a reversible USB update and Undo, then Keep and a separate restart check. Use a test project for removal/reinstall; do not overwrite completed project setup expecting Undo to reverse it.\n\nHolding FUNC during startup skips module restoration. To return, reinstall your known previous firmware and restore your backed-up saved-set files. Project/sample backups remain separate.\n\nThis candidate still needs exact hardware testing. The base and loader sources are unchanged; packages are the original USB-managed packages. Keep source licences and notices. Underlying Elektron firmware is private; do not redistribute this installer.\n`))
  return {files,receipt,zip:storedZip(files),runtime:facts.runtime,symbols:facts.symbols}
}

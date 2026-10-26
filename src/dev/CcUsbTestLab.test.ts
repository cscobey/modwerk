// @vitest-environment jsdom
import { act,createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach,beforeEach,expect,it,vi } from 'vitest'
import type { OctatrackLink,LinkState } from '../engine/elekloader/octatrack-link'
import { original,test,packageSetDigest,replaceRevision,TEST_RECORD_KEY } from './cc-usb-test'
import CcUsbTestLab from './CcUsbTestLab'
vi.mock('./cc-usb-test',async importOriginal=>({...await importOriginal<object>(),verifiedTestDocument:(_doc:unknown,revision:string)=>new Uint8Array([revision==='test'?17:13]),readSavedPackages:(data:unknown)=>data}))
let dispose:(()=>Promise<void>)|undefined
beforeEach(()=>{vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);localStorage.clear()})
afterEach(async()=>{await dispose?.();vi.restoreAllMocks();vi.unstubAllGlobals()})
const find=(el:HTMLElement,label:string)=>[...el.querySelectorAll('button')].find(b=>b.textContent===label)!
async function setup(){
 let rows=[{module:'f36a496d',sha256:original.sha256},{module:'12345678',sha256:'a'.repeat(64)}],saved=rows.map(r=>({...r})),baseline=rows
 let state:LinkState={status:'ready',active:'b'.repeat(64),identity:{base:test.base,canSubmit:true,model:'MKII',capabilities:{abi:10,features:903,maxSites:128,maxCopies:128}}}
 const listeners=new Set<()=>void>(),set=(next:LinkState)=>{state=next;listeners.forEach(f=>f())}
 const modules=()=>rows.map(r=>({module:r.module,layout:1,handle:1,name:r.module==='f36a496d'?(r.sha256===test.sha256?test.title:test.originalTitle):'Companion'}))
 const control={saved:7,dropCompanion:false,dropTrialCompanion:false,wrongUndo:false,testPassed:true}
 const inventory=()=>control.dropCompanion?modules().slice(0,1):modules()
 const update=vi.fn(async(_label:string,changes:{data:Uint8Array}[],check:()=>Promise<string|null>)=>{baseline=rows;rows=replaceRevision(rows,changes[0].data[0]===17?'test':'original');const failure=await check();set({...state,status:failure?'ready':'trial',tested:!failure,active:'c'.repeat(64)})})
 const selftest=vi.fn(async(report:(r:unknown)=>void)=>{report({state:control.testPassed?2:3});return control.testPassed?null:'failed'})
 const undo=vi.fn(async()=>{if(!control.wrongUndo)rows=baseline;set({...state,status:'ready',active:'b'.repeat(64)})})
 const keep=vi.fn(async()=>{saved=rows.map(r=>({...r}));set({...state,status:'ready'})})
 const link={start:()=>()=>{},subscribe:(f:()=>void)=>{listeners.add(f);return()=>listeners.delete(f)},getState:()=>state,retry:async()=>{},runtimeSetIdentity:async()=>packageSetDigest(rows),savedBackup:async()=>saved,inventory:async()=>inventory(),inspectTrial:async()=>({modules:control.dropTrialCompanion?inventory().slice(0,1):inventory()}),update,selftest,undo,keep,health:async()=>({saved:control.saved,live:rows.length,savedCount:saved.length})} as unknown as OctatrackLink
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({original:{},test:{}})})))
 const el=document.createElement('div');document.body.append(el);const root=createRoot(el);dispose=async()=>{await act(()=>root.unmount());el.remove()};await act(()=>root.render(createElement(CcUsbTestLab,{link})))
 const click=async(label:string)=>{await act(async()=>find(el,label).click())}
 return {el,click,control,update,undo,keep,selftest}
}
it('prepares read-only, trials the other package, verifies Undo, then Keep and a separate restart',async()=>{
 const t=await setup();await t.click('Prepare and read installed version');expect(t.update).not.toHaveBeenCalled()
 expect(find(t.el,'Trial original revision').disabled).toBe(true)
 await t.click('Trial test revision');expect(t.el.textContent).toContain('Trial verified: MIDI2 TEST 17');expect(t.keep).not.toHaveBeenCalled()
 await t.click('Undo trial');expect(t.el.textContent).toContain('Undo verified: MIDI CC SLOTS');expect(localStorage.getItem(TEST_RECORD_KEY)).toBeNull()
 await t.click('Trial test revision');await t.click('Keep revision');expect(t.el.textContent).toContain('Card save confirmed: MIDI2 TEST 17')
 await t.click('Check after restart');expect(t.el.textContent).toContain('Startup restoration is not confirmed')
 t.control.saved=1;await t.click('Check after restart');expect(t.el.textContent).toContain('Restart verified: MIDI2 TEST 17')
 t.control.saved=7;await t.click('Prepare and read installed version');await t.click('Trial original revision');await t.click('Keep revision');expect(t.el.textContent).toContain('Card save confirmed: MIDI CC SLOTS')
 t.control.saved=1;await t.click('Check after restart');expect(t.el.textContent).toContain('Restart verified: MIDI CC SLOTS')
 expect(t.update.mock.calls.every(c=>c[1].length===1)).toBe(true)
})
it('blocks Keep for changed trial inventory and keeps Undo available',async()=>{
 const t=await setup();await t.click('Prepare and read installed version');t.control.dropTrialCompanion=true;await t.click('Trial test revision')
 expect(t.el.textContent).toContain('inventory');expect(find(t.el,'Keep revision').disabled).toBe(true);expect(find(t.el,'Undo trial').disabled).toBe(false);expect(t.keep).not.toHaveBeenCalled()
})
it('does not report Undo verified when the test package remains live',async()=>{
 const t=await setup();await t.click('Prepare and read installed version');await t.click('Trial test revision');t.control.wrongUndo=true;await t.click('Undo trial')
 expect(t.el.textContent).not.toContain('Undo verified:');expect(t.el.textContent).toContain('running package hashes differ')
})
it('leaves a failed card save unconfirmed and allows a read-only retry',async()=>{
 const t=await setup();await t.click('Prepare and read installed version');await t.click('Trial test revision');t.control.saved=8;await t.click('Keep revision')
 expect(find(t.el,'Check after restart').disabled).toBe(true);expect(t.el.textContent).toContain('Card save is not confirmed')
 t.control.saved=7;await t.click('Check card save');expect(find(t.el,'Check after restart').disabled).toBe(false)
})
it('offers no Keep after a self-test failure',async()=>{
 const t=await setup();await t.click('Prepare and read installed version');t.control.testPassed=false;await t.click('Trial test revision');expect(find(t.el,'Keep revision')).toBeUndefined();expect(t.keep).not.toHaveBeenCalled()
})

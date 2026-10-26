// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState, useSyncExternalStore } from 'react'
import { OctatrackLink } from '../engine/elekloader/octatrack-link'
import type { MissingModule } from '../engine/elekloader/upload-usb'
import { ccTrialProblem, type LocalCcPackage } from './cc-slots'
import { original, test, type Revision, type PackageRow, type TestReceipt, revisionPin, verifiedTestDocument, packageSetDigest, replaceRevision, inventoryProblem, readSavedPackages, revisionOf, parseTestReceipt, TEST_RECORD_KEY } from './cc-usb-test'
import './cc-slots.css'
interface Review {base:string;active:string|null|undefined;rows:PackageRow[];revision:Revision;modules:MissingModule[]}
interface Trial {before:Review;revision:Revision;rows:PackageRow[];active:string|null|undefined;verified:boolean;modules?:MissingModule[]}
export default function CcUsbTestLab({link:supplied}:{link?:OctatrackLink}) {
  const [link]=useState(()=>supplied??new OctatrackLink())
  const state=useSyncExternalStore(link.subscribe,link.getState)
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('')
  const [packages,setPackages]=useState<Record<Revision,Uint8Array>>(),[review,setReview]=useState<Review>(),[trial,setTrial]=useState<Trial>()
  const [receipt,setReceipt]=useState<TestReceipt|undefined>(()=>{try{return parseTestReceipt(localStorage.getItem(TEST_RECORD_KEY))}catch{return}})
  const [undoVerified,setUndoVerified]=useState(receipt?.undoVerified??false)
  useEffect(()=>link.start(),[link])
  async function run(job:()=>Promise<void>) {setBusy(true);setError('');setMessage('');try{await job()}catch(e){setError(e instanceof Error?e.message:'The test could not be verified.')}finally{setBusy(false)}}
  function remember(next:TestReceipt){setReceipt(next);try{localStorage.setItem(TEST_RECORD_KEY,JSON.stringify(next))}catch{setError('This browser could not save the restart receipt. Keep this tab open.')}}
  async function read():Promise<Review> {
    const before=link.getState()
    if(before.status!=='ready'||before.identity?.base!==test.base)throw new Error('Connect to the reviewed USB card base (0c5934e1) first.')
    const first=await link.runtimeSetIdentity(),snapshots=await link.savedBackup(),modules=await link.inventory(),last=await link.runtimeSetIdentity(),after=link.getState()
    if(!first||first!==last||!modules||after.status!=='ready'||after.identity?.base!==before.identity.base||after.active!==before.active)throw new Error('The device or module set changed while checking. Read again.')
    const rows=readSavedPackages(snapshots,before.identity.base),revision=revisionOf(rows)
    if(packageSetDigest(rows)!==first)throw new Error('The running package hashes differ from the newest saved set. No update was started.')
    const why=inventoryProblem(rows,modules,revision);if(why)throw new Error(why)
    const result={base:before.identity.base,active:after.active,rows,revision,modules};setReview(result);return result
  }
  async function prepare() {
    setReview(undefined);setPackages(undefined)
    const response=await fetch('/__local/midi-cc-slots/usb-test.json',{cache:'no-store'})
    const document=await response.json() as {original:LocalCcPackage;test:LocalCcPackage;error?:string}
    if(!response.ok)throw new Error(document.error??'Could not build the reviewed USB test pair.')
    const pair={original:verifiedTestDocument(document.original,'original'),test:verifiedTestDocument(document.test,'test')}
    const r=await read();setPackages(pair);setMessage('Confirmed '+revisionPin(r.revision).title+' and all '+r.rows.length+' exact saved/running packages. Nothing sent.')
  }
  async function start(revision:Revision) {
    if(!review||!packages)throw new Error('Prepare and read the installed version first.')
    const fresh=await read()
    if(packageSetDigest(fresh.rows)!==packageSetDigest(review.rows))throw new Error('The reviewed package set changed. Prepare again.')
    const before=link.getState(),why=ccTrialProblem(before,review.modules,review.base+':'+review.active)
    if(why||before.identity?.base!==review.base||before.active!==review.active)throw new Error(why??'The reviewed connection changed. Prepare again.')
    if(revision===review.revision)throw new Error('Choose the other revision for a real package replacement.')
    const rows=replaceRevision(review.rows,revision)
    setTrial(undefined)
    await link.update('Midi Mode 2 · '+revisionPin(revision).version,[{module:'midi-cc-slots',data:packages[revision]}],async()=>{
      let passed=false;const failure=await link.selftest(r=>{passed=r.state===2})
      return failure??(passed?null:'The base did not report a completed self-test.')
    })
    const after=link.getState()
    if(after.status!=='trial'||!after.tested||after.identity?.base!==review.base)throw new Error(after.notice?.text??'The update did not reach a tested trial.')
    const next={before:review,revision,rows,active:after.active,verified:false};setTrial(next)
    const inspection=await link.inspectTrial()
    const problem=inventoryProblem(rows,inspection.modules,revision);if(problem)throw new Error(problem+' Use Undo; do not Keep.')
    setTrial({...next,verified:true,modules:inspection.modules});setMessage('Trial verified: '+revisionPin(revision).title+'. Self-test passed; the companion inventory is unchanged. Check MIDI controls, then Undo or Keep.')
  }
  function currentTrial() {
    const now=link.getState()
    if(!trial||now.status!=='trial'||now.identity?.base!==trial.before.base||now.active!==trial.active)throw new Error('This is no longer the reviewed trial.')
    return trial
  }
  async function undo() {
    const t=currentTrial();await link.undo()
    if(link.getState().status!=='ready')throw new Error('Undo is not confirmed. Read the device notice.')
    setTrial(undefined)
    const r=await read()
    if(packageSetDigest(r.rows)!==packageSetDigest(t.before.rows))throw new Error('Undo did not restore the exact original module set.')
    setUndoVerified(true);setMessage('Undo verified: '+revisionPin(r.revision).title+' returned with every original companion package. Nothing was kept.')
  }
  async function confirmSaved(expected:TestReceipt,restart:boolean) {
    const r=await read(),health=await link.health(),after=link.getState()
    if(after.status!=='ready'||after.identity?.base!==expected.base||after.active!==r.active||packageSetDigest(r.rows)!==packageSetDigest(expected.rows))throw new Error('The package set differs from the kept revision. Persistence is not confirmed.')
    if(!health||health.live!==expected.rows.length||health.savedCount!==expected.rows.length||health.saved!==(restart?1:7))throw new Error(restart?'Startup restoration is not confirmed. Restart after a confirmed card save, reconnect and check again.':'Card save is not confirmed. Keep the device on and choose Check card save again.')
    remember({...expected,saved:true,restored:restart})
    setMessage(restart?'Restart verified: '+revisionPin(r.revision).title+' and every exact companion package restored. Check project names, channels and CC controls.':'Card save confirmed: '+revisionPin(r.revision).title+'. You can power-cycle, reconnect and choose Check after restart.')
  }
  async function keep() {
    const t=currentTrial();if(!t.verified)throw new Error('The trial identity must pass before Keep.')
    const expected:TestReceipt={schema:1,base:t.before.base,revision:t.revision,rows:t.rows,saved:false,restored:false,undoVerified}
    await link.keep()
    if(link.getState().status!=='ready')throw new Error('Keep is not confirmed. Read the device notice.')
    setTrial(undefined);remember(expected);await confirmSaved(expected,false)
  }
  const ready=state.status==='ready'&&!busy,prepared=ready&&!!review&&!!packages&&review.active===state.active&&review.base===state.identity?.base
  const displayed=state.status==='trial'&&trial?.verified&&trial.modules?{revision:trial.revision,rows:trial.rows,modules:trial.modules}:review
  return <main className="cc-slots-lab"><a href="/">← Local Modwerk app</a><h1>Midi Mode 2 · USB update test</h1>
    <p>Two distinct packages: original {original.version} and test {test.version}. The test reports <strong>{test.title}</strong> in the device inventory. Only the package display name changes; MIDI code, project format and controls are identical. This checks package replacement and rollback, not new MIDI behavior.</p>
    <p>Use a backed-up test project, stop transport and finish or cancel INIT. Leave USB DISK MODE. Close other connected tabs. This page changes only Midi Mode 2 and verifies the hashes of every companion.</p>
    <ol><li>Connect, then Prepare and read installed version.</li><li>Trial test revision; check controls, then Undo trial. Wait for Undo verified.</li><li>Trial test revision again; check controls and Keep revision. Wait for Card save confirmed.</li><li>Power-cycle, reconnect and Check after restart. Check project settings on the device.</li><li>Prepare again, Trial original revision, Keep revision and repeat the restart check to finish on your original build.</li></ol>
    <p role="status">Status: {state.status}{busy?' · Working…':''}</p>{state.identity&&<p>Base: <code>{state.identity.base}</code></p>}
    <button className="button" disabled={busy||!['idle','ready','stock','busy'].includes(state.status)} onClick={()=>void run(async()=>{setReview(undefined);await link.retry()})}>Connect Octatrack</button>{state.status==='unsupported'&&<p>Open this page in Chrome or Edge with WebUSB.</p>}
    <button className="button" disabled={!ready} onClick={()=>void run(prepare)}>Prepare and read installed version</button>
    {displayed&&<><h2>{state.status==='trial'?'Verified trial inventory':'Last verified installed set'}</h2><p>{revisionPin(displayed.revision).title} · {displayed.rows.length} modules</p><ul>{displayed.modules.map(m=><li key={m.module}>{m.name} <code>{m.module}</code></li>)}</ul></>}
    <button className="button button-primary" disabled={!prepared||review?.revision==='test'} onClick={()=>void run(()=>start('test'))}>Trial test revision</button>
    <button className="button" disabled={!prepared||review?.revision==='original'} onClick={()=>void run(()=>start('original'))}>Trial original revision</button>
    {state.status==='trial'&&<div><button className="button" disabled={busy||!trial} onClick={()=>void run(undo)}>Undo trial</button><button className="button button-primary" disabled={busy||!trial?.verified||!state.tested} onClick={()=>void run(keep)}>Keep revision</button></div>}
    {receipt&&<section><h2>Last Keep receipt</h2><p>{revisionPin(receipt.revision).title} · {receipt.restored?'Restart verified':receipt.saved?'Card save confirmed':'Card save not confirmed'}</p><button className="button" disabled={!ready||receipt.restored} onClick={()=>void run(()=>confirmSaved(receipt,false))}>Check card save</button><button className="button" disabled={!ready||!receipt.saved||receipt.restored} onClick={()=>void run(()=>confirmSaved(receipt,true))}>Check after restart</button></section>}
    {message&&<p role="status">{message}</p>}{state.notice&&<p role="status">{state.notice.text}</p>}{error&&<p role="alert">{error}</p>}
    <details><summary>Reviewed package hashes</summary><p>Original: <code>{original.sha256}</code></p><p>Test: <code>{test.sha256}</code></p></details>
  </main>
}

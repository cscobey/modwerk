import pin from '../../sdk/drafts/midi-cc-slots/local-build.json' with { type: 'json' }
import { useEffect, useState, useSyncExternalStore } from 'react'
import { OctatrackLink } from '../engine/elekloader/octatrack-link'
import { removalPackage } from '../engine/elekloader/module-set'
import type { MissingModule } from '../engine/elekloader/upload-usb'
import { ccPackage, ccTrialProblem, ccExpectedModules, ccPersistenceProblem, parseCcInstallRecord, CC_INSTALL_KEY, CC_SLOTS_ID, type CcInstallRecord, type LocalCcPackage } from './cc-slots'
import './cc-slots.css'

export default function CcSlotsLab({ link: supplied }: { link?: OctatrackLink }) {
  const [link] = useState(() => supplied ?? new OctatrackLink())
  const state = useSyncExternalStore(link.subscribe, link.getState)
  const [built, setBuilt] = useState<{ data: Uint8Array; sha256: string }>()
  const [inventory, setInventory] = useState<MissingModule[]>()
  const [reviewed, setReviewed] = useState<string>()
  const [trial, setTrial] = useState<{ record: CcInstallRecord; active: string | null | undefined }>()
  const [record, setRecord] = useState<CcInstallRecord | undefined>(() => {
    try { return parseCcInstallRecord(localStorage.getItem(CC_INSTALL_KEY)) } catch { return undefined }
  })
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [result, setResult] = useState('')
  useEffect(() => link.start(), [link])
  const problem = ccTrialProblem(state, inventory, reviewed)
  const installed = inventory?.some(m => m.module === CC_SLOTS_ID)
  async function run(job: () => Promise<void>) {
    setBusy(true); setError(''); setResult('')
    try { await job() } catch (e) { setError(e instanceof Error ? e.message : 'The module could not be prepared.') } finally { setBusy(false) }
  }
  function remember(next: CcInstallRecord) {
    setRecord(next)
    try { localStorage.setItem(CC_INSTALL_KEY, JSON.stringify(next)) } catch { /* This tab can still verify; reload loses the record. */ }
  }
  async function prepare() {
    setBuilt(undefined); setReviewed(undefined); setInventory(undefined)
    const response = await fetch('/__local/midi-cc-slots', { cache: 'no-store' })
    const document = await response.json() as LocalCcPackage & { error?: string }
    if (!response.ok) throw new Error(document.error ?? 'Local compilation failed.')
    const data = ccPackage(document)
    const before = link.getState(), modules = await link.inventory(), after = link.getState()
    if (!modules || before.identity?.base !== after.identity?.base || before.active !== after.active || after.status !== 'ready') throw new Error('The unit changed or its module list could not be read. Prepare again.')
    setInventory(modules); setReviewed(after.identity!.base + ':' + after.active); setBuilt({ data, sha256: document.sha256 })
  }
  async function start(action: CcInstallRecord['action']) {
    const before = link.getState(), why = ccTrialProblem(before, inventory, reviewed, action)
    if (why || !built || !inventory) throw new Error(why ?? 'Build the module first.')
    const next: CcInstallRecord = { schema: 1, base: before.identity!.base, packageSha256: built.sha256, action, saved: false, restored: false, expected: ccExpectedModules(inventory, action) }
    setTrial(undefined)
    await link.update(`MIDI CC Slots · ${action}`, [{ module: 'midi-cc-slots', data: action === 'remove' ? removalPackage('midi-cc-slots') : built.data }], async () => {
      let passed = false
      const failure = await link.selftest(reading => { passed = reading.state === 2 })
      return failure ?? (passed ? null : 'the base did not report a completed self-test')
    })
    const after = link.getState()
    if (after.status === 'trial' && after.tested && after.identity?.base === next.base) setTrial({ record: next, active: after.active })
  }
  async function verify(next: CcInstallRecord, restart: boolean) {
    const before = link.getState(), modules = await link.inventory(), reading = await link.health(), after = link.getState()
    if (before.identity?.base !== after.identity?.base || before.active !== after.active) throw new Error('The unit changed while checking. Reconnect and check again.')
    if (modules) setInventory(modules)
    const why = ccPersistenceProblem(next, after, modules, reading, restart)
    if (why) throw new Error(why)
    setInventory(modules); remember({ ...next, saved: true, restored: restart })
    setResult(restart ? 'Startup restoration confirmed by the base. The reviewed module set is present. Check the MIDI controls on your test project.' : 'Card save confirmed for the complete module set. You can now power-cycle the Octatrack, reconnect, then choose Check after restart.')
  }
  async function keep() {
    const before = link.getState()
    if (!trial || before.status !== 'trial' || !before.tested || before.identity?.base !== trial.record.base || before.active !== trial.active) throw new Error('Start and test this module trial first.')
    await link.keep()
    const after = link.getState()
    if (after.status !== 'ready' || after.identity?.base !== trial.record.base || after.active !== trial.active) throw new Error('Keep was not confirmed. Read the connection notice before continuing.')
    remember(trial.record); setTrial(undefined); setReviewed(undefined)
    await verify(trial.record, false)
  }
  return <main className="cc-slots-lab">
    <a href="/">← Local Modwerk app</a><h1>Midi Mode 2</h1>
    <p>Local install · module {pin.version}</p><p><a href="/?preview=midi-usb-update">USB update / Undo / restart test →</a></p>
    <p>Before INIT, choose Keep installed for this update. After Save to New, also open PROJECT → SAVE PROJECT and let it finish; Save to New may leave working files only. Project setup: back up a disposable project, set Bank A (Bank 1) / Part 1 names and channels, stop transport and recorders, then save the project normally. Double-tap MIDI SRC: F opens NAME/PUSH. Hold FUNC and push D at INIT (FN+ / PUSH); no typing is needed. Progress shows the bank being checked, applied or restored. NO cancels at a safe boundary. Wait for MIDI SETUP SAVED. The first setup retains legacy name/channel overrides. On a saved setup, REPLACE ALL? YES/NO asks before replacement: YES copies Bank A / Part 1 names and channels to all banks and Parts, including empty names and OFF. NO cancels.</p>
    <p>After INIT, renaming overrides only that bank, across its Parts. Channel edits use normal project saves. Bank changes and restart never reapply Bank A defaults. Save to New carries the names and completed marker into an independent project.</p>
    <p>This update accepts valid working and saved bank files with different channel settings and records each original map for cancellation or recovery. Bare page browsing stays available during progress; editing, playback and bank changes stay held. NO cancels safely. Report any CHECK FAILED or APPLY FAILED code; repeatedly saving cannot resolve every check failure.</p>
    <p>Try the MIDI controls, then choose Keep installed before starting INIT. An unfinished setup needs this version to recover after restart; older builds refuse its pending journal. Keep saves the complete running module set for your installed base to restore. Finish or cancel INIT before Undo or another module change.</p>
    <p>Names autosave while stopped: wait for MIDI PROFILE SAVED. Keep all MIDI4_*.DAT files with project backups; two hold names and the marker, and two hold recovery checkpoints. Existing MIDI3_*.DAT and MIDI2_*.DAT profiles import read-only and remain unchanged. Interrupted, uncommitted INIT restores the previous snapshot. Undo/removal does not reverse completed native bank edits; restore your backup for that. Exact emulator checks passed; physical power cycling and full resident dispatch remain unqualified. The draft requires a base reporting loader ABI 8, 24 sites and 25 stock copies.</p>
    <section aria-label="Connected Octatrack"><h2>Your Octatrack</h2>
      <p>Status: {state.status}</p>
      {state.identity && <p>Base: <code>{state.identity.base}</code></p>}
      {state.status === 'unsupported' ? <p>Open this page in a browser with WebUSB, such as Chrome or Edge.</p> : <button className="button" disabled={busy || !['idle', 'ready', 'stock', 'busy'].includes(state.status)} onClick={() => void run(() => link.retry())}>Connect Octatrack</button>}
      {state.status === 'stock' && <p>The USB module interface was not found. Leave USB DISK MODE and reconnect. If this remains, install the USB-enabled Modwerk base.</p>}
      {state.status === 'busy' && <p>Close another app or tab using the Octatrack, then reconnect.</p>}
      <button className="button" disabled={busy || state.status !== 'ready' || !state.identity?.canSubmit} onClick={() => void run(prepare)}>Build draft and read installed modules</button>
      {inventory && <><h3>Installed modules</h3>{inventory.length ? <ul>{inventory.map(module => <li key={module.module}>{module.name} <code>{module.module}</code></li>)}</ul> : <p>No runtime modules reported.</p>}</>}
      {built && <p>Module SHA-256: <code>{built.sha256}</code></p>}
      {state.status === 'ready' && problem && <p>{problem}</p>}
      <button className="button button-primary" disabled={busy || !built || !!problem} onClick={() => void run(() => start('install'))}>{installed ? 'Try updated module' : 'Start temporary USB trial'}</button>
      {installed && <button className="button" disabled={busy || !built || !!problem} onClick={() => void run(() => start('remove'))}>Try removing MIDI CC Slots</button>}
      {state.status === 'trial' && <>
        <p>The base self-test passed. {trial?.record.action === 'remove' ? 'Check native PB/AT behavior, then Keep removal to make it survive restart.' : 'Check the CC controls and outgoing MIDI, then Keep to install across restarts.'}</p>
        <button className="button button-primary" disabled={busy || !trial || !state.tested} onClick={() => void run(keep)}>{trial?.record.action === 'remove' ? 'Keep removal' : 'Keep installed'}</button>
        <button className="button" onClick={() => void run(async () => { await link.undo(); setTrial(undefined); setReviewed(undefined) })} disabled={busy}>Undo trial</button>
      </>}
      {record && <section aria-label="Saved installation"><h3>Restart check</h3>
        <p>{record.restored ? 'The last startup check confirmed the reviewed module set was restored.' : record.saved ? 'The card save was confirmed. Restart restoration still needs a check.' : 'The card save is not confirmed. Keep the Octatrack on and check the save before restarting.'}</p>
        <button className="button" disabled={busy || state.status !== 'ready' || record.restored} onClick={() => void run(() => verify(record, false))}>Check card save</button>
        <button className="button" disabled={busy || state.status !== 'ready' || !record.saved} onClick={() => void run(() => verify(record, true))}>Check after restart</button>
      </section>}
      {result && <p role="status">{result}</p>}
      {state.notice && <p role="status">{state.notice.text}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
    <section><h2>Try the controls</h2><p>Both MIDI CONTROL pages show assigned CC numbers above the knobs. SETUP captions show PB, AT or CC for the current mode.</p><ol><li>Select a MIDI track and double-tap FX1.</li><li>Click A or B to switch its PB or AT position into CC mode.</li><li>Turn to choose CC0–127, then press YES.</li><li>Return to CONTROL 1; use FUNC + encoder press to enable the value, then turn it.</li><li>Click the encoder in SETUP again to restore native PB or AT.</li></ol><p>CC mode starts at CC0 each time. The base self-test does not qualify MIDI behavior or project persistence.</p></section>
  </main>
}

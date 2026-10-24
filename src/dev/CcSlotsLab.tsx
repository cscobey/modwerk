import { useEffect, useState, useSyncExternalStore } from 'react'
import { OctatrackLink } from '../engine/elekloader/octatrack-link'
import type { MissingModule } from '../engine/elekloader/upload-usb'
import { ccPackage, ccTrialProblem, type LocalCcPackage } from './cc-slots'
import './cc-slots.css'

export default function CcSlotsLab({ link: supplied }: { link?: OctatrackLink }) {
  const [link] = useState(() => supplied ?? new OctatrackLink())
  const state = useSyncExternalStore(link.subscribe, link.getState)
  const [built, setBuilt] = useState<{ data: Uint8Array; sha256: string }>()
  const [inventory, setInventory] = useState<MissingModule[]>()
  const [reviewed, setReviewed] = useState<string>()
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  useEffect(() => link.start(), [link])
  const problem = ccTrialProblem(state, inventory, reviewed)
  async function run(job: () => Promise<void>) {
    setBusy(true); setError('')
    try { await job() } catch (e) { setError(e instanceof Error ? e.message : 'The draft could not be prepared.') } finally { setBusy(false) }
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
  return <main className="cc-slots-lab">
    <a href="/">← Local Modwerk app</a>
    <h1>MIDI CC Slots</h1>
    <p>Local development trial · 0.0.4-experimental</p>
    <p>This draft adds CC mode to the PB and AT positions. It has emulator evidence; hardware, saved projects and mixed-module behavior are unqualified. Use a disposable test project.</p>
    <p>The trial stops playback and adds this one module alongside the installed set. Undo restores the previous set. Nothing here flashes firmware or keeps the draft on the card.</p>
    <section aria-label="Connected Octatrack"><h2>Your Octatrack</h2>
      <p>Status: {state.status}</p>
      {state.identity && <p>Base: <code>{state.identity.base}</code></p>}
      {state.status === 'unsupported' ? <p>Open this page in a browser with WebUSB, such as Chrome or Edge.</p> : <button className="button" disabled={busy || !['idle', 'ready', 'stock'].includes(state.status)} onClick={() => void run(() => link.connect())}>Connect Octatrack</button>}
      <button className="button" disabled={busy || state.status !== 'ready'} onClick={() => void run(prepare)}>Build draft and read installed modules</button>
      {inventory && <><h3>Installed modules</h3>{inventory.length ? <ul>{inventory.map(module => <li key={module.module}>{module.name} <code>{module.module}</code></li>)}</ul> : <p>No runtime modules reported.</p>}</>}
      {built && <p>Draft SHA-256: <code>{built.sha256}</code></p>}
      {state.status === 'ready' && problem && <p>{problem}</p>}
      <button className="button button-primary" disabled={busy || !built || !!problem} onClick={() => void run(async () => {
        const why = ccTrialProblem(link.getState(), inventory, reviewed)
        if (why || !built) throw new Error(why ?? 'Build the draft first.')
        await link.update('MIDI CC Slots · local draft', [{ module: 'midi-cc-slots', data: built.data }], () => link.selftest())
      })}>Start temporary USB trial</button>
      {state.status === 'trial' && <><p>The base self-test passed. Now check the CC controls and outgoing MIDI. That self-test does not qualify this feature.</p><button className="button" onClick={() => void run(() => link.undo())} disabled={busy}>Undo trial</button></>}
      {state.notice && <p role="status">{state.notice.text}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
    <section><h2>Try the controls</h2><p>Both MIDI CONTROL pages show assigned CC numbers above the knobs. SETUP captions show PB, AT or CC for the current mode.</p><ol><li>Select a MIDI track and double-tap FX1.</li><li>Click A or B to switch its PB or AT position into CC mode.</li><li>Turn to choose CC0–127, then press YES.</li><li>Return to CONTROL 1; use FUNC + encoder press to enable the value, then turn it.</li><li>Click the encoder in SETUP again to restore native PB or AT.</li></ol><p>CC mode starts at CC0 each time. Verify MIDI with a receiver or monitor, then undo the trial before returning to your working project.</p></section>
  </main>
}

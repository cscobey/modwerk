# MIDI and USB

Read [the module guides index](README.md) first. A module that sends or reacts to MIDI clock or notes in time also follows [sequencing.md](sequencing.md).

**Applies to** modules with manifest `category: midi-usb`, including MIDI generators and MIDI effects (below). [CC Map](../../sdk/octabam/modules/cc-map/README.md) maps MIDI CC 68–73 to FX1 SETUP controls. [USB Audio](../../sdk/octabam/modules/usb-audio-out-tracks-main-cue/README.md) sends eight stereo tracks, MAIN and CUE over USB.

## Behave like the instrument

- [ ] **A complete message map in the README:** every CC, note, channel and SysEx value you read or send, what it does, and the range. CC Map lists CC 68–73 and what each one controls.
- [ ] **Say what you consume.** CC Map's limitation list says CC 62–73 are consumed even when AUDIO CC IN is disabled. State for every message whether it is passed through to stock handling, consumed, or both.
- [ ] **Do not break common messages.** CC 64–67 overlap sustain, portamento, sostenuto and soft pedal. List overlaps with common controllers, and what a musician loses.
- [ ] **Use the stock enable and channel settings.** CC Map is enabled with the stock AUDIO CC IN checkbox and follows the track's TRIG CH. Do not add a private channel setting. State the default, and what happens when the setting is off.
- [ ] **Feedback.** When a MIDI message changes a value, the panel shows it (`verify_ccfeedback.py`), including values that are parameter-locked or LFO-modulated at that moment. **Verify** the interaction and record the result.
- [ ] **Parameter locks and LFOs.** A CC-driven parameter and a lock or LFO on the same parameter: say which wins, and test it.
- [ ] **USB:** the device enumerates as the instrument's own identity, with the interfaces the host expects (`verify_usb.py` checks the Elektron 1935:0002 identity, the MSC interface and the INQUIRY and CSW responses). Sample alignment and channel layout are tested (`verify_usb_align.py`, `verify_usb_in.py`), startup behaviour is stated (USB Audio reports a reordering burst 0.5–1.5 s after the stream opens), and the hosts you measured are named: "Windows and Linux hosts have not been measured" is a legitimate sentence, an omission is not.
- [ ] **Stock tables stay local.** A POST producer's gain curve is DSP data expanded to 32-bit ColdFire words. Use the shared named reconstruction recipe, with a bounded source span and no literal table in packages; a raw stock-byte scan alone does not prove a changed encoding is stock-free.
- [ ] **Shared USB ownership is explicit.** The card composer includes the internal USB MIDI platform code; the beta base owns the USB functions and their shared reset/ISR sites. Use that shared SDK/base code, never depend on another catalogue module. Only one USB output layout can be composed.
- [ ] **Keep POST state continuous across runtime profile changes.** Its four-block snapshot history and gain ramp must advance on the instrument's frame even while another layout or audio-off is selected. Reinitialize host cursors and endpoint state on a profile change, while preserving that musical history. Budget and measure the added frame work; synthetic ColdFire parity does not establish DSP pairing or hardware headroom.
- [ ] **Bound the profile commit.** Prefer immutable descriptor tables that each stay within one 4 KiB page. Select them only after the old endpoint retires; do not copy descriptors or clear the entire ring with frame interrupts masked. The producer's first-block cushion and cursors must exclude old-layout samples; poison the old ring to check this. Preserve handler-entry registers and condition flags across table dispatch too: an audio-off PEA must retain the original CCR, not the lookup's flags. Check the actual continuation as well as synthetic handler-entry captures. Emulator success still leaves cache, driver recovery and hardware timing unqualified.
- [ ] **A stopped controller is not a retired control transfer.** Refuse a profile commit while EP0 owns data/status/completion, stock awaits an OUT stage, or an old clock SET latch remains pending. In the opt-in base emulator, a clock SET interrupted by unplug retained both EP0 OUT and its latch. Preserve pending state on refusal; only the owner-authorized transition may drain/cancel it, retire cached vendor replies and then reconnect. Ordinary bus-reset rollback must remain enabled.
- [ ] **Publish only complete sample frames.** A track counter can advance before delayed MAIN/CUE writes reach the same slots. Fence packet availability at the slowest component, including counter wrap, and clear the bounded fresh-start gap for future-offset CUE. Exercise a nearly drained queue as well as steady streaming: a synthetic test caught old ring bytes in MAIN/CUE after an earlier streaming pass, and the same reader error reproduced in the ordinary base. This is not physical evidence of any reported audio symptom.

## MIDI generators and MIDI effects

A **MIDI generator** makes notes or controllers from the transport (an arpeggiator, a Euclidean or probability sequencer, a chord or CC sequencer). A **MIDI effect** changes a stream that already exists (transpose, scale and chord mapping, velocity curves, humanise, delay and echo, filtering, channel and port routing). Both are ColdFire code, so the manifest has `category: midi-usb` and `compatibility.location: MIDI tracks` (or `Project sequencer` when it acts on the whole project), and they carry a `coldfire` performance record. A generator follows [sequencing.md](sequencing.md) completely: the instrument's own transport, tempo, track speed and swing, never a clock of your own. Copy the shape of the closest existing module, and agree the design with the owner before you spend long on one that has no precedent. No module here yet transforms MIDI notes (CC Map maps controllers only). A MIDI effect that changes a note's pitch takes `ev_midi_note_key` ([EVENTS.md](../../sdk/machines/octatrack/EVENTS.md)): it runs in the MIDI sequencer's interrupt, once per note, so keep it to a few microseconds and read nothing slow. `ev_arp_setup_knob` gives a module one ARP SETUP encoder turn (KEY while a trig is held, for example) before stock edits the track's setting, and `ev_arp_setup_text` lets it draw that value its own way.

Where a MIDI track's setup lives in the Part, what the UI writers store when a value changes, how notes and CCs go out and where the CTRL pages draw their labels is in [MIDI_TRACKS.md](../../sdk/octabam/docs/MIDI_TRACKS.md), a reading of the 1.40C image that was not run on a unit.

**MIDI generators** contribute to the base table `ot_midi_generators` ([EVENTS.md](../../sdk/machines/octatrack/EVENTS.md)) from their `runtime.json`. MIDI NOTE SETUP (double-tap SRC, and double-tap TRACK in MIDI mode) lists OFF and the generators in its empty left half. A MIDI track running one shows the generator's own pages on the MIDI pages it names in `pages`: always ARP (AMP), with a second page on FUNC+AMP, and as the owner chose on 24 October 2026, SRC (the NOTE page) for its main controls; FX1 and FX2 stay for MIDI effects, LFO stays stock's. Holding a trig shows stock's page, so locks stay stock's. Values behind a page it takes keep their stock meaning (the NOTE page's NOT2-4 still add chord notes to every trig), so a generator that takes SRC sets or shows NOTE, VEL and LEN itself and leaves NOT2-4 off. The base keeps the choice in the track's arp step mask and resets the arpeggiator (MODE OFF) on every change; the generator keeps up to 16 settings in the track's arp note bytes (value - 64, the -64..63 stock's validator keeps). Stock's validator clamps every other MIDI Part byte to its page's ranges, and MIDI NOTE SETUP's encoders D and F edit its two unused slots unseen, so do not store anything there. A generator writes the track's trigs and NOTE, VEL and LEN locks (pattern + 0x48d0 + 0x8b0 t: masks at +0, length +0x28, locks +0x30 + 32 step, timing and conditions +0x830 + 2 step) and the stock sequencer plays them: no clock of its own, every note-off stock's, nothing to run while playing. The trig word there is two bytes, high first: bits 15-13 the trig count - 1, bits 12-7 the micro-timing in 1/24 of a step (two's complement, -23..23), bits 6-0 the trig condition as an index into stock's labels at 0x400b2588 (0 none, 9-29 1% to 99%, 30-64 1:2 to 8:8). On the owner's MKII (24 October 2026, VECTOR's PROB and HUMN, MIDI recorded over USB) a 1% condition let none of 46 notes through and every micro-timed note sounded within 1 ms of grid + offset; a negative offset on the first step does not sound before PLAY. On a card build there is no base: the module links `elekloader/midi_generators.c` with `MG_FIXED` naming its record and patches the same four sites itself; its runtime package names those detours in `replaces`.

Keep a generator's edits cheap; they run on the UI task while the pattern plays. Module code and data run uncached, so write the record in place, only the bytes that change, rather than copying 2 KB in and out, and set your own track's bit of stock's per-step lock index (0x46c7d2e4 for MIDI tracks, 0x46c7d48c for audio) instead of calling stock's rebuild 0x400339d8, which rescans every track (about 3 ms on the owner's MKII). A 64-step rewrite took 0.5 ms that way on the owner's MKII ([traps](../OCTATRACK_HARDWARE_TRAPS.md#coldfire-and-dsp-load)).

- [ ] **Every note-on gets its note-off.** On stop, on a change of Part, pattern or channel, when the module is bypassed, when a parameter change would move the note, and when the module is removed from a running project. **Verify** each and record the result; a stuck note is the failure musicians notice first.
- [ ] **Velocity 0 is a note-off** and running status is understood, as on the wire.
- [ ] **Say what passes through.** Real-time messages (clock, start, stop, continue), SysEx and every message type you do not touch pass through unchanged and in order, including in the middle of your output. State it per message type, as above.
- [ ] **No loops.** MIDI thru plus a module that sends to the same port can feed itself. Say what stops it.
- [ ] **Bounded work and bounded output.** The most events you emit for one input (a chord of eight, a ratchet of sixteen, an echo with feedback) is a number, it is documented, and the output queue's behaviour when full is documented too: drop what and count it. A feedback echo must decay.
- [ ] **Latency and jitter.** State the latency you add and whether it varies. A transform that is not allowed to move notes in time adds none; a look-ahead is stated and the same offset is applied to what it should line up with.
- [ ] **Polyphony and channels.** The number of simultaneous notes, what happens at the limit (steal the oldest, refuse the newest), and which channels and ports you read and write.
- [ ] **Safe defaults.** A freshly enabled module changes nothing a musician plays until a control is turned (a transparent MIDI effect is a bit-exact passthrough of every message, tested), and a generator is silent until it is told to play.
- [ ] **Locks, LFOs and scenes.** Where a control is parameter-locked, modulated by an LFO or morphed by a scene, say which wins and test it, as above.
- [ ] **Performance.** The worst event under a flood at wire rate, and what the module adds to the stock image's frame interrupt and idle time: [Performance](README.md#performance). A MIDI module is the likeliest to be slow in the interrupt, so do the work once per event and never once per byte, and do not wait on a full output.

## Integrate

- [ ] Conflicts are declared in `compatibility`; shared audio/MIDI endpoint and descriptor ownership belongs to the SDK/base, not to a second catalogue module.
- [ ] Over USB, USB Audio is a base layout, not a runtime package: each output layout (and USB MIDI alone) is its own published base, all sharing every address outside a fixed USB reserve. A module set with USB Audio asks for its layout, and the site installs that base over USB before anything else syncs; a set without it leaves the base's layout alone ([the base's variants](../../sdk/machines/octatrack/elekloader/README.md#the-base-in-the-browser)). A change to USB code must fit `USB_RESERVE` and regenerates every variant. Windows keeps one capture endpoint per device and stores its channel count: after a switch from twenty channels to Main + Cue or Main on the same unit (21 October 2026, Windows 11, class driver), WASAPI, MME and DirectSound refused to open it until that format is reselected (Sound settings → Recording → Properties → Advanced), while WDM-KS opened the 2-channel layout at once.
- [ ] `sdk/catalog.json` entry, thumbnail, `resources.impact`, README sections, tutorial and screenshots of the setting that enables it (`PROJ` → `MIDI` → `CONTROL` for CC Map).
- [ ] A module with no Octatrack page of its own (an automatic USB module) uses the narrow `access.noUiReason` and still documents the host connection and routing. See [MODULE_UI_CAPTURES.md](../MODULE_UI_CAPTURES.md).
- [ ] `evidence/performance.json` passes `npm run perf:audit -- check` ([Performance](README.md#performance)).
- [ ] `npm run module:verify -- <id> --os <your 1.40C>` and `npm run module:doctor -- <id>` are green.

## Test

Flood and stop it: notes, CC and clock at the wire rate, stopped mid-note, a Part change while it runs, and count what is left sounding and what was dropped. `verify_midi.py`, `verify_ccmap.py`, `verify_usb.py`, `verify_usb_align.py` and `verify_usb_in.py` are the patterns. A host-side test is part of the work: name the operating system, the USB speed and the software you used, or say "not tested".

To test a MIDI track's KEY in `ot_emu`, write it into the saved Part (MIDI setup at body + 0x4e2, 36 bytes a track, KEY at field 17), not the live byte: stock copies the Part's KEY over the live one when the pattern starts, so a poke after the load is gone by the first note. Check the run's output differs between keys; a run where it does not tested nothing.

Match startup settings in native/worker image comparisons. The worker defaults to docking startup; the USB layout verifier explicitly requests classic startup to match its native composition. Different startup hooks are a real image difference, not a USB layout regression.

For a private source-built POST base, run the executed ColdFire arithmetic probe:

```sh
python3 -B scripts/verify-octatrack-usb-post.py \
  --build /private/post-base-build --emulator /path/to/ot_emu \
  --output /private/new-post-probe
```

It binds IDENTIFY to the build receipt, supplies synthetic snapshots with fake audio frames disabled, and compares eight tracks' four-block history, per-sample gain ramps and closed-stream state against an independent integer model. The actual producer's sixteen-channel ring packing and full-speed saturated sum are checked with distinct stereo signals, silence and both clipping directions. EMAC checks cover the gain helper and actual caller in twelve modes each, including open/closed paths, with a skipped-restoration negative control. The probe replaces only the dormant stock ISR epilogue with an authored C return in emulator RAM; it records that patch and the image, symbols and emulator hashes. This is ColdFire execution evidence; it does not establish DSP pairing, physical mute/solo/scene behaviour, audio quality or chip timing. The authored memory-reader wrapper supports older emulator binaries without a `peek` command; do not infer a firmware failure from an unsupported bench command. For long borrowed-call runs, use the [isolated emulator adapter](../OCTATRACK_ELEKLOADER_MIGRATION.md#borrowed-call-probes) to avoid the upstream caller-stack leak.

## Digitakt and Digitone

SysEx ids are resources: claim them (`sysex:0x7d` in `platform.claims`), because two mods may never claim the same one ([Digitakt guide](../../sdk/machines/digitakt/README.md)). The core delivers key and encoder events to your handler (`ev_key`, `ev_enc`); return nonzero only when you take the event. A MIDI generator or MIDI effect follows the same rules as on the Octatrack (note-offs, pass-through, the most events one input can produce) and records in TESTING.md the shared memory, fast SRAM and time per event it measured under a flood of notes, CC and clock.

## Prototyping MIDI UI names

The isolated `sdk/drafts/midi-track-names` experiment demonstrates the stock
name editor and normal MIDI channel-header override. UI success is separate
from persistence: a Part/track-indexed RAM table has no bank/project identity
and cannot satisfy save/reload/copy/clear or reboot requirements. Keep such
experiments out of installable packages until those lifecycle paths and shared
UI ownership are designed and tested. A stock key table may serve several
windows; gate a prototype to its exact page and preserve stock handling in
other contexts. Test actual LCD output as well as stored text.


A live editor adds a module-lifetime requirement. Stock can cache input-table
callbacks, so restoring a table word alone may leave a retired code address in
the cache. Test removal while the dialog is open, including both confirm and
cancel, and poison retired memory to expose stale calls. The Midi Mode 2 local
naming test uses stable stock routine entry detours, a stock-owned editor buffer
and stock redraw callback; no module destination/callback survives its removal.
This does not establish project-name storage or general shared UI ownership.


For project-local persistence, run card calls only in an admitted stopped engine
task, never in a UI callback or ISR. A wake queue may retain its message pointer:
use a stable stock sentinel rather than a module-owned buffer, and preserve a
stock return address across a blocking receive. Test the actual card routines
with fresh emulator processes as well as the portable storage core. A stock-only
reconstruction has no runtime registry; declare any private scheduling shim and
bind both image hashes rather than treating it as the complete installed base.
Sidecar files require explicit backup/copy/reload semantics and separate physical
qualification; successful module-set Keep does not prove entered data was saved.


Bank name templates need explicit per-track override flags: an empty name may
be a deliberate local override, while an unedited track still inherits. Bind a
name editor's commit to its captured destination, rather than a bank selected
later by an engine poll. When a larger private runtime no longer fits a firmware
zero cave, publish its verified relocation/site fixture into verified-unused RAM
after emulator boot; record that simulation and its hashes explicitly. Never
claim that a stock/shim or manual publication probe exercised the resident loader.

For a one-time MIDI template, distinguish native bank/Part state, saved Part
copies, UI caches and actual outgoing MIDI. A template written only into current
Parts can be undone by Reload Part. A cached UI lane can lag the bank's valid
channel even when a controller sends on the correct channel. Verify all these
separately. Save to New needs a successful clone boundary with both project
identities; folder-change polling cannot safely distinguish copying from loading
an unrelated project. Stage disposable cards for serialization research before
implementing an on-device transaction; staged files do not qualify interruption
recovery or a production lifecycle event.


### Prove standalone card startup separately

A runtime publication fixture does not test a card recipe. Boot the MAIN
decoded from the exact packaged BIN in a fresh emulator process, with no saved
runtime module set, injected RAM code, direct calls or timing/IRQ shim. Use the
shared core’s tick/key/encoder tables, retain the runtime package’s stock guards
and hash-copy references, and compare complete native and browser BIN/SYX
outputs under identical startup settings. Record UART output separately from
assignment-state checks; a working setup screen does not prove MIDI transmission.
Emulator results remain separate from physical flash and restart qualification.

For a resident object in the existing card engine, retain that engine’s bootstrap,
logger and arena ownership; do not install a second core boot/arena recipe.
Guard and check the union of platform and module writes before applying any.
Compare the new object’s complete relocated text with an independent native
link, then boot the actual combined BIN and check persistence again. Keep the
card adapter identity separate from a retained USB implementation pin in build
reports; success on a standalone image does not qualify a different combined
boot path or companion audio behavior.

For an initial card installer using the existing USB base, use its MWST saved-set
format, not the MWMS upload transaction. Bind each seed to the exact base digest,
retain original unrelocated packages and sector-pad the files as modset.c does.
Replace both seed peers only after backing them up; an old higher generation
can otherwise win. Verify the actual C reader and fallback/foreign-base behavior,
and compare the included base with the ordinary published base download. This
does not qualify native restoration, a host USB driver or physical reboot.

### Verifying a USB revision change

A module ID/layout does not distinguish code revisions. Pin both full package
hashes, retain every companion hash and verify the device's MWS1 full-set digest
at the idle boundaries after Undo/Keep and after restart. The cached request 38
digest is deliberately unavailable while a whole-set trial owns its rows; do not
poll it throughout the trial or weaken the base's ownership checks. Inspect the
read-only inventory/name during that trial, then check exact hashes once idle.
A label-only package revision can exercise replacement/rollback without changing
project behavior; identify that limited scope explicitly. It does not qualify a
future changed MIDI implementation. Ordinary saved-file tail padding may retain
old bytes after Keep; validate the logical body checksum and ignore only padding
beyond the declared logical length, within the sector-aligned file bounds.

Saved-file export (requests 31–33) is optional and is absent from published base
`0c5934e1…`, even though it supports MWS1 identity and Keep/startup status. Do not
require that export merely to exercise module updates. For an exact reviewed
module subset, derive candidate rows from pinned package hashes and require the
live MWS1 digest to match all of them. Use saved=7 plus complete counts for the
base's save/read-back confirmation, then saved=1 plus the exact runtime digest
after restart. State that saved-file bytes were not exported. If export is
available, validate its files; a failed, partial or corrupt export must not be
silently treated as unsupported. Unknown packages or a mismatched digest stop
the test; matching names/IDs alone never permit an update.

Keep a local USB installer's exact base/package review separate from a historical
resident card composer's compiler fingerprint. An upstream merge invalidates the
relevant review; rebuild and recheck that path before updating its pins. Preserve
old hardware-test base/package identities separately so a test page cannot treat
a newer base as already qualified. Draft-specific setup and storage details live
in [Midi Mode 2 local setup](../../sdk/drafts/midi-cc-slots/LOCAL_SITE.md) and
[storage lessons](../../sdk/drafts/midi-cc-slots/HARDWARE_NOTES.md).

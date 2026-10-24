# Midi Mode 2 — local development draft

Unqualified development draft. A stock-free USB trial package can be compiled
by the local app; no public catalogue entry or release is added. Hardware and
saved-project persistence are not qualified. Use only a disposable test project
for trials. The local page offers explicit Keep, removal and restart checks;
it does not flash firmware. The user reported restoration and working controls on 0.0.4
after restart; 0.0.6 project profiles have not been tested on hardware; independently bound hardware qualification remains outstanding.

The prototype replaces either MIDI CONTROL 1 PB/AT position with an
independent CC 0–127 assignment per MIDI track. Zero in each assignment byte
means stock PB/AT; 1–128 encodes CC 0–127. Existing CC1–10 retain their storage.
The proposed assignments belong to each Part, matching stock CC assignments.

Stock 1.40C already has six CONTROL 1 SETUP bytes per MIDI track, although
SETUP hides its first two positions. This prototype exposes those positions
and routes mapped values through the stock CC sender, including its enable,
channel, mute and duplicate-value handling. It creates no transport clock.
The stopped-panel gate has measured the two CC positions, stock controls and
STK restoration. Sequencing, persistence and hardware runtime integration remain
unqualified. See TESTING.md.

## Name, copy and artwork

The presentation name is **Midi Mode 2**. The installed development identity
remains `midi-cc-slots`; no native code or package hash changes for the name.
The [proposed module copy](presentation/COPY.md),
[original CC Map-style artwork](presentation/thumbnail.svg) and
[reviewed emulator screenshot gallery](media/README.md) are ready for review.
They do not register or publish the module.

## Version 0.0.6 project-profile test

Eight ten-character names are shared across the project. Double-tap MIDI SRC,
click F (NAME/PUSH), enter a name and confirm with YES. Channel defaults come
from **Bank 1, Part 1**. On first visiting a bank/Part outside Bank 1, OFF channels
inherit those defaults; existing nonzero channels are preserved. Initialized
bank/Part profiles retain independent overrides, including OFF. Later default
changes do not overwrite previously initialized profiles.

Names and channel profiles autosave to `MIDI2_0.DAT` and `MIDI2_1.DAT` in the
current project folder while transport and recorders are stopped. Wait for
**MIDI PROFILE SAVED** before switching off. A failed write reports **MIDI SAVE
FAILED** and retains the preceding checkpoint. Copy both files when backing up
or moving a project; do not delete them expecting native project saves to
contain this data. A native Save As/copy may omit them. Same-project reload,
Part copy/clear and native project save/rollback integration remain unqualified;
shared names deliberately do not belong to a Part. Changing project folders
loads that project's profile instead of carrying the previous names across.

Use a disposable project for hardware tests. Keep installs the module itself;
profile files store entered names and channel settings independently. Ordinary
CC assignments still use stock Part/project saving. The native emulator card
restart test supplies the base UI callback through a declared private shim;
it is not evidence of a physical reboot or the full base/companion set.

For an already installed same-ID draft, open the local updater below and choose
**Try updated module**. Merely adding an already installed module does not
replace its package.

## Earlier version 0.0.5 naming test

The earlier local test version combined the existing CC behavior with temporary
MIDI track names. Double-tap SRC on a MIDI track, then click F at NAME/PUSH.
Use the stock name editor (ten characters), YES to confirm or NO to cancel.
PUSH shares the neighboring value's vertical baseline. A nonempty name
replaces the normal MIDI channel header; CHAN remains editable in SRC SETUP.

Names are volatile and only indexed by the current Part and MIDI track.
They reset when the module is replaced or restarted. Bank/project identity,
save/load/reload and Part copy/clear are not integrated; stay in one disposable
test project and bank. Keep installs the module, not the entered names.

To replace an earlier same-ID draft, open
`http://127.0.0.1:5173/?preview=midi-cc-slots`, build/read modules and choose
**Try updated module**. Verify CC behavior and naming before Keep. The normal
module-set review cannot distinguish these same-ID individual package versions
from its inventory; the module detail page links to this explicit updater.

## Controls and usage

On MKII, select a MIDI track and press FX1 for CONTROL 1. Double-tap FX1 to
open MIDI CTRL 1 SETUP. The stock FUNC + FX1 shortcut also opens this menu.

Click encoder A to switch its PB position to CC mode, or encoder B to switch
its AT position. Each switches independently. The SETUP caption follows the
mode: PB or AT for native, CC for mapped. STK means native behavior; a number
below CC is the assignment. A click changes the mode immediately.

In CC mode, turn that encoder to choose CC 0–127 and press YES to confirm the
number. Turning alone cannot leave STK or switch back to it at the bottom of
the CC range. Click again to restore PB or AT. Switching into CC mode starts
at CC0; the previous CC number is not remembered across a return to STK.

Return to CONTROL 1 with FX1. Enable each value with the normal FUNC + encoder
press and turn it to send values. Ordinary main-page encoder clicks retain
their stock behavior. On both main CONTROL pages, each CC header is its
assigned number (0–127),
not a CC1–CC10 slot name. Remapped PB/AT headers also show their CC number;
native PB and AT keep their names. Short numeric headers and the two-letter
SETUP captions fit fully inside the stock highlight. Values stay ordinary
0–127 bytes.

Build private experiments only, using output folders outside every checkout:

```sh
python3 sdk/drafts/midi-cc-slots/build_probe.py --stock /private/local/MAIN.bin --output /private/local/cc-candidate
python3 sdk/drafts/midi-cc-slots/build_monitor.py --native /local/octabam --build /local/emulator-build --output /private/local/cc-monitor
python3 sdk/drafts/midi-cc-slots/verify_panel.py --candidate /private/local/cc-candidate/candidate.private.bin --emulator /private/local/cc-monitor/ot_emu --output /private/local/cc-panel
```

The monitor builds only a private CLI adapter against the selected emulator's
existing libraries. Its extra command reads UART0 output; it neither injects
MIDI nor edits firmware state. Inputs and library fingerprints are recorded.
The panel gate uses real double-taps, keys and encoder clicks, reads channel
bytes to correct stock encoder acceleration, and decodes MIDI running status.
It covers mode clicks, held-encoder fast editing and the full controller
range. Add `--sequencer` to include its two playback-lock cases.

## Local app, installation and removal

For the normal local catalogue, set `VITE_LOCAL_CC_SLOTS=1` in the checkout's
ignored `.env.local` and start the development server. Open Modules → MIDI & USB
and choose **Midi Mode 2**, marked **Local draft**, or open
`http://127.0.0.1:5173/module/midi-cc-slots/`. Add it to your module set, then
use Your Octatrack → Sync to Octatrack to review, trial and explicitly Keep.
An already installed `f36a496d` is recognized as the same module. Preserve
other selected modules when reviewing the set.

This overlay and its on-demand, hash-verified package endpoint are development
only. Production builds do not register the draft. Card firmware builds refuse
sets containing this draft with instructions to use USB. The public catalogue
and native card composer remain unchanged. The diagnostic page below remains
available for detailed restart checks.

Use Node 24, Python 3.12+ and `m68k-elf` binutils on PATH. From this checkout:

```sh
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/?preview=midi-cc-slots` in a WebUSB-capable
browser. Exit USB DISK MODE after ejecting the card. Choose **Connect Octatrack**,
then **Build draft and read installed modules**. Review the base digest,
installed modules and draft package digest. **Start temporary USB trial**
adds only this draft and runs the base self-test through the existing link.
The base rejects conflicting patches. Test the controls and outgoing MIDI,
then choose **Undo trial** or **Keep installed**. Do not use your working project
for qualification. Keep saves the complete running module set to the CF card;
use the installed Modwerk base, not a temporarily RAM-booted base. Wait for
**Card save confirmed** before switching off. A missing or failed save status
does not count as success; leave the unit on, check its card and choose
**Check card save** again.

After a confirmed save, power-cycle manually, reconnect and choose **Check after
restart**. This requires the same base, the base’s startup-restoration result,
and the reviewed module IDs/layouts including companions. Browser metadata
survives a page refresh; it is not a backup or a readback of package bytes.
A successful check still needs a front-panel/MIDI check on a test project.

To remove the feature, build/read modules again, choose **Try removing MIDI CC
Slots**, check native PB/AT behavior, then **Keep removal**. Repeat the card-save
and restart checks. Only this module is changed; companions must remain.
Keep installs the feature, while CC assignments use the normal Octatrack
Part/project save workflow, which remains unqualified for this draft.

The route and compiler endpoint exist only in the development server. The
endpoint compiles original source into a temporary directory, returns a
stock-free ABI 7 package and removes its temporary files. It accepts no
firmware input. The compiler refuses source changes whose package digest differs from the
last software-verified local build. The app checks package identity, connected loader capabilities
and an inventory snapshot tied to the base and running set before sending.
It sends only one module change, with an explicit tested-trial Keep or Undo.
Keep uses the existing base’s whole-set card persistence; the page confirms
the diagnostic save result rather than assuming a resolved Keep call saved.
It never writes firmware.
Hardware support is checked on the connected unit, not inferred from its
firmware filename. Unknown or insufficient capabilities block the trial.

To reproduce the package and private software proofs:

```sh
python3 -B sdk/drafts/midi-cc-slots/build_runtime.py --output /private/local/cc.mwrm
python3 -B sdk/drafts/midi-cc-slots/verify_runtime.py --package /private/local/cc.mwrm --stock /private/local/MAIN.bin --output /private/local/cc-runtime-proof
python3 -B sdk/drafts/midi-cc-slots/verify_loader.py --package /private/local/cc.mwrm --main /private/local/MAIN.bin
python3 -B sdk/drafts/midi-cc-slots/verify_persistence.py --package /private/local/cc.mwrm --main /private/local/MAIN.bin
```

`verify_runtime.py` can also check every site/copy guard against a privately
decoded user build with `--installed-main`. It checks direct overlap with the
current app base's patch sites and scans literal code for stock overlaps.
`verify_loader.py` uses the actual C loader with host machine glue to test the
exact package's publication, Undo, repeat install, removal and reclamation;
it does not execute ColdFire code, model real tasks or establish hardware safety.
`verify_persistence.py` also compiles the real saved-set implementation, keeps
the exact package in simulated files and restores it in fresh processes. It
covers removal/restart and failed-write fallback while preserving a synthetic
companion. It does not exercise physical card I/O or establish reboot behavior
on a unit.

## Compatibility and limitations

The emulator prototype patches stock sites directly. The relocatable USB
package uses guarded private sites and hash-backed stock copies; it does not claim the emulator code cave on a unit. No current base
event or direct base write overlaps those sites. The user reported the controls and display working on hardware, without an
independently read build identity. On-device
install/self-test/Undo/removal and persistence still need exact-build testing. Full
release metadata, card composition and Keep qualification remain outstanding.
An opt-in local development listing is available; no public catalogue entry is added.
No compatibility with MIDI Scenes or other modules is established merely
because the candidate hook addresses do not overlap their current recipes.
Same-channel competing tracks and mixed PB/CC assignments need explicit tests.

## Authorship and licences

Original experimental adapters: Cooper Scobey, MIT. Stock routines and tables
remain private. Build-time replay spans must be read from the user's own
verified image; they must never be copied into the repository or uploaded.

## Screens and audio

Five actual MKII emulator LCD captures and reviewed captions are in
[media/README.md](media/README.md), with sanitized source/image/package provenance.
Firmware, raw LCD/RAM planes and capture working files stay private.
No receiver audio or physical-device capture.

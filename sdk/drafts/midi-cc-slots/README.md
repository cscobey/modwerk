# MIDI CC Slots — private emulator prototype

Unqualified research draft. Not a released module, runtime package or hardware
candidate. Do not select it in module sets or install it on an instrument.

The intended feature replaces either MIDI CONTROL 1 PB/AT position with an
independent CC 0–127 assignment per MIDI track. Zero in each assignment byte
means stock PB/AT; 1–128 encodes CC 0–127. Existing CC1–10 retain their storage.
The proposed assignments belong to each Part, matching stock CC assignments.

Stock 1.40C already has six CONTROL 1 SETUP bytes per MIDI track, although
SETUP hides its first two positions. This prototype exposes those positions
and routes mapped values through the stock CC sender, including its enable,
channel, mute and duplicate-value handling. It creates no transport clock.
The stopped-panel gate has measured the two CC positions, stock controls and
STK restoration. Sequencing, persistence and runtime integration remain
unqualified. See TESTING.md.

## Controls and usage

On MKII, MIDI → FX1 opens CONTROL 1; FUNC + FX1 opens its SETUP. The proposed
A/B selectors display STK for native behavior, otherwise a CC number. Enable
each value with the normal FUNC + encoder press. The main-page PB/AT labels
still identify the original positions; their values are ordinary 0–127 bytes.

Build private experiments only, using output folders outside every checkout:

```sh
python3 sdk/drafts/midi-cc-slots/build_probe.py --stock /private/local/MAIN.bin --output /private/local/cc-candidate
python3 sdk/drafts/midi-cc-slots/build_monitor.py --native /local/octabam --build /local/emulator-build --output /private/local/cc-monitor
python3 sdk/drafts/midi-cc-slots/verify_panel.py --candidate /private/local/cc-candidate/candidate.private.bin --emulator /private/local/cc-monitor/ot_emu --output /private/local/cc-panel
```

The monitor builds only a private CLI adapter against the selected emulator's
existing libraries. Its extra command reads UART0 output; it neither injects
MIDI nor edits firmware state. Inputs and library fingerprints are recorded.
The panel gate uses real keys and encoders, reads channel bytes to correct
stock encoder acceleration, and decodes MIDI running status.

## Compatibility and limitations

The prototype patches stock sites directly in a private emulator image. Base
events, runtime ownership, USB install/self-test/Keep/Undo/removal, full module
metadata and native composition are outstanding. No catalogue entry is added.
No compatibility with MIDI Scenes or other modules is established merely
because the candidate hook addresses do not overlap their current recipes.
Same-channel competing tracks and mixed PB/CC assignments need explicit tests.

## Authorship and licences

Original experimental adapters: Cooper Scobey, MIT. Stock routines and tables
remain private. Build-time replay spans must be read from the user's own
verified image; they must never be copied into the repository or uploaded.

## Screens and audio

Stock MKII screen inspection performed locally. Private firmware-derived
captures are retained outside Git. No receiver audio or hardware capture.

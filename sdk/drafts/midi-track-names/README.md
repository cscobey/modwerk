# MIDI track names — emulator prototype

Original MIT experiment by Cooper Scobey, 0.0.1-experimental. This is a solo
stock-1.40C MAIN experiment, not an installable module or card update. It does
not change the existing Midi Mode 2 runtime source, package or catalogue entry.

## Controls and scope

Select a MIDI track and double-tap SRC to open MIDI NOTE SETUP (the MIDI SRC
setup page). The unused F position shows NAME / PUSH. Click F to open the
stock name editor with the title MIDI TRACK NAME. Use its normal arrows,
LEVEL encoder and character grid; YES commits and NO cancels. The prototype
uses the stock restricted naming alphabet and allows ten characters.

A nonempty name replaces MIDI Ch:01 (or the disabled-channel label) on the
normal track screen, including both CONTROL pages. The channel remains in
the CHAN setting in MIDI NOTE SETUP. Empty names retain the stock header.
Audio tracks do not use the name override or open this editor.

There are 32 volatile 16-byte slots, indexed by the current Part and MIDI
track. This proves track/Part separation within one emulator session, not
project integration. Names currently do **not** follow bank/project identity,
save, load, reload, Part copy/clear or reboot. Changing banks/projects could
reuse names from the same numbered slots. Do not use this image on hardware.

## Reproduce privately

Use Python and m68k-elf binutils, an existing reviewed `ot_emu`, and your own
verified original stock 1.40C MAIN. Pick new output directories outside every
Git checkout. No stock code, copied spans, firmware, raw LCD, cards or compiled
outputs belong in Git.

```sh
python3 -B sdk/drafts/midi-track-names/build_probe.py --stock /private/local/MAIN.bin --output /private/local/names-build
python3 -B sdk/drafts/midi-track-names/verify_panel.py --emulator /local/ot_emu --candidate /private/local/names-build/candidate.private.bin --receipt /private/local/names-build/receipt.json --output /private/local/names-panel
```

The builder verifies the whole stock image hash, checks its solo code space,
and copies the displaced header instructions only from that private input.
Its receipt records source/image identities and patch guards. Placement is
for this isolated experiment only; it overlaps the existing CC prototype's
solo placement and cannot be combined as-is. Runtime/base composition needs
a separate design, including shared UI events and removal of callbacks.

The verifier uses real panel input for every name edit. It only reads memory
and the actual LCD; it never injects names or edits a card. PNGs use the shared
LCD decoder at integer scale six. Reports and command logs remain private.

## Next work

- Design storage keyed to project/bank/Part and bind every lifecycle operation.
- Verify clearing a name, all stock editing shortcuts and compact views.
- Test channel edits/disabled channels, MKI and a playing sequencer.
- Integrate through shared base events and a relocatable runtime package;
  qualify coexistence, install/Undo/removal and persistence separately.

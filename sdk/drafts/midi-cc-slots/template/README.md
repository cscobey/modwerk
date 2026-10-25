# On-device project initialization experiment

This opt-in implementation is separate from the local site's reviewed 0.0.7
build. Do not promote it until its exact native workflow and removal checks
pass. Emulator results do not qualify hardware or public catalogue admission.

## Player behavior

On an unprotected, stopped test project, set Bank A / Part 1 names and MIDI
channels, then save the project normally. In MIDI SRC SETUP, encoder D shows
INIT / PUSH. Push D and type APPLY in the stock confirmation editor. NO cancels.
The completed operation initializes native current and saved Parts once and
freezes inherited names as independent bank names. Existing legacy initialized
channel profiles (including OFF) and explicit name overrides are retained.
Initialize before making new bank-specific edits during migration: an old
saved profile remains authoritative for an already initialized legacy Part.

Afterward, bank and pattern changes never read or apply a sidecar channel map.
Channels belong to normal project/bank storage. Save channel edits normally.
Names save separately in the project folder. Bank A edits do not propagate
after initialization. Save to New copies names and the completed marker into
the actual new destination; ordinary project loading never implies a clone.
A protected template may be copied through native Save to New; INIT itself
requires an unprotected project.

## Storage and recovery

Back up the complete project before testing. Names and the initialization
marker use alternating, CRC-checked `MIDI4_0.DAT` / `MIDI4_1.DAT` checkpoints.
The old `MIDI3_*.DAT` and `MIDI2_*.DAT` files are read for migration and left
unchanged. Keep all sidecars with project backups.

Initialization requires all sixteen `.work` / `.strd` bank pairs to have valid
checksums, matching non-channel data and channels matching the native engine.
Missing, damaged or unsaved banks produce SAVE PROJECT FIRST without applying
the map. A verified journal (`MIDI4_J0.DAT` / `MIDI4_J1.DAT`) records the previous
channel map and channel-neutral fingerprints before mutation. Only sectors
containing channel cells or the bank checksum are rewritten; unrelated bytes
are preserved. Every bank copy is read back and verified before its peer is
changed.

An interrupted, uncommitted initialization restores the recorded previous map,
then reloads the native project. It never recalculates Bank A defaults. A torn
sector can be repaired from the other verified saved copy. If neither copy
matches its recorded fingerprint, recovery stops rather than inventing data.
A completed metadata checkpoint retires the intent without reapplying channels.
This does not prove resilience against arbitrary physical CF/FAT corruption.

Undo or removal restores module code; it does not reverse a completed native
bank initialization. Restore a project backup to reverse those project edits.

## Proposed shared lifecycle events

The earlier prototype proposes successful project-clone and project-activation
events. This private implementation explores three guarded stock boundaries:
source capture before the Save to New destination check (`0x40084f44`), successful
destination bank-write completion (`0x4008505c`), and full project load completion
through the native bank loader (`0x400905d4`, full-load caller `0x400853de`).
Failures must not emit successful-clone notifications. Background bank loads
must not masquerade as project activation. Source capture must include dirty
in-memory names and destination completion must occur in the stopped engine.

These direct sites are experimental, not admitted shared SDK events. Owner
review and shared event integration remain prerequisites for public release.
No module may depend on Octakit or another module for these notifications.

## Checks

Run host transaction/fault and actual bank-sector tests with:

```sh
python3 -B -m unittest sdk.tests.test_midi_template_journal \
  sdk.tests.test_midi_template_banks
```

Build privately with `build_runtime.py --profile --project-template`, then run
`verify_runtime.py --profile --project-template --external` with private stock.
`verify.py` drives the real D encoder, stock text editor, native Save to New and
fresh emulator processes. Its card and firmware outputs stay outside Git.
The private publication supplies the normal UI tick callback and a separately
recorded fixture for the documented first-sector card-write interrupt race
(`TRAPS.md#trap-first-sector-irq`); neither fixture ships in the module. Generic
resident key/encoder dispatch, exact hardware timing and power loss remain
separate qualifications. Record observed results, not intended results.

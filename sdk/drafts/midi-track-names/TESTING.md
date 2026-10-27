# Emulator evidence — 24 October 2026

Solo 1.40C experiment; no hardware or USB access. Original authored image is
868 bytes, including 512 bytes for 32 volatile names. Candidate MAIN SHA-256:
`f2338280fdddaa75bfb62a1f98d850b858e8fb30d7ef0e021a2db624452b74d9`.
Authored names.s SHA-256: `28e459eb0c6278bbaf62bc062e1723d2ae9a099339b965d60faf532763f3597e`.
The stock input hash and exact source identities are recorded by build_probe.py
and the private receipt. The currently installed Midi Mode 2 package is unchanged.

The MKII stopped-panel verifier passed 46 checks for empty initialization, entry
through F in MIDI NOTE SETUP, name edits with real stock-editor key presses,
YES commit, NO cancellation, independent names on all eight MIDI tracks,
separation across all four Parts, a ten-character name without adjacent-slot
overwrite, and exclusion from audio SRC SETUP. Source settings are compared
before and after the first name edit. No names are injected into RAM.

Actual LCD PNGs were visually reviewed: NAME / PUSH in the previously blank F
position; stock MIDI TRACK NAME editor; BASS in the channel-header position
on NOTE and both CONTROL pages; unchanged unnamed Track 2; BASS after return
and cancellation; ten W characters fitting in the header; native audio SRC.
Screenshots are emulator illustrations only, not hardware evidence.

Not tested/implemented: physical behavior, MIDI timing/output, actual channel
edits, MKI, compact/arranger views, project/bank identity, file storage,
save/load/reload, Part copy/clear, reboot persistence, coexistence, USB lifecycle
or native card packaging. The direct stock UI hooks and solo cave are research
placements, not approved runtime/base integration sites. No public release.

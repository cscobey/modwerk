# Midi Mode 2 release measurements

This is an incomplete qualification record for 0.0.18-experimental. The runtime
package is unchanged. No timing pass or complete RAM/stack bound is claimed.

## Reproduced memory layout — 29 October 2026

Run from the repository root with the reviewed m68k-elf toolchain on PATH:

```sh
python3 -B sdk/drafts/midi-cc-slots/measure_memory.py --output /private/local/new-midi-memory-run
```

The destination must be new and outside Git. It retains private ELF, linker
maps, objects and compiler stack reports. The sanitized result is
[evidence/memory-layout-0.0.18.json](evidence/memory-layout-0.0.18.json).
The command refuses evidence if its package differs from `local-build.json`.
Audit and ordinary compilation both reproduce package SHA-256
`8d971baca19198b9e35d7644c7c8810f917471f980eadc2db03fab8de3668451`.

| Allocation or file | Bytes | Scope |
| --- | ---: | --- |
| Encoded package | 33,434 | Transfer/card file, not resident RAM |
| Text sections | 13,860 | Code, inline constants/replay placeholders and 136 bytes of assembly-owned state |
| C zero-initialized sections | 14,636 | Profile, I/O buffers, CRC table and state |
| Merged C strings | 442 | Resident image |
| Linker gaps and sentinel | 26 | Resident image |
| Complete dense image | 28,964 | Sum of preceding image rows |
| Runtime module header | 510 | Target ABI, 36 hooks |
| 24 site records | 1,728 | 72 bytes each, includes original and replacement bytes |
| Pool header alignment | 2 | Round header and sites to 16 bytes |
| Pool image alignment | 12 | Round image to 16 bytes |
| Resident pool extent | 31,216 | One project-wide module, not one allocation per MIDI track |
| Two same-size revisions | 62,432 | Old plus candidate retained for replacement/Undo |

The 25 stock copies are reconstructed into existing image placeholders. They do
not allocate separate spans. Relocation records remain package metadata. No
authored DSP program, DSP buffer or module-owned heap is allocated. State for
all eight tracks and 16 banks is already inside this image. The stock editor
buffer and channel/project structures are reused; their storage belongs to the
base/stock system. Four 4,096-byte MIDI4 sidecars are project card storage.

The pool calculation uses target-compiled `sizeof` from the current loader and
Octatrack event header, then follows `loader.c`'s admission formula. It excludes
the base's preallocated upload staging, ownership ledger and event tables.
It is not a whole-system peak or a measured pool delta on the physical unit.
Different bases require a new target ABI probe.

Compiler `-fstack-usage` reports a largest individual C frame of 1,440 bytes in
`persist_bank`. This is **not** the stack peak: caller frames, assembly wrappers,
stock file calls and interrupt/task context must still be bounded. There are no
unbounded compiler frame records; `dynamic,bounded` describes bounded outgoing
call arguments too. Hardware stack canaries have not been measured.

## Read-only hardware meter capture

The USB bridge must already be running, with the browser disconnected. Safely
eject and leave USB DISK MODE first. This command sends only identify,
inventory, whole-set digest and public load requests:

```sh
node sdk/drafts/midi-cc-slots/capture_load.mjs --output /private/local/new-stopped.json --label 'Test project, stopped, MIDI2 and named companions' --seconds 20
```

It refuses overwriting a file, records unavailable values as null, verifies an
unchanged whole-set digest and warns if the cached frame counter stands still
or meters are unavailable. A cached counter alone cannot establish that the
audio engine stopped. One-second polling is not an interrupt timing probe.

On 29 October the connected unit identified base
`c1ae2ee92a829e06aa9398d35981b8228efdd34c578c9583ef36fba8f5bc637f`.
Inventory listed SIDECHAIN COMP, Play Modes, Mute Modes, MIDI MODE 2 and Analog
BD. Its whole-set digest was
`6b9b601b7df88a41b46bd1299397ece3b42d0a825989da3edcd0b06c3fc02e64`.
This does not independently resolve each package's hash. Initial 20-second
capture was in disk mode, confirmed by Cooper; a second was after Cooper
reported returning to the normal stopped project screen. Both returned null
CPU/DSP meters and a nonadvancing cached frame counter. Neither provides a load
measurement. Development memory requests were explicitly unsupported.
Cooper then reported that PLAY did not start playback after leaving disk mode.
The bridge was closed; Cooper power-cycled the unit and reported that playback
worked again. Cause and module attribution are unestablished. Disk-mode exit
and playback recovery need reproduction before release; do not characterize the
initial captures as a normal stopped baseline.
Raw readings remain private; no firmware, RAM or project contents are included
in this report. No install, removal, Keep, project save or flash was performed.

## Remaining measurements

1. Resolve disk-mode exit/playback recovery and unavailable public meters before
   using any load percentages.
2. Review a temporary development-base session separately, including exact
   symbols, complete companion packages and recovery back to the existing kept
   set. Do not Keep on a temporary base: its identity differs from the flashed
   base and can replace both saved-set peers. Do not flash for measurements.
3. Measure pool free/largest run before, during replacement, after Undo and
   after temporary removal/reinstall; verify the exact original runtime set.
4. Bound assembly and nested C/stock stack use, staging lifetimes and transient
   allocations. Reconcile these with task stack capacity and hardware guards.
5. Run matched baseline and module tests with unchanged companions/project:
   eight MIDI tracks, PB/AT and CC modes, CC0/127 and value endpoints, simultaneous
   p-lock/LFO CC activity, same-channel competition, bank/Part changes, name
   browsing/editor confirm/cancel and autosave. Record worst path and deadline,
   interrupt/frame gaps and idle headroom. Separate stopped INIT/replace/cancel,
   recovery and Save to New latency from real-time playback paths.
6. Capture outgoing MIDI with a receiver and test incoming note/CC/clock flood
   near wire rate at 240 BPM or above for at least 60 seconds. Count drops and
   stuck notes, stop mid-note, change Part and inspect companion audio. Retain
   tool versions, actual workload and limitations. Public status maxima cannot
   replace worst-case cycles/event evidence.
7. Finish `tests.qualification` and the performance record only with the actual
   numbers, then prepare public catalogue integration and owner review. The
   current local draft remains opt-in.

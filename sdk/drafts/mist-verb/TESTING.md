# Mist Verb testing

Date: 2026-10-23. Version: 0.1.0-experimental. Target instrument: Octatrack MKII.
Fork base: `bedbb362` (current with upstream when prepared). This is unpublished
work on `feat/mist-verb`, under `sdk/drafts/mist-verb/`.

## Commands and source identity

All commands run from the Modwerk worktree. The host tests require a C++17
compiler, Python 3.10+ and no firmware or external Python packages:

```sh
python3 -B sdk/drafts/mist-verb/verify_reference.py --output /PRIVATE/mist-reference
```

`verify_reference.py` checks every upstream file against sources.json, creates
storage-only derivative headers in the private output folder, and compiles
with `-O2 -DTEST -fno-fast-math -ffp-contract=off`. `TEST` selects stmlib's
portable saturating conversion instead of ARM-only inline assembly. The
original upstream files stay unchanged.

Result: PASS, 63 cases × two storage candidates, exact floating-point output
identity with the original at 32,000 Hz. Cases cover TIME 0/.5/.98, diffusion
0/.7/.95, LP coefficient 0/.5/1, diffuser amount 0/1, input gain 0/.2/1 and
wet/dry 0/.5/1, through different chunk sizes including single samples.
They are an enumerated matrix, not every combination of all controls.

PASS: every 16-bit bit pattern at each packed-field position and ring ends;
neighbour preservation, twelve full random fill/read passes, physical words
bounded to 24 bits, clear, startup silence and exact dry bypass with SMEAR 0.
The 64,000-sample cases wrap the original ring and all independent lines.
A generated 8-second WAV has two seconds of synthesized excitation and a tail.

Report and input-source hashes: `evidence/reference.json`. These tests do
not cover native fixed-point arithmetic, native LFO accuracy or sample-rate
conversion. The per-line host candidate's finite uint32 tick counter is a
short-test model, not the intended long-running firmware counter design.

## Native storage primitive test

```sh
python3 -B sdk/drafts/mist-verb/verify_packing_dsp.py \
  --sdk /ABSOLUTE/modwerk/sdk/octabam \
  --stock /PRIVATE/stock-MAIN.bin \
  --assembler /ABSOLUTE/dsp_asm \
  --host /ABSOLUTE/dsp_host \
  --disassembler /ABSOLUTE/dsp56kDisassemble \
  --output /PRIVATE/mist-packing
```

Result: PASS. The 142-word packed_probe.asm was assembled at P:0x15000,
disassembled and rejected on unexpected MPYSU/REP/invalid instructions. Its
code span was verified not to overlap the local original stock payload.
The source is not inserted into an instrument image or USB package.

Eight distinct FX2 instances, four on each emulated core, each process 65,536
integer test cells: every 16-bit bit pattern and four logical ring wraps.
Trigger splits 0, 1, 7 and 15 are assigned on each core. Current and previous
cells must match the input sequence. The native access span is guarded to
10,924 Y words, shared Y is guarded and Y starts with garbage (seed 1776).

Observed peak: 6,639 executed instructions per core per 16-frame call with
four probe instances. This is a storage probe with two reads and one write
per sample; it is NOT a reverb cycle count, hardware utilization or supported
full-effect instance count. Evidence: `evidence/packing-dsp.json`.

The local existing DSP tools were rebuilt from the earlier Modwerk checkout
`f99681ec170884593079b514da8b2f706d07e7d6` and its patched vendor source.
Their identity differs from the current fork's complete pinned container;
record the latter separately before claiming release reproducibility.

## Experimental native 32 kHz audio core

`generate_core.py` writes `core32.asm`; `--check` rejects stale generated code.
`render_core32.py` takes the same tool/SDK/stock/output options as the storage
probe. It assembles the core, injects a 128-word calculated gain table into a
private stock memory dump and runs one instance per core. It never builds or
flashes instrument firmware. Sample rate for this experiment is 32,000 Hz.

PASS: both core outputs identical, exact MIX 0 dry bypass, nonzero wet tail,
no Y guard/shared-memory/code clobber under garbage start. The 12,972-word
buffer is progressively cleared over 102 dry calls. The final core is 1,253
program words plus 128 gain-table words. init preserves r1/n1/m1.

Settings: TIME 110, DAMP 64, DIFF 94, SMEAR 0, GAIN 83, MIX 127/0. Five seconds
of audio after a 4,096-sample silent pre-roll; one second of original synthesized
noise excitation. Every result is in evidence/core32.json. This is not an
extreme-controls, trigger-split or full-load stress test.

The initial 24-bit oscillator recurrence showed substantial drift; the current
experiment retains 48-bit oscillator histories. It approximates the upstream
coefficient recurrence and omits the tiny low-history × epsilon product.
It is not IEEE-float emulation. It also quantizes scalar arithmetic to fixed
point. The native/reference waveform residual is **−10.15 dB relative to the
reference energy** on this test: a measured discrepancy, not a source-parity
pass. Diagnose numerical/modulation differences and measure decay/spectrum
and listening behavior before claiming fidelity.

Peak: **22,327 executed instructions per core per 16 tank frames**, one
instance on each core. This prototype is substantially too costly for the
design target and includes no sample-rate conversion. Optimization is required.
It is not a measured hardware deadline, a stock-matched benchmark or a proven
supported instance count. The unoptimized address primitives were kept so
sound and memory semantics could be checked before optimization.

## Sound quality and remaining audio integration

Not tested: the full 44.1↔32 kHz conversion and instrument audio engine.
Alias rejection, clipping, DC, idle tails, oscillator drift and knob smoothing
must be measured on the actual assembled effect. Reference playback is not a
native audio test. No full-effect fx:audit or SPRING REV benchmark has run.

## Integration and performance

Not tested: contiguous P/X/Y placement beside stock effects, Analog BD and
common companions; native/browser parity; worst-case effect cycles; full
instrument stress; actual chooser, parameter delivery, locks, LFOs, scenes,
crossfader, Part/project save/load and missing-module fallback.

The site MCP passed protocol initialization, tool discovery and a read-only
reverb catalogue call using an isolated private workspace. It returned Mini
Verb and E-Verb; it does not list this unpublished draft. No device/API writes
or external messages were made. This is domain evidence, not rendered UI.

No module:doctor pass is claimed. Drafts are intentionally excluded from
publication; verify.py fails deliberately. Do not move this source into the
catalogue or claim release qualification merely to silence these gates.

## Hardware and lifecycle

Not tested on MKI or MKII. USB installation/self-test/Keep/Undo, removal,
missing-module handling, usable audio, board timing and physical reboot
persistence all remain open. The user selected emulator-first development.
Only actual reported version/image-matched hardware results or the owner's
explicit scoped waiver can complete the applicable release requirements.

## Remaining implementation order

1. The pinned Docker toolchain is built, and its reference test passes on
   Linux as well as macOS. Keep this identity bound to later native builds.
2. Optimize the initial native core using the proven per-line layout, diagnose
   its measured source discrepancy and compare with the oracle again.
3. Implement and test 44.1↔32 kHz conversion, control smoothing and dry/wet
   headroom. Keep delay lengths and source quantization unless a measured,
   documented tradeoff is agreed.
4. Benchmark/optimize against expensive stock SPRING REV on both cores,
   including moving controls and trigger splits. Run the sound audit.
5. Build native/browser/USB packages through the shared builders, verify
   placement/compositions and capture the real emulator UI. Qualify lifecycle
   and persistence, retaining physical hardware gaps explicitly.
6. Promote only after qualification, run module:doctor and pr:ready, then
   submit for first owner review and verify the published download after merge.

## Project checks

The complete project check passed with Node 24 and Python 3.14: 323 test files,
2,529 tests passed; SDK checks, lint, type checks, build and catalogue checks
also passed. The sandboxed attempt had local-socket EPERM failures; the same
checks passed with local-socket access. These are project regression results,
not qualification of the draft or its unfinished audio path.

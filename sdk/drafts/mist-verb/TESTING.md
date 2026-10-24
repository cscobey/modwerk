# Mist Verb testing

Date: 2026-10-23. Version: 0.1.6-experimental. Target instrument: Octatrack MKII.
Fork base: `bedbb362` (current with upstream when prepared). This is unpublished
work on `feat/mist-verb` in `cscobey/modwerk`, under `sdk/drafts/mist-verb/`.
The user requested fork-only development. The earlier upstream draft PR is
closed; further upstream submission requires a new user instruction.

## Current native milestone

Current native build: **0.1.6-experimental**, separate SMEAR input diffuser
removed. TIME/DAMP/DIFF/GAIN/MIX remain; encoder D is inactive, E/F retain
GAIN/MIX. The original tank topology, lengths and quantization are unchanged.
See [NATIVE_SRC.md](NATIVE_SRC.md) and `evidence/no-smear/` for the current
source-hashed reports and before/after comparisons.

- Tank: 13,432 Y words, 1,109 code words plus 128 gain words; nominal fixture
  peak 12,737 executed instructions/core/16 tank frames.
- Joined: 13,808 Y-word extent, 2,135 code words, 6,274 SRC words plus 128 gain
  words (8,537 P words total). X extent remains 240 including unused gaps.
- Three static both-core cases match 0.1.5 at SMEAR zero byte-for-byte,
  including exact dry and a high feedback/gain mixed case. Joined nominal
  peak falls 31,139 → 28,046 instructions/core/16 input frames (about 10%).
- Dynamic five-control traces match the host model at splits 0/1/15;
  audio matches across splits after startup alignment and silence stays zero.
- Full-scale standalone SRC matches its host reference after history relocation.
  Dirty seed 1776, Y/shared/code guards and both-core identity pass throughout.
- Matched 64-case moving-control benchmark: Mist 29,067 versus Spring 5,094
  peak instructions/core/16 input frames (5.71×); no chip-cycle claim.
- Bounded clear is now 132 words/call, retaining 102 calls and the known
  partition-dependent startup. Four tank controls ramp for 8 ms; MIX for
  5.805 ms. No installed or hardware qualification is claimed.

`verify_src_layout.py --check` still proves exact reconstruction of all 66
SRC coefficient rows and 1,522 schedule endpoints. The unimplemented layout
could save 2,128 P words; its estimated total is now 6,409 before decoder
changes, still above the documented empty package arenas.

The chronological sections below retain historical results. Their earlier
layouts, separate diffuser and statements of missing SRC describe those stages.
The current CLI takes `--controls TIME,DAMP,DIFF,GAIN` (four values).

`npm run module:doctor -- mist-verb` reports no installed module: this draft
is intentionally outside the module catalogue and installable module folders.
It is not a green release gate; package integration and qualification remain
unfinished. No catalogue entry is added to bypass that refusal.

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
no Y guard/shared-memory/code clobber under garbage start. The 15,480-word
buffer is progressively cleared over 102 dry calls (152 words per full call).
The final core is 1,452
program words plus 128 gain-table words. init preserves r1/n1/m1.

Settings: TIME 110, DAMP 64, DIFF 94, SMEAR 0, GAIN 83, MIX 127/0. Five seconds
of audio after a 4,096-sample silent pre-roll; one second of original synthesized
noise excitation. Every result is in evidence/core32.json. This is not an
extreme-controls, trigger-split or full-load stress test.

The initial 24-bit oscillator recurrence showed substantial drift; the current
experiment retains 48-bit oscillator histories. It approximates the upstream
coefficient recurrence and omits the tiny low-history × epsilon product.
It is not IEEE-float emulation. It also quantizes scalar arithmetic to fixed
point. The native/reference waveform residual is **−29.01 dB relative to the
reference energy** on this test: a measured discrepancy, not a source-parity
pass. The earlier coefficient 24 for the slower oscillator produced −10.15 dB;
matching the original float coefficient (epsilon 25) and its initial history
reduces that error. Diagnose remaining numerical/modulation differences and measure decay/spectrum
and listening behavior before claiming fidelity.

Peak: **16,798 executed instructions per core per 16 tank frames**, one
instance on each core. This prototype is substantially too costly for the
design target and includes no sample-rate conversion. Optimization is required.
It is not a measured hardware deadline, a stock-matched benchmark or a proven
supported instance count. Independent rings now use direct cells for six allpasses and packed cells
for two input allpasses and the two long delays. See the matched comparisons below.

## Sound quality and remaining audio integration

A host integer conversion reference and an offline 44.1 kHz signal chain
are tested in SRC.md. Not tested: native DSP conversion or the instrument
audio engine.
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
6. Promote only after qualification, run module:doctor and pr:ready. Keep work
   on the fork branch; any future upstream submission and publication remain
   separate decisions, with first owner review required by that release path.

## Project checks

The complete project check passed with Node 24 and Python 3.14: 323 test files,
2,529 tests passed; SDK checks, lint, type checks, build and catalogue checks
also passed. The sandboxed attempt had local-socket EPERM failures; the same
checks passed with local-socket access. These are project regression results,
not qualification of the draft or its unfinished audio path.

## Modulation regression (2026-10-23)

`verify_modulation.cpp` compares the 48-bit native recurrence model against
the unchanged upstream cosine oscillator for 5,000 updates (five seconds).
Compile as C++17 with `-O2 -DTEST -ffp-contract=off -I<draft>/upstream`,
then run the executable; on macOS use the SDK C++ include path as in the
reference harness. This is a host arithmetic model, not native DSP evidence.

PASS: peak delay-position errors 0.06178 samples (0.5 Hz) and 0.20376 samples
(0.3 Hz), below the diagnostic's quarter-sample bound. The old epsilon 24
failed at 8.26857 samples. This bound covers this five-second diagnostic only,
not long-term oscillator drift or perceptual equivalence. The corrected native
render separately passed both-core identity, exact dry bypass and memory guards.

## Fixed-tap address optimization (0.1.2-experimental)

The global 16,384-cell layout and quantized audio math are unchanged. Twenty
fixed taps cache a physical pair pointer and its 0/1/2 cell position in
X r7+$50..$77. Each advances exactly once per processed sample; a ring wrap
lands on cell 16,383 (position 0 of the final partial pair), not position 2.
Moving taps still calculate their addresses. The full owned scalar span is
now 120 words, with the same 12,972-word Y buffer.

Compared with commit `66129855628c66590bb1a534285f04616224ae4d`, both cores'
wet and dry raw outputs are bit-identical in all three cases below. Each runs
164,096 frames with dirty memory seed 1776, shared/buffer/code guards, a
4,096-frame pre-roll and five seconds of signal/tail. This traverses the full
global ring repeatedly. Program size grows by 600 words; scalar state grows
by 40 words. This is an instruction-count optimization, not a proven chip
cycle or deadline improvement.

| TIME/DAMP/DIFF/SMEAR/GAIN | Split | Before peak | After peak |
| --- | ---: | ---: | ---: |
| 110/64/94/0/83 | 0 | 22,330 | 18,908 |
| 70/100/60/127/100 | 1 | 22,394 | 18,970 |
| 127/0/127/127/127 | 15 | 22,381 | 18,963 |

Counts are executed instructions per core per 16 frames, one instance/core.
MIX 127 and MIX 0 are rendered separately. The before/after measurements use
identical settings and input. Source identities, raw-output hashes and source
residuals are in `evidence/cache-optimization.json`. This does not cover all
knob combinations, moving parameters, asymmetric stereo input, many-instance
stress, or hardware timing. The extreme case is output preservation evidence,
not a sound-quality qualification at extreme settings.

Reproduce using `render_core32.py` with the tool/SDK/stock/output arguments
above, adding `--controls TIME,DAMP,DIFF,SMEAR,GAIN --split N`. To compare,
extract the baseline draft at the named commit into a private directory and
copy the current `render_core32.py` into it (the old renderer lacks these
options). Render that baseline first. Render the current draft with the same
options plus `--compare-output /PRIVATE/baseline-render`. The comparison
refuses different settings or any different input/wet/dry bytes on either core.
Keep extracted firmware and rendered outputs private as before.

## Mixed ring storage (0.1.3-experimental)

The ten independent ring lengths match the host-proven per-line layout. The
eight all-pass rings use one 24-bit Y word per quantized 16-bit cell; the two
long delays still pack three cells into two words. No audio arithmetic or
source delay length changes. Heads occupy X r7+$50..$59; their physical bases
occupy +$60..$69; init clears through +$6f. The diffuser starts at Y+13644.
The bounded clear chunk grows from 128 to 154 words so initialization still
takes 102 calls despite the larger buffer.

Compared with `6c6048571568ebefaf6d3c37a8aa9f9f4d1f152e`, both cores' wet/dry
raw outputs remain bit-identical in the same three 164,096-frame cases:

| TIME/DAMP/DIFF/SMEAR/GAIN | Split | Before peak | After peak |
| --- | ---: | ---: | ---: |
| 110/64/94/0/83 | 0 | 18,908 | 15,084 |
| 70/100/60/127/100 | 1 | 18,970 | 15,145 |
| 127/0/127/127/127 | 15 | 18,963 | 15,140 |

Counts are executed instructions/core/16 frames for one instance/core, not
chip cycles. This is another approximately 20% reduction, or approximately
32% relative to the 22,330-instruction 0.1.1 baseline. Program words fall
1,857 → 1,446, scalar words 120 → 112, while Y words grow 12,972 → 15,692.
Clean buffer/shared/code guards and exact dry bypass pass at dirty seed 1776.
Source identities and identical-output hashes: `evidence/mixed-storage.json`.
The earlier global-ring/cache results above are historical, not the current
memory layout. Full-load and moving-control qualification remain untested.

## Host SRC and offline 44.1 kHz path

See SRC.md for the complete design, commands, acceptance thresholds and
resource gap. `verify_src.py --sanitize` passes the integer host reference
under UndefinedBehaviorSanitizer. The offline 44.1 kHz demonstration maps
227,556 original asymmetric stereo frames to 165,120 tank frames and back
to 227,556 frames, with zero SRC-clipped samples on that signal. The native
core still passes both-core identity, dry bypass and access guards. Its
reference residual is −25.90 dB on this different stereo signal, not parity.

This does not execute a native 44.1 kHz effect. The unchanged input WAV is
only a dry listening reference. Native SRC, complete mixing/smoothing, total
processing budget, placement and firmware/USB integration are still pending.

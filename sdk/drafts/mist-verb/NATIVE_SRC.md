# Native 44.1 kHz experiment

Version 0.1.6-experimental removes the separate SMEAR input diffuser.
The original reverb tank, its internal diffusion and modulation remain.
`core44100.asm` runs stereo 44.1 kHz → 32 kHz conversion, the native reverb
without the separate input diffuser, 32 kHz → 44.1 kHz conversion, and dry/wet mixing. The unchanged
input stays outside conversion for exact MIX 0 bypass. This is a standalone
DSP experiment, not an installed effect or instrument firmware.

## Arithmetic and streaming

`generate_native_src.py` generates the standalone converter (`native_src.asm`),
the joined experiment (`core44100.asm`) and original P-memory tables
(`native_src_tables.json`). Run it after `generate_core.py`; `--check` verifies
all three outputs. The joined tank is generated from `core32.asm`, with unique
labels and its MIX forced fully wet so the outer 44.1 kHz mixer owns dry audio.

The FIR coefficients and rational clock match [the host reference](SRC.md).
A 320-entry down schedule and 441-entry up schedule each store a coefficient
row pointer and Q23 blend weight. This avoids division in the sample loop;
the schedules repeat without clock drift. Each output runs two adjacent stereo FIR
phases and blends their rounded outputs. Each coefficient is reused for both
channels, and parallel Y reads overlap the next sample fetch with the current
multiply-accumulate. Both accumulators retain their extension bits; the right
sum is saved/restored before the common rounding helper uses its accumulator.
The coefficient pointer uses r3; proc saves/restores the caller's r3 and m3.
Rounding is explicitly half away from zero, rather than the DSP's convergent rounding instruction.

Wide rounded FIR endpoints are stored at quarter scale with their low bits,
then reconstructed exactly before subtraction/addition. This avoids clipping
an endpoint before blending. Generation asserts coefficient absolute sums
below 3 and adjacent-row difference sums below 1 (with rounding allowance),
which bound the intermediate storage and signed-24 phase delta for full-scale
input. Only the final output saturates, matching the host reference.

The output queue holds eight stereo frames, starts with two silent frames,
and has measured end-of-call occupancy 2–4. Its peak occupancy before a read
can be five; a four-frame queue was rejected by the first exact-output test.
The two startup frames add 2/44100 seconds to the converter's nominal 1.811 ms
filter delay. This is not a measurement of instrument latency.

The core clears 132 Y words per full clearing call, completing in 102 calls.
During this clearing period the wrapper returns dry audio and advances no
converter state. Trigger splits issue two clearing calls per 16-frame block;
therefore startup duration still depends on call partitioning. This is a known
experimental limitation to resolve before lifecycle qualification. After
clearing, the tank runs one frame per downsampled output. The wrapper saves
and restores the caller's audio pointer and frame count around each tank call.
The four tank controls ramp for 256 tank samples (8 ms). MIX ramps for 256
44.1 kHz samples (5.805 ms). A new target starts from the current fractional
value, so an interrupted ramp remains continuous. Slopes retain 24 fractional
bits and truncate toward zero; the last sample snaps to the exact target.
This keeps the ramps bounded, including tiny changes toward zero. Initial
values start at their targets. Tested static renders match 0.1.5 at SMEAR zero.
Targets are calculated once per external call; only ramp steps run in the
sample loop. Unchanged targets do not restart a ramp.

After settling, MIX 127 returns wet directly and MIX 0 returns dry exactly.
Intermediate knob targets retain the existing value / 128 mapping, with a
wide final multiply-accumulate. Ramp timing and state are measured below;
audible click suppression and instrument control publication are not yet
qualified. All wrapper source splices require exactly one match, so a changed
generator template cannot silently omit a dry-channel store or another step.

## Storage and placement

Two additional input allpasses (241 and 399 cells) now use packed storage,
saving 212 Y words. Their quantization and delay lengths are unchanged.
The standalone tank occupies 13,432 Y words, all for its original delay
rings. Removing the separate diffuser frees 2,048 words. Histories move down
by that amount, retaining their alignment. Packed-ring placement is unchanged;
using the freed space to reduce packed-storage overhead is future work.

| Allocation | Relative Y offsets | Words |
| --- | --- | ---: |
| Tank | 0–13431 | 13432 |
| Down left, 128-aligned | 13440–13535 | 96 |
| Down right, 128-aligned | 13568–13663 | 96 |
| Up left, 64-aligned | 13696–13743 | 48 |
| Up right, 64-aligned | 13760–13807 | 48 |

The owned extent including alignment gaps is 13,808 24-bit words (41,424
bytes), ending 2,062 words before the reserved key window at 15870. Active
storage is 13,720 words plus 88 words of padding. The joined scalar extent
is X r7+00..ef (240 words including gaps/scratch/clearing). Init clears tank
state 00..6f and wrapper state 70..ef. The added targets, slopes, fractional
values and counters are instance-local; no mutable global state is added.

The standalone tank uses 1,109 program words plus 128 gain-table words.
The joined experiment uses 2,135 program words plus 6,274 SRC table/schedule
words and the same 128-word gain table. Test placements are P:15000 for
code, P:18000 for SRC tables and P:14000 for gain; the driver refuses overlap
with the private stock dump. These are standalone experiment placements,
not allocated packages or a proof of coexistence with other effects.

## Reproduction and evidence

Use the same private `--sdk`, `--stock`, `--assembler`, `--host`,
`--disassembler` and `--output` arguments as `render_core32.py`:

```sh
python3 -B sdk/drafts/mist-verb/verify_native_src.py [tool arguments] --full-scale --frames 70560 --split 15
python3 -B sdk/drafts/mist-verb/verify_native_src.py [tool arguments] --reverb --frames 70560
python3 -B sdk/drafts/mist-verb/verify_native_src.py [tool arguments] --reverb --mix 0 --split 15
```

The driver assembles and disassembles each candidate, refuses unexpected
opcodes, renders both cores under dirty-memory seed 1776 with Y/shared/code
guards, compares every output sample, and records source hashes and instruction
counts. `--control-events` verifies every recorded coefficient, fractional
value, remaining sample count and target against `control_reference.py`,
including a reversal before the first ramp finishes. `--signal dc|impulse|silence` covers converter-only fixtures;
`--controls TIME,DAMP,DIFF,GAIN` and `--mix` exercise the joined path.
Private dumps, binaries and raw audio remain outside Git. Stock-free reports
are in `evidence/native-src/`.

For the joined reference, the computer converts the input down, the standalone
32 kHz DSP core processes it, and the computer converts it up. The comparison
aligns documented clearing and the two startup queue frames. Exact agreement
proves equivalence to that fixed-point chain for the tested cases; it does
not erase the tank's measured discrepancy from the original floating-point
Clouds implementation. Both versions still need sound-quality assessment.

## Historical 0.1.5 optimization and control results

Matched static renders preserve both cores' audio bytes exactly against
0.1.4. All use the same input, settings and call splits as their baselines:

| Case | Before peak | 0.1.5 peak |
| --- | ---: | ---: |
| Converter-only full-scale stress, split 15 | 29133 | 17683 |
| Joined wet, nominal controls | 42769 | 31139 |
| Joined mixed, extreme controls, split 1 | 42971 | 31407 |
| Joined exact dry bypass, split 15 | 42741 | 31187 |

Units are executed instructions/core/16 input frames, one instance/core.
This reduces converter work about 39% and the joined static cases about 27%.
The converter grows from 511 to 565 code words; the joined experiment grows
from 2040 to 2547 words to add stereo scheduling, control targets and ramps.
SRC coefficients/schedules and Y history space remain unchanged.

Dynamic tests check 441 active blocks each at splits 0, 1 and 15. All six
coefficient/fraction/counter/target traces match the independent integer
model exactly. Audio bytes agree across the three splits after aligning the
documented startup period. The same control sequence produces exact zero
output from silence. Peak counts are 32188, 32276 and 32276 respectively;
these cases do not cover every possible modulation pattern. Dynamic reports
leave `exactHostParity` null: they verify the control traces and compare audio
across partitions, rather than claiming a host audio oracle for changing
parameters. No listening assessment is claimed.

Reports: `evidence/performance-controls/`. Private renders are separate.

## Historical 0.1.5 matched stock SPRING REV comparison

`benchmark_spring.py` runs 1024 blocks (16384 input frames) for one instance
on each core. Both effects receive the same stereo input, slot placement,
dirty seed 1776 and all trigger splits 0–15. Controls hold minima/maxima,
then move independently each block; each of Spring's three TYPE values is
held in its own sweep so an expensive type is not diluted by type changes.
The report also records means after excluding 256 warmup blocks.

Use the same `--sdk`, `--stock` and `--host`, plus a current successful
`verify_native_src.py --reverb --frames 70560` output as `--native-render`,
and a private `--output` directory. The benchmark refuses stale native
source hashes and keeps all stock routines, descriptors and raw audio private.
Its stock-free report is `evidence/performance-controls/spring-comparison.json`.
This finite standalone emulator workload does not measure chip cycles, an
instrument audio chain, maximum instances or a real-time deadline.

The measured peak is **32327 for Mist Verb versus 5094 for SPRING REV**,
approximately **6.35×** in this workload. This substantial remaining gap
means optimization remains the next priority.
Startup duration independent of call partitioning, installed package placement,
coexistence, instrument controls, firmware/USB lifecycle and hardware
qualification also remain unfinished. No supported instance count or
installable build is claimed.

## Program-memory fit investigation (host proof, no DSP change)

Run `python3 -B verify_src_layout.py --check` from this folder to reproduce
`evidence/src-layout.json`. The current joined program, SRC data and gain
table occupy **8,537 P words**. The package hook guide documents only
**4,304 / 4,432 words** in the empty module arena of its named base build
([arena measurements](../../../docs/OCTATRACK_PACKAGE_DSP_HOOKS.md)). Those
are shared resources, so a standalone high-address emulator placement does
not establish that this engine can be installed or coexist with other FX.

The host proof reconstructs all 66 coefficient rows exactly, then checks
both interpolation endpoints at all 761 rational-clock positions. Phases
1–31 have a zero terminal tap, and phases 17–31 mirror phases 15–1 over
the remaining taps. Keep phase 0 and normalized phase 32 separately.
This permits 2,558 coefficient words plus 66 one-word relative descriptors,
instead of 4,752 coefficient words. Keeping the current schedules saves
**2,128 words**, without changing coefficients, cutoff or phase weights.

This is a checked layout proposal, not an implemented native optimization.
It would still need **6,409 words before changes to the decoder**, exceeding
the documented empty arenas by 2,105 / 1,977 words. The DSP reader would
need signed coefficient strides, variable tap counts and a fresh history
pointer for each phase; omitting a zero tap otherwise breaks the existing
full-ring wrap assumption. Preserve any newly used address registers and
measure both code size and execution cost after implementing it. Exact row
reconstruction does not prove DSP audio parity or a processing improvement.
No extra X-memory table allocation or larger P arena has been established.


## 0.1.6 removal of the separate input diffuser

`evidence/no-smear/` records the current build. Removing all eight separate
input-diffuser stages also removes their coefficient mapping and control
ramp. The tank's own eight allpasses, two long delays, damping, modulation,
gain and mixer are unchanged. D is inactive; E GAIN and F MIX retain their
positions. `--controls` now takes four values: TIME,DAMP,DIFF,GAIN.
The unchanged licensed upstream diffuser stays in the source reference.

Three matched static cases retain identical bytes on both cores against
0.1.5 with SMEAR zero: nominal wet (72,192 frames), high feedback/gain with
MIX 40 and split 1 (14,928), and exact dry with split 15 (14,928). Peaks drop
31,139 → 28,046, 31,402 → 28,300 and 31,187 → 28,085 instructions/core/16
input frames, about 10%. The nominal standalone tank is 12,737 instructions
per 16 tank frames on this converted stereo fixture, versus 16,798 before.
Code falls 1,452 → 1,109 words for the tank, 2,547 → 2,135 joined. Y extent
falls 15,856 → 13,808. Tables are unchanged. Clearing uses 132 words/call to
keep the same 102-call startup; its call-partition limitation is unchanged.

Five-control traces match the integer model at splits 0, 1 and 15, with
identical audio after startup alignment. The moving controls preserve exact
silence. Converter full-scale stress remains host-exact after relocation.
All renders use dirty seed 1776, both cores and buffer/shared/code guards.
The 64-case stock benchmark (three Spring types and all sixteen splits)
now peaks at 29,067 for Mist versus 5,094 for Spring, approximately 5.71×.
This remains a substantial performance gap, not a hardware timing result.
The 8,537 P-word total still exceeds the documented empty package arena;
no installation or sound-quality qualification is claimed.

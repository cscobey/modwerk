# Native 44.1 kHz experiment

Version 0.1.5-experimental optimizes the native converters and adds sample-timed control ramps.
`core44100.asm` runs stereo 44.1 kHz → 32 kHz conversion, the native reverb
and diffuser, 32 kHz → 44.1 kHz conversion, and dry/wet mixing. The unchanged
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

The core clears 152 Y words per full clearing call, completing in 102 calls.
During this clearing period the wrapper returns dry audio and advances no
converter state. Trigger splits issue two clearing calls per 16-frame block;
therefore startup duration still depends on call partitioning. This is a known
experimental limitation to resolve before lifecycle qualification. After
clearing, the tank runs one frame per downsampled output. The wrapper saves
and restores the caller's audio pointer and frame count around each tank call.
The five tank controls ramp for 256 tank samples (8 ms). MIX ramps for 256
44.1 kHz samples (5.805 ms). A new target starts from the current fractional
value, so an interrupted ramp remains continuous. Slopes retain 24 fractional
bits and truncate toward zero; the last sample snaps to the exact target.
This keeps the ramps bounded, including tiny changes toward zero. Initial
values start at their targets so a static render stays identical to 0.1.4.
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
The standalone tank occupies 15,480 Y words: rings 0–13431 and diffuser
13432–15479. Three matched comparisons against 0.1.3 test preservation of
wet/dry bytes. Nominal tank cost rises from 15,084 to 16,798 instructions per
16 tank frames as the tradeoff for making room.

| Allocation | Relative Y offsets | Words |
| --- | --- | ---: |
| Tank and diffuser | 0–15479 | 15480 |
| Down left, 128-aligned | 15488–15583 | 96 |
| Down right, 128-aligned | 15616–15711 | 96 |
| Up left, 64-aligned | 15744–15791 | 48 |
| Up right, 64-aligned | 15808–15855 | 48 |

The owned extent including alignment gaps is 15,856 24-bit words (47,568
bytes), ending 14 words before the reserved key window at 15870. Active
storage is 15,768 words plus 88 words of padding. The joined scalar extent
is X r7+00..ef (240 words including gaps/scratch/clearing). Init clears tank
state 00..6f and wrapper state 70..ef. The added targets, slopes, fractional
values and counters are instance-local; no mutable global state is added.

The standalone tank uses 1,452 program words plus 128 gain-table words.
The joined experiment uses 2,547 program words plus 6,274 SRC table/schedule
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
`--controls TIME,DAMP,DIFF,SMEAR,GAIN` and `--mix` exercise the joined path.
Private dumps, binaries and raw audio remain outside Git. Stock-free reports
are in `evidence/native-src/`.

For the joined reference, the computer converts the input down, the standalone
32 kHz DSP core processes it, and the computer converts it up. The comparison
aligns documented clearing and the two startup queue frames. Exact agreement
proves equivalence to that fixed-point chain for the tested cases; it does
not erase the tank's measured discrepancy from the original floating-point
Clouds implementation. Both versions still need sound-quality assessment.

## Optimization and control results

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

## Matched stock SPRING REV comparison

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

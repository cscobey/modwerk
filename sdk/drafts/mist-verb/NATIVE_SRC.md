# Native 44.1 kHz experiment

Version 0.1.4-experimental moves both rate converters onto the emulated DSP.
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
the schedules repeat without clock drift. Each output runs two adjacent FIR
phases per channel and blends their rounded outputs. Rounding is explicitly
half away from zero, rather than the DSP's convergent rounding instruction.

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
Controls are unsmoothed. MIX 127 returns wet directly; MIX 0 returns dry
exactly; intermediate MIX values use the existing 0–126 / 128 mapping with a
wide final multiply-accumulate. No claim of click-free control changes is made.

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
is X r7+00..b5 (182 words including gaps/scratch). Init clears tank state
00..6f and wrapper state 70..af; scratch b0..b5 is written before use.

The standalone tank uses 1,452 program words plus 128 gain-table words.
The joined experiment uses 2,040 program words plus 6,274 SRC table/schedule
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
counts. `--signal dc|impulse|silence` covers converter-only fixtures;
`--controls TIME,DAMP,DIFF,SMEAR,GAIN` and `--mix` exercise the joined path.
Private dumps, binaries and raw audio remain outside Git. Stock-free reports
are in `evidence/native-src/`.

For the joined reference, the computer converts the input down, the standalone
32 kHz DSP core processes it, and the computer converts it up. The comparison
aligns documented clearing and the two startup queue frames. Exact agreement
proves equivalence to that fixed-point chain for the tested cases; it does
not erase the tank's measured discrepancy from the original floating-point
Clouds implementation. Both versions still need sound-quality assessment.

Measured joined peaks are about 42,800–43,000 executed instructions per core
per 16 input frames in these cases, for one instance/core. Counts are not DSP
cycles or a real-time deadline measurement. This remains a costly prototype.
Next work is performance optimization and a matched stock SPRING REV benchmark,
control smoothing, startup/lifecycle behavior, actual package placement and
coexistence, followed by firmware/USB and hardware qualification. No supported
instance count or installable build is claimed.

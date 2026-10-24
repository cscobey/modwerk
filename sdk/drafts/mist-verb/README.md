# Mist Verb

Unpublished port preparation, version **0.1.7-experimental**, author **cscobey**.
Target: Mutable Instruments Clouds reverb tank as
an independent Octatrack MKII FX2 insert on OS 1.40C. MKI is not tested.

**A native 44.1 kHz experiment now runs conversion, reverb and dry/wet mixing
on both emulated DSP cores. There is no installable firmware effect yet.**
`core44100.asm` is the joined experiment; `core32.asm` remains the tank test.
`engine.asm` remains the integration scaffold.
`verify.py` deliberately refuses qualification.
This draft is absent from the live catalogue and all release/USB packages.

## Overview

The original MIT-licensed Clouds source by Émilie Gillet is pinned in
[sources.json](sources.json), with unchanged files under `upstream/`. The
original C++ is the sound oracle. The port targets the original 32 kHz tank,
its ten delay lengths, its quantized 16-bit storage with twelve fractional
bits, both slow modulation oscillators. The separate stereo input diffuser and
SMEAR control were removed in 0.1.6 to save memory and processing.
No disting NT firmware or Elektron code is copied.

Two host storage models now match that original reverb exactly across 63
parameter cases each: a global packed ring and independent per-delay rings.
The native core now uses independent per-delay rings: all eight allpasses
and the 4,782-cell delay retain 16-bit quantization in direct 24-bit words;
only the 3,411-cell delay uses packed storage. This spends some of the audio
memory freed by SMEAR removal to reduce per-sample work. The host oracle
still uses upstream floating-point arithmetic and its original oscillators.

`packed_probe.asm` separately proves the basic packed-cell access on the
emulated DSP56300, with eight distinct instances on both cores. It processes
test integers, not audio. Its performance is not the cost of a reverb.

`generate_core.py` translates the pinned topology into the initial native
`core32.asm`: eight reverb allpasses, two damping poles,
modulated reads, packed delay memory and a widened final mixer.
`render_core32.py` executes it on both emulated cores at a **test rate of
32 kHz**. The new [native 44.1 kHz experiment](NATIVE_SRC.md) wraps this tank
with both converters and the final mixer, all running on the emulated DSP.
Its tested output matches the earlier host-conversion/native-tank chain
exactly, including full-scale converter saturation and exact dry bypass.
Stereo FIR scheduling and removal of the separate input diffuser reduce
processing work; short sample-timed ramps smooth the five control targets. The tank still has measured
differences from the original floating-point source. The complete path remains expensive and unqualified for installation.

[SRC.md](SRC.md) describes the computer reference and filter design.
[NATIVE_SRC.md](NATIVE_SRC.md) records the DSP arithmetic, streaming behavior,
aligned storage, placement, costs, test commands and remaining work.

## Controls

These are the target instrument controls. The joined experiment has 8 ms
tank-control ramps and 5.8 ms MIX ramps; no firmware parameter page is implemented. All are
continuous 0–127 main-page controls. The six SETUP parameter slots are unused.

| Encoder | Name | Proposed default | Purpose |
|---|---|---:|---|
| A | TIME | 96 | Reverb feedback/decay, bounded below unity |
| B | DAMP | 64 | Darkens the recirculating tail |
| C | DIFF | 94 | Tank diffusion; nominal 70% starting point |
| D | — | — | Unused; separate input diffuser removed |
| E | GAIN | 83 | Tank input gain; planned −40 to 0 dB range, about −14 dB default |
| F | MIX | 40 | Dry/wet; 0 exact dry after the ramp, 127 fully wet |

The final coefficient curves must be documented and tested before promotion.
The tank LFOs run freely in seconds, as on Clouds; they are not pattern
sequencers and do not generate an independent musical clock.

## Usage

For now use the reference and storage tests in [TESTING.md](TESTING.md).
The WAVs from verify_reference.py demonstrate the original C++ reference.
The WAVs from render_core32.py demonstrate the native 32 kHz experiment. They use an original synthesized noise/tone excitation and no samples
from another product.

### Target tutorial (not verified on firmware)

1. Select an audio track. Hold FUNC and press FX2; select Mist Verb with LEVEL
   and press YES. This chooser entry does not exist in a built image yet.
2. Press FX2; adjust A TIME and B DAMP, then raise F MIX while playing a sample.
3. Return MIX to 0 for dry audio, or choose NONE in FX2 SETUP to remove it.

## Compatibility and limitations

- FX2 only initially. Its 16,384-word allocation can hold the proposed packed
  tank and conversion histories. FX1 has 3,072 words and cannot hold this layout. No shared
  bus, other module dependency or stock behavior hook is planned.
- Proposed non-stock effect ID: `0x07`, unused among the fork's declarations
  at base `bedbb362`. USB IDs are assigned through the base's module lifecycle.
- The tank occupies Y offsets 0–15237. Aligned stereo conversion histories
  extend ownership through 15727, leaving 142 words before the reserved key
  window at 15870. See NATIVE_SRC.md for active storage and padding.
- The host class uses 32-bit containers for each modeled 24-bit word. Its C++
  object size is not the DSP allocation. The fixed-point tank still differs
  from its floating-point source.
- Independent per-delay rings matched the original across the recorded test
  cases; that is not a proof of every possible input or future implementation.
- Native conversion and mixing pass the recorded exact-chain comparisons.
  Control-ramp timing, retargeting and partition consistency are tested.
  Three static both-core comparisons match 0.1.5 with SMEAR zero exactly.
  Further storage and table optimizations preserve eight recorded fixtures
  and all sixteen moving-control benchmark splits byte-for-byte versus 0.1.6.
  Program/table memory falls 8,537 → 6,526 words; nominal processing about 8%.
  The joined Y extent rises to 15,728 words to make delay access faster.
  The matched benchmark still measures 5.28× Spring’s instructions.
  See `evidence/optimization/`; installed fit remains unproven.
  Startup behavior, audible results and installed controls still need qualification.
- Worst-case stock SPRING REV remains the performance design target. The
  joined path measures roughly 31,100–32,300 executed instructions per core
  per 16 input frames, one instance/core. These are not chip cycles or a
  hardware benchmark. The finite matched SPRING REV comparison in NATIVE_SRC.md
  measures a peak about 6.35× stock in that workload. Further optimization is
  required; no supported full-effect instance count exists yet.
- Card/browser composition with stock effects, Analog BD and common custom
  companions is not tested. No new conflict flags or companion approvals have
  been added. Contiguous program/table placement remains to be measured.
- USB package ownership, installation, self-test, Keep/Undo, removal and
  missing-module behavior are all pending. A module update must not require
  rebuilding the base. There is no card-only release fallback.
- Parameter locks, LFOs, scenes, crossfader, Parts, projects and persistence are
  not tested. No physical unit has run this source.

## Tests and measurements

See [TESTING.md](TESTING.md), [reference evidence](evidence/reference.json) and
[native packing evidence](evidence/packing-dsp.json). Both test paths passed;
neither qualifies the audio engine. All firmware, memory dumps, binaries,
renders and emulator cards remain outside Git.

## Authorship and licences

Original Clouds reverb/diffuser: Copyright 2014 Émilie Gillet, MIT.
The imported stmlib headers retain their 2012 and 2014 notices, also MIT.
Port preparation, reference harness and storage proofs: Copyright 2026 cscobey,
MIT. See [LICENSE](LICENSE) and the complete notices in every original header.
The Modwerk/Octabam SDK retains its existing attribution and licences.

This independent port is not affiliated with or endorsed by Mutable
Instruments, Expert Sleepers or Elektron. Its name is Mist Verb; Clouds is
identified only as the source algorithm.

## Screens and audio

No firmware UI capture exists. The private `core32/wet.wav` is a DSP-emulator
experiment at 32 kHz, not audio from an Octatrack. Its input is original
synthesized noise. No listening assessment or sound-equivalence pass is claimed.

No illustration is represented as an instrument screen. Optional reference WAVs are generated privately by `verify_reference.py`.
An actual native audio preview and black-and-white firmware screenshots are
required before publication.

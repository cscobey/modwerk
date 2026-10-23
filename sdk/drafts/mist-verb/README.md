# Mist Verb

Unpublished port preparation, version **0.1.2-experimental**, author **cscobey**.
Target: Mutable Instruments Clouds reverb and the separate stereo diffuser as
an independent Octatrack MKII FX2 insert on OS 1.40C. MKI is not tested.

**A standalone 32 kHz reverb core now renders on both emulated DSP cores,
but there is no installable 44.1 kHz firmware effect yet.**
`core32.asm` is the experiment; `engine.asm` remains the integration scaffold.
`verify.py` deliberately refuses qualification.
This draft is absent from the live catalogue and all release/USB packages.

## Overview

The original MIT-licensed Clouds source by Émilie Gillet is pinned in
[sources.json](sources.json), with unchanged files under `upstream/`. The
original C++ is the sound oracle. The port targets the original 32 kHz tank,
its ten delay lengths, its quantized 16-bit storage with twelve fractional
bits, both slow modulation oscillators, and the separate stereo diffuser.
No disting NT firmware or Elektron code is copied.

Two host storage models now match that original reverb exactly across 63
parameter cases each: a global packed ring and independent per-delay rings.
The second design is a candidate for a later memory-layout optimization.
The current native core keeps the global ring and caches its fixed tap addresses. This is a storage proof; the reference still uses upstream
floating-point arithmetic and its original oscillators.

`packed_probe.asm` separately proves the basic packed-cell access on the
emulated DSP56300, with eight distinct instances on both cores. It processes
test integers, not audio. Its performance is not the cost of a reverb.

`generate_core.py` translates the pinned topology into the initial native
`core32.asm`: the diffuser, eight reverb allpasses, two damping poles,
modulated reads, packed delay memory and a widened final mixer.
`render_core32.py` executes it on both emulated cores at a **test rate of
32 kHz**. It does not run at the Octatrack's 44.1 kHz audio rate yet.
The native experiment has measured numerical differences and excessive cost;
its render is not an exact reproduction or a qualified effect.
Fixed taps now cache their packed addresses: three before/after renders are
bit-identical while executed instruction counts fall about 15 percent. This
uses 1,857 program words (previously 1,257), plus the same 128-word gain table,
and 120 scalar X words (previously 80). Full placement remains unverified.

## Controls

These are the target instrument controls. The standalone core has initial
unsmoothed mappings; no firmware parameter page is implemented. All are
continuous 0–127 main-page controls. The six SETUP parameter slots are unused.

| Encoder | Name | Proposed default | Purpose |
|---|---|---:|---|
| A | TIME | 96 | Reverb feedback/decay, bounded below unity |
| B | DAMP | 64 | Darkens the recirculating tail |
| C | DIFF | 94 | Tank diffusion; nominal 70% starting point |
| D | SMEAR | 0 | Separate stereo input diffuser amount |
| E | GAIN | 83 | Tank input gain; planned −40 to 0 dB range, about −14 dB default |
| F | MIX | 40 | Dry/wet; 0 exact dry, 127 fully wet |

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
  tank and diffuser. FX1 has 3,072 words and cannot hold this layout. No shared
  bus, other module dependency or stock behavior hook is planned.
- Proposed non-stock effect ID: `0x07`, unused among the fork's declarations
  at base `bedbb362`. USB IDs are assigned through the base's module lifecycle.
- Planned ownership per FX2 instance: Y offsets 0–10923 for 16,384 packed
  16-bit cells; 10924–12971 for 2,048 24-bit diffuser cells. Total 12,972
  physical 24-bit words, equivalent to 38,916 bytes on the DSP. This leaves
  2,898 words before the reserved key window, and never needs offsets
  15870–16383. The core render has clean access guards; integrated 44.1 kHz engine bounds
  remain unverified.
- The host class uses 32-bit containers for each modeled 24-bit word. Its C++
  object size is not the DSP allocation. Diffuser fixed-point precision is
  not yet proven against its floating-point source.
- Independent per-delay rings matched the original across the recorded test
  cases; that is not a proof of every possible input or future implementation.
- 44.1↔32 kHz sample-rate conversion is still required. A timing-accurate tank
  alone does not establish bandwidth, alias rejection or total processing cost.
- Worst-case stock SPRING REV is the performance design target. Benchmark
  expensive settings, moving controls and trigger splits on both cores. The optimized 32 kHz core peaks at 18,908 executed
  instructions per 16 tank frames, for one instance on each core. That is
  neither hardware timing nor a full 44.1 kHz effect budget. It requires
  substantial optimization; no supported full-effect instance count exists yet.
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

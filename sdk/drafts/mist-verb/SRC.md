# Sample-rate-conversion reference

This is an original, MIT-licensed host reference for the eventual 44.1↔32 kHz
DSP path. This file describes the host reference; the tested DSP translation
and remaining qualification limits are in [NATIVE_SRC.md](NATIVE_SRC.md).
`render_44100.py` can process an original stereo demonstration through host
conversion, the actual emulated 32 kHz core, then host conversion back to 44.1 kHz.

## Design

The general method is finite, windowed-sinc interpolation with a low-pass
filter before downsampling, as described in [Windowed Sinc Interpolation,
Physical Audio Signal Processing](https://dsprelated.com/freebooks/pasp/Windowed_Sinc_Interpolation.html).
The implementation and coefficients here are newly written; no code or table
is copied from that reference.

- Down: 44,100 → 32,000 Hz, 96 taps. Up: 32,000 → 44,100 Hz, 48 taps.
- Both banks use a 14,500 Hz cutoff and Kaiser beta 8.6. The intended flat
  passband is through 13 kHz; attenuation above it is an intentional bandwidth
  tradeoff for the 32 kHz reverb path, not a claim of flat response to 16 kHz.
- 32 fractional phase intervals, with 33 coefficient rows per bank and linear
  interpolation of two FIR outputs. Each stored row sums to exactly 1 in Q23.
- All streaming sample, coefficient, clock and accumulation arithmetic is
  integer. A bounded rational clock preserves the 320:441 ratio across chunks.
- FIR MACs use wide accumulators; outputs round to Q23 before the phase blend.
  Final outputs saturate to signed 24-bit range and count clipped samples.
- Nominal combined filter group delay is 47.5/44100 + 23.5/32000 seconds,
  approximately 1.811 ms. This is not total instrument latency or reverb delay.
- The converter is causal and starts with zero history. It does not implicitly
  flush at EOF: supply zero input to render its trailing response. Dry audio
  should remain outside this conversion path when the final mixer is built.

`generate_src.py` creates `src_coefficients.h`; `--check` refuses stale output.
`rational_src.h` is the streaming host implementation. `src_convert.cpp` is a
private raw-audio driver (interleaved stereo, signed 24-bit values in little-endian
32-bit containers). It accepts `down|up input.raw output.raw`.

## Verification

```sh
python3 -B sdk/drafts/mist-verb/verify_src.py --output /PRIVATE/mist-src --sanitize
```

This compiles the tests and converter using C++17 and runs UndefinedBehaviorSanitizer.
No firmware is needed. Results and source hashes are in `evidence/src.json`.
The tests compare regular and irregular chunks, reset/silence, exact steady DC,
20 seconds of sample counts, separate and swapped stereo channels, analytic
passband tones, downsampling aliases and upsampling images. Passband residuals
measure energy left after fitting the intended sine/cosine, so small unwanted
sidebands are not hidden inside a fundamental-amplitude measurement.

Acceptance for this reference: passband gain within 0.1 dB at the tested
100/1000/10000/13000 Hz tones; spurious energy below −65 dB relative to input;
downsampling aliases and interpolation images below −70 dB at the tested
frequencies. This finite set is not a complete spectral sweep or a hardware
sound-quality qualification. Full-scale transient headroom and listening
assessment remain separate work.

## Offline 44.1 kHz demonstration

Run `render_44100.py` with the same `--sdk`, `--stock`, `--assembler`, `--host`,
`--disassembler` and private `--output` arguments as `render_core32.py`.
It creates different original signals for left and right, converts them to
32 kHz, renders both emulated cores, and returns the wet result at 44.1 kHz.
The native core's dry bypass and memory guards still run. `dry-44100.wav` is
an unchanged input listening reference, not a test of a native 44.1 kHz mixer.
Private WAVs, firmware-derived memory files and binaries must not be committed.
The stock-free report is in `evidence/pipeline-44100.json`.

## Native implementation

The native converter and joined 44.1 kHz reverb experiment are now tested.
See [NATIVE_SRC.md](NATIVE_SRC.md) for exact output comparisons, aligned
histories, coefficient/schedule placement and instruction counts. Installation,
control smoothing, full-load timing and hardware qualification remain pending.

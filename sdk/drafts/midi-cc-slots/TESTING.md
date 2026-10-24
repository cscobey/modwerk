# MIDI CC Slots investigation

Status: incomplete, unqualified emulator research. No physical hardware used.

## Observed stock behavior

- Original local MAIN SHA-256:
  `164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e`.
- MAIN load base is `0x40000400`, not `0x40000000`.
- MKII boot and actual panel keys reach MIDI CONTROL 1 and its SETUP.
  SETUP A/B are blank; C–F show the four stock CC assignments.
- CONTROL 1 SETUP writers at `0x4003fc44`, `0x4003fd34` and `0x4003fe14`
  address six bytes per MIDI track with a 36-byte track stride and 6322-byte
  Part stride. The direct assignment writer only accepts four CC positions.
- The shared value transmitter starts at `0x4009eec8`. Parameter IDs 18/19
  dispatch PB/AT; 20–29 dispatch the ten assigned CCs. Its active value and
  assignment records use a 68-byte live track stride.
- SETUP visibility uses a 64-bit descriptor mask, shifted by four bits per
  position. Its first SETUP positions start at bits 24/28 of the low word;
  editing only the high word does not expose them.

These are local source/control-flow observations, not proof of full saved
project semantics or of the candidate feature.

## Current candidate: 0.0.2-experimental

MAIN SHA-256 `984120afb2d5255a9d708caa83647cd900f0e0fe544a19394bfc5e9fa875fe85`.
The private unit is 420 bytes including local replay spans, at the same
guarded solo-image zero run. It remains outside the composer/base allocation.

Double-tapping stock FX1 already opens MIDI CTRL 1 SETUP. Its encoder handler
receives down and up events; only a clean A/B release switches mode. Stock's
turn-while-held guard suppresses the click after accelerated editing. The
new clamp preserves STK while turning and keeps CC0 as the mapped lower bound.
The other encoder handlers and normal main-page presses retain stock behavior.

The updated gate passed 382 checks and a second build reproduced the private
candidate byte-for-byte. It adds 16 menu checks to the previous 366 output checks:
double-tap entry, independent A/B click toggles, rotation staying in its mode,
CC0/127 boundaries, stock CC1 click confirmation, held-encoder acceleration,
main-page isolation, and immediate live/in-memory Part updates on mode clicks.
Those in-memory Part observations are not saved-project persistence results.
The gate also requires the actual SETUP popup to be open before editing it;
stale staged values alone cannot establish that a double-tap opened the menu.

## Previous candidate: v4 / 0.0.1-experimental

MAIN SHA-256 `49ce9b6cd40f5d9195472e7a60792784a50060700d32e5110df996713d133c53`.
Built with `build_probe.py`; original adapters occupy a guarded stock zero
run at `0x400d6b20`. This is a solo emulator experiment, not an allocation
claim in the card composer or base. Original replay spans stay in the private
build folder and are not source assets.

The MKII panel/UART gate passed 366 assertions:

- Eight tracks on eight distinct output channels, both slots assigned to
  CC0/127, with values 1/63/64/126/127/0: 96 assertions.
- Both slots traversed every other CC assignment on track 1: 254 assertions.
- Remaining CONTROL 1 and CONTROL 2 CC positions transmitted their stock
  controllers and value 37: 10 assertions.
- STK restored native pitch bend and channel aftertouch: two assertions.
- Changing track 1 back to STK left track 2's two mappings intact: two assertions.
- Actual grid recording and playback emitted track 2's CC0/127 locks at
  42/43 while the live base remained 5/5: two assertions.

The gate reads actual UART0 transmission from the private native monitor.
It rejects emulator faults and decodes running status. The lock fixture uses
the stock sequencer, internal clock, actual grid-record and transport keys,
and a 1.2-second playback. It does not test card writes or a receiver's response.
Run the command in README.md with `--sequencer` to include that fixture.

The manual transmitter is not the playback transmitter. Candidate v3 passed
the 364 panel checks but failed the lock fixture: UART0 carried native PB/AT
at the locked values. PC watches identified separate sequencer paths at
`0x4009fd84` and `0x4009fdf8`. Candidate v4 routes mapped lanes from those
paths into the same stock CC sender after stock enable/channel eligibility
checks. Unmapped lanes replay the original guarded span. The passing lock
fixture is a regression against that observed failure, not evidence of full
sequencer/LFO/mute/shared-channel coverage.

The first append-after-image placement was rejected after SETUP stopped with
an illegal instruction; a peek read all-ones at that proposed address. It was
replaced with the SDK's guarded zero-run location before any passing result.
An early byte-string MIDI assertion also failed on valid running status;
the gate now decodes complete channel messages before comparing them.

`module:doctor -- midi-cc-slots` reports no catalogue module. This research
folder deliberately has no release manifest and is not publication-ready.

## Required acceptance matrix — outstanding

Enable/disable behavior beyond initial enabling; wider sequencer locks and LFOs;
shared channels; Part save/reload; project
save/load and fresh volatile state; missing-module fallback; MIDI Scenes and
base coexistence; bounded wire-rate flood; runtime install/removal; hardware.

Never describe an injected-memory or borrowed-call probe as a front-panel,
sequencer, persistence or physical reboot test.

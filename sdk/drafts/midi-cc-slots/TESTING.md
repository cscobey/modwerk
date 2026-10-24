# MIDI CC Slots investigation

Status: unqualified development draft. Software evidence below is locally
observed; hardware reports are identified separately. No physical unit was
driven by the verification scripts.

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

## Earlier candidate: 0.0.2-experimental

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

## Local USB draft 0.0.3 — 24 October 2026

- `build_runtime.py`: deterministic ABI 7, 1,470 bytes, 14 guarded sites,
  seven hash-backed copies, 420-byte image; no ColdFire self-reference words.
- `verify_runtime.py`: every site and copy guard passed against stock MAIN and
  a user-supplied Modwerk ELEKLOADER card image (SHA-256 in evidence/runtime.json).
  No direct current-base patch overlap. Literal stock-overlap scan passed at
  the existing 16-byte floor, without exemptions.
- Package reconstruction at 0x400d6b20 reproduces the 382-check candidate
  byte for byte. Reconstruction at 0x400d7000 passed all 382 panel/sequencer
  checks again. This proves the adapter can move; it does not test USB loading.
- `verify_loader.py`: exact package prepare, publish, Undo, repeated install,
  removal and full memory reclamation passed against the user's MAIN using
  the real C loader with host glue. ColdFire code is not executed by this test.
- Local HTTP endpoint returned the same package digest as the direct build.
  Capability/stale-inventory/package-identity and DOM trial tests cover that
  preparation sends nothing, an explicit trial adds only the draft, and the
  real link's self-test callback is supplied. At that revision no Keep action existed.
- Hardware USB, actual loader coexistence, saved Part/project persistence,
  LFO/shared-channel behavior, Keep/restart and physical reboot: **not tested**.
  The 14 unchanged sites in a supplied file do not prove the connected unit's
  identity or its currently installed runtime set; the page reviews both.

## Assignment headers and SETUP captions 0.0.4 — 24 October 2026

- 398 emulator checks passed: all 382 previous checks plus four mode-caption
  checks, native PB/AT header restoration, numeric headers on eight tracks,
  the CC5–CC10 headers on CONTROL 2, and two other-page isolation checks.
  Label values are traced at the
  authored renderer, using real panel edits and read-only PC watches.
- Private LCD captures visually inspected: CONTROL 1 headers 0, 127, 7, 1,
  2, 10; CONTROL 2 headers 71–76; SETUP CC127/CC0 and the complete highlighted
  CC caption. Captures stay outside Git.
- The display adapter takes only the label argument path on the two MIDI
  CONTROL descriptors. Other page descriptors pass through stock. Native
  PB/AT headers retain their stock text. SETUP's short PB/AT/CC captions fit
  the existing highlight rather than changing shared text rendering.
  Private stock disassembly contains no incoming branch into either displaced
  label span. The guarded replacements reproduce the displaced argument pushes.
- The 1,914-byte package has 16 guarded sites, eight copies and an unchanged
  sender/click implementation. Guard and literal scans passed; exact C-loader
  install, Undo, repeat install, removal and reclamation passed with host glue
  against the supplied firmware MAIN. Its reconstructed image is byte-identical
  to the panel-tested private candidate.
- The local compiler now refuses a generated package whose digest differs
  from local-build.json, so editing native source cannot silently offer an
  unverified package through the running development server.
- User reported “the control works” on the unit before this display update.
  No build identity was independently read; this is a reported control
  result, not qualification of persistence, coexistence or this version.
- User subsequently reported the display update working. The connected build
  identity was not independently read; this remains a reported result.
- Exact-build USB lifecycle and physical restart persistence: **not tested**.


## Local persistence workflow — 24 October 2026

The native package remains 0.0.4-experimental, 1,914 bytes, SHA-256
`1f435661235af72d7cd5847e380a14c6cfe29c1189c33471e62ea072e8016c64`.
Only the local app workflow and software verification changed.

- Explicit Keep follows this page's own tested one-module trial; Undo remains.
  Removal stages only the empty same-ID package, then requires explicit Keep.
- DOM checks cover review sending nothing, explicit Keep, save-failure and
  missing-diagnostics rejection/recovery, companion preservation, removal and
  Undo, plus refusal of an unreported legacy self-test. Restart verification rejects the immediate saved result and requires
  the distinct startup-restored result with matching base and IDs/layouts.
- `verify_persistence.py` compiles the actual C runtime loader and modset.c
  against the supplied private MAIN. The exact package is kept, restored in a
  fresh process, removed, then absent in another fresh process. A synthetic
  companion survives throughout. Failed writes leave the prior saved set
  restorable in a fresh process. Files are simulated in a temporary directory;
  no physical card I/O, ColdFire execution, task scheduling or USB is exercised.
- The running local compiler endpoint returned the same pinned package digest.
- The user subsequently pasted “Startup restoration confirmed by the base”
  from the local page and reported the controls working after restart. This
  is a reported Keep/restart result, not an independently read exact-build
  hardware qualification. Persistent removal on the unit remains untested.
- Module persistence does not establish assignment persistence in saved Parts
  or projects. Inventory/diagnostic checks do not read back package bytes.


## Midi Mode 2 presentation — 24 October 2026

The presentation name is now Midi Mode 2. Proposed listing copy, control
instructions, five screenshot captions and an original vector thumbnail are
in `presentation/`. The thumbnail follows CC Map’s dark grid and lilac routing
style and was rendered locally and visually inspected. It is a conceptual
illustration, not device UI evidence. No native source, installed module ID,
package bytes, catalogue entry or generated publication metadata changed.
The initial capture plan distinguished physical LCD photographs, supported
development-base exports and emulator captures; the user then chose emulator images.


## Midi Mode 2 emulator screenshot walkthrough — 24 October 2026

- Five actual LCD images captured with the shared capture script and the
  existing reviewed ot_emu, MKII panel, stopped transport, disposable empty
  card and real key/encoder input. No memory injection or reconstructed labels.
- Source slots.s SHA-256 matches the candidate build receipt. The captured
  image SHA-256 matches the previously verified runtime reconstruction of the
  unchanged pinned 0.0.4 package. Full bindings and capture plan are in
  media/capture.json; firmware and raw planes remain private.
- All five 768×384 PNGs visually reviewed. SETUP starts at native PB/AT/STK;
  CC assignment capture shows A=0/B=127; CONTROL 1 shows enabled values 64/32
  on channel 01; CONTROL 2 shows headers 71–76, all values OFF; restoration
  shows native PB with B still assigned CC127. Captions match visible states.
- Palette uses only grayscale 24/240 at integer scale 6, preserving every
  rendered LCD/popup pixel. No error popups or private project names appear.
- This is UI illustration evidence from an emulator. It does not add physical
  USB, receiver MIDI, project-persistence or release-qualification evidence.
  Catalogue registration remains outstanding.

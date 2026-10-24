# Midi Mode 2

**Card label:** Two more MIDI CC controls

**Family:** MIDI track control

**Short description**

Turn MIDI CONTROL 1’s pitch bend and aftertouch positions into two extra CC controls. See the assigned CC number above every CC knob on both MIDI CONTROL pages.

**Overview**

Give each MIDI track two more CC controls without leaving the Octatrack’s familiar MIDI pages. Midi Mode 2 lets you switch the pitch bend and aftertouch positions independently between their native functions and any CC from 0 to 127.

Double-tap FX1 to open CONTROL 1 SETUP, then click encoder A or B to change its mode. Choose a CC number, confirm with YES and return to CONTROL 1 to send values. Click the encoder again in SETUP whenever you want native pitch bend or aftertouch back.

Both MIDI CONTROL pages show the assigned controller numbers above their CC knobs, so you can see which controller you’re adjusting. Native positions keep their PB and AT labels.

**Highlights**

- Two additional CC controls per MIDI track when both positions are switched to CC.
- Choose any CC from 0 to 127 independently for each position.
- See assigned CC numbers across both MIDI CONTROL pages.
- Restore native pitch bend or aftertouch with an encoder click in SETUP.

**Controls**

| Where | Action | Result |
| --- | --- | --- |
| MIDI track | Double-tap FX1 | Open MIDI CONTROL 1 SETUP. |
| CONTROL 1 SETUP | Click A | Switch the pitch bend position between PB and CC. |
| CONTROL 1 SETUP | Click B | Switch the aftertouch position between AT and CC. |
| SETUP, in CC mode | Turn A or B, then press YES | Choose and confirm a CC number from 0 to 127. |
| CONTROL 1 | FUNC + encoder press | Enable the position’s value using the normal Octatrack control. |
| CONTROL 1, enabled CC position | Turn its encoder | Send values from 0 to 127 for the assigned CC. |
| CONTROL 1 SETUP | Click the mapped encoder again | Restore native PB or AT. Switching back to CC starts at CC0. |

**First use**

1. Select a MIDI track and set its output channel for the instrument you want to control.
2. Double-tap FX1 to open MIDI CONTROL 1 SETUP.
3. Click A to switch PB to CC. Turn A to choose a controller number supported by your receiving instrument, then press YES.
4. Press FX1 to return to CONTROL 1. The number above A identifies its assigned CC.
5. Enable the value with FUNC + encoder press, then turn A to send values. Repeat with B if you also want to replace aftertouch.
6. To restore a native function, return to SETUP and click its encoder again.

**Behavior to know**

Entering CC mode starts at CC0; the previous CC assignment is not remembered after returning to PB or AT. The feature’s installation can survive restart through Keep. Saving CC assignments is a separate Part/project operation; assignment save/reload and broader compatibility testing remain outstanding.

## Screenshot walkthrough — captions prepared, images pending

These are proposed captions. Verify the actual labels and values against each captured image before using them in a listing. The artwork is an illustration, not an Octatrack screen capture.

1. **Open the assignment page — CONTROL 1 SETUP.** Select a MIDI track and double-tap FX1. Encoder A belongs to pitch bend and B to aftertouch; click either encoder to switch that position into CC mode.
2. **Choose two controllers — CONTROL 1 SETUP.** Turn A or B in CC mode to choose a number from 0 to 127, then press YES. Choose controller numbers supported by the receiving instrument; the two positions are independent.
3. **Send a value — CONTROL 1.** Press FX1 to return to the main page. Enable the position with FUNC + encoder press, then turn it; the number above the knob identifies the outgoing CC, while the value below is what you send.
4. **Read the other assignments — CONTROL 2.** Press FX2 to view the second MIDI CONTROL page. Its CC knobs also show their assigned controller numbers instead of slot names.
5. **Return to native control — CONTROL 1 SETUP.** Double-tap FX1 and click a mapped encoder again. PB or AT returns for that position; entering CC mode again starts at CC0.

## Presentation status

Display name: **Midi Mode 2**. The existing development ID, route and installed package remain `midi-cc-slots`; this presentation work does not rebuild or replace the native module. Catalogue registration is a separate next step.

The user reported the controls, labels and restoration after restart working on their unit. These are reported results, with no independently read device/base identity. They do not establish saved-project behavior or compatibility with every module.

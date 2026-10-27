Midi Mode 2's next local candidate lets bare SRC/AMP/LFO/FX page keys pass
through while Apply runs. Editing, bank/project changes and modified page-key
shortcuts stay blocked; NO still requests safe cancellation. Bank verification
uses one CRC lookup per byte instead of two without dropping any file checks.

The user clarified that 0.0.9 completed and copied MIDI channel 6 correctly,
but held the controls for over ten seconds. Physical timing of this follow-up
is unmeasured; ordinary page access is separate from allowing performance or
project edits during an active channel-map transaction.

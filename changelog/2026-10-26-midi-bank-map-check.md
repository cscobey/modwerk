Midi Mode 2 0.0.13 fixes a save-check loop when valid working and stored bank
files contain different MIDI channels. Each original map is now recorded and
restored separately on cancellation or interruption. Other validation failures
show CHECK FAILED with a bank code. Keep the updated module installed before
INIT so it can recover an unfinished setup after restart.

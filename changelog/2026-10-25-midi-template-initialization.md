Add a private on-device MIDI project initialization experiment with an explicit
INIT confirmation, checked channel-sector writes and interruption rollback.
Native Save to New hooks carry project names and the initialization marker.
Normal bank changes no longer restore channels from the profile sidecar.

The opt-in local listing now selects 0.0.8 after its exact emulator workflow
passed. Hardware timing, resident dispatch and shared lifecycle event admission
remain separate qualification steps. Document the bank-file close/truncation
trap and test both transaction faults and torn neighboring sector data.

Add a separate local Midi Mode 2 USB update test with a visibly named test
package, explicit return to the original, and exact package/companion checks
after Undo, Keep and restart. MIDI behavior, project format, the normal local
catalogue package and the card installer remain unchanged.

Fix preparation on the published base when optional saved-file export is absent.
Verify the exact running package set against reviewed hashes, then use the base’s
save and restart confirmations. Failed exports and unknown packages still stop.

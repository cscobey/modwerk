# Midi Mode 2 presentation draft

`COPY.md` contains the proposed module-page copy, controls and screenshot captions. `thumbnail.svg` is original vector artwork in CC Map’s dark-grid, lilac routing-diagram style, following the shared module thumbnail guide. Its example numbers describe assignments, not measured output or device pixels. The artwork is covered by the draft’s MIT licence; no hardware screenshots or third-party screen pixels are included.

This is presentation work only. Nothing here registers the module, changes the runtime ID, rebuilds the native package or publishes the site. Keep `midi-cc-slots` as the installed ID when adopting the display name so the current installation remains addressable.

## Capture the walkthrough

Use a disposable test project. Capture CONTROL 1 SETUP before and after switching A/B to CC, CONTROL 1 with the two assignments enabled, CONTROL 2 with numeric headers, then SETUP with a native position restored. The five proposed captions in `COPY.md` follow that order. Check every caption against the finished pixels and record the actual values, module package/version, base identity when available, model and capture method.

For the physical device, use clear straight-on LCD photographs, or the development base’s read-only screen request if that exact base supports it. The normal WebUSB module installer does not by itself guarantee screen-export support. Do not rebuild, flash or temporarily boot a different base just for these assets. Close another app/tab holding the USB interface before using the existing device bridge; only one client can claim it directly.

On an already supported development base, the existing tool can export the current LCD without changing panel state:

```sh
npm run device -- screen --png /absolute/private/output/midi-mode-2-setup.png --scale 4
```

This requires the repository’s device bridge/tool setup; see [Driving the Octatrack](../../../../docs/OCTATRACK_DRIVING.md). If the base refuses development requests, use photographs or the already-supported emulator capture workflow instead. Do not treat an unsupported capture request as a module failure.

For clean exported pixels without a hardware capture interface, use the real headless emulator framebuffer and a matching privately built image, following [Module UI captures](../../../../docs/MODULE_UI_CAPTURES.md). Label emulator captures accurately; they illustrate controls and do not qualify hardware behavior. Preserve rendered pixels and use integer scaling. Never redraw or generate the screen labels.

Keep raw captures and firmware-derived working assets private while selecting the images. Review provenance and rights under the shared capture contract before adding any publication media. Registration and screenshot evidence remain the next stage.

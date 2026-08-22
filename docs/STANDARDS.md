# Standards — the sidelog

The governing rule, stated once: **a constraint that lives as a literal gets enforced in
the three places somebody remembered and violated in the fourth.**

This is the running record of constraints the runtimes impose on us — what each one is,
where it came from, where it is enforced, and, where it applies, the code that was found
violating it. It is a sidelog rather than a spec: entries are added when a standard is
*discovered*, usually by finding something that broke it.

Every entry here is a field of `NodeDAWNKit/Media/MediaStandards.swift` and editable at
**⌘, → Standards**. The defaults are what shipped; the file is `~/.olympiad/media-standards.json`.

**The cost of changing one, stated once:** frame lengths and resolution are folded into
`SequenceStore.cacheKey`. Move them and every clip whose length moves misses the cache —
correctly, since a different length is different pixels, but it is not free.

## Discovered

### Frame counts are 8n+1 · `frameModulus`, `frameMin`, `frameMax`, `frameChoices`

LTX's latent temporal stride is 8, so a clip is `8n + 1` frames, from 17 to 97. At 24 fps
that is the ladder 25/33/49/73/81/97 — 1.04s to 4.04s, and nothing in between.

| | |
|---|---|
| Enforced by | `MediaStandards.snapFrames`, `isLegal` |
| Reached through | `SequenceClip.snapFrames`, `SequenceClip.frameChoices` |
| Honoured by | `setFrames` (the trim handle), `addClip`, `ScoreConductor.conduct`, `splitClips` |

**Found violating it — `TimelineDeckViews.quantiseAll()`.** It snapped clip lengths to the
*musical grid* and multiplied by 24, which produced **48** and **96**: inside the range,
displayed as 2.00s and 4.00s, and not 8n+1. Two different standards were sharing the word
"snapped", and the function's own doc comment claimed the property it lacked — "a real
clip length and not a display trick". Found in a real `arrangement.json`: every clip on
disk was 48 or 96, so *every* length shown was a length that would not render.

Fixed by snapping twice — the grid decides where a clip should land, the runtime always
decides what it will accept — and by reporting how many clips moved rather than moving
them quietly.

The general lesson, which is why this file exists: **in-range is not the same as legal.**
A bounds check passes 48 and 50 happily. `isLegal` is the test that was missing.

### Frame rate · `fps`

24, and it was written as the literal `24` in `SequenceClip.seconds`,
`SequenceStore.setFrames`, `resetSlots`, `ScoreConductor` and `quantiseAll`. Every
seconds↔frames conversion now reads the standard. A frame rate hardcoded in one
conversion and read from a setting in another is a timeline that disagrees with itself.

### Dimensions divide by 32 · `resolutionDivisor`, `resolutionMin`, `resolutionMax`

256 to 1024, divisible by 32. Was enforced only in `MediaDesk.set_res`'s guard —
correctly, but in one place, and as a literal. `SequenceStore.resPresets` is a separate
hand-written list that happens to satisfy it; nothing checked that it did.

Every clip in one chain must share a size, so this bounds the whole arrangement rather
than a clip.

### Chain budget · `maxSeconds`

120 seconds, hard. Clips that would exceed it are refused rather than trimmed —
`addClip`, `setFrames` and `resetSlots` all check before committing.

### QC gate · `qcGateThreshold`

5 of 10. The one entry here that is a *policy* rather than a runtime fact, and it earns
its place because it decides whether work is redone: in GATE mode a continuity frame
below it gets one reseeded retry and the better take continues the chain. Raising it
spends more renders.

## Standing rule for reporting

`docs/SHOT-GRAMMAR.md` §III: **a declared duration is always approximated, and the drift
is reported rather than absorbed.** `MediaStandards.drift(requested:)` is the number to
report. A five-second shot is not a five-second shot here — it is 97 frames and a 0.96s
lie if nobody says so.

## Not yet captured

Named here so they are not rediscovered from scratch:

- **Steps and sampler defaults** (`steps` 8, `seedBase` 42) — in `cacheKey`, so they are
  standards by the same argument, but they read as tuning rather than as constraints and
  no runtime has yet refused a value.
- **The provenance parameter vocabulary.** `JobCache` scopes an engine's
  nondeterminism evidence to records sharing its parameter *keys*, so the key set is
  itself a standard: adding one resets that engine's evidence in both directions. Adding
  `"lane"` to `ltx-2.5-chain` did exactly that, deliberately.
- **Container and codec** for assembled output — currently whatever
  `AVAssetExportSession`'s preset yields.

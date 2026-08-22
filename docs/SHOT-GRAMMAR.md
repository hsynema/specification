# Shot grammar — a prompt is a vector, not a sentence

The governing rule, stated once: **the model fills one window; the app owns the cut.**
Everything below follows from that. A grammar written for a model that cuts internally
is the wrong grammar here — LTX renders one clip of 25–97 frames and hands forward a
frame. Sequencing, timing, and continuity are ours, measured, and already have owners in
the tree: `Media/SequenceModel.swift` holds the chain, `Media/ScoreConduction.swift`
holds the clock.

Distilled from the ONE STUDIO / Seedance 2.0 prompt engine. That engine targets a model
that takes a whole shot list in one prompt and cuts inside itself. Most of its
architecture is therefore inapplicable, and the parts that survive are the parts about
*craft* rather than about Seedance.

Status vocabulary, borrowed from `MEDIA-RENDER-TAXONOMY.md`: **GROUNDED** (holds for the
local renderer, verifiable against a render), **UNVERIFIED** (a technique that works on
large caption-trained models; untested on LTX at our sizes and step counts — mark it,
don't assume it), **OURS** (has no counterpart in the source engine; written here because
a local chain needs it).

## I · Discarded, with cause

| Dropped | Why it does not apply |
|---|---|
| `[SHOT N: 0s–Xs]` timestamp architecture | LTX renders one clip per call. Timestamps inside a prompt address nothing; the clip's length is `frames`, and the sequence's timing is `ScoreConductor`'s. |
| `[CHARACTER LOCK]`, `[@image N]` identity pins | LTX has no identity conditioning. Continuity here is *pixel* continuity — `SequenceClip.anchorImagePath` and the previous clip's last frame. Borrowing the language would claim a mechanism we do not have. |
| `[BEAT MAP: bpm estimate · cut pattern]` | A language model guessing tempo from a song title. `ScoreConductor.plan` cuts on the real tempo map, and `measure` returns energy, centroid, entropy, flux, onsets and bar↔frame drift per segment. Measured beats estimated; the conduction fills the beat fields, never the model. |
| `[Audio: score · SFX · ambience]` | LTX generates no audio. Audio is arranged on the DAW side and joined at assembly (`SequenceClip.audioGain`, `transitionSec`). |
| 3–5 shots · 2–5 s each | Not our envelope. See §III. |
| `[Constraints: … no drift, smooth motion]` | Negative constraints as prose. Drift is what QC measures at each link (`QCMode.gate`, `qcGateThreshold = 5`); asking the model not to drift does not stop it drifting. |
| Aspect as free text (`2.39:1 anamorphic`) | A chain must share one size — `SequenceStore.resPresets` is the closed set, because every clip in a cut renders at one resolution. |
| The music-video engine entire (lip-sync, performance mode, genre grammar) | Lip-sync needs audio-conditioned generation. Nothing in the local path takes an audio conditioning signal. |
| `---PROMPT_BREAK---` multi-variant transport | The idea survives (§VI); the transport does not. Variants here are seeds, not re-prompts. |
| Studio bundles (camera + grade + *score* + *editing rhythm*) | Half of each bundle addresses things one clip cannot express. Kept only for their visual half. |

## II · The prompt is a vector

The source engine's deepest move is not the shot list — it is that a prompt is assembled
from orthogonal axes rather than typed as a sentence. That transfers completely, and it
buys something here it did not buy there: a precise dirty-set.

Two scopes, because they dirty differently:

**Sequence-wide** — one value for the whole chain, appended to every clip's prompt.

| Field | Holds |
|---|---|
| `environment` | location · time of day · atmosphere · practical light sources |
| `lens` | focal length · aperture · depth of field |
| `grade` | palette · contrast · stock or LUT reference |
| `style` | era · visual register |

**Per clip** — varies shot to shot.

| Field | Holds |
|---|---|
| `subject` | who/what, and the one thing it does — the motion thesis (§IV) |
| `camera` | exactly one move from the closed set (§V) |
| `light` | the source and direction *for this framing* |

Why the split is not cosmetic: `SequenceStore.cacheKey` folds prompt, seed, frames,
width, height, steps and the anchor hash into a clip's cache name. Today `prompt` is one
opaque string, so changing the grade and changing shot 3's action are indistinguishable
to the cache — both are "the string changed." Split, the dirty-set becomes exact:

- a sequence-wide edit dirties **every** clip, correctly and visibly;
- a per-clip edit dirties **N onward**, through the anchor chain that
  `SequenceModel` already walks.

This also replaces `masterPrompt` — the pipe-separated field at
`Workspaces/MediaTimeline.swift:402` (`"master prompt — separate shots with |"`). A pipe
is a delimiter, not a grammar; it cannot say which half of the string is chain-wide.

## III · The real envelope

Not 2–5 seconds. `SequenceClip.frameChoices` at 24 fps:

| Frames | Seconds |
|---|---|
| 25 | 1.04 |
| 33 | 1.38 |
| 49 | 2.04 |
| 73 | 3.04 |
| 81 | 3.38 |
| 97 | 4.04 |

`snapFrames` clamps to 17…97 and rounds to the nearest 8n+1, so a declared duration is
always *approximated*. When a shot list states a length, snap it and **report the drift**
rather than silently absorbing it — the same discipline `ScoreConductor.SegmentFeature`
already keeps in its `drift` field. A five-second shot is not a five-second shot here; it
is 97 frames and a 0.96 s lie if nobody says so.

Chain budget: `SequenceStore.maxSeconds = 120`.

## IV · Craft rules that transfer

**One camera move per clip.** GROUNDED. The source engine states it as a rule; at 25–97
frames it is closer to arithmetic. A second move inside one second has no time to read as
a move — it reads as instability, and it poisons the last frame, which is the next clip's
anchor.

**Every clip carries one motion thesis.** GROUNDED, expanded from the engine's "always
include at least one physics showcase." A two-second clip with no motion event is a
wasted render *and* an ambiguous hand-off: the anchor frame it passes forward could have
come from anywhere in the clip. Name the event — cloth settling, smoke crossing the key
light, a hand entering frame, water breaking. One per clip, not three.

**Name a real thing.** The principle is GROUNDED: a concrete referent ("Kodak 5219",
"sodium vapour street lamp", "overcast north light") is a token with a visual
distribution behind it; "cinematic", "epic", "beautiful" are not discriminative and cost
you the tokens they occupy.

The *specific* trick of naming cinematographers and studios is **UNVERIFIED** here. It
works on models trained over caption corpora dense with those names. LTX at 512×384 and
8 steps has a different caption distribution, and I have not tested whether "Roger
Deakins backlight" outperforms "single hard backlight, deep shadow, no fill." Until
somebody renders both against the same seed, treat auteur names as unproven and prefer
the physical description — which is what the name was standing in for anyway.

## V · Closed vocabularies

Closed because the point of a vocabulary is to force specificity a person typing at 2 a.m.
will not produce. These live as data, not prose — `MediaPreset` in `Media/Presets.swift`
already has the shape (`prompt`, `aspect`, `tier`, `frames`, `steps`, `seed`), and
`PresetStore.upsert` is additive by covenant, so the vocabulary grows and never loses an
entry that once worked.

**Camera move** — pick exactly one.

`static` · `push in` · `pull back` · `truck left` · `truck right` · `tilt up` ·
`tilt down` · `orbit` · `crane up` · `crane down` · `handheld follow` · `rack focus`

Dropped from the source list: whip pan, zoom burst, corkscrew, FPV thread, match cut,
bullet-time 360. Some are two moves wearing one name; some are cuts, which are ours;
the rest need more frames than the envelope has.

**Light** — source, then direction, then quality.

Source: `practical` (named — neon, headlight, monitor, fire, candle, LED strip) ·
`daylight` · `overcast` · `moonlight` · `stage`
Direction: `front` · `side` · `back` · `top` · `underlit`
Quality: `hard` · `soft` · `diffused` · `specular`

**Grade** — named stock or process, not a mood.

`Kodak 5219 tungsten` · `Vision3 250D` · `Fuji Eterna` · `Ektachrome 100` ·
`bleach bypass` · `teal–orange split` · `desaturated high-contrast` · `warm low-key` ·
`cool neutral`

## VI · Continuity — the vocabulary the source engine never needed

OURS, entirely. Seedance cuts inside itself, so it has no words for the seam between two
renders. That seam is our hard problem: `anchorImagePath`, the previous clip's last
frame, and the vision QC that scores each link 0–10 and reseeds below 5 under
`QCMode.gate`.

Every link declares its **mode**:

| Mode | Anchor | Meaning |
|---|---|---|
| `carry` | previous clip's last frame | Camera keeps moving, subject continues. Highest continuity demand; QC scores this link hardest. |
| `reframe` | previous clip's last frame | Same scene, new framing. Composition shifts; scene facts hold. |
| `cut` | `anchorImagePath`, set explicitly | A deliberate new shot. The chain break is intentional and QC should not penalise it. |

The distinction matters mechanically, not just descriptively: `SequenceClip`'s doc
comment already says an explicit anchor "replaces the continuity frame from the previous
clip — a deliberate cut to a new shot." The mode is that fact, named, so QC can tell a
failed carry from an intended cut. Right now it cannot, and a hard cut scored as a
continuity failure is a false negative that `GATE` will spend a reseed on.

And every `carry` or `reframe` link declares its **pin list** — what must not drift:

`light direction` · `time of day` · `wardrobe / colour` · `lens` · `subject scale` ·
`background geometry`

The pin list is the thing QC is actually judging. Naming it turns a 0–10 score into an
answer about *what* broke, which is the difference between a number and a diagnosis.

## VII · Variants are seeds

The source engine generates several radically different prompts per concept and separates
them with `---PROMPT_BREAK---`. The impulse is right and the mechanism is wrong for us: N
prompts is N cache misses forever, while N seeds against one prompt is N cache entries
that stay free to revisit — `cacheKey` already includes `seed`, and `PresetStore` already
keeps the recipe that produced a look.

So: hold the vector fixed, sweep the seed, keep the take. What the source engine does by
re-prompting, we do by re-seeding, and the cache means the rejected takes cost nothing to
reconsider.

## VIII · Where it lands

| Piece | Home |
|---|---|
| Vector fields on a clip | `SequenceClip` — split `prompt` into per-clip body + chain suffix |
| Chain-wide fields | `SequenceStore`, beside `resWidth`/`steps`/`seedBase` |
| Closed vocabularies | `Media/Presets.swift`, as tables |
| Continuity mode + pin list | `SequenceClip`, read by the QC pass |
| Dirty-set precision | `SequenceStore.cacheKey`, once the fields are separate |
| Timing authority | unchanged — `ScoreConductor` |

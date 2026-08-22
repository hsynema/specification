# Westwyrd Shot Grammar

**Revision 0 · DESIGNED.** The SYN-layer vocabulary for H.SYN.EMA.
Machine-readable form: `data/shot-grammar/westwyrd/`. Reader: `data/shot-grammar/loader.py`.

The governing rule, stated once: **the codec says that a director marks an edit seam; it
does not say what a director can mark. This is that vocabulary, and it is additive — it
specifies no byte layout, claims no separator, and changes nothing about how a file is
folded, verified or read.**

Two things this document is careful not to be. It is not an extension of the `.syn`
single-work object, which is a complete format on its own terms, developing in its own
lane, and not this grammar's to direct. And it is not a second opinion about the
container: `H.SYN.EMA` defines five layers under one Root State Hash, and every structural
statement here is quoted from that specification rather than re-derived.

---

## I · Why a shot grammar is a format problem now, and was not before

The history of moving media is the history of one boundary: the seam where clip A ends and
clip B begins. Five eras, and the fifth is the only one that lost something the fourth had.

| Era | Medium | Seam mechanism | State cleared? | In-band? | Joint inspectable by |
|---|---|---|---|---|---|
| 1 · 1895– | cellulose | cement weld / tape splice | n/a — physically discrete | n/a | a loupe |
| 2 · 1956– | quad tape | razor at the guard band; PLL lockup | sync re-acquired | yes — the control track | ferrofluid + microscope |
| 3 · 1980s– | SMPTE / NLE | a point on a timeline | n/a — discrete files | n/a | the EDL |
| 4 · 1990s– | H.264 / HEVC | **a forced IDR at the cut** | **yes — the DPB is flushed** | **yes — a syntax element** | bitstream inspection |
| 5 · 2022– | latent diffusion | **none** | **no** | **no** | **nothing** |

Read the last two rows together and the diagnosis is exact. **Era 4 already solved this.**
An IDR frame is an explicit, in-band, machine-checkable instruction to discard prior
temporal state at a discontinuity. A decoder that ignores one produces visibly wrong
output, so the instruction is enforced by the medium rather than by discipline.

Era 5 regressed past era 1. A diffusion model is a continuous probability estimator over a
smooth vector space; prompted across a scene change it interpolates, because interpolation
is its only mode. It morphs, it melts, it hallucinates ghost frames where its cross-frame
attention breaks, and in a sliding autoregressive window the previous scene's latents pull
the new one back toward the old — lighting, geometry and character bending gradually
toward what came before.

And the second loss is worse than the first. In every prior era the joint could be
*examined*: a splice under a loupe, a magnetic track raised in iron powder, a NAL unit type
in a bitstream. A generated frame is a probability sample. **A morph and a cut are both
just pixels**, so inspection tells you nothing, and no amount of looking at the output
recovers what was asked for.

H.SYN.EMA answers both losses at once, and the answers are already in the specification:
the I-Node is the in-band clearance instruction, and the E track is the loupe. What is
missing — and what this document supplies — is the vocabulary a director uses to decide
where the I-Nodes go.

> Two corrections to the received account, because a rationale section that is wrong is
> worse than no rationale. Quadruplex heads scan **transversely** across the tape width;
> diagonal scan is helical and arrived later, with Type C and the cassette formats. The
> guard-band razor cut and the ferrofluid technique are as described. And Avid Media
> Composer and Lightworks were competing systems from different companies, not one product.

## II · Where this sits

H.SYN.EMA is one `.syn` file, magic `HSYN`, five layers folded to one 32-byte Root State
Hash carried in the header.

| letter | layer | track | this grammar |
|---|---|---|---|
| **H** | Hash — header and determinism key | preamble | untouched |
| **SYN** | Synthesise — the instruction bitstream | 0 | **this document** |
| **E** | Evidence — the audit ledger | 1 | one proposed field, §VI |
| **M** | Map — the derivation DAG | 2 | untouched |
| **A** | Assemble — compiled timeline and media | 3+ | one seam class lives here, §V |

SYN stores coding units, not frames: parameter sets, **I-Nodes** carrying a latent seed and
a full prompt and standing on nothing earlier, and **P-Nodes** carrying only a delta from an
upstream anchor. The grammar below is the typed content of those payloads.

## III · The shot vector, by unit kind

A prompt is a vector, not a sentence — and the coding units already impose the axis split,
so the grammar only has to name which field belongs to which unit.

**SPS · sequence scope.** Constant for the work. `environment` · `lens` · `grade` ·
`style`. The codec already fixes the model digest, sampler and resolution here; these are
the creative fields that are constant by the same logic. A production shoots on a lens
package; a per-shot lens is a continuity error with extra steps.

**EPS · span scope.** An override of the SPS across a reel or sequence. A re-graded reel is
a small localised unit rather than a rewrite, and a Color Sequence in the MovieLabs sense
is exactly this span.

**I-Node · shot scope.** The full prompt. `subject` · `action` · `framing` · `angle` ·
`camera` · `light`. One camera move, from the closed set. One motion event, named. A unit
with no motion event is a wasted synthesis and an ambiguous hand-off — the frame it passes
forward could have come from anywhere in the clip.

**P-Node · delta scope.** A closed list of what a delta may contain: `prompt-diff` ·
`camera-motion` · `temporal-delta` · `control-vector`. **Never a seed.** A seed is what
makes a unit intra; a predicted unit that reseeds is unmoored from its anchor and its delta
means nothing.

Full tables with industry notation, aliases and per-term limits:
`data/shot-grammar/westwyrd/unit-scopes.csv`, resolving into `data/shot-grammar/taxonomy/`.

## IV · The camera vocabulary is a composition rule, not a menu

Twelve moves, closed. Each declares the motion it **hands forward** at its last frame and
the motion it **accepts** at frame zero.

`static` · `push in` · `pull back` · `truck left` · `truck right` · `tilt up` ·
`tilt down` · `orbit` · `crane up` · `crane down` · `handheld follow` · `rack focus`

Across a P-chain, unit N's hands-forward must appear in unit N+1's accepts. An orbit welded
to a locked-off static is a visible stop, and the grammar refuses it before the GPU finds
out. Across an I-Node the constraint lifts entirely, because nothing is carried — which is
the whole reason an intra unit is cheap to cut on and a predicted one is not.

Thirteen further moves are catalogued and marked `EXCLUDED` — whip pan, dolly zoom,
corkscrew, plain zoom, bullet-time. They stay in the table because a parser reading an
imported shot list must **recognise** a whip pan in order to refuse it. A vocabulary that
silently omits what it cannot render produces a parse failure where it should produce a
diagnosis.

## V · Seam classes, and the intra decision

The codec emits an I-Node when any of four conditions holds: a **scene cut**, accumulated
**drift past τ**, a **random-access point** coming due, or an **edit seam the director
marked**. The first and fourth are editorial. This grammar types them.

| class | unit | forces intra | via | pins asserted |
|---|---|---|---|---|
| `HOLD` | P-Node | no | — | all eight |
| `CARRY` | P-Node | no | — | seven |
| `REFRAME` | P-Node | no | — | five |
| `CUT` | I-Node | yes | scene-cut | none owed |
| `MARK` | I-Node | yes | edit-seam | none owed |
| `MATCH` | I-Node | yes | edit-seam | match-invariant |
| `GRAFT` | I-Node | yes | scene-cut | none owed |
| `DISSOLVE` | A-layer | n/a | — | — |

Four of these are worth their own sentence.

**`HOLD` has no counterpart in any prior era.** It is one shot longer than the generation
window, continued across units. Not an edit at all — the seam exists only because the
runtime has a maximum clip length. On film you could roll ten minutes; here a long take is
a P-chain, and the seams inside it must read as no seams at all. It therefore carries the
strictest pin set in the grammar, because nothing is supposed to be happening.

**`MARK` exists so that wanting a seam is a sufficient reason to have one.** An I-Node the
director asks for whether or not the content demands it, so the shot stays independently
re-cuttable. It costs bytes and buys editability — the format's single strongest lever,
spent deliberately and recorded as deliberate.

**`MATCH` makes the match cut checkable.** One named quantity — a shape-mask IoU, a
motion-vector angle, a dominant hue — asserted to agree across the seam within a declared
tolerance, measured on the last frame before and the first frame after. A match cut whose
match is not checkable is a cut with a note attached. The tolerance is deliberately loose:
a match cut is a perceptual effect, and a tight numeric threshold would refuse cuts that
work.

**`GRAFT` is the other new one.** A seam whose two sides came from different engines or
different weights. It forces an intra unit because a P-Node's delta is meaningless against
an anchor another model made, and the SPS/EPS boundary moves with it.

**`DISSOLVE` is not a SYN construct at all** — it is a transition parameter on an A-track
cut pointer, applied to finished frames. Declaring a dissolve in SYN is the specific
mislabel the class exists to prevent: a blend a generative model produced across two
prompts is a morph, and it is not the same object.

## VI · The pin set — drift, decomposed

This is the one place the grammar proposes something the codec does not already have, and
it is small.

The encoder measures drift by periodically synthesising a shadow intra frame and comparing
it against the predicted chain; when the distance crosses τ it forces an I-Node and resets
the accumulator. The specification is deliberate that drift is *measured, not assumed* —
and it leaves the comparison itself open.

A scalar distance is a threshold. **Decomposed into named pins it becomes a diagnosis.**

`light-direction` · `time-of-day` · `wardrobe` · `lens` · `subject-scale` ·
`background-geometry` · `subject-identity` · `grain-and-grade`

Each carries a measurement method and a default tolerance in thousandths — no float ever
enters a preimage, so a tolerance is `90`, not `0.09`. Two are new to the generative era
and have no prior-era counterpart:

- **`subject-identity`.** No previous medium could lose an actor between two frames of one
  take. It is the signature failure of long predicted chains, and the embedding model used
  to measure it must be named on the seam, because a distance is meaningless without one.
- **`grain-and-grade`.** Photochemical grain was stochastic and unaddressable. Generated
  grain has a seed, so it can change mid-take, and must be pinned where it must not.

The proposal to the E layer is one field: `drift_components`, the per-pin distances from
that shadow-frame comparison. It changes no existing structure. What it buys is the
difference between *"drift 0.34 > τ, forcing intra"* and *"subject-identity drifted 0.42,
everything else held"* — the first tells the encoder what to do, the second also tells the
director why.

## VII · Interoperation, because a standard nobody can adopt is a document

Every term in the taxonomy carries its industry abbreviation and aliases, and the vocabulary
was assembled from the public record rather than invented:

- **MovieLabs Ontology for Media Creation v2.8** — the shot grammar the five MovieLabs
  owner studios have collectively published, CC BY 4.0. `Shot`, `Sequence`, `Editorial
  Shot`, `VFX Shot`, `Slate UID`, `Setup`, `Take` all have formal definitions there, and
  this grammar's terms map onto them rather than competing. A Westwyrd I-Node is an OMC
  Shot; a P-chain between two I-Nodes is one Shot's interior.
- **ETC/MovieLabs VFX Image Sequence Naming v1.0** — the cross-studio file-naming grammar.
  An H.SYN.EMA work's exported frames name themselves under it unchanged.
- **ISDCF DCNC** — 741 registered studio codes. Westwyrd holds none, and the dataset
  records that as empty rather than reserving one, because a code you have not registered
  is a code somebody else may hold.
- **Netflix VFX shot-and-version naming** — the only studio-published shot-ID template in
  the public domain, and the model for shot IDs incrementing by tens.

The interoperation is the adoption path. A grammar that requires abandoning OMC, ETC and
DCNC asks a studio to change everything at once; this one asks them to type a seam.

## VIII · Status, stated at the correct tier

**DESIGNED.** No line of this grammar is implemented in `dawn-syn`, `synctl` or the codec.
Nothing has been encoded, decoded, or measured against a render.

What is **BUILT** and can be run today is the dataset and its reader: 140 taxonomy terms
across ten files with a shared schema, seven notation grammars, 741 registered studio
codes, a validator that refuses unknown enums and dangling source keys, and a hash chain
over the studio records. `python3 data/shot-grammar/loader.py`.

What is **MODELLED** — existing in the tree and composed rather than assumed — is the link
mode and pin list of `docs/SHOT-GRAMMAR.md`, the frame ladder and QC gate of
`docs/STANDARDS.md`, the closed camera vocabulary with its hands-forward and accepts pairs
in `NodeDAWNKit/Media/PromptLibrary.swift`, and the chain construction of
`NodeDAWNKit/Syn/LedgerChain.swift`.

Design parameters in the tables — tolerances, the eight pins, the seven classes — are
structure and targets, never measured results. No tolerance here was fitted against a
labelled corpus, because this build does not have one, and inventing a calibration would
put a fabricated number inside a threshold that refuses work.

## IX · What this grammar does not establish

Carried from the H.SYN.EMA boundary list, which is not this document's to shorten, plus two
that belong to the grammar itself. The full table with attribution is
`data/shot-grammar/westwyrd/boundaries.csv`.

- **That the work is good.** An audience, a critic — never a checksum.
- **That a credit is true**, that a right is held, that the maker meant well, that the
  prompt is real.
- **That a signature says who sat at the machine.** A P-256 attestation proves a machine
  held a key and witnessed a computation. A coerced signature is a valid signature.
- **That a frame nobody re-synthesised is correct.** Stage 8 is optional and expensive; a
  stage that could not run is reported SKIPPED and named individually, because *three
  frames unchecked* must never read as *three frames fine*.
- **That a declared seam class is the right one for the shot.** The grammar checks that a
  `MATCH`'s invariant agrees and that a `HOLD`'s delta is a pure temporal advance. It has no
  opinion on whether the cut belongs there.
- **That a pin measured within tolerance means continuity held.** The pin set is a
  decomposition of drift, not a definition of it. Something can break that no pin measures,
  and the grammar reports which pins ran rather than implying they were sufficient.

The last one is the honest centre of this document. Everything above makes the seam
*addressable, typed and evidence-bearing* — which is exactly what era 5 lost and no more
than that. A format can restore the loupe. It cannot decide whether the cut was any good.

---

**See also:** `docs/SHOT-GRAMMAR.md` (the prompt-vector argument this grammar formalises) ·
`docs/STANDARDS.md` (the runtime constraints it must satisfy) ·
`data/shot-grammar/README.md` (the dataset and its provenance discipline)

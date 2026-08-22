# Shot grammar — the dataset

The governing rule, stated once: **the vocabulary is the industry's, the notation is the
studio's, and the look is somebody's opinion — and a table that mixes the three is worse
than no table.**

This is the machine-readable half of `docs/SHOT-GRAMMAR.md`. That document argues; this
directory is what it argues about, in CSV, with a reader at `loader.py`.

```bash
python3 data/shot-grammar/loader.py          # counts, then validates
```

## The finding that shaped it

No major Hollywood studio publishes a shot grammar. The research is in the sources table;
the short version is that "shot grammar per studio" turns out to be three different
questions with three different answers:

| Layer | Varies by studio | Public | Lives in |
|---|---|---|---|
| Shot **vocabulary** — ECU, HA, push, dissolve | No | Yes | `taxonomy/` |
| Shot **notation** — how a shot is named, numbered, versioned | **Yes** | Partly | `notation/`, `registries/` |
| House **style** — grade, coverage, cutting rate | Yes, as a reading | Trade press only | `studios/*/style.csv` |

The middle layer is the only one where per-studio difference is a documented fact rather
than a critical claim, and even there the public surface is thin: **Netflix is the only
major with a published shot-naming specification.** Disney, Warner, Universal, Paramount,
Sony, Amazon MGM and Apple keep theirs behind partner portals. Those studios carry a row
in `studios/notation.csv` recording the absence rather than a reconstruction dressed as a
spec — see `status = unknown`.

Two things *are* public and cross-studio, and both matter more than any single studio's
silence.

**The MovieLabs Ontology for Media Creation v2.8** formally defines `Shot`, `Sequence`,
`Editorial Shot`, `VFX Shot`, `Slate UID`, `Setup` and `Take`, with a worked Slate UID
encoding — `15A-1`, `2B-4SER`, `2-3PU`. MovieLabs is jointly run by Paramount, Sony,
Universal, Disney and Warner Bros., so this *is* those five studios' collectively published
shot grammar, and it is CC BY 4.0. It also says, verbatim, that each member decides
independently whether to adopt it — so the dataset records governance as `documented` and
adoption as `unknown`, which are different claims.

**ETC/MovieLabs VFX Image Sequence Naming**
specification, written by a working group chaired out of Universal Pictures with Disney,
Marvel, Lucasfilm/ILM, Paramount, Warner Bros., Fox, Sony, DreamWorks, HBO, Netflix, Weta
and Digital Domain contributing. Contributing is not adopting, and the dataset says so:
those rows carry `status = contributor`, not `documented`.

## Layout

```
_schema/     enums.csv · sources.csv · schema.csv      the column contracts
taxonomy/    ten files, one shared 15-column header    the vocabulary + its notation
notation/    schemes.csv + one directory per scheme    parseable identifier grammars
registries/  isdcf-studio-codes.csv                    741 registered studio codes
studios/     studios · notation · style · bodies       flat, and the source of truth
             serials · ledger · HEAD                   identity, and its hash chain
studios/<slug>/                                        generated projection of the above
westwyrd/    the Westwyrd Shot Grammar tables          a proposal, not a record — see below
build/       split_studios.py · seal_studios.py        projection, and the seal
loader.py    reader, formatter, validator
```

The flat tables under `studios/` are where edits go. The per-studio directories are
generated from them so the two cannot drift:

```bash
python3 data/shot-grammar/build/split_studios.py           # regenerate
python3 data/shot-grammar/build/split_studios.py --check   # fail if stale
```

## Three identifiers, three jobs

Studios carry a **serial**, a **digest** and a place in a **chain**, because "did this
studio's shot grammar change?" is three questions.

| | | |
|---|---|---|
| `serial` | `SG-014` | Identity. Allocated once, never reused. **Encodes nothing** — a serial that encodes a fact becomes wrong the day the fact changes. |
| `digest` | 16 hex | State. Over a canonical form of the studio's own record; moves if and only if the recorded facts move. |
| `group_digest` | 16 hex | The studio folded with every label it owns. A change at Pixar moves Disney's group digest and leaves Disney's own digest still. |
| `link` | 64 hex | Position in history. `SHA256(prev ‖ 0x1D ‖ canonical)` — the same construction as `NodeDAWNKit/Syn/LedgerChain.swift`, separators included. |

```bash
python3 data/shot-grammar/build/seal_studios.py            # what drifted since the last seal
python3 data/shot-grammar/build/seal_studios.py --seal     # append a row per changed digest
```

The limit is `LedgerChain`'s own, and it matters more here rather than less:
**tamper-evident is not tamper-proof.** Anyone who can write `ledger.csv` can rewrite a row
and recompute every link after it. The chain becomes evidence only once somebody else has
seen a head — which is why `studios/HEAD` is a separate file worth committing and quoting.
Both mechanisms are sabotage-tested: editing a fact reports the drift and the serial that
moved; editing a sealed row reports `BREAK at row N` and refuses to seal on top of it.

## westwyrd/ — a proposal, kept in its own namespace

Everything else in this dataset catalogues what the industry has published. `westwyrd/`
does not: it is the **Westwyrd Shot Grammar**, the SYN-layer vocabulary for H.SYN.EMA,
specified in [WESTWYRD-SHOT-GRAMMAR.md](../../docs/WESTWYRD-SHOT-GRAMMAR.md).

It is separated because mixing a proposal into a record is the failure this whole dataset
is arranged to prevent. Nine tables: the five eras of the seam as rationale, the container's
five layers, the shot vector by coding unit, seven seam classes mapped onto the encoder's
intra-versus-predicted decision, eight pins that decompose drift, and the boundary list.

Status is **DESIGNED** — no line of it is implemented in `dawn-syn`, `synctl` or the codec.
The `.syn` single-work object is a complete format developing in its own lane; nothing here
extends, versions or re-specifies a byte of it.

## Two columns that carry the weight

**`provenance`** separates a rule from an impression. `published-spec` and
`industry-standard` are quotable; `trade-reported` describes what somebody did once;
`critical-reading` is an interpretation with, sometimes, a live counter-argument — Marvel
carries a row recording that criticism argues both sides of whether its house style
exists at all. `Row.is_spec` is the test.

**`local_status`** borrows GROUNDED / UNVERIFIED / OURS from `docs/SHOT-GRAMMAR.md` and
adds EXCLUDED, so the taxonomy can hold the whole industry vocabulary while still saying
which part of it survives the local renderer. Twelve of the twenty-five camera moves are
GROUNDED — exactly the closed set at §V. The other thirteen are in the table because a
parser reading an imported shot list needs to *recognise* a whip pan in order to refuse
it, and a vocabulary that silently omits the terms it cannot render produces a parse
failure where it should produce a diagnosis.

## What the loader does

```python
from loader import load
g = load()

g.abbrev("XCU")                     # alias-aware: -> extreme close-up
g.parse("netflix-vfx", "AGM_104_TCC_067_0010_comp_NFX_v001")
g.schemes["netflix-vfx"].check(version="1")   # -> ["... does not match ^v[0-9]{3,4}$"]
g.legal_carry("cam.rotate.orbit", "cam.locked.static")   # -> False
g.studio("netflix").documented      # only what Netflix actually published
g.validate()                        # [] when clean
```

`Scheme.parseable` is false for five of the seven schemes, and the reasons differ. ETC has
optional trailing fields, so a short name is ambiguous — the spec itself warns that
automated parsing of file names is risky and recommends embedding the metadata instead.
The slates have no delimiter at all: `24A` is two fields in one token. The cache key is a
digest, so its fields are inputs, not substrings. Refusing to guess in those five cases is
the point; `check()` against each field's regex is what to use instead.

`validate()` is not decoration. It caught the European slate scheme claiming to be
splittable, the ETC Show ID being counted twice because it has a feature form and an
episodic form, and two regexes that a bare comma had silently torn in half mid-column.

## Known gaps

- **Illumination, Imageworks, Wētā FX, Digital Domain and Westwyrd Pictures** hold no ISDCF
  studio code. Their rows carry an empty `isdcf_code` rather than a guess.
- **Twenty-eight of thirty-seven studios have no style rows.** Not an oversight — no source
  was found that says anything specific enough about their visual grammar to be worth a
  row. An empty `style.csv` is the honest output.
- **The DCNC** has content modifiers, 3D and HFR fields and subtitle variants beyond the
  twelve core fields encoded here. The sixteen content-type codes are verbatim from the
  registry; the aspect, territory and audio value lists are the common cases, not the
  complete registries.
- **Average shot length per studio** would be the one quantitative style axis worth
  having. Cinemetrics holds the measurement corpus but not aggregated by studio, so
  `taxonomy/rhythm.csv` carries the bands and `studios/style.csv` carries no ASL figures.

## Sources

Every row's `source_key` resolves against `_schema/sources.csv`, which holds the title,
publisher, year and URL for each. The load-bearing ones:

- [VFX Image Sequence Naming v1.0](https://movielabs.com/prodtech/sdw/vfx/ETC-ImageSequenceNaming-v1.0-063020-FINAL.pdf) — ETC at USC / MovieLabs, 2020
- [VFX Shot and Version Naming Recommendations](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360057627473-VFX-Shot-and-Version-Naming-Recommendations) — Netflix
- [DCNC Illustrated Guide](https://www.isdcf.com/registry/illustratedguide/) and [Studio Code Registry](https://www.isdcf.com/registry/studios/) — ISDCF
- [Shot List Abbreviations](https://www.studiobinder.com/blog/shot-list-abbreviations/) — StudioBinder

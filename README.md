# H.SYN.EMA

**A compound container for verifiable generative cinema.**

One `.syn` file, magic `HSYN`, five layers under one 32-byte Root State Hash.

> The film is the decision; the pixels are only its cache.
> The header is the key, the bitstream is the code, the container is the evidence.

A finished film is not a grid of pixels — it is a decision: a seed, a prompt, a cut, a mix.
H.SYN.EMA stores the decision and proves it. A cryptographic header that is also the
determinism key; an instruction bitstream that stores generative *logic* as coding units
rather than flat frames; and multiplexed alongside them, the evidence of how each frame was
made, the graph of how the work was assembled, and a compiled timeline with a playable proxy.

Any party can re-derive every frame from the bitstream, re-check every claim of authorship
against the ledger, and re-compute the work's root **without trusting the tool that produced
it**.

---

## The format is free. Permanently.

`PATENTS.md` grants a perpetual, worldwide, royalty-free, **irrevocable** licence under any
necessary claims, with defensive termination as the only condition. No fee, no registration,
no notice, nothing to sign.

This is not a concession that can be withdrawn once adoption arrives. HEVC fragmented across
four licensors, implementers backed away, and a royalty-free alternative took the market.
A format that can be taxed is a format that will be routed around.

Specification and vocabularies: **CC BY 4.0** — the same licence the MovieLabs Ontology for
Media Creation uses. Code: **Apache 2.0**.

## The papers

| | |
|---|---|
| [`papers/H.SYN.EMA-format-specification.pdf`](papers/H.SYN.EMA-format-specification.pdf) | The container: five layers, one Root State Hash, eight verification stages, and the honest boundary |
| [`papers/H.SYN.EMA-codec-design.pdf`](papers/H.SYN.EMA-codec-design.pdf) | The encoder and decoder: coding units, the intra/predicted decision, the determinism contract, the cache |

Both carry an OpenTimestamps proof alongside them.

## What is here

| | |
|---|---|
| [`docs/WESTWYRD-SHOT-GRAMMAR.md`](docs/WESTWYRD-SHOT-GRAMMAR.md) | The SYN-layer vocabulary — the shot grammar proper |
| [`docs/SHOT-GRAMMAR.md`](docs/SHOT-GRAMMAR.md) | The prompt-vector argument the grammar formalises |
| [`docs/STANDARDS.md`](docs/STANDARDS.md) | Runtime constraints any implementation must satisfy |
| [`data/shot-grammar/`](data/shot-grammar/) | 45 machine-readable tables with a reader and a validator |
| [`data/shot-grammar/westwyrd/`](data/shot-grammar/westwyrd/) | Seam classes, coding-unit scopes, drift pins, boundaries |

```bash
python3 data/shot-grammar/loader.py     # counts, then validates
```

## Interoperation, not replacement

Every term carries its industry abbreviation, and the vocabulary was assembled from the
public record rather than invented.

- **MovieLabs OMC v2.8** — an I-Node is an OMC `Shot`; a P-chain is one `Shot`'s interior.
  `Slate UID`, `Setup` and `Take` carry unchanged.
- **C2PA** — complementary, not rival. C2PA answers *who signed*; this answers *what ran*.
- **ETC/MovieLabs VFX Image Sequence Naming** — exported frames name themselves under it.
- **OpenTimelineIO** — the A-track compiles to and from it.
- **ISDCF DCNC** — 741 registered studio codes, mirrored.

## Status

**DESIGNED.** The specification and the vocabularies are complete and validated. The
reference encoder, decoder and verifier are not yet written, and no line of this is
implemented in a shipping codec.

Design parameters — tolerances, the eight drift pins, the seven seam classes — are structure
and targets, never measured results. Nothing here was fitted against a labelled corpus,
because inventing a calibration would put a fabricated number inside a threshold that
refuses work.

## What a valid file does not establish

| not established | whose job it is |
|---|---|
| that the work is good | an audience, a critic — never a checksum |
| that a credit is true | a contract, a court |
| that a right is held | a rights holder, a registry |
| that the maker meant well | no cryptography can read intent |
| that the prompt is real | the world, not the seed |
| that a frame nobody re-synthesised is correct | the synthesis stage — reported SKIPPED, never silently passed |

A format earns trust by the precision of what it refuses, not the length of what it claims.
The full list travels inside every file and every rendered document, emitted from a constant,
so no code path produces a work that omits it.

---

Published by **Westwyrd Federated Instruments**.
Licence [`LICENSE.md`](data/shot-grammar/LICENSE.md) · Patents
[`PATENTS.md`](data/shot-grammar/PATENTS.md) · Trademarks
[`TRADEMARK.md`](data/shot-grammar/TRADEMARK.md)

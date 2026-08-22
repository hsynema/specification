# What ships, and what does not

The strategy only works if the format is genuinely free and genuinely complete in public.
It also only pays if four things stay private. Those two facts are not in tension — they
are the same design — but the line between them has to be drawn once, precisely, and never
drifted across in a hurry before a deadline.

**The test:** anything an implementer needs in order to conform ships. Anything a
*competitor* needs in order to replace the registry, the mark, or the service does not.

---

## Ships — the whole format, no reservations

| what | why it must be public |
|---|---|
| The format specification | A spec held back is not a standard. No body adopts a document it cannot redistribute. |
| The codec design | Same. An encoder nobody can write is not an encoder. |
| The Westwyrd Shot Grammar and every vocabulary table | The vocabularies *are* the interoperation. Holding one back creates the fork you are trying to prevent. |
| The reference encoder, decoder and verifier | The single most common way a format dies is arriving as prose. This is also what makes the support contract credible rather than a hostage situation. |
| The **conformance vectors** — fixtures with known roots, and forgeries each refused at a named stage | Anyone must be able to prove their own implementation correct without asking permission. A conformance suite you have to buy is a tollbooth, and tollbooths get forked. |
| The patent grant and licence | Irrevocable and up front, or legal never lets engineering start. |
| The industry taxonomy, notation grammars and studio registry mirror | Assembled from public sources. Publishing it back is the cheapest credibility available. |
| The boundary lists | The honesty is the product. It is also the hardest thing here for a competitor to copy. |

## Stays — the four businesses

| what | why it stays | what would happen if it shipped |
|---|---|---|
| **The registry backend** — allocation logic, holder records, billing, the authoritative namespace | Layer 1. A registry is an operated service, not a file. | Anyone stands up a rival namespace and the identifiers stop meaning one thing, which is the only thing identifiers are for. |
| **The conformance test *harness* and the mark** | Layer 2. The vectors are public so anyone can self-check; the *certification* — running the suite as a disinterested party and licensing the mark — is the service. | The mark becomes self-asserted, and a self-asserted mark is worth nothing to the studio relying on it. |
| **The verification service** — orchestration, scheduling, the GPU fleet, the re-synthesis pipeline at scale | Layer 3, the revenue engine. The *protocol* for verification is public; running it for other people is the business. | The margin, immediately. The protocol being public is what makes the service trustworthy; the operation being private is what makes it a business. |
| **The adoption strategy** — `westwyrd/adoption/`, `docs/WESTWYRD-ADOPTION.md` | Not commercial sensitivity. It names targets, entry points, decision-maker functions, and explicit *do-not* lines per company. | Actively harmful. Publishing a document that says how to approach Disney and what not to say to Sony ends both conversations before they start. **This is the one item on the list that damages the project rather than merely costing money.** |

### Also private, for ordinary reasons

Encoder performance work beyond the reference path; the golden-vector *generator* (the
vectors ship, the tool that mints new ones does not); customer and pipeline telemetry;
anything under `attestations/`, `genesis/` or `contracts/` that carries keys, wallet
identifiers or machine credentials.

## The rule for future decisions

When something new is written, ask which of these it is:

1. **Needed to conform** → ships, no exceptions, no delay.
2. **Needed to compete with the registry, the mark or the service** → stays.
3. **Neither** → ships by default. The reputational return on being the open party
   compounds, and the things worth keeping are already on the short list above.

A specification with a private annex is not a specification. If a decision feels close,
it belongs in category 1 — the four items in the stay column are the whole list, and
lengthening it is how a standard quietly becomes a product.

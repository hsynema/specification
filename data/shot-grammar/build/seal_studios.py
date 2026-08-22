"""Serials, digests, and a hash chain over the studio grammar records.

Three identifiers, doing three jobs that people routinely try to make one identifier do:

    serial     SG-014      identity. Allocated once, never reused, never re-derived.
    digest     16 hex      state. Changes if and only if the recorded facts change.
    link       64 hex      position in history. Chains one revision to the one before.

**The serial encodes nothing.** Not the tier, not the parent, not the ISDCF code — a
serial that encodes a fact becomes wrong the day the fact changes, and then you have an
identifier that lies and a migration nobody wants to run. Disney could sell a label
tomorrow; SG-002 would still be Disney's row.

**The digest is the whole point.** It is taken over a canonical form of everything this
dataset asserts about one studio: its metadata, its notation rows, its style rows, its
standards-body participation. Add a body, correct a code, downgrade a style row's
confidence — the digest moves, and the move is the evidence that something changed.
Nothing else has to be remembered or diffed.

**The chain is borrowed, deliberately.** `NodeDAWNKit/Syn/LedgerChain.swift` already
solved this for the render ledger, and it states the honest limit better than a comment
here could:

    link = SHA256(prev ‖ 0x1D ‖ canonical)

with fields joined by 0x1E and lists by 0x1F. Same separators, same reasoning — the 0x1D
between prev and canonical exists because without it a canonical form beginning with hex
could be split differently against a shorter prev and produce a colliding preimage.

And the same limit applies, restated because it matters more here, not less:
**tamper-evident is not tamper-proof.** Anyone who can write `ledger.csv` can rewrite
row 12 and recompute every link after it, and the result verifies perfectly. The chain
becomes evidence at the moment somebody else has seen a head. `HEAD` is written as a
separate file for exactly that reason — it is the one value worth committing, quoting in
a message, or handing to anyone who might later need to disagree with you about what this
dataset said in 2026.

Usage:

    python3 build/seal_studios.py --allocate    assign serials to studios that lack one
    python3 build/seal_studios.py --seal        append a row for every changed digest
    python3 build/seal_studios.py --verify      recompute everything, report drift (default)
"""

from __future__ import annotations

import csv
import hashlib
import io
import sys
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIOS = ROOT / "studios"

RS = "\x1e"  # record separator — between fields of a canonical form
US = "\x1f"  # unit separator  — between elements of a list within a field
GS = "\x1d"  # group separator — between prev and canonical, in the link

SERIAL_PREFIX = "SG"
DIGEST_CHARS = 16


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def link(prev: str, canonical: str) -> str:
    """link = SHA256(prev ‖ 0x1D ‖ canonical). Same construction as LedgerChain.link."""
    h = hashlib.sha256()
    h.update(prev.encode("utf-8"))
    h.update(GS.encode("utf-8"))
    h.update(canonical.encode("utf-8"))
    return h.hexdigest()


def read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def canonical_for(
    meta: dict[str, str],
    serial: str,
    notation: list[dict[str, str]],
    style: list[dict[str, str]],
    bodies: list[dict[str, str]],
) -> str:
    """Everything the dataset asserts about one studio, in one order-independent string.

    Sorted rather than file-ordered, because a reordered CSV is the same claim. A value
    type over the fields that matter, not the CSV text, for the reason LedgerChain gives:
    two writers serialising identical facts with different formatting must not produce
    different digests, or the chain breaks on whitespace and reports it as tampering.
    """
    nrows = sorted(
        US.join((r["scheme"], r["key"], r["value"], r["status"])) for r in notation
    )
    srows = sorted(
        US.join((r["axis"], r["taxonomy_id"], r["value"], r["confidence"])) for r in style
    )
    brows = sorted(
        US.join((r["body"], r["role"], r["since"])) for r in bodies
    )
    return RS.join(
        [
            serial,
            meta["slug"],
            meta["isdcf_code"],
            meta["tier"],
            meta["parent"],
            RS.join(nrows),
            RS.join(srows),
            RS.join(brows),
        ]
    )


def digests() -> dict[str, dict[str, str]]:
    """Current serial, digest and group digest for every studio, computed fresh.

    Two digests, because "did Disney's shot grammar change?" has two honest answers.
    `digest` covers the studio's own record. `group_digest` folds in every descendant, so
    a change at Pixar moves Walt Disney Studios' group digest without touching its own —
    and the ledger records both moves, at their own serials, on the same day.

    Collapsing the two would lose the distinction between a studio changing its practice
    and a label it owns changing theirs, which is precisely the distinction anyone
    tracking this over years will want back.
    """
    meta_rows = read(STUDIOS / "studios.csv")
    notation = read(STUDIOS / "notation.csv")
    style = read(STUDIOS / "style.csv")
    bodies = read(STUDIOS / "bodies.csv")
    serials = {r["slug"]: r["serial"] for r in read(STUDIOS / "serials.csv")}

    out: dict[str, dict[str, str]] = {}
    children: dict[str, list[str]] = {}
    for meta in meta_rows:
        slug = meta["slug"]
        serial = serials.get(slug, "")
        canonical = canonical_for(
            meta,
            serial,
            [r for r in notation if r["slug"] == slug],
            [r for r in style if r["slug"] == slug],
            [r for r in bodies if r["slug"] == slug],
        )
        full = sha256(canonical)
        out[slug] = {
            "serial": serial,
            "digest": full[:DIGEST_CHARS],
            "digest_full": full,
            "canonical_len": str(len(canonical)),
        }
        if meta["parent"]:
            children.setdefault(meta["parent"], []).append(slug)

    def group(slug: str, seen: frozenset[str] = frozenset()) -> str:
        if slug in seen:
            raise ValueError(f"parent cycle through '{slug}' in studios.csv")
        seen = seen | {slug}
        parts = [out[slug]["digest_full"]] + sorted(
            group(c, seen) for c in children.get(slug, [])
        )
        return sha256(RS.join(parts))

    for slug in out:
        out[slug]["group_digest"] = group(slug)[:DIGEST_CHARS]
    return out


def allocate(today: str) -> int:
    """Assign a serial to every studio that lacks one. Append-only; never reallocates."""
    path = STUDIOS / "serials.csv"
    header = ["slug", "serial", "allocated", "retired", "note"]
    existing = read(path)
    taken = {r["serial"] for r in existing}
    by_slug = {r["slug"] for r in existing}

    n = max((int(s.split("-")[1]) for s in taken), default=0)
    added = []
    for meta in read(STUDIOS / "studios.csv"):
        if meta["slug"] in by_slug:
            continue
        n += 1
        added.append(
            {
                "slug": meta["slug"],
                "serial": f"{SERIAL_PREFIX}-{n:03d}",
                "allocated": today,
                "retired": "",
                "note": "",
            }
        )
    if added:
        write(path, header, existing + added)
    print(f"serials: {len(existing)} existing, {len(added)} allocated")
    return len(added)


def load_ledger() -> list[dict[str, str]]:
    return read(STUDIOS / "ledger.csv")


def verify(ledger: list[dict[str, str]]) -> tuple[int | None, str]:
    """Recompute every link. Returns (index of first break or None, head)."""
    prev = ""
    for i, row in enumerate(ledger):
        canonical = RS.join(
            (row["rev"], row["serial"], row["slug"], row["digest"], row["group_digest"], row["date"])
        )
        expected = link(prev, canonical)
        if row["prev"] != prev or row["link"] != expected:
            return i, prev
        prev = row["link"]
    return None, prev


def seal(today: str) -> int:
    header = ["rev", "date", "serial", "slug", "digest", "group_digest", "prev", "link"]
    ledger = load_ledger()

    broke, _ = verify(ledger)
    if broke is not None:
        print(f"refusing to seal: chain BREAK at row {broke} — every link after it is unverifiable")
        return -1

    latest: dict[str, tuple[str, str]] = {}
    for row in ledger:
        latest[row["slug"]] = (row["digest"], row["group_digest"])

    current = digests()
    missing = [s for s, d in current.items() if not d["serial"]]
    if missing:
        print(f"refusing to seal: {len(missing)} studio(s) have no serial — run --allocate first")
        for s in missing:
            print(f"  {s}")
        return -1

    prev = ledger[-1]["link"] if ledger else ""
    rev = len(ledger)
    appended = []
    for slug in sorted(current):
        d = current[slug]
        if latest.get(slug) == (d["digest"], d["group_digest"]):
            continue
        canonical = RS.join(
            (str(rev), d["serial"], slug, d["digest"], d["group_digest"], today)
        )
        lk = link(prev, canonical)
        appended.append(
            {
                "rev": str(rev),
                "date": today,
                "serial": d["serial"],
                "slug": slug,
                "digest": d["digest"],
                "group_digest": d["group_digest"],
                "prev": prev,
                "link": lk,
            }
        )
        prev = lk
        rev += 1

    if appended:
        write(STUDIOS / "ledger.csv", header, ledger + appended)
        (STUDIOS / "HEAD").write_text(prev + "\n", encoding="utf-8")
        print(f"sealed {len(appended)} revision(s); HEAD -> {prev[:16]}…")
    else:
        print("nothing changed; no revision sealed")
    return len(appended)


def report() -> int:
    ledger = load_ledger()
    broke, head = verify(ledger)
    current = digests()

    latest: dict[str, dict[str, str]] = {}
    for row in ledger:
        latest[row["slug"]] = row

    drifted = [
        s for s, d in sorted(current.items())
        if s not in latest
        or latest[s]["digest"] != d["digest"]
        or latest[s]["group_digest"] != d["group_digest"]
    ]

    print(f"{len(current)} studios · {len(ledger)} ledger rows")
    if broke is not None:
        print(f"  BREAK at row {broke} — every link after it is unverifiable")
    elif ledger:
        print(f"  chain holds · HEAD {head}")
    else:
        print("  no chain yet — run --seal")

    if drifted:
        print(f"\n{len(drifted)} studio(s) differ from their sealed digest:")
        for s in drifted:
            row = latest.get(s, {})
            for kind in ("digest", "group_digest"):
                was, now = row.get(kind, "—"), current[s][kind]
                if was != now:
                    print(f"  {current[s]['serial'] or '???'}  {s:30} {kind:12} {was} -> {now}")
        return 1
    if ledger:
        print("  every studio matches its sealed digest")
    return 0 if broke is None else 1


def main() -> int:
    args = set(sys.argv[1:])
    today = next(
        (a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--date=")),
        _date.today().isoformat(),
    )
    if "--allocate" in args:
        allocate(today)
        return 0
    if "--seal" in args:
        return 0 if seal(today) >= 0 else 1
    return report()


if __name__ == "__main__":
    raise SystemExit(main())

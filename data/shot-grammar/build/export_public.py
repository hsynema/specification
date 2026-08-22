"""Stage the publishable tree, and refuse to stage anything on the private list.

The split is specified in PUBLICATION-SPLIT.md. This script is that document made
executable, because a policy nobody can run is a policy somebody will forget at 2am before
a deadline.

It is deliberately a *deny* list with an *allow* list on top, and it fails closed: a path
matching nothing is refused rather than shipped, so a new directory cannot be published by
accident. Adding something to the public tree is a decision somebody has to make on purpose.

    python3 build/export_public.py --out /tmp/hsynema-public
    python3 build/export_public.py --check          list what would ship, stage nothing

It stages. It does not commit, and it does not push.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent

#: Never published. Ordered most-dangerous first — see PUBLICATION-SPLIT.md.
DENY = (
    "westwyrd/adoption",          # names targets and do-not lines; harmful, not merely costly
    "__pycache__",
    ".ots",                        # the proof travels with the stamp, separately
)

#: Published from the dataset. Anything not matching is refused, not shipped.
ALLOW_PREFIXES = (
    "_schema/", "taxonomy/", "notation/", "registries/", "westwyrd/", "build/",
    "studios/",
)
ALLOW_FILES = (
    "README.md", "LICENSE.md", "PATENTS.md", "TRADEMARK.md",
    "PUBLICATION-SPLIT.md", "CORPUS-STAMP.json", "CORPUS-STAMP-BOUND.json",
    "loader.py", ".gitignore",
)

#: Published from the wider repo, by path relative to it.
ALLOW_DOCS = (
    "docs/WESTWYRD-SHOT-GRAMMAR.md",
    "docs/SHOT-GRAMMAR.md",
    "docs/STANDARDS.md",
    "docs/MEDIA-RENDER-TAXONOMY.md",
)

#: Named here so the refusal is explicit rather than incidental.
NEVER_FROM_REPO = ("docs/WESTWYRD-ADOPTION.md",)

#: Files that ship, but only after rows describing private material are dropped. The
#: manifest and the source list both index the whole dataset by design, so they name the
#: adoption tables — which discloses the strategy's shape even though no row of it ships.
FILTER_ROWS = {
    "_schema/schema.csv": lambda row: "adoption" not in row[0],
    "_schema/sources.csv": lambda row: row[0] != "westwyrd-adoption",
}


def classify(rel: str) -> tuple[bool, str]:
    for d in DENY:
        if d in rel:
            return False, f"denied — matches {d!r}"
    if rel in ALLOW_FILES:
        return True, "allowed file"
    for p in ALLOW_PREFIXES:
        if rel.startswith(p):
            return True, f"allowed under {p}"
    return False, "no rule matches — refused (this script fails closed)"


def collect() -> tuple[list[tuple[Path, str]], list[tuple[str, str]]]:
    ship: list[tuple[Path, str]] = []
    held: list[tuple[str, str]] = []

    for path in sorted(ROOT.rglob("*")):
        if path.is_dir():
            continue
        rel = str(path.relative_to(ROOT))
        ok, why = classify(rel)
        (ship.append((path, f"data/shot-grammar/{rel}")) if ok else held.append((rel, why)))

    for rel in ALLOW_DOCS:
        p = REPO / rel
        if p.exists():
            ship.append((p, rel))
        else:
            held.append((rel, "listed for publication but missing from the repo"))

    for rel in NEVER_FROM_REPO:
        if (REPO / rel).exists():
            held.append((rel, "denied — private by policy, see PUBLICATION-SPLIT.md"))

    return ship, held


def main() -> int:
    args = sys.argv[1:]
    check = "--check" in args
    out = next((Path(a.split("=", 1)[1]) for a in args if a.startswith("--out=")), None)

    ship, held = collect()

    # A leak check over bytes rather than paths. Naming the strategy in prose is fine and
    # sometimes required — PUBLICATION-SPLIT.md has to say what it holds back. Reproducing
    # its content is not, and the two are told apart by whether the file is one we filter.
    ALLOWED_TO_MENTION = {
        "data/shot-grammar/PUBLICATION-SPLIT.md",
        "data/shot-grammar/build/export_public.py",
    }
    leaked = []
    for src, dest in ship:
        if src.suffix not in (".csv", ".md", ".py", ".json") or dest in ALLOWED_TO_MENTION:
            continue
        text = src.read_text(encoding="utf-8", errors="ignore")
        rel = dest.removeprefix("data/shot-grammar/")
        if rel in FILTER_ROWS:
            continue
        for needle in ("WESTWYRD-ADOPTION", "westwyrd/adoption", "forcing-function"):
            if needle in text:
                leaked.append((dest, needle))

    print(f"ship {len(ship)} · hold {len(held)}")
    print()
    for rel, why in held:
        print(f"  HOLD  {rel:52} {why}")

    if leaked:
        print("\nREFUSING — private content found inside a file marked for publication:")
        for dest, needle in leaked:
            print(f"  {dest}: contains {needle!r}")
        return 1

    h = hashlib.sha256()
    for _, dest in sorted(ship, key=lambda t: t[1]):
        h.update(dest.encode())
    print(f"\npublished path-set digest {h.hexdigest()[:16]}")

    if check or out is None:
        print("\n--check (or no --out): nothing staged.")
        return 0

    if out.exists():
        shutil.rmtree(out)
    import csv, io
    filtered = 0
    for src, dest in ship:
        target = out / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        rel = dest.removeprefix("data/shot-grammar/")
        keep = FILTER_ROWS.get(rel)
        if keep is None:
            shutil.copy2(src, target)
            continue
        with src.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        head, body = rows[0], [r for r in rows[1:] if keep(r)]
        filtered += len(rows) - 1 - len(body)
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerows([head] + body)
        target.write_text(buf.getvalue(), encoding="utf-8")
    if filtered:
        print(f"dropped {filtered} row(s) describing private material")
    print(f"staged {len(ship)} file(s) into {out}")
    print("staged only — not committed, not pushed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

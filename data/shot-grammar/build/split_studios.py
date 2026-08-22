"""Fan the three flat studio tables out into one directory per studio.

The flat tables under `studios/` are the source of truth — they are what a script wants
to read, and they are where edits go. The per-studio directories are a projection of
them, regenerated rather than maintained, so the two cannot drift apart. Nothing reads
the directories that could read the tables instead.

    python3 build/split_studios.py            regenerate
    python3 build/split_studios.py --check    fail if a regeneration would change anything

Serials, digests and history come from build/seal_studios.py and are carried through into
each directory. Run the seal first; this script only projects what is already there.
"""

from __future__ import annotations

import csv
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIOS = ROOT / "studios"


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), [dict(r) for r in reader]


def render(header: list[str], rows: list[dict[str, str]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def build() -> dict[Path, str]:
    meta_header, meta_rows = read(STUDIOS / "studios.csv")
    not_header, not_rows = read(STUDIOS / "notation.csv")
    sty_header, sty_rows = read(STUDIOS / "style.csv")
    bod_header, bod_rows = read(STUDIOS / "bodies.csv")
    led_header, led_rows = read(STUDIOS / "ledger.csv")
    _, ser_rows = read(STUDIOS / "serials.csv")
    serials = {r["slug"]: r["serial"] for r in ser_rows}

    files: dict[Path, str] = {}
    index: list[dict[str, str]] = []

    for meta in meta_rows:
        slug = meta["slug"]
        notation = [r for r in not_rows if r["slug"] == slug]
        style = [r for r in sty_rows if r["slug"] == slug]
        bodies = [r for r in bod_rows if r["slug"] == slug]
        history = [r for r in led_rows if r["slug"] == slug]

        files[STUDIOS / slug / "meta.csv"] = render(meta_header, [meta])
        files[STUDIOS / slug / "notation.csv"] = render(not_header, notation)
        files[STUDIOS / slug / "style.csv"] = render(sty_header, style)
        files[STUDIOS / slug / "bodies.csv"] = render(bod_header, bodies)
        if led_header:
            files[STUDIOS / slug / "history.csv"] = render(led_header, history)

        documented = sum(1 for r in notation if r["status"] == "documented")
        index.append(
            {
                "serial": serials.get(slug, ""),
                "slug": slug,
                "name": meta["name"],
                "tier": meta["tier"],
                "isdcf_code": meta["isdcf_code"],
                "digest": history[-1]["digest"] if history else "",
                "group_digest": history[-1]["group_digest"] if history else "",
                "revisions": str(len(history)),
                "notation_rows": str(len(notation)),
                "documented_rows": str(documented),
                "style_rows": str(len(style)),
                "body_rows": str(len(bodies)),
                "directory": f"studios/{slug}",
            }
        )

    index_header = [
        "serial", "slug", "name", "tier", "isdcf_code", "digest", "group_digest", "revisions",
        "notation_rows", "documented_rows", "style_rows", "body_rows", "directory",
    ]
    files[STUDIOS / "index.csv"] = render(index_header, index)
    return files


def main() -> int:
    check = "--check" in sys.argv
    files = build()

    if check:
        stale = [p for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print(f"{len(stale)} file(s) would change:")
            for p in sorted(stale):
                print(f"  {p.relative_to(ROOT)}")
            return 1
        print(f"{len(files)} generated file(s) are current")
        return 0

    for directory in STUDIOS.iterdir():
        if directory.is_dir():
            shutil.rmtree(directory)

    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    dirs = len({p.parent for p in files} - {STUDIOS})
    print(f"wrote {len(files)} file(s) across {dirs} studio director" + ("y" if dirs == 1 else "ies"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

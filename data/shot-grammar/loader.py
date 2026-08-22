"""Reader for the shot-grammar dataset.

The dataset is CSV, and CSV is the source of truth — this module reads it, it does not
own it. Three axes, deliberately kept apart because they are known to different degrees:

    taxonomy/    the shot vocabulary and its notation. Industry-wide, not studio-specific.
    notation/    parseable identifier grammars. Field order, padding, regex.
    studios/     what is attributable to one studio, tagged with how well it is known.

Every row carries `provenance`, and rows do not mix. A row that says Netflix requires a
'v' prefix on version numbers and a row that says A24 favours motivated practical light
are not the same kind of claim, and `Row.is_spec` is the test that separates them.

    from loader import load
    g = load()
    g.abbrev("ECU")                       -> the extreme close-up row
    g.parse("netflix-vfx", "AGM_104_TCC_067_0010_comp_NFX_v001")
    g.format("netflix-vfx", showID="AGM", shotID="0010", version="v001", ...)
    g.studio("a24").style                 -> that studio's style rows
    g.validate()                          -> list of problems, empty when clean
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path

ROOT = Path(__file__).resolve().parent

#: Provenance values that mean "someone wrote this down and meant it as a rule".
SPEC_PROVENANCE = {"published-spec", "industry-standard"}

#: Local status values, borrowed from docs/SHOT-GRAMMAR.md so the two agree.
LOCAL_STATUS = {"GROUNDED", "UNVERIFIED", "OURS", "EXCLUDED"}

#: Values in studios/notation.csv `scheme` that name a kind of finding rather than a
#: naming grammar. Kept explicit so a mistyped scheme name is still an error.
_NON_SCHEME_KEYS = {
    "capture-standard",
    "house-practice",
    "open-source",
    "prime-video-delivery",
    "apple-immersive-video",
    "production-naming-spec",
    "post-delivery-spec",
}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


@dataclass(frozen=True)
class Row:
    """One taxonomy entry — a term, its notation, and how far it can be trusted here."""

    data: dict[str, str]

    def __getattr__(self, name: str) -> str:
        try:
            return self.data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @property
    def is_spec(self) -> bool:
        """True when this row states a rule rather than reports an impression."""
        return self.data.get("provenance", "") in SPEC_PROVENANCE

    @property
    def renders(self) -> bool:
        """True when the local renderer is known to honour this term."""
        return self.data.get("local_status") == "GROUNDED"

    @property
    def accepts_set(self) -> set[str]:
        raw = self.data.get("accepts", "")
        return set(filter(None, raw.split("|")))


@dataclass
class Scheme:
    """A parseable identifier grammar: field order, separators, patterns."""

    meta: dict[str, str]
    fields: list[dict[str, str]] = dc_field(default_factory=list)
    vocab: dict[str, list[dict[str, str]]] = dc_field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.meta["scheme"]

    @property
    def delimiter(self) -> str:
        return self.meta.get("delimiter", "_")

    @property
    def parseable(self) -> bool:
        """Whether a name in this scheme can be split back into its fields.

        Three ways a scheme fails this. It may have optional fields, so a short name is
        ambiguous (ETC). Its fields may not be delimited at all, so there is nothing to
        split on (the slates — 24A is two fields and one token). Or its fields may be
        inputs to a digest rather than substrings of the result (the cache key), where
        the direction is one-way by construction.
        """
        return self.meta.get("parseable", "yes") == "yes"

    def parse(self, name: str) -> dict[str, str]:
        """Split a name into its fields, positionally.

        The ETC spec warns that automated parsing of file names is risky and that
        embedded metadata is the safer route. It is offered here because the workflow
        this dataset serves is people reading names, and refused wherever it would be a
        guess rather than a read.
        """
        if not self.parseable:
            raise ValueError(
                f"{self.id} is not parseable — see Scheme.parseable. Match against each "
                "field's `pattern` instead, or read the metadata the name stands in for."
            )
        parts = name.split(self.delimiter)
        if len(parts) != len(self.fields):
            raise ValueError(
                f"{self.id} expects {len(self.fields)} fields, got {len(parts)}"
            )
        return {f["field"]: p for f, p in zip(self.fields, parts)}

    def format(self, **values: str) -> str:
        """Join field values in the scheme's order.

        A missing optional field still emits its separator, per ETC §3.1: given
        `a_b_c` with b absent, the name is `a__c`, not `a_c`.
        """
        out = []
        for f in self.fields:
            name = f["field"]
            if name in values:
                out.append(str(values[name]))
            elif f["required"] in ("yes", "required"):
                raise ValueError(f"{self.id}: field '{name}' is required")
            else:
                out.append("")
        return self.delimiter.join(out)

    def check(self, **values: str) -> list[str]:
        """Test each supplied value against its field's regex. Returns problems."""
        problems = []
        by_name = {f["field"]: f for f in self.fields}
        for name, value in values.items():
            f = by_name.get(name)
            if f is None:
                problems.append(f"{self.id}: no field named '{name}'")
                continue
            pattern = f.get("pattern", "")
            if pattern and not re.fullmatch(pattern, str(value)):
                problems.append(
                    f"{self.id}.{name}: '{value}' does not match {pattern}"
                )
        return problems


@dataclass
class Studio:
    meta: dict[str, str]
    notation: list[dict[str, str]] = dc_field(default_factory=list)
    style: list[dict[str, str]] = dc_field(default_factory=list)
    bodies: list[dict[str, str]] = dc_field(default_factory=list)
    #: Every sealed revision of this studio's record, oldest first.
    history: list[dict[str, str]] = dc_field(default_factory=list)
    serial: str = ""

    @property
    def slug(self) -> str:
        return self.meta["slug"]

    @property
    def documented(self) -> list[dict[str, str]]:
        """Notation rows a studio actually published, as opposed to contributed to."""
        return [r for r in self.notation if r["status"] == "documented"]

    @property
    def sealed_digest(self) -> str:
        """The digest as of the last seal. Compare against build/seal_studios.digests()
        to learn whether the record has moved since — that comparison is the whole
        traceability mechanism, and it lives in the build script, not here."""
        return self.history[-1]["digest"] if self.history else ""

    @property
    def revisions(self) -> int:
        return len(self.history)


@dataclass
class Grammar:
    taxonomy: list[Row]
    schemes: dict[str, Scheme]
    studios: dict[str, Studio]
    registries: dict[str, list[dict[str, str]]]
    #: The Westwyrd Shot Grammar tables — the SYN-layer vocabulary for H.SYN.EMA.
    #: Kept in its own namespace because it is a proposal against a named format, not
    #: part of the industry record the rest of this dataset catalogues.
    westwyrd: dict[str, list[dict[str, str]]]
    sources: dict[str, dict[str, str]]
    enums: dict[str, dict[str, str]]
    ledger: list[dict[str, str]] = dc_field(default_factory=list)
    #: The published chain head. The one value worth quoting to a third party — see
    #: build/seal_studios.py on why a chain nobody has witnessed proves only that the
    #: file agrees with itself.
    head: str = ""

    # -- lookup ---------------------------------------------------------------

    def by_id(self, term_id: str) -> Row | None:
        return next((r for r in self.taxonomy if r.id == term_id), None)

    def abbrev(self, code: str) -> Row | None:
        """Resolve a notation abbreviation, aliases included. Case-insensitive."""
        want = code.strip().upper()
        for r in self.taxonomy:
            if r.data.get("abbrev", "").upper() == want:
                return r
        for r in self.taxonomy:
            aliases = (a.strip().upper() for a in r.data.get("aliases", "").split("|"))
            if want in aliases:
                return r
        return None

    def category(self, name: str) -> list[Row]:
        return [r for r in self.taxonomy if r.data.get("category") == name]

    def renderable(self, category: str | None = None) -> list[Row]:
        rows = self.category(category) if category else self.taxonomy
        return [r for r in rows if r.renders]

    def studio(self, slug: str) -> Studio | None:
        return self.studios.get(slug)

    def by_serial(self, serial: str) -> Studio | None:
        """Resolve a studio by its permanent serial — the identifier that outlives
        renames, reorganisations and sales."""
        return next((s for s in self.studios.values() if s.serial == serial), None)

    def parse(self, scheme: str, name: str) -> dict[str, str]:
        return self.schemes[scheme].parse(name)

    def format(self, scheme: str, **values: str) -> str:
        return self.schemes[scheme].format(**values)

    def legal_carry(self, from_id: str, to_id: str) -> bool:
        """Can clip B's camera move begin where clip A's left off, across a carry?

        docs/SHOT-GRAMMAR.md §VI: an orbit handing into a locked-off static is a visible
        stop. Across a cut the constraint lifts entirely, because nothing is carried.
        """
        a, b = self.by_id(from_id), self.by_id(to_id)
        if a is None or b is None:
            raise KeyError(f"unknown camera term: {from_id!r} or {to_id!r}")
        return a.data.get("hands_forward", "") in b.accepts_set

    # -- validation -----------------------------------------------------------

    def validate(self) -> list[str]:
        problems: list[str] = []

        seen: dict[str, str] = {}
        for r in self.taxonomy:
            if r.id in seen:
                problems.append(f"duplicate taxonomy id: {r.id}")
            seen[r.id] = r.data.get("category", "")

            status = r.data.get("local_status", "")
            if status and status not in LOCAL_STATUS:
                problems.append(f"{r.id}: unknown local_status '{status}'")

            key = r.data.get("source_key", "")
            if key and key not in self.sources:
                problems.append(f"{r.id}: source_key '{key}' is not in _schema/sources.csv")

            for motion in r.accepts_set:
                if motion not in self.enums.get("motion", {}):
                    problems.append(f"{r.id}: accepts '{motion}' is not a motion value")
            hands = r.data.get("hands_forward", "")
            if hands and hands not in self.enums.get("motion", {}):
                problems.append(f"{r.id}: hands_forward '{hands}' is not a motion value")

        for scheme in self.schemes.values():
            for f in scheme.fields:
                pattern = f.get("pattern", "")
                if not pattern:
                    continue
                try:
                    re.compile(pattern)
                except re.error as exc:
                    problems.append(f"{scheme.id}.{f['field']}: bad regex — {exc}")
            # A field may have alternate forms, given as '1' and '1b'. They occupy one
            # position in the name, so they count once — the ETC Show ID has a feature
            # form and an episodic form and is still the first field either way.
            positions = {f["order"].rstrip("abcdefgh") for f in scheme.fields}
            declared = scheme.meta.get("field_count", "")
            if declared and declared.isdigit() and int(declared) != len(positions):
                problems.append(
                    f"{scheme.id}: schemes.csv declares {declared} fields, "
                    f"fields.csv defines {len(positions)} positions"
                )
            example = scheme.meta.get("example", "")
            if example and scheme.parseable:
                try:
                    scheme.parse(example)
                except ValueError as exc:
                    problems.append(f"{scheme.id}: example does not parse — {exc}")

        codes = {r["code"] for r in self.registries.get("isdcf-studio-codes", [])}
        for s in self.studios.values():
            code = s.meta.get("isdcf_code", "")
            if code and code not in codes:
                problems.append(f"{s.slug}: isdcf_code '{code}' is not in the registry")
            for row in s.notation + s.style + s.bodies:
                key = row.get("source_key", "")
                if key and key not in self.sources:
                    problems.append(f"{s.slug}: source_key '{key}' is unknown")
            for row in s.style:
                term = row.get("taxonomy_id", "")
                if term and self.by_id(term) is None:
                    problems.append(f"{s.slug}: taxonomy_id '{term}' does not exist")
            for row in s.notation:
                scheme = row.get("scheme", "")
                if scheme in self.schemes:
                    continue
                # Not every key in the notation table names a scheme — capture-standard,
                # open-source and production-naming-spec are categories of finding, not
                # grammars. They are legal; a typo'd scheme name is not, and the two are
                # only distinguishable against this list.
                if scheme not in _NON_SCHEME_KEYS:
                    problems.append(f"{s.slug}: '{scheme}' is neither a scheme nor a known finding kind")

        serials: dict[str, str] = {}
        for s in self.studios.values():
            if not s.serial:
                problems.append(f"{s.slug}: no serial allocated — run build/seal_studios.py --allocate")
                continue
            if s.serial in serials:
                problems.append(f"serial {s.serial} is claimed by both {serials[s.serial]} and {s.slug}")
            serials[s.serial] = s.slug

        for name, rows in self.westwyrd.items():
            for i, row in enumerate(rows):
                for key in ("source", "origin"):
                    val = row.get(key, "")
                    if val and val not in self.sources:
                        problems.append(f"westwyrd/{name}.csv row {i}: {key} '{val}' is unknown")
                term = row.get("taxonomy_file", "")
                for path in filter(None, term.split("|")):
                    if not (ROOT / path).exists():
                        problems.append(f"westwyrd/{name}.csv row {i}: taxonomy_file '{path}' missing")

        prev = ""
        for i, row in enumerate(self.ledger):
            if row["prev"] != prev:
                problems.append(f"ledger row {i}: prev does not match the previous link")
                break
            prev = row["link"]
            if row["slug"] not in self.studios:
                problems.append(f"ledger row {i}: unknown studio '{row['slug']}'")
        if self.ledger and self.head and prev != self.head:
            problems.append("HEAD does not match the last link in ledger.csv")

        return problems


def load(root: Path | str = ROOT) -> Grammar:
    root = Path(root)

    taxonomy = [Row(r) for f in sorted((root / "taxonomy").glob("*.csv")) for r in _read(f)]

    sources = {r["source_key"]: r for r in _read(root / "_schema" / "sources.csv")}

    enums: dict[str, dict[str, str]] = {}
    for r in _read(root / "_schema" / "enums.csv"):
        enums.setdefault(r["enum"], {})[r["value"]] = r["definition"]

    schemes: dict[str, Scheme] = {}
    for meta in _read(root / "notation" / "schemes.csv"):
        schemes[meta["scheme"]] = Scheme(meta=meta)
    for directory in sorted((root / "notation").iterdir()):
        if not directory.is_dir():
            continue
        fields_csv = directory / "fields.csv"
        if fields_csv.exists():
            for row in _read(fields_csv):
                scheme = schemes.setdefault(row["scheme"], Scheme(meta={"scheme": row["scheme"]}))
                scheme.fields.append(row)
        for vocab_csv in sorted(directory.glob("vocab-*.csv")):
            rows = _read(vocab_csv)
            if rows:
                name = vocab_csv.stem.removeprefix("vocab-")
                schemes[rows[0]["scheme"]].vocab[name] = rows

    registries = {
        f.stem: _read(f) for f in sorted((root / "registries").glob("*.csv"))
    }
    # Recursive, because the Westwyrd tables are grouped into subdirectories. Keyed by
    # path relative to westwyrd/ minus the extension, so a nested `group/risks` and a
    # future top-level `risks` could never collide.
    #
    # Some groups are private and are absent from a published tree. Their absence is not
    # an error: this reads what is present rather than asserting what should be.
    westwyrd = {
        str(f.relative_to(root / "westwyrd").with_suffix("")): _read(f)
        for f in sorted((root / "westwyrd").rglob("*.csv"))
    }

    studios = {r["slug"]: Studio(meta=r) for r in _read(root / "studios" / "studios.csv")}
    for name, attr in (("notation", "notation"), ("style", "style"), ("bodies", "bodies")):
        for row in _read(root / "studios" / f"{name}.csv"):
            getattr(studios[row["slug"]], attr).append(row)
    for row in _read(root / "studios" / "serials.csv"):
        if row["slug"] in studios:
            studios[row["slug"]].serial = row["serial"]
    ledger = _read(root / "studios" / "ledger.csv")
    for row in ledger:
        if row["slug"] in studios:
            studios[row["slug"]].history.append(row)

    head_file = root / "studios" / "HEAD"
    head = head_file.read_text(encoding="utf-8").strip() if head_file.exists() else ""

    return Grammar(taxonomy, schemes, studios, registries, westwyrd, sources, enums,
                   ledger, head)


if __name__ == "__main__":
    import sys

    g = load()
    problems = g.validate()
    print(
        f"{len(g.taxonomy)} taxonomy rows · {len(g.schemes)} schemes · "
        f"{len(g.studios)} studios · "
        f"{sum(len(v) for v in g.registries.values())} registry rows · "
        f"{sum(len(v) for v in g.westwyrd.values())} westwyrd rows · "
        f"{len(g.ledger)} sealed revisions"
    )
    if g.head:
        print(f"HEAD {g.head}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print("clean")

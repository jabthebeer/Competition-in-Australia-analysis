"""Load, validate and query the register (``regulation-register/records/*.json``)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .schema import ChangeRecord


def default_register_dir() -> Path:
    """``regulation-register/`` at the repository root (this file is alicia/src/alicia/register/)."""
    return Path(__file__).resolve().parents[4] / "regulation-register"


@dataclass
class LoadResult:
    records: list[ChangeRecord] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _describe(err: ValidationError) -> list[str]:
    out = []
    for e in err.errors():
        where = ".".join(str(p) for p in e["loc"]) or "(record)"
        out.append(f"{where}: {e['msg']}")
    return out


def load_records(records_dir: Path | None = None) -> LoadResult:
    """Read every record; collect problems rather than stopping at the first."""
    records_dir = records_dir or default_register_dir() / "records"
    result = LoadResult()
    seen: dict[str, Path] = {}
    for path in sorted(records_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.problems.append(f"{path.name}: not valid JSON ({exc})")
            continue
        try:
            rec = ChangeRecord.model_validate(data)
        except ValidationError as exc:
            result.problems.extend(f"{path.name}: {m}" for m in _describe(exc))
            continue
        if path.stem != rec.id:
            result.problems.append(f"{path.name}: file name must match id '{rec.id}'")
        if rec.id in seen:
            result.problems.append(f"{path.name}: duplicate id '{rec.id}' (also in {seen[rec.id].name})")
            continue
        seen[rec.id] = path
        result.records.append(rec)
    return result


def write_record(rec: ChangeRecord, records_dir: Path | None = None) -> Path:
    records_dir = records_dir or default_register_dir() / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    path = records_dir / f"{rec.id}.json"
    payload = rec.model_dump(mode="json", exclude_none=False)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def families(records: Iterable[ChangeRecord]) -> dict[str, list[ChangeRecord]]:
    """Records grouped by family, each family sorted by effective date (not-yet-commenced last)."""
    out: dict[str, list[ChangeRecord]] = {}
    for r in records:
        if r.family:
            out.setdefault(r.family, []).append(r)
    for members in out.values():
        members.sort(
            key=lambda r: (
                r.effective_commencement is None,
                r.effective_commencement.date if r.effective_commencement else None,
                r.jurisdiction,
            )
        )
    return dict(sorted(out.items()))


def filter_records(
    records: Iterable[ChangeRecord],
    *,
    jurisdiction: str | None = None,
    direction: str | None = None,
    channel: str | None = None,
    industry: str | None = None,
    family: str | None = None,
    text: str | None = None,
) -> Iterator[ChangeRecord]:
    """Filter by exact fields; ``industry`` matches an ANZSIC code prefix (e.g. '46' matches '4623')."""
    needle = text.lower() if text else None
    for r in records:
        if jurisdiction and r.jurisdiction != jurisdiction.upper():
            continue
        if direction and r.direction != direction:
            continue
        if channel and channel not in r.channels:
            continue
        if industry and not any(i.anzsic.startswith(industry) or industry.startswith(i.anzsic) for i in r.industries):
            continue
        if family and r.family != family:
            continue
        if needle and needle not in " ".join([r.id, r.title, r.summary, r.notes or ""]).lower():
            continue
        yield r

"""Import desk-research candidate records into the register as drafts.

Usage: uv run python scripts/import_candidates.py candidates.json [--reviewed-note TEXT]

Each record is validated against the schema, given review status "draft" with a note on
where it came from, and written to regulation-register/records/<id>.json. Existing files
are not overwritten unless --replace is given (a reviewed record is never replaced).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from alicia.register.catalogue import default_register_dir, write_record
from alicia.register.schema import ChangeRecord

NOTE = (
    "Drafted by AI-assisted desk research on 14-15 October 2026 from the sources cited. "
    "Not yet checked by a person: verify dates, industries and the direction hypothesis before use."
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--replace", action="store_true")
    args = p.parse_args()
    records_dir = default_register_dir() / "records"
    written = skipped = 0
    for raw in json.loads(Path(args.source).read_text(encoding="utf-8")):
        raw.setdefault("review", {"status": "draft", "notes": NOTE})
        rec = ChangeRecord.model_validate(raw)
        path = records_dir / f"{rec.id}.json"
        if path.exists():
            existing = ChangeRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if existing.review.status == "reviewed" or not args.replace:
                skipped += 1
                continue
        write_record(rec, records_dir)
        written += 1
    print(f"Wrote {written} record(s); skipped {skipped} existing.")


if __name__ == "__main__":
    main()

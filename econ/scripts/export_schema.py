"""Write the JSON Schemas for register records and evaluation results to regulation-register/schema/.

Usage: uv run python scripts/export_schema.py
"""

from __future__ import annotations

import json

from regimpact.register import evaluation
from regimpact.register.catalogue import default_register_dir
from regimpact.register.schema import json_schema


def main() -> None:
    out = default_register_dir() / "schema" / "change-record.schema.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(json_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    out = default_register_dir() / "schema" / "evaluation.schema.json"
    out.write_text(json.dumps(evaluation.json_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

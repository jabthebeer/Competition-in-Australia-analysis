"""Record Federal Register API responses used by the offline tests.

Usage: uv run python scripts/record_frl_fixtures.py
Writes tests/fixtures/frl/responses.json: {url: body}. Long version lists are trimmed to the
versions the tests need (the first version, plus any starting 2021-01-01 to 2024-12-31),
keeping each response's structure unchanged. Source: Federal Register of Legislation API.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx

from regimpact.legislation.base import make_client
from regimpact.legislation.frl import FederalRegister
from regimpact.register.schema import Instrument

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "frl" / "responses.json"
CASES = [
    Instrument(title="Mutual Recognition Amendment Act 2021", role="amending"),
    Instrument(
        title="Treasury Laws Amendment (More Competition, Better Prices) Act 2022",
        register_id="C2022A00054",
        role="amending",
    ),
    Instrument(title="Competition and Consumer (Industry Codes—Food and Grocery) Regulations 2024", role="regulation"),
]


def trim(url: str, body: dict) -> dict:
    if "/Versions?" not in url or len(body.get("value", [])) <= 12:
        return body
    keep = [v for i, v in enumerate(body["value"]) if i == 0 or "2021-01-01" <= v["start"][:10] <= "2024-12-31"]
    return {**body, "value": keep}


def main() -> None:
    recorded: dict[str, dict] = {}

    def hook(resp: httpx.Response) -> None:
        resp.read()
        recorded[str(resp.request.url)] = resp.json()

    with make_client() as client:
        client.event_hooks["response"] = [hook]
        reg = FederalRegister()
        for inst in CASES:
            reg.lookup(inst, client)
    out = {
        "recorded_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "source": "https://api.prod.legislation.gov.au/v1/",
        "responses": {u: trim(u, b) for u, b in sorted(recorded.items())},
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Recorded {len(recorded)} responses to {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

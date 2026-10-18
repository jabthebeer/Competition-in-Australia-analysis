"""Run a specification's stages in order and check that every output reproduces byte for byte.

Stages run as separate processes from the ``alicia/`` folder (``python analyses/<analysis>/<script>``),
exactly as each analysis documents. Before a stage runs, the runner records the bytes of every file it
writes; afterwards it reports each file as identical, changed or created.

Pre-registration guard: a stage of kind ``estimate`` (the unblinded, registered run) only runs when every
design and dry-run output of the specification is committed to git and unmodified, so a design cannot be
changed after its estimate has been seen without the change showing in the history.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from .spec import Specification, Stage, analyses_dir

ALICIA = Path(__file__).resolve().parents[3]
REPO = ALICIA.parent


@dataclass(frozen=True)
class OutputCheck:
    path: str
    status: str  # identical, changed, created, missing
    sha256: str | None


@dataclass
class StageResult:
    stage: Stage
    returncode: int
    seconds: float
    outputs: list[OutputCheck] = field(default_factory=list)
    log: str = ""

    @property
    def reproduced(self) -> bool:
        return self.returncode == 0 and all(o.status == "identical" for o in self.outputs)


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def select(spec: Specification, names: list[str] | None = None) -> list[Stage]:
    if not names:
        return list(spec.stages)
    unknown = set(names) - {s.name for s in spec.stages}
    if unknown:
        raise ValueError(f"{spec.id}: no stage named {', '.join(sorted(unknown))}")
    return [s for s in spec.stages if s.name in names]


def design_outputs(spec: Specification) -> list[str]:
    return [p for s in spec.stages if s.kind in ("design", "dry-run") for p in s.writes]


def uncommitted(paths: list[str]) -> list[str]:
    """Paths (relative to alicia/) that are not tracked by git or differ from the committed version."""
    bad = []
    for p in paths:
        rel = f"alicia/{p}" if not p.startswith("../") else p[3:]
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel], cwd=REPO, capture_output=True, text=True
        ).returncode
        clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=REPO).returncode
        if tracked != 0 or clean != 0:
            bad.append(p)
    return bad


def run_stage(spec: Specification, stage: Stage, python: str = sys.executable) -> StageResult:
    before = {p: _sha(ALICIA / p) for p in stage.writes}
    script = analyses_dir() / spec.analysis / stage.script
    t = time.time()
    proc = subprocess.run([python, str(script), *stage.args], cwd=ALICIA, capture_output=True, text=True)
    result = StageResult(stage, proc.returncode, time.time() - t, log=(proc.stdout + proc.stderr)[-4000:])
    for p in stage.writes:
        after = _sha(ALICIA / p)
        if after is None:
            status = "missing"
        elif before[p] is None:
            status = "created"
        else:
            status = "identical" if after == before[p] else "changed"
        result.outputs.append(OutputCheck(p, status, after))
    return result


def run(
    spec: Specification,
    names: list[str] | None = None,
    python: str = sys.executable,
    allow_uncommitted_design: bool = False,
    echo=print,
) -> list[StageResult]:
    stages = select(spec, names)
    if any(s.kind == "estimate" for s in stages) and not allow_uncommitted_design:
        bad = uncommitted(design_outputs(spec))
        if bad:
            raise PermissionError(
                f"{spec.id}: commit the design stage before the registered estimate; uncommitted: {', '.join(bad)}"
            )
    results = []
    for stage in stages:
        echo(f"{spec.id}: {stage.name} ({stage.kind}) ...")
        r = run_stage(spec, stage, python)
        results.append(r)
        for o in r.outputs:
            echo(f"    {o.status:9} {o.path}")
        echo(f"    exit {r.returncode} in {r.seconds:.0f}s")
        if r.returncode != 0:
            echo(r.log)
            break
    return results

"""ABN Bulk Extract (Australian Business Register) as count panels by postcode, state and month.

The weekly extract (data.gov.au dataset ``abn-bulk-extract``, CC BY 3.0 AU) is a snapshot of every
ABN (about 20.6 million): status (active or cancelled) and the date that status began, entity type,
main business location (state and postcode), GST status and date, and names. It has no industry;
industry is inferred from business names (``alicia.pipeline.names``).

Because it is a snapshot, what can be measured is limited:
- cancellations by month are complete for ABNs still cancelled (exits), but an ABN cancelled and
  later reactivated drops out, and ATO bulk cancellations are administrative;
- registrations cannot be recovered: an active ABN's date is when its current active status began,
  so counts by that month are survivors only (the "active since" measures);
- the stock of active ABNs is exact for the snapshot date.
True entry and exit flows need successive snapshots; ``snapshot_summary`` writes a small summary of
each extract processed so flows can be built going forward.

Record-level output (``data/processed/abr_abn/records/``) stays local: it is large and ties ABNs of
sole traders to postcodes. Only aggregate counts are committed.
"""

from __future__ import annotations

import json
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from . import names, schema, store

SOURCE = "abr_abn"
LICENCE = "CC BY 3.0 AU, Australian Business Register (ABN Bulk Extract)"
FILES = ("public_split_1_10.zip", "public_split_11_20.zip")

RE_UPDATED = re.compile(r'<ABR recordLastUpdatedDate="(\d{8})"')
RE_ABN = re.compile(r'<ABN status="(\w+)" ABNStatusFromDate="(\d{8})">(\d+)</ABN>')
RE_ENTITY = re.compile(r"<EntityTypeInd>([^<]*)</EntityTypeInd><EntityTypeText>([^<]*)</EntityTypeText>")
RE_STATE = re.compile(r"<State>([^<]*)</State>")
RE_POSTCODE = re.compile(r"<Postcode>([^<]*)</Postcode>")
RE_GST = re.compile(r'<GST status="(\w+)" GSTStatusFromDate="(\d{8})"')
RE_MAIN = re.compile(r'<NonIndividualName type="MN"><NonIndividualNameText>([^<]*)</NonIndividualNameText>')
RE_OTHER = re.compile(
    r'<NonIndividualName type="(?:BN|TRD|OTN)"><NonIndividualNameText>([^<]*)</NonIndividualNameText>'
)


def entity_group(code: str, text: str) -> str:
    t = text.lower()
    if code == "IND":
        return "individual"
    if "superannuation" in t or "super fund" in t:
        return "super fund"
    if "partnership" in t:
        return "partnership"
    if "trust" in t:
        return "trust"
    if "government" in t or "commonwealth" in t:
        return "government"
    if "company" in t or code in {"PRV", "PUB"}:
        return "company"
    return "other"


def parse_line(line: str) -> dict | None:
    """One <ABR> record (one per line) -> the fields kept. Names are used only to infer industry."""
    abn = RE_ABN.search(line)
    if not abn:
        return None
    ent = RE_ENTITY.search(line)
    code, text = (ent.group(1), ent.group(2)) if ent else ("", "")
    st = RE_STATE.search(line)
    pc = RE_POSTCODE.search(line)
    gst = RE_GST.search(line)
    upd = RE_UPDATED.search(line)
    others = [n.replace("&amp;", "&") for n in RE_OTHER.findall(line)]
    main = RE_MAIN.search(line)
    main_name = main.group(1).replace("&amp;", "&") if main and code != "IND" else None
    return {
        "abn": int(abn.group(3)),
        "status": abn.group(1),
        "status_from": int(abn.group(2)),
        "entity": code,
        "group": entity_group(code, text),
        "state": st.group(1) if st else "",
        "postcode": pc.group(1) if pc else "",
        "gst": gst.group(1) if gst else "",
        "gst_from": int(gst.group(2)) if gst else 0,
        "updated": int(upd.group(1)) if upd else 0,
        "industry": names.classify(main_name, *others),
    }


def parse_member(zip_path: str, member: str, out_dir: str) -> tuple[str, int]:
    rows = []
    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as fh:
        for raw in fh:
            if raw.startswith(b"<ABR "):
                rec = parse_line(raw.decode("utf-8", "replace"))
                if rec:
                    rows.append(rec)
    df = pd.DataFrame(rows)
    out = Path(out_dir) / (Path(member).stem + ".parquet")
    df.to_parquet(out, index=False)
    return member, len(df)


def parse_all(workers: int = 4) -> Path:
    raw = store.raw_dir(SOURCE)
    out_dir = store.PROCESSED / SOURCE / "records"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for f in FILES:
        with zipfile.ZipFile(raw / f) as zf:
            jobs += [(str(raw / f), m.filename) for m in zf.infolist() if m.filename.endswith(".xml")]
    with ProcessPoolExecutor(workers) as pool:
        paths, members = [j[0] for j in jobs], [j[1] for j in jobs]
        for member, n in pool.map(parse_member, paths, members, [str(out_dir)] * len(jobs)):
            print(f"  {member}: {n:,} records", flush=True)
    return out_dir


def _month(yyyymmdd: pd.Series) -> pd.Series:
    return pd.to_datetime((yyyymmdd // 100).astype(str) + "01", format="%Y%m%d", errors="coerce")


def _count(df: pd.DataFrame, keys: list[str], measure: str, period: pd.Series | None = None) -> pd.DataFrame:
    d = df.assign(period=period) if period is not None else df
    out = d.groupby(keys, dropna=False, observed=True).size().rename("value").reset_index()
    out["measure"] = measure
    return out


def _frame(counts: pd.DataFrame, geo_level: str, geo_col: str | None, industry: bool, breakdown: bool) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "measure": counts["measure"],
            "geo_level": geo_level,
            "geo_code": counts[geo_col] if geo_col else "AUS",
            "breakdown": counts["group"] if breakdown else "",
            "period": counts["period"],
            "value": counts["value"],
        }
    )
    if industry:
        out["industry_scheme"] = "ANZSIC06-inferred"
        out["industry_code"] = counts["industry"]
        out["industry_level"] = counts["industry"].map(names.level)
    else:
        out["industry_scheme"] = "none"
        out["industry_code"] = ""
        out["industry_level"] = "total"
    return out


def build(reparse: bool = False) -> pd.DataFrame:
    rec_dir = store.PROCESSED / SOURCE / "records"
    if reparse or not any(rec_dir.glob("*.parquet")):
        parse_all()
    cols = ["status", "status_from", "group", "state", "postcode", "gst", "gst_from", "industry"]
    df = pd.read_parquet(rec_dir, columns=cols)
    snapshot = _snapshot_date()
    df["postcode"] = df["postcode"].where(df["postcode"].str.fullmatch(r"\d{4}"), "")
    df["state"] = df["state"].where(df["state"].isin(schema.STATES), "")
    for c in ("group", "state", "postcode", "industry", "status", "gst"):
        df[c] = df[c].astype("category")

    can = df[df["status"] == "CAN"]
    act = df[df["status"] == "ACT"]
    gst = act[act["gst"] == "ACT"]
    flows = (
        ("abn_cancellations", can, _month(can["status_from"])),
        ("abn_active_since", act, _month(act["status_from"])),
        ("gst_active_since", gst, _month(gst["gst_from"])),
    )
    parts = []
    for measure, d, period in flows:
        # From July 1999 (when ABNs began) to the last full month before the extract; a few dates are
        # in the future.
        keep = (period >= pd.Timestamp("1999-07-01")) & (period < snapshot.to_period("M").to_timestamp())
        d, period = d[keep], period[keep]
        parts.append(
            _frame(
                _count(d[d["postcode"] != ""], ["postcode", "group", "period"], measure, period[d["postcode"] != ""]),
                "POA",
                "postcode",
                False,
                True,
            )
        )
        parts.append(
            _frame(
                _count(d[d["state"] != ""], ["state", "group", "period"], measure, period[d["state"] != ""]),
                "STE",
                "state",
                False,
                True,
            )
        )
        parts.append(_frame(_count(d, ["group", "period"], measure, period), "AUS", None, False, True))
        ind = d["industry"] != ""
        di, pi = d[ind], period[ind]
        parts.append(
            _frame(
                _count(di[di["state"] != ""], ["state", "industry", "period"], measure, pi[di["state"] != ""]),
                "STE",
                "state",
                True,
                False,
            )
        )
        parts.append(_frame(_count(di, ["industry", "period"], measure, pi), "AUS", None, True, False))
    flows_panel = schema.make(
        pd.concat(parts, ignore_index=True),
        source=SOURCE,
        unit="count",
        adjustment="original",
        period_type="month",
        vintage=f"ABN Bulk Extract {snapshot:%Y-%m-%d}",
    )
    store.write_panel(flows_panel, SOURCE, "flows_month")

    # Stock of active ABNs on the snapshot date.
    stock_parts = [
        _frame(
            _count(act[act["postcode"] != ""], ["postcode", "group"], "abn_active", None).assign(period=snapshot),
            "POA",
            "postcode",
            False,
            True,
        ),
        _frame(
            _count(act[act["state"] != ""], ["state", "group"], "abn_active", None).assign(period=snapshot),
            "STE",
            "state",
            False,
            True,
        ),
        _frame(
            _count(
                act[(act["industry"] != "") & (act["postcode"] != "")], ["postcode", "industry"], "abn_active", None
            ).assign(period=snapshot),
            "POA",
            "postcode",
            True,
            False,
        ),
        _frame(
            _count(
                act[(act["industry"] != "") & (act["state"] != "")], ["state", "industry"], "abn_active", None
            ).assign(period=snapshot),
            "STE",
            "state",
            True,
            False,
        ),
    ]
    stock = schema.make(
        pd.concat(stock_parts, ignore_index=True),
        source=SOURCE,
        unit="count",
        adjustment="original",
        period_type="day",
        vintage=f"ABN Bulk Extract {snapshot:%Y-%m-%d}",
    )
    store.write_panel(stock, SOURCE, "stock_snapshot")
    local = cancellations_sa4(can, snapshot)
    snapshot_summary(df, snapshot)
    return pd.concat([flows_panel, stock, local], ignore_index=True)


def cancellations_sa4(can: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """ABN cancellations by SA4 x inferred industry x month (and all industries), apportioned from
    postcodes with the ABS population shares (``geo.apportion``), so local designs can compare
    areas within a state by industry. Values are fractional where a postcode spans SA4s."""
    from . import geo

    period = _month(can["status_from"])
    keep = (period >= pd.Timestamp("1999-07-01")) & (period < snapshot.to_period("M").to_timestamp())
    d = can[keep & (can["postcode"] != "")].assign(period=period[keep])
    parts = [
        _frame(_count(d, ["postcode", "period"], "abn_cancellations"), "POA", "postcode", False, False),
        _frame(
            _count(d[d["industry"] != ""], ["postcode", "industry", "period"], "abn_cancellations"),
            "POA",
            "postcode",
            True,
            False,
        ),
    ]
    poa = schema.make(
        pd.concat(parts, ignore_index=True),
        source=SOURCE,
        unit="count",
        adjustment="original",
        period_type="month",
        vintage=f"ABN Bulk Extract {snapshot:%Y-%m-%d}",
    )
    sa4 = geo.apportion(poa, "SA4")
    store.write_panel(sa4, SOURCE, "cancellations_sa4_month")
    return sa4


def _snapshot_date() -> pd.Timestamp:
    raw = store.raw_dir(SOURCE)
    with zipfile.ZipFile(raw / FILES[0]) as zf:
        first = sorted(m.filename for m in zf.infolist())[0]
    return pd.Timestamp(first[:8])


def snapshot_summary(df: pd.DataFrame, snapshot: pd.Timestamp) -> Path:
    """Small per-extract summary, so successive weekly extracts can be compared going forward."""
    d = store.PROCESSED / SOURCE / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    summary = {
        "snapshot": snapshot.date().isoformat(),
        "records": int(len(df)),
        "by_status": {k: int(v) for k, v in df["status"].value_counts().items()},
        "active_by_group": {k: int(v) for k, v in df.loc[df["status"] == "ACT", "group"].value_counts().items()},
        "active_with_inferred_industry": int(((df["status"] == "ACT") & (df["industry"] != "")).sum()),
    }
    path = d / f"{snapshot:%Y-%m-%d}.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return path

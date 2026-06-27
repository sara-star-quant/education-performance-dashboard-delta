#!/usr/bin/env python3
"""Build a self-contained snapshot JSON from the cited raw CSVs.

Pipeline: raw CSV -> per-year pillars -> normalize -> EPI -> deltas ->
region/country rankings -> attribution -> tags -> overlay merge ->
developing-segment -> validate -> data/snapshots/<ver>.json + manifest.

Standard library only. No figures are invented; every number derives from
data/sources/*. See docs/guide/methodology.md.
"""
import csv
import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "sources")
CFGDIR = os.path.join(ROOT, "data", "config")
# Published data lives under docs/ so GitHub Pages (served from /docs) can fetch it.
PUBDIR = os.path.join(ROOT, "docs", "data")
SNAPDIR = os.path.join(PUBDIR, "snapshots")

VERSION = "2026Q3"
GENERATED = "2026-06-27"          # passed in, not Date.now (reproducible)
REF_YEAR = 2023
WINDOWS = [1, 3, 5, 10]
KEY_YEARS = [2013, 2018, 2020, 2022, 2023]
PILLARS = ["R", "P", "A", "O"]
PILLAR_NAMES = {
    "R": "Rankings / elite institutions",
    "P": "Research output",
    "A": "Attainment & enrollment",
    "O": "Graduate outcomes",
}
DEFAULT_WEIGHTS = {"R": 0.25, "P": 0.25, "A": 0.25, "O": 0.25}
AI_TAG_THRESHOLD = 0.012          # >=1.2% of works mention AI/ML -> "actively using AI"
QUANTUM_TAG_THRESHOLD = 0.006     # >=0.6% mention quantum -> "quantum programs active"


def load_json(p):
    with open(p) as f:
        return json.load(f)


def read_csv(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


# ---------- load ----------
cfg = load_json(os.path.join(CFGDIR, "countries.json"))
watchcfg = load_json(os.path.join(CFGDIR, "watchlist.json"))
overlay_path = os.path.join(SRC, "overlay.json")
overlay = load_json(overlay_path) if os.path.exists(overlay_path) else {}

countries = cfg["countries"]
by_iso2 = {c["iso2"]: c for c in countries}
regions = cfg["regions"]

# World Bank: indicator -> iso2 -> year -> value
wb = defaultdict(lambda: defaultdict(dict))
for r in read_csv("worldbank.csv"):
    wb[r["indicator"]][r["iso2"]][int(r["year"])] = float(r["value"])

# OpenAlex research: iso2 -> year -> works
research = defaultdict(dict)
for r in read_csv("openalex_research.csv"):
    research[r["iso2"]][int(r["year"])] = int(r["works_count"])

# Institution leaderboard + country map
inst_country = {}
for r in read_csv("openalex_inst_country.csv"):
    if r["country_code"]:
        inst_country[r["inst_id"]] = r["country_code"]
leaderboard = read_csv("openalex_inst_leaderboard.csv")

# Per-country institutions (attribution)
country_insts = defaultdict(lambda: defaultdict(dict))  # iso2 -> inst_id -> year -> {name,works}
for r in read_csv("openalex_country_institutions.csv"):
    country_insts[r["iso2"]][r["inst_id"]][int(r["year"])] = {
        "name": r["display_name"], "works": int(r["works_count"]),
    }

# AI/quantum tag signals
tag_signals = {}
for r in read_csv("openalex_tags.csv"):
    tag_signals[r["iso2"]] = r


def wb_val(indicator, iso2, year, tol=2):
    """Nearest available WB value within +/- tol years (real adjacent obs)."""
    series = wb.get(indicator, {}).get(iso2, {})
    if not series:
        return None, None
    if year in series:
        return series[year], year
    for d in range(1, tol + 1):
        for y in (year - d, year + d):
            if y in series:
                return series[y], y
    return None, None


# ---------- raw pillars per country/year ----------
# R: rank-decay over global top-200 leaderboard
rank_raw = defaultdict(dict)  # iso2 -> year -> score
for r in leaderboard:
    cc = inst_country.get(r["inst_id"])
    if not cc or cc not in by_iso2:
        continue
    y = int(r["year"])
    rank_raw[cc][y] = rank_raw[cc].get(y, 0.0) + 1.0 / math.log10(int(r["global_rank"]) + 10)

raw = {p: defaultdict(dict) for p in PILLARS}  # pillar -> iso2 -> year -> (value, src_year)
for c in countries:
    iso = c["iso2"]
    for y in KEY_YEARS:
        # R (0 is a real value: no globally-elite institution that year)
        raw["R"][iso][y] = (rank_raw.get(iso, {}).get(y, 0.0), y)
        # P research output
        if y in research.get(iso, {}):
            raw["P"][iso][y] = (research[iso][y], y)
        # A attainment (tertiary enrollment gross %)
        v, sy = wb_val("tertiary_enrollment_gross_pct", iso, y)
        if v is not None:
            raw["A"][iso][y] = (v, sy)
        # O outcomes = -unemployment_advanced (higher is better)
        v, sy = wb_val("unemployment_advanced_pct", iso, y)
        if v is not None:
            raw["O"][iso][y] = (-v, sy)


def normalize_year(pillar, year):
    """min-max 0..100 across countries with a value that year."""
    vals = {iso: d[year][0] for iso, d in raw[pillar].items() if year in d}
    if not vals:
        return {}
    lo, hi = min(vals.values()), max(vals.values())
    if hi == lo:
        return {iso: 50.0 for iso in vals}
    return {iso: 100.0 * (v - lo) / (hi - lo) for iso, v in vals.items()}


norm = {p: {y: normalize_year(p, y) for y in KEY_YEARS} for p in PILLARS}


def zscore_year(pillar, year):
    vals = {iso: d[year][0] for iso, d in raw[pillar].items() if year in d}
    if len(vals) < 2:
        return {}
    mean = sum(vals.values()) / len(vals)
    var = sum((v - mean) ** 2 for v in vals.values()) / len(vals)
    sd = math.sqrt(var) or 1.0
    return {iso: 50.0 + 10.0 * (v - mean) / sd for iso, v in vals.items()}


def epi_from(normfn, iso, year, weights=DEFAULT_WEIGHTS):
    parts, wsum = 0.0, 0.0
    present = []
    for p in PILLARS:
        nv = normfn[p].get(year, {}).get(iso)
        if nv is not None:
            parts += weights[p] * nv
            wsum += weights[p]
            present.append(p)
    if wsum == 0:
        return None, present
    return parts / wsum, present


# ---------- assemble countries ----------
out_countries = []
epi_ref = {}
for c in countries:
    iso = c["iso2"]
    series = {}
    pillar_series = {p: {} for p in PILLARS}
    for y in KEY_YEARS:
        e, present = epi_from(norm, iso, y)
        if e is not None:
            series[y] = round(e, 2)
        for p in PILLARS:
            nv = norm[p].get(y, {}).get(iso)
            if nv is not None:
                pillar_series[p][y] = round(nv, 2)

    if REF_YEAR not in series:
        continue
    epi_ref[iso] = series[REF_YEAR]

    deltas = {}
    pillar_deltas = {p: {} for p in PILLARS}
    for dt in WINDOWS:
        y0 = REF_YEAR - dt
        if y0 in series and REF_YEAR in series:
            deltas[str(dt)] = round(series[REF_YEAR] - series[y0], 2)
        for p in PILLARS:
            if y0 in pillar_series[p] and REF_YEAR in pillar_series[p]:
                pillar_deltas[p][str(dt)] = round(pillar_series[p][REF_YEAR] - pillar_series[p][y0], 2)

    present_ref = [p for p in PILLARS if REF_YEAR in pillar_series[p]]
    coverage = {p: (REF_YEAR in pillar_series[p]) for p in PILLARS}
    confidence = "high" if len(present_ref) == 4 else "med" if len(present_ref) == 3 else "low"

    # confounders
    gdp, _ = wb_val("gdp_per_capita_usd", iso, REF_YEAR)
    rd, _ = wb_val("rd_pct_gdp", iso, REF_YEAR)
    size, _ = wb_val("tertiary_enrollment_count", iso, REF_YEAR)
    if size is None:
        size, _ = wb_val("population", iso, REF_YEAR)
    base_rank = raw["R"][iso].get(REF_YEAR - 5, (0.0,))[0]

    # attribution: institution with biggest works growth 2018->2023
    top_inst = None
    best = -1
    for iid, yrs in country_insts.get(iso, {}).items():
        if 2023 in yrs:
            w23 = yrs[2023]["works"]
            w18 = yrs.get(2018, {}).get("works", 0)
            growth = w23 - w18
            if growth > best:
                best = growth
                top_inst = {
                    "name": yrs[2023]["name"],
                    "openalex_id": iid,
                    "works_2018": w18,
                    "works_2023": w23,
                    "works_growth": growth,
                    "metric_climbed": "research output (OpenAlex works)",
                    "evidence": f"Annual works rose from {w18:,} (2018) to {w23:,} (2023).",
                }

    # tags (country level): AI/quantum derived + overlay
    tags = {}
    ts = tag_signals.get(iso)
    if ts and ts.get("ai_share") not in (None, ""):
        share = float(ts["ai_share"])
        tags["ai_using"] = {
            "value": share >= AI_TAG_THRESHOLD,
            "evidence": f"{ts['display_name']}: {float(share)*100:.2f}% of 2020-2023 works mention AI/ML (OpenAlex).",
            "confidence": "med",
        }
    if ts and ts.get("quantum_share") not in (None, ""):
        share = float(ts["quantum_share"])
        tags["quantum_programs"] = {
            "value": share >= QUANTUM_TAG_THRESHOLD,
            "evidence": f"{ts['display_name']}: {float(share)*100:.2f}% of 2020-2023 works mention quantum (OpenAlex).",
            "confidence": "med",
        }
    # overlay tags (delivery, funding, quantum_phd, ...) override/extend
    ov_country = overlay.get("country_tags", {}).get(iso, {})
    for k, v in ov_country.items():
        tags[k] = v

    # reason: overlay if cited, else data-derived
    reason = overlay.get("country_reasons", {}).get(iso)
    if not reason:
        d5 = deltas.get("5")
        rtxt = []
        if d5 is not None:
            rtxt.append(f"EPI {'rose' if d5 >= 0 else 'fell'} {abs(d5):.1f} points over 5y")
        pw = research.get(iso, {})
        if 2018 in pw and 2023 in pw and pw[2018]:
            g = 100.0 * (pw[2023] - pw[2018]) / pw[2018]
            rtxt.append(f"research output {'+' if g>=0 else ''}{g:.0f}% (2018-2023)")
        if rd is not None:
            rtxt.append(f"R&D {rd:.2f}% of GDP")
        reason = {
            "text": "; ".join(rtxt) + ".",
            "citations": ["OpenAlex", "World Bank"],
            "auto_generated": True,
        }

    out_countries.append({
        "iso2": iso, "iso3": c["iso3"], "name": c["name"], "echarts": c["echarts"],
        "region": c["region"],
        "epi": series, "epi_ref": series[REF_YEAR],
        "pillars": pillar_series, "deltas": deltas, "pillar_deltas": pillar_deltas,
        "coverage": coverage, "confidence": confidence,
        "confounders": {
            "gdp_per_capita_usd": gdp, "rd_pct_gdp": rd,
            "size": size, "base_rank": round(base_rank, 3),
        },
        "tags": tags,
        "top_institution": top_inst,
        "reason": reason,
        "cost_funding": overlay.get("cost_funding", {}).get(iso),
    })

cmap = {c["iso2"]: c for c in out_countries}

# ---------- regions ----------
out_regions = []
for rid, rname in regions.items():
    members = [c for c in out_countries if c["region"] == rid]
    if not members:
        continue
    rdelta = {}
    for dt in WINDOWS:
        num = den = 0.0
        for c in members:
            d = c["deltas"].get(str(dt))
            w = c["confounders"]["size"] or 0
            if d is not None and w:
                num += w * d
                den += w
        if den:
            rdelta[str(dt)] = round(num / den, 2)
    out_regions.append({
        "id": rid, "name": rname,
        "members": [c["iso2"] for c in members],
        "delta": rdelta,
        "epi_mean_ref": round(sum(c["epi_ref"] for c in members) / len(members), 2),
    })


def rank_by(items, key_window, n=None):
    valid = [x for x in items if x[1].get(key_window) is not None]
    valid.sort(key=lambda x: x[1][key_window], reverse=True)
    return [x[0] for x in valid][:n] if n else [x[0] for x in valid]


top3_regions = {
    str(dt): rank_by([(r["id"], r["delta"]) for r in out_regions], str(dt), 3)
    for dt in WINDOWS
}
top30_countries = {
    str(dt): rank_by([(c["iso2"], c["deltas"]) for c in out_countries], str(dt), 30)
    for dt in WINDOWS
}

# ---------- developing segment ----------
epis = sorted(c["epi_ref"] for c in out_countries)
p30_epi = epis[int(len(epis) * 0.30)]  # bottom-30% EPI = genuinely lower-performing

developing = []
flagged = set()
for c in out_countries:
    d5 = c["deltas"].get("5")
    # genuinely lower-EPI systems that are nonetheless improving
    if c["epi_ref"] < p30_epi and d5 is not None and d5 > 0:
        flagged.add(c["iso2"])

watch = {w["country"]: w for w in watchcfg["watchlist"]}
# iso3 -> iso2 helper for benchmark codes (watchlist uses iso3)
iso3_to_iso2 = {c["iso3"]: c["iso2"] for c in countries}

for iso2 in sorted(flagged | {iso3_to_iso2.get(k) for k in watch if iso3_to_iso2.get(k)}):
    if iso2 not in cmap:
        continue
    c = cmap[iso2]
    flag = []
    if iso2 in flagged:
        flag.append("criteria")
    wkey = c["iso3"]
    bench = {}
    if wkey in watch:
        flag.append("watchlist")
        for role in ("neighbor", "peer"):
            bcode3 = watch[wkey]["benchmarks"][role]
            biso2 = iso3_to_iso2.get(bcode3)
            if biso2 in cmap:
                b = cmap[biso2]
                bench[role] = {
                    "iso2": biso2, "name": b["name"],
                    "epi_ref": b["epi_ref"],
                    "epi_gap": round(b["epi_ref"] - c["epi_ref"], 2),
                    "pillar_gap": {
                        p: round((b["pillars"][p].get(REF_YEAR, 0) - c["pillars"][p].get(REF_YEAR, 0)), 2)
                        for p in PILLARS
                        if REF_YEAR in b["pillars"][p] and REF_YEAR in c["pillars"][p]
                    },
                }
    ov = overlay.get("developing", {}).get(iso2, {})
    developing.append({
        "iso2": iso2, "name": c["name"],
        "flag_reason": flag,
        "epi_ref": c["epi_ref"], "delta": c["deltas"],
        "benchmarks": bench,
        "missing_features": ov.get("missing_features", []),
        "youth_motivators": ov.get("youth_motivators", []),
    })

# ---------- universal approach (basic; enriched by correlate.py) ----------
top30_5y = set(top30_countries["5"])
lever_counts = defaultdict(int)
for c in out_countries:
    if c["iso2"] in top30_5y:
        for k, v in c["tags"].items():
            if isinstance(v, dict) and v.get("value"):
                lever_counts[k] += 1
universal = {
    "note": "Candidate levers = feature tags common among the strongest 5y improvers. "
            "Statistical association is computed in correlate.py (insights page).",
    "candidate_levers": sorted(
        ({"feature": k, "count_in_top30": n} for k, n in lever_counts.items()),
        key=lambda x: x["count_in_top30"], reverse=True,
    ),
}

# ---------- sensitivity check (min-max vs z-score top lists) ----------
z_epi = {}
for c in out_countries:
    e, _ = epi_from({p: {y: zscore_year(p, y) for y in KEY_YEARS} for p in PILLARS},
                    c["iso2"], REF_YEAR)
    if e is not None:
        z_epi[c["iso2"]] = e
z_delta = {}
zfns = {p: {y: zscore_year(p, y) for y in KEY_YEARS} for p in PILLARS}
for c in out_countries:
    e1, _ = epi_from(zfns, c["iso2"], REF_YEAR)
    e0, _ = epi_from(zfns, c["iso2"], REF_YEAR - 5)
    if e1 is not None and e0 is not None:
        z_delta[c["iso2"]] = e1 - e0
z_top30 = [x for x, _ in sorted(z_delta.items(), key=lambda kv: kv[1], reverse=True)][:30]
overlap = len(set(z_top30) & top30_5y)
sensitivity = {
    "method_a": "min-max", "method_b": "z-score",
    "top30_overlap_5y": overlap,
    "stable": overlap >= 24,
    "note": f"{overlap}/30 countries shared between min-max and z-score top-30 (5y).",
}

# ---------- snapshot ----------
snapshot = {
    "meta": {
        "version": VERSION, "generated": GENERATED, "reference_year": REF_YEAR,
        "windows": WINDOWS, "key_years": KEY_YEARS,
        "weights": DEFAULT_WEIGHTS, "normalization": "min-max",
        "pillars": PILLAR_NAMES,
        "sources": ["World Bank Indicators API (CC BY 4.0)", "OpenAlex (CC0)"],
    },
    "regions": out_regions,
    "countries": out_countries,
    "top3_regions": top3_regions,
    "top30_countries": top30_countries,
    "developing": developing,
    "universal_approach": universal,
    "sensitivity": sensitivity,
    "subnational": overlay.get("subnational", {}),
    "correlation": None,  # filled by correlate.py
}


def validate(s):
    assert s["meta"]["version"], "missing version"
    assert s["countries"], "no countries"
    for c in s["countries"]:
        assert "epi_ref" in c and "deltas" in c, f"bad country {c.get('iso2')}"
        assert "tags" in c and "confounders" in c
    for dt in WINDOWS:
        assert str(dt) in s["top30_countries"]
    assert s["regions"], "no regions"
    return True


validate(snapshot)
os.makedirs(SNAPDIR, exist_ok=True)
outp = os.path.join(SNAPDIR, f"{VERSION}.json")
with open(outp, "w") as f:
    json.dump(snapshot, f, separators=(",", ":"))

manifest = {
    "latest": VERSION,
    "snapshots": [{
        "version": VERSION, "generated": GENERATED,
        "reference_year": REF_YEAR,
        "country_count": len(out_countries),
        "path": f"snapshots/{VERSION}.json",
    }],
}
with open(os.path.join(PUBDIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"countries: {len(out_countries)}  regions: {len(out_regions)}  developing: {len(developing)}")
print(f"top3 regions (5y): {top3_regions['5']}")
print(f"top5 countries (5y): {top30_countries['5'][:5]}")
print(f"sensitivity: {sensitivity['note']}")
print(f"-> {outp}")

#!/usr/bin/env python3
"""Fetch raw, citable source data into data/sources/ as tidy CSVs.

Sources (all free, no-auth, reproducible):
  - World Bank Indicators API  -> attainment, outcomes, confounders
  - OpenAlex API               -> research output (works) + per-year institution
                                  leaderboard (rankings proxy + attribution)

No figures are invented; every row is a direct API value. See
docs/guide/data-sources.md for the citation list.
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "sources")
CFG = os.path.join(ROOT, "data", "config", "countries.json")
# OpenAlex contact + key, supplied ONLY via env (never stored in the repo).
# For the scheduled GitHub Action, set OPENALEX_API_KEY and OPENALEX_MAILTO secrets.
MAILTO = os.environ.get("OPENALEX_MAILTO", "").strip()
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()

WB_INDICATORS = {
    "SE.TER.ENRR": "tertiary_enrollment_gross_pct",      # attainment
    "SE.TER.CUAT.BA.ZS": "attainment_bachelors_pct",     # attainment (sparse)
    "SL.UEM.ADVN.ZS": "unemployment_advanced_pct",       # outcomes (inverted)
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",              # confounder
    "GB.XPD.RSDV.GD.ZS": "rd_pct_gdp",                   # confounder
    "SP.POP.TOTL": "population",                         # size / per-capita
    "SE.TER.ENRL": "tertiary_enrollment_count",         # enrollment weight
}

# Years for the per-year institution leaderboard (windows 1/3/5/10 from 2024).
LEADERBOARD_YEARS = [2014, 2019, 2021, 2023, 2024]
# Recent window for AI/quantum tag signals and the research-momentum panel.
TAG_WINDOW = "2021-2024"
RESEARCH_YEARS = range(2013, 2025)  # 2013..2024; 2025+ are not yet fully indexed


def _redact(url):
    """Strip the api_key so it never reaches logs or tracebacks."""
    if OPENALEX_API_KEY:
        url = url.replace(OPENALEX_API_KEY, "***")
    return url


def get_json(url, tries=6):
    last = None
    if OPENALEX_API_KEY and "openalex.org" in url:
        url += f"&api_key={OPENALEX_API_KEY}"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "edu-delta-dashboard/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:  # noqa: PERF203
            last = e
            time.sleep((8 if e.code == 429 else 2) * (i + 1))
        except Exception as e:  # noqa: BLE001 - network retry
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed: {_redact(url)}\n{last}")


def load_cfg():
    with open(CFG) as f:
        return json.load(f)


def fetch_worldbank(countries):
    iso2 = ";".join(c["iso2"] for c in countries)
    rows = []
    for ind, label in WB_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/{iso2}/indicator/{ind}"
            f"?format=json&date=2013:2024&per_page=20000"
        )
        data = get_json(url)
        if not isinstance(data, list) or len(data) < 2 or data[1] is None:
            print(f"  WB {ind}: no data")
            continue
        n = 0
        for obs in data[1]:
            if obs.get("value") is None:
                continue
            rows.append({
                "indicator": label,
                "iso2": obs["country"]["id"],
                "iso3": obs.get("countryiso3code", ""),
                "year": int(obs["date"]),
                "value": obs["value"],
            })
            n += 1
        print(f"  WB {ind} ({label}): {n} obs")
        time.sleep(0.3)
    out = os.path.join(SRC, "worldbank.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["indicator", "iso2", "iso3", "year", "value"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  -> wrote {out} ({len(rows)} rows)")


def fetch_openalex_research(countries):
    """Per-country works count per year (research output pillar)."""
    wanted = {c["iso2"] for c in countries}
    rows = []
    for year in RESEARCH_YEARS:
        url = (
            "https://api.openalex.org/works"
            f"?filter=publication_year:{year}"
            "&group_by=authorships.institutions.country_code"
            f"&mailto={MAILTO}"
        )
        data = get_json(url)
        for g in data.get("group_by", []):
            cc = g["key"].rsplit("/", 1)[-1]
            if cc in wanted:
                rows.append({"iso2": cc, "year": year, "works_count": g["count"]})
        print(f"  OpenAlex research {year}: {len(data.get('group_by', []))} countries")
        time.sleep(0.3)
    out = os.path.join(SRC, "openalex_research.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iso2", "year", "works_count"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  -> wrote {out} ({len(rows)} rows)")


def fetch_openalex_institutions():
    """Per-year global institution leaderboard (rankings proxy + attribution)."""
    lb = []          # id, display_name, year, works_count, global_rank
    inst_ids = set()
    for year in LEADERBOARD_YEARS:
        rank = 0
        # group_by returns the top 200 groups and does not paginate.
        url = (
            "https://api.openalex.org/works"
            f"?filter=publication_year:{year}"
            "&group_by=authorships.institutions.id"
            f"&per-page=200&mailto={MAILTO}"
        )
        data = get_json(url)
        for g in data.get("group_by", []):
            rank += 1
            iid = g["key"].rsplit("/", 1)[-1]
            inst_ids.add(iid)
            lb.append({
                "inst_id": iid,
                "display_name": g.get("key_display_name", ""),
                "year": year,
                "works_count": g["count"],
                "global_rank": rank,
            })
        time.sleep(0.3)
        print(f"  OpenAlex leaderboard {year}: {rank} institutions")
    out = os.path.join(SRC, "openalex_inst_leaderboard.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["inst_id", "display_name", "year", "works_count", "global_rank"], lineterminator="\n")
        w.writeheader()
        w.writerows(lb)
    print(f"  -> wrote {out} ({len(lb)} rows)")

    # Map institution id -> country (batch)
    ids = sorted(inst_ids)
    crows = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        flt = "openalex_id:" + "|".join(chunk)
        url = (
            "https://api.openalex.org/institutions"
            f"?filter={urllib.parse.quote(flt, safe='|:')}"
            "&select=id,display_name,country_code&per-page=50"
            f"&mailto={MAILTO}"
        )
        data = get_json(url)
        for r in data.get("results", []):
            crows.append({
                "inst_id": r["id"].rsplit("/", 1)[-1],
                "display_name": r.get("display_name", ""),
                "country_code": r.get("country_code") or "",
            })
        time.sleep(0.3)
    out = os.path.join(SRC, "openalex_inst_country.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["inst_id", "display_name", "country_code"], lineterminator="\n")
        w.writeheader()
        w.writerows(crows)
    print(f"  -> wrote {out} ({len(crows)} rows)")


def fetch_openalex_country_institutions(countries):
    """Top institutions within each country for attribution (who climbed most)."""
    years = [2019, 2024]
    rows = []
    for c in countries:
        cc = c["iso2"]
        for year in years:
            url = (
                "https://api.openalex.org/works"
                f"?filter=institutions.country_code:{cc},publication_year:{year}"
                "&group_by=authorships.institutions.id"
                f"&per-page=25&mailto={MAILTO}"
            )
            data = get_json(url)
            rank = 0
            for g in data.get("group_by", [])[:15]:
                rank += 1
                rows.append({
                    "iso2": cc,
                    "inst_id": g["key"].rsplit("/", 1)[-1],
                    "display_name": g.get("key_display_name", ""),
                    "year": year,
                    "works_count": g["count"],
                    "country_rank": rank,
                })
            time.sleep(0.2)
        print(f"  {cc}: top institutions captured")
    out = os.path.join(SRC, "openalex_country_institutions.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iso2", "inst_id", "display_name", "year", "works_count", "country_rank"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  -> wrote {out} ({len(rows)} rows)")


def _count(filt):
    url = f"https://api.openalex.org/works?filter={urllib.parse.quote(filt, safe=':,')}&per-page=1&mailto={MAILTO}"
    return get_json(url)["meta"]["count"]


def _count_safe(filt):
    try:
        return _count(filt)
    except Exception as e:  # noqa: BLE001
        print(f"    ! skip ({e})")
        return None


def fetch_openalex_tags(countries):
    """Derive AI/quantum research-activity signals at COUNTRY level.

    A reproducible, cited proxy: share of the country's recent works (TAG_WINDOW)
    mentioning the theme, aggregated across all the country's institutions. This
    captures national strength (e.g. Australia's quantum leaders) that a single
    top-by-output institution would miss. Maps to taxonomy tags ai_using /
    quantum_programs; other tags stay curated in overlay.json.
    """
    out = os.path.join(SRC, "openalex_tags.csv")
    fields = ["iso2", "works_total", "works_ai", "works_quantum", "ai_share", "quantum_share"]
    done, rows = set(), []
    if os.path.exists(out):
        with open(out) as f:
            for r in csv.DictReader(f):
                rows.append(r)
                done.add(r["iso2"])

    def flush():
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    for c in countries:
        iso2 = c["iso2"]
        if iso2 in done:
            continue
        base = f"institutions.country_code:{iso2},publication_year:{TAG_WINDOW}"
        total = _count_safe(base); time.sleep(1.0)
        ai = _count_safe(base + ",title_and_abstract.search:artificial intelligence OR machine learning"); time.sleep(1.0)
        quantum = _count_safe(base + ",title_and_abstract.search:quantum"); time.sleep(1.0)
        rows.append({
            "iso2": iso2,
            "works_total": total if total is not None else "",
            "works_ai": ai if ai is not None else "",
            "works_quantum": quantum if quantum is not None else "",
            "ai_share": round(ai / total, 5) if (ai and total) else "",
            "quantum_share": round(quantum / total, 5) if (quantum and total) else "",
        })
        print(f"  {iso2}: ai={ai} quantum={quantum} total={total}")
        flush()
    print(f"  -> wrote {out} ({len(rows)} rows)")


def main():
    os.makedirs(SRC, exist_ok=True)
    cfg = load_cfg()
    countries = cfg["countries"]
    print("World Bank ...")
    fetch_worldbank(countries)
    print("OpenAlex research output ...")
    fetch_openalex_research(countries)
    print("OpenAlex institution leaderboard ...")
    fetch_openalex_institutions()
    print("OpenAlex per-country institutions ...")
    fetch_openalex_country_institutions(countries)
    print("OpenAlex AI/quantum tag signals ...")
    fetch_openalex_tags(countries)
    print("done.")


if __name__ == "__main__":
    main()

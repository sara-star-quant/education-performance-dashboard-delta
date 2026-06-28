# Global Education Performance Delta Dashboard

A static, installable (PWA) dashboard showing the **change in higher-education
performance per region and per country** over 1, 3, 5, and 10 years, built only
from **trusted public sources** with citations. GitHub Pages friendly.

It answers:

1. **Top 3 regions** improving most over 1/3/5 years.
2. **Top 30 countries** with significant progress, each with the institution that
   contributed most and the cited reason.
3. A **universal approach**: reusable levers, informed by a controlled
   [correlation study](docs/guide/correlation-study.md) of program features
   (AI, quantum, delivery mode, funding, ...), plus a balanced-by-region view.

Scope: higher education (bachelors, masters, PhD) and youth talent pathways.

## Documentation

Full cross-linked guide in **[docs/guide](docs/guide/README.md)**:
[dashboard](docs/guide/dashboard.md) -
[methodology](docs/guide/methodology.md) -
[data sources](docs/guide/data-sources.md) -
[taxonomy](docs/guide/taxonomy.md) -
[correlation study](docs/guide/correlation-study.md) -
[developing systems](docs/guide/developing-countries.md) -
[architecture](docs/guide/architecture.md) -
[licensing](docs/guide/licensing.md) -
[disclaimer](docs/guide/disclaimer.md).

## How it works

```
data/sources/*.csv        raw, cited extracts from public sources (World Bank, OpenAlex)
        |  build/build_snapshot.py   normalize -> EPI -> deltas -> rankings -> tags
        |  build/correlate.py        feature x outcome, controlled regression
        v
docs/data/snapshots/<ver>.json   self-contained snapshot (history + analysis)
docs/data/manifest.json          list of snapshots + "latest" pointer
        |  docs/  (static site, ECharts bundled locally, PWA)
        v
GitHub Pages (served from /docs)
```

## Data integrity

- No fabricated numbers. Every figure traces to a source in
  [`data/sources/SOURCES.md`](data/sources/SOURCES.md) with an access date.
- Licensed ranking tables (QS/THE/ARWU) are not republished; the Rankings pillar
  is a transparent OpenAlex output-based proxy ([details](docs/guide/data-sources.md)).
- Missing data is excluded, never imputed or zero-filled.

## Build / refresh

```sh
cp .env.example .env        # optional: OPENALEX_API_KEY (Premium), OPENALEX_MAILTO
build/refresh.sh            # fetch -> build -> correlate
build/refresh.sh --no-fetch # rebuild from existing CSVs only
```

Zero Python dependencies (standard library only). Secrets are read from the
gitignored `.env` or prompted - never committed.

## Preview

```sh
cd docs && python3 -m http.server 8000   # open http://localhost:8000
```

## Licensing (open-core)

- Code: **[AGPL-3.0](LICENSE)**
- Data & content: **[CC BY-NC 4.0](LICENSE-DATA.md)** (commercial use by license)

See [licensing](docs/guide/licensing.md) for commercial data licensing,
hosted/white-label, and consulting options.

## Disclaimer

**No advice of any kind. No warranty. No liability.** This project is
informational and educational only; figures come from third-party public sources
and may be incomplete or wrong; the index is an opinionated construct and the
analysis is observational, not causal. Use at your own risk. Full terms:
[disclaimer](docs/guide/disclaimer.md).

## Scope of the first snapshot

A cited seed cohort of 50 countries across seven regions (2014-2024, reference
year 2024) that exercises every dashboard feature. Coverage expands toward the
60-80 threshold-passing target in later quarterly snapshots.

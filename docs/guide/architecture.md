# Architecture

## Pipeline

```
build/fetch_sources.py   World Bank + OpenAlex  -> data/sources/*.csv (cited)
build/build_snapshot.py  CSV + overlay.json     -> docs/data/snapshots/<ver>.json + manifest
build/correlate.py       snapshot               -> snapshot.correlation + ranked levers
docs/ (static, ECharts)  fetch snapshot         -> dashboard + insights
```

Python is **standard library only** (no numpy/pandas) for zero-friction
reproducibility. The build normalizes pillars, computes the EPI and deltas,
ranks regions/countries, aggregates tags, attaches confounders, assembles the
developing-segment and sub-national blocks, runs a normalization sensitivity
check, and validates the output against the schema before writing.

## Snapshot schema (per file)

- `meta`: version, generated date, reference year, windows, key years, weights,
  normalization, pillar names, sources.
- `regions[]`: id, name, members, per-window delta, mean EPI.
- `countries[]`: iso codes, region, per-year `epi` and normalized `pillars`,
  per-window `deltas` and `pillar_deltas`, `coverage`/`confidence`,
  `confounders`, `tags` (value + evidence + confidence), `top_institution`,
  `reason` (+ citations), `cost_funding`.
- `top3_regions`, `top30_countries`: ordered id lists per window.
- `developing[]`, `subnational{}`, `universal_approach`, `sensitivity`,
  `correlation`.

Published data lives under `docs/data/` so GitHub Pages (served from `/docs`)
can fetch it. Raw source CSVs and `overlay.json` stay under `data/` and are not
published.

## Refresh

Snapshots are versioned per quarter (e.g. `2026-Q3`) and refreshed ~2-3x/quarter.

```sh
cp .env.example .env     # add OPENALEX_API_KEY (optional) + OPENALEX_MAILTO
build/refresh.sh         # fetch -> build -> correlate   (or --no-fetch to rebuild)
```

Secrets are read from the gitignored `.env` or prompted by the script; for the
scheduled GitHub Action set them as repository secrets (`OPENALEX_API_KEY`,
`OPENALEX_MAILTO`).

**Advancing the reference year.** `REF_YEAR`, `VERSION`, `GENERATED`, and
`year_range`/`key_years` are pinned constants in `build/build_snapshot.py`, so
the scheduled refresh re-runs the *same* window rather than rolling forward.
Moving to a new period is a deliberate edit: bump `VERSION` (e.g. `2026-Q4`),
set the new `REF_YEAR`/`GENERATED`, extend the year lists, then re-run. This
keeps published snapshots stable and reproducible between intentional bumps.

## Frontend & PWA

Framework-free HTML/CSS + vanilla JS, [ECharts](https://echarts.apache.org/)
bundled locally (no CDN dependency, works offline). A web manifest +
service worker (`docs/sw.js`) make it an installable, offline-capable PWA: the
app shell is cached cache-first; snapshot data is network-first so a fresh
snapshot wins online and the last one serves offline.

### Hardening note

The client renders only first-party snapshot JSON. Institution names originate
from OpenAlex; for defense-in-depth a future version can sanitize text fields at
build time (or render via safe DOM methods) rather than template strings.

## Flutter-later track

The data layer (JSON snapshots) is intentionally frontend-agnostic. A future
Flutter app (web/iOS/Android/desktop from one Dart codebase) can consume the
same `docs/data/manifest.json` + snapshot files unchanged - no pipeline changes
needed. The web/PWA app ships first; Flutter is added only if native app-store
distribution is required.

[Back to docs](README.md).

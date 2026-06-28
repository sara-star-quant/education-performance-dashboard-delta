# Data sources

All quantitative figures come from free, no-auth, reproducible public APIs.
Nothing is hand-entered except the cited qualitative overlay.

| Source | License | Pillar / use |
| --- | --- | --- |
| [World Bank Indicators API](https://data.worldbank.org/) | CC BY 4.0 | Attainment (tertiary enrollment), Outcomes (advanced-education unemployment), confounders (GDP/capita, R&D % GDP, population, enrollment count) |
| [OpenAlex](https://openalex.org/) | CC0 | Research output (works/year), per-year global institution leaderboard (Rankings proxy + attribution), AI/quantum research signals |

World Bank requires attribution (CC BY 4.0); OpenAlex is public domain (CC0).
Full indicator list and the raw extract files are in
[`data/sources/SOURCES.md`](../../data/sources/SOURCES.md).

## How figures are fetched

`build/fetch_sources.py` pulls everything into tidy CSVs under `data/sources/`.
It is deterministic and re-runnable. Credentials (an optional OpenAlex Premium
key and a contact email) are read **only** from environment variables / a
gitignored `.env` - never stored in the repo. See [architecture](architecture.md#refresh).

## Rankings pillar: an honest proxy

Licensed ranking tables (QS, THE, ARWU) are not republished. The Rankings pillar
is a transparent, reproducible **output-based proxy**: each country's rank-decay
score over OpenAlex's per-year global top-200 institutions. To use licensed data
instead, replace `data/sources/openalex_inst_leaderboard.csv` with an equivalent
ranked list - the rest of the pipeline is unchanged. See [methodology](methodology.md).

## Recent-year indexing lag (why the reference year is 2024)

OpenAlex keeps indexing recent years for months after they end. In mid-2026 the
2024 counts show only a mild, roughly proportional undercount that cross-country
normalization absorbs, so 2024 is the reference year. **2025 is not yet usable**:
its counts are inflated by indexing artifacts (e.g. one large country shows ~3x
its normal annual output for 2025), so the build excludes 2025 and later. A
recent-research "momentum" panel was evaluated and dropped for the same reason;
it will return once 2025 indexes fully.

## Qualitative overlay

`data/sources/overlay.json` holds what APIs cannot provide - delivery/funding
tags, country reason narratives, sub-national breakdowns, cost/funding, and
developing-segment notes. Every entry is cited inline. Anything missing renders
as "not available" on the dashboard; it is never fabricated.

See also: [methodology](methodology.md) - [taxonomy](taxonomy.md) - [back to docs](README.md).

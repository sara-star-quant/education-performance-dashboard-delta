# Dashboard guide

The live dashboard (`docs/index.html`) and the [Insights page](correlation-study.md)
(`docs/insights.html`) read the latest snapshot from `docs/data/`.

## Controls

- **Window (1/3/5/10y):** the time horizon for every delta on the page.
- **Filter by feature:** restrict the map and table to countries whose top
  institution carries a tag (e.g. *Actively using AI*, *Quantum programs*).
- **Pillar weights:** four sliders re-weight Rankings / Research / Attainment /
  Outcomes. The EPI and all deltas, the map, regions, and the top-30 table
  recompute live in the browser. Defaults are equal (25 each).
- **Snapshot picker:** switch between quarterly snapshots.

## Views

- **World map:** choropleth colored by the selected-window EPI delta (green =
  improving, red = declining). Click a country for its detail drawer.
- **Top improving regions:** the three macro-regions with the highest
  enrollment-weighted mean EPI delta for the window.
- **Top 30 countries:** ranked by EPI delta; sortable; shows confidence and tags.
- **Developing systems:** see [developing-countries](developing-countries.md).

## Country detail drawer

Opens from the map or table. Shows the EPI trend across key years, the
normalized pillar change for the window, the **institution that contributed
most** (with the metric it moved as evidence), the **cited reason**, feature
tags, cost/funding (if available), and a **sub-national breakdown** for large
countries where data exists (otherwise a clear "country-level only" note).

## Reading it honestly

- EPI is an opinionated composite; use the weight sliders and the per-pillar
  bars to see what drives a result. See [methodology](methodology.md).
- Confidence flags mark pillar coverage. Missing data is excluded, not imputed.
- Institution attribution shows evidence, not causation.

[Back to docs](README.md).

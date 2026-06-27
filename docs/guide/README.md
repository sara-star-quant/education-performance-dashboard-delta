# Documentation

Cross-linked guide to the Global Education Performance Delta Dashboard. These
pages render best on GitHub; the live dashboard is the static site in `docs/`.

## Start here

- [Dashboard guide](dashboard.md) - what every view shows and how to read it.
- [Methodology](methodology.md) - the Education Performance Index (EPI), pillars, normalization, deltas, thresholds.
- [Data sources](data-sources.md) - every source, license, and how figures are fetched.
- [Feature taxonomy](taxonomy.md) - the tag definitions and coding rubric.
- [Correlation study](correlation-study.md) - the controlled, observational analysis behind the Insights page.
- [Developing-systems segment](developing-countries.md) - how the gap analysis works.
- [Architecture](architecture.md) - pipeline, snapshot schema, refresh cadence, PWA, and the Flutter-later roadmap.
- [Licensing & use](licensing.md) - the open-core model and commercial options.
- [Disclaimer](disclaimer.md) - no advice, no warranty, no liability.

## At a glance

- **What it measures:** change in higher-education performance (bachelors, masters, PhD) per region and per country over 1/3/5/10 years.
- **Pillars:** Rankings, Research output, Attainment, Outcomes - combined into the EPI ([methodology](methodology.md)).
- **Outputs:** top-3 improving regions, top-30 improving countries with the institution that contributed most and the cited reason, a feature-tag layer, a [correlation study](correlation-study.md), and a [developing-systems gap view](developing-countries.md).
- **Data integrity:** no fabricated numbers; missing data is excluded, never imputed. See [data sources](data-sources.md).

## Project layout

```
build/      fetch + transform pipeline (Python, stdlib only)
data/       config, raw cited source CSVs, curated overlay (not published)
docs/       the static site (GitHub Pages root) + docs/data published snapshots + this guide
```

Back to the [project README](../../README.md).

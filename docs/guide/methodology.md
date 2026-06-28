# Methodology: Education Performance Index (EPI)

This document defines how the dashboard turns public-source data into the
Education Performance Index (EPI), its time deltas, and the regional/country
rankings. Everything here is reproducible by `build/build_snapshot.py`.

## Scope

Higher education only: bachelors, masters, PhD, and the talent pathways that
feed them. K-12 / PISA is out of scope.

## The four pillars

Per country, per year, each pillar is a raw measure derived from a public
source, then normalized to a 0-100 scale across the countries present in that
year.

| Pillar | Source(s) | Raw measure |
| --- | --- | --- |
| Rankings (R) | QS, THE, ARWU published top lists | rank-decay score = sum over a country's ranked institutions of `1 / log10(rank + 10)` |
| Research (P) | Nature Index Share, Scimago | normalized output + citation impact |
| Attainment (A) | UNESCO UIS, World Bank | tertiary gross enrollment ratio + completion |
| Outcomes (O) | OECD, QS Employability | employment rate of tertiary graduates / employability |

![EPI methodology: the four pillars are min-max normalized per year, combined into a weighted EPI (adjustable sliders), turned into 1/3/5/10-year deltas, and ranked into top-3 regions and top-30 countries with institution attribution; feature tags feed the correlation study.](../diagrams/epi-methodology.svg)

*Flow as implemented in the seed (OpenAlex output-based Rankings proxy, OpenAlex works, World Bank attainment/outcomes). The table above lists the conceptual pillar sources; see [data sources](data-sources.md) for what the seed actually uses.*

### Rank-decay score (Rankings pillar)

A country gets credit for every institution it has in a published global list,
weighted so that top ranks count far more than the long tail:

```
rankscore(country) = sum over institutions i of 1 / log10(rank_i + 10)
```

`+10` keeps rank 1 finite and softens the curve. We report both the absolute
rankscore and a per-capita variant (`rankscore / population_millions`), but the
EPI uses the absolute normalized value (per-capita is shown for context only, to
avoid tiny states dominating; see "Weak points").

## Normalization

For pillar `X` in year `t`, with the set of countries `C_t` that have a value:

```
norm_X(c, t) = 100 * (X(c, t) - min_Ct(X)) / (max_Ct(X) - min_Ct(X))
```

This is **min-max**. The build also computes a **z-score** variant
(`(x - mean) / std`, rescaled) used only for the sensitivity check. Min-max is
the published default because 0-100 is legible on the dashboard.

Missing pillars are left as `null` and **never imputed**. A country's EPI is the
weighted mean over the pillars it actually has, with the weights renormalized to
the present pillars (so a 3-pillar country is not penalized to zero, but its
`coverage` flag records the gap).

## EPI

```
EPI(c, t) = ( wR*normR + wP*normP + wA*normA + wO*normO ) / (sum of weights of present pillars)
```

Default weights are equal (`wR = wP = wA = wO = 0.25`). The dashboard exposes
sliders so a user can re-weight and re-rank live; the snapshot stores the
default-weight EPI plus the normalized pillars so the client can recompute.

## Deltas

For each window `dt` in {1, 3, 5, 10} years:

```
delta(c, dt) = EPI(c, t0) - EPI(c, t0 - dt)
```

where `t0` is the snapshot's reference year. Per-pillar deltas are kept too, so
the dashboard can say *what* drove a country's gain.

## Region delta

Regions are UN/World-Bank macro-regions. A region's delta is the
**enrollment-weighted mean** of its member countries' EPI deltas:

```
region_delta(rg, dt) = sum_c (enrollment_c * delta(c, dt)) / sum_c enrollment_c
```

Enrollment = total tertiary enrollment (UNESCO/World Bank). This stops a single
small country from swinging a region.

## Rankings produced

- **Top 3 regions** by 3y and 5y delta (1y shown alongside).
- **Top 30 countries** by composite EPI delta. Default window 5y; 1y/3y toggle.

## Country attribution (who + why)

- **Top institution:** the single institution in the country with the largest
  rank climb (or largest Nature Index share growth) over the window. We show the
  *metric it moved* as evidence; we do not assert causation.
- **Reason:** a short, cited narrative (reform, funding, internationalization,
  targeted R&D, talent pathway).

## Country selection threshold

A country enters the core snapshot only if it passes coverage:

- at least 3 of the 4 pillars present, AND
- at least 1 institution in a published global ranking list.

Below-threshold countries are excluded (not imputed). The first snapshot targets
the 60-80 countries that pass. The developing-countries segment (see
`taxonomy.md` and `config/watchlist.json`) tolerates lower coverage and is
tracked separately.

## Confounders (for the correlation study)

Stored per country for the controlled regression in `correlate.py`:

- GDP per capita (World Bank)
- R&D as % of GDP (World Bank/OECD)
- system size (total tertiary enrollment)
- base ranking level (rankscore at start of window) — guards against
  regression-to-the-mean, since low starters climb more easily.

## Money normalization

Tuition and funding are captured in source currency and stored as **USD** and
**PPP-adjusted USD**, retaining `source_ccy`, the FX/PPP factor, and the year.
Missing money fields are explicit `"not available"`, never zero.

## Weak points and how they are handled

- **Heterogeneous pillars in one index** — mitigated by user-adjustable weights,
  per-pillar transparency, and this document.
- **Normalization choice** — sensitivity check compares min-max vs z-score; if
  the top-3 regions or top-30 list reorder materially, the build logs it.
- **Per-capita bias** — both absolute and per-capita rankscores reported; EPI
  uses absolute.
- **Regression to the mean** — base level is a control in the regression.
- **Coverage gaps** — explicit per-pillar coverage flags; no silent imputation.
- **Causation** — attribution and correlation are framed as evidence/association,
  never cause.
- **Sub-national reconciliation** — where both state and country figures exist,
  the build flags mismatches instead of silently rolling up.

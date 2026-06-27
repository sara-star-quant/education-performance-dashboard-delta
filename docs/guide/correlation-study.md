# Correlation study

Powers the [Insights page](../insights.html). Asks: **do program features
associate with faster ranking / EPI gains?** Answered as association, never
causation.

## Design

- **Unit:** country (seed). Tags are derived from each country's top institution.
  Institution-level analysis turns on once per-institution tags are populated.
- **Outcome:** 5-year EPI delta.
- **Predictors:** each binary feature tag (see [taxonomy](taxonomy.md)).
- **Controls (confounders):** log GDP per capita, R&D % of GDP, log system size,
  and **base ranking level** - the last guards against regression-to-the-mean
  (low starters climb more easily).
- **Methods:** Pearson / point-biserial for the raw association; ordinary least
  squares with the controls for the adjusted estimate. Each result reports the
  coefficient, 95% CI, p-value (normal approximation), n, and model R-squared.
  Pure standard library - see `build/correlate.py`.

## Honesty guardrails

- **Association, not causation.** The page says so prominently.
- **Multiple comparisons:** with several tags tested, single p-values are
  treated cautiously (a Bonferroni alpha is shown).
- **No imputation:** rows missing a control are dropped listwise; n is shown.
- **Small cohort:** the seed has tens of countries; results are directional.

## From correlation to "universal levers"

Features with a positive controlled association feed the **candidate universal
levers** list - the reusable approaches other systems might adopt. Because the
evidence is observational, these are candidates to investigate, not prescriptions.

## Robustness

The build also runs a **normalization sensitivity check** (min-max vs z-score):
if the top-3 regions or top-30 countries reorder materially, it is flagged on
the Insights page. See [methodology](methodology.md#normalization).

[Back to docs](README.md).

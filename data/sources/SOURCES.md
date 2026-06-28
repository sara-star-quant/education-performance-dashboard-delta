# Sources

All quantitative figures derive from these public APIs. Snapshot generated for
reference year 2024 (version 2026-Q3). Raw extracts are the CSVs in this folder;
`build/fetch_sources.py` reproduces them.

## Quantitative (automated, exact)

| Source | License | Used for | Files |
| --- | --- | --- | --- |
| [World Bank Indicators API](https://data.worldbank.org/) | CC BY 4.0 | tertiary enrollment, advanced-education unemployment, GDP/capita, R&D % GDP, population, tertiary enrollment count | `worldbank.csv` |
| [OpenAlex](https://openalex.org/) | CC0 | research output (works) per country/year; per-year global institution leaderboard; per-country institution leaders (attribution); AI/quantum research-activity signals | `openalex_research.csv`, `openalex_inst_leaderboard.csv`, `openalex_inst_country.csv`, `openalex_country_institutions.csv`, `openalex_tags.csv` |

World Bank indicators used: `SE.TER.ENRR`, `SE.TER.CUAT.BA.ZS`, `SL.UEM.ADVN.ZS`,
`NY.GDP.PCAP.CD`, `GB.XPD.RSDV.GD.ZS`, `SP.POP.TOTL`, `SE.TER.ENRL`.

Attribution note: World Bank requires attribution (CC BY 4.0). OpenAlex is CC0.

### Pillar provenance

- **Rankings / elite (R):** OpenAlex per-year global top-200 institution
  leaderboard, rank-decayed by country. This is a transparent, reproducible
  *output-based proxy* for licensed ranking tables (QS/THE/ARWU), which are not
  republished here. Substitute licensed data by replacing the leaderboard CSV.
- **Research output (P):** OpenAlex works count per country per year.
- **Attainment (A):** World Bank tertiary gross enrollment ratio.
- **Outcomes (O):** World Bank unemployment with advanced education (inverted).

## Qualitative (curated overlay, each entry cited)

`overlay.json` holds tags (delivery/funding/etc.), country reason narratives,
sub-national breakdowns, cost/funding, and developing-segment notes that the
APIs cannot provide. Citations are inline in that file. Key sources used in the
seed:

- Malta: [EU Education and Training Monitor 2025](https://op.europa.eu/webpub/eac/education-and-training-monitor/en/country-reports/malta.html), [Newsbook (intl enrolment)](https://newsbook.com.mt/en/international-students-now-account-for-over-a-third-of-maltas-tertiary-enrollments/), [Eurydice Malta](https://eurydice.eacea.ec.europa.eu/eurypedia/malta/types-higher-education-institutions).
- Georgia: [World Bank (medical education)](https://blogs.worldbank.org/en/education/how-georgia-is-using-medical-education-to-build-better-health-ca), [RAND (STEM partnerships)](https://www.rand.org/pubs/research_reports/RRA363-2.html), [OC Media (foreign-student policy)](https://oc-media.org/georgia-to-stop-accepting-foreign-students-in-state-universities-as-of-next-academic-year/).

Missing qualitative fields render as "not available" on the dashboard; they are
never fabricated.

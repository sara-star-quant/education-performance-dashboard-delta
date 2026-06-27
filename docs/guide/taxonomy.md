# Feature tag taxonomy and coding rubric

Tags describe program/feature traits of institutions (and, aggregated, of
countries). Each institution tag is **boolean** and must carry:

- `value`: `true` / `false`
- `evidence`: a source URL + one-line justification
- `confidence`: `high` | `med` | `low`

A tag is only set `true` with cited evidence. Absent evidence => `false` with
`confidence: low` (we did not find it, which is not proof of absence — noted on
the dashboard).

Country-level tag value = **share of that country's profiled top institutions**
carrying the tag (0-1), plus a country boolean (`any` institution has it).

## Tag families

### AI orientation (multi — an institution can have several)

| Tag | Set true when ... |
| --- | --- |
| `ai_educating` | The institution offers dedicated AI/ML degrees, majors, or a named AI school/department. |
| `ai_using` | AI is embedded in teaching or research workflows (AI research institutes, AI-in-curriculum mandates, large AI grant programs). |
| `ai_adapting` | The institution has a published strategy integrating AI into operations/curriculum but not yet (a) dedicated degrees or (b) embedded workflows. |

`ai_adapting` is the weakest rung; if `ai_educating` or `ai_using` is true,
`ai_adapting` is implied true.

### Delivery mode (pick the most permissive that applies)

| Tag | Set true when ... |
| --- | --- |
| `delivery_remote` | Fully online degree programs are offered. |
| `delivery_hybrid` | Blended on-campus + online programs are offered. |
| `delivery_onsite_only` | Only on-campus delivery; no online/hybrid degree programs found. |

### Funding source

| Tag | Set true when ... |
| --- | --- |
| `funding_government` | Primary funding is public/government (national or state). |
| `funding_edu_org` | Significant funding from endowment, private foundation, or educational organizations. |

Both can be true (mixed funding).

### Quantum

| Tag | Set true when ... |
| --- | --- |
| `quantum_programs` | Any quantum-related program, course track, or research center. |
| `quantum_phd` | A PhD pathway in quantum science/technology/computing. |

`quantum_phd` true implies `quantum_programs` true.

### Other crucial features (extensible — finalized during research)

| Tag | Set true when ... |
| --- | --- |
| `industry_rnd_partnership` | Formal industry/R&D partnerships or co-funded labs. |
| `intl_dual_degree` | International dual/joint-degree programs. |
| `youth_pathway` | Scholarship / talent-pathway programs aimed at youth entry. |
| `open_access_mandate` | Institutional open-access research mandate. |
| `entrepreneurship_support` | Incubator / accelerator / entrepreneurship programs. |
| `stem_intensive` | STEM-dominant program portfolio. |

## Confidence guidance

- `high`: official institution page, government source, or major ranking body.
- `med`: reputable secondary source (national press, established education media).
- `low`: inference, older source, or absence-of-evidence default.

## Use in the correlation study

Each tag becomes a binary predictor of ranking/EPI delta, at both institution
and country level, controlled for the confounders in `methodology.md`. Results
are reported as **association, not causation**, with n shown and a
multiple-comparisons caveat.

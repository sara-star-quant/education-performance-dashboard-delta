# Roadmap

Direction for the Global Education Performance Delta Dashboard. Grouped by
theme, roughly in priority order. Items map to GitHub issues. Nothing here is a
commitment to a date.

## Data depth

- [ ] Expand the cohort from 50 to the 60-80 threshold-passing countries.
- [ ] Add citation-impact to the Research pillar (field-weighted citation impact / 2-year mean citedness from OpenAlex), not just works count.
- [ ] Optional licensed-rankings adapter (QS/THE/ARWU) to replace the OpenAlex output-based Rankings proxy where a license exists.
- [ ] Broaden institution-level feature tags (delivery, funding, quantum PhD) so the institution-level correlation can run, not just country-level.
- [ ] Expand cost/tuition, grants, and 5-year funding-inflow coverage with citations.
- [ ] Add sub-national breakdowns beyond US/Germany (India, Canada, Brazil, China, UK).

## Methodology

- [ ] Subject/field-level breakdowns (CS, medicine, engineering) so strengths are visible per discipline.
- [ ] Confidence-weighted EPI and explicit uncertainty bands.
- [ ] Saved weighting presets (research-led, access-led, outcomes-led).
- [ ] Continuous yearly series (not just key years) where sources allow.

## Analysis

- [ ] Institution-level controlled regression once institution tags are populated.
- [ ] Lagged analysis: does a feature precede the gain (directionality), with clear non-causal framing.
- [ ] "Improvement archetypes" clustering of how countries climbed.

## Product / UX

- [ ] Country-vs-country compare mode.
- [ ] Shareable URL state (window, weights, filters, selected country).
- [ ] Export: table to CSV, chart to PNG, one-click country/region PDF report.
- [ ] Search box for countries/institutions.
- [ ] Accessibility pass (keyboard nav, ARIA, contrast) and internationalization.

## Platforms (for convenience and potential clients)

- [ ] PWA polish: PNG maskable icons, cache-versioning, install prompts.
- [ ] Flutter app (web/iOS/Android/desktop from one Dart codebase) consuming the same JSON snapshots unchanged. See [architecture](docs/guide/architecture.md#flutter-later-track).
- [ ] Embeddable widget / iframe for partner sites.
- [ ] Public read-only JSON API (or documented snapshot endpoints) for programmatic access.
- [ ] White-label theming for hosted/institutional deployments.

## Ops / CI

- [x] Scheduled snapshot refresh (GitHub Actions, monthly).
- [ ] Schema-validation CI check on every PR.
- [ ] Markdown link checker for the docs hub.
- [ ] Lighthouse / performance budget check for the dashboard.
- [ ] Deploy previews for PRs.

## Commercial (open-core)

- [ ] Commercial data-license tier (CC BY-NC exemption). See [licensing](docs/guide/licensing.md).
- [ ] Hosted / white-label offering.
- [ ] Bespoke country/institution gap-analysis reports and advisory.

Contributions and feature requests: open a GitHub issue.

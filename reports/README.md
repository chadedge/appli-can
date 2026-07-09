# `reports/` — where your output lands

The pipeline writes its results here: normalized data, schema summaries, and the
funnel dashboard / report built from your dumps in `../input/`.

## What to expect here
- **Schema summaries** — what fields each vendor's dump actually contained
  (output of the `identify_*_schema` steps).
- **Normalized data** — every company's dump mapped onto one common structure.
- **Funnel report** — your applications cross-referenced against timestamps and
  automated screening telemetry, so you can see the black box per company.

## Privacy
**Everything written here is git-ignored** (except this README), because reports
are derived from your personal data. Nothing in this folder gets committed or
pushed unless you deliberately change `.gitignore`.

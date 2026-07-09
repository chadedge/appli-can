# The Appli-CAN! Master Schema

Every vendor hands back a different shape. This schema is the **one structure**
they all get normalized onto, so your applications can be compared and reported
on together. It's defined as Pydantic models in [`applican/schema.py`](applican/schema.py)
and version-stamped (`schema_version`, currently `0.1.0`).

## Guiding principles
1. **Normalize what means the same thing** — dates, funnel stages, outcomes, and
   scores are converted to canonical forms so cross-company comparison works.
2. **Never lose the original** — every normalized field keeps its verbatim vendor
   value in a `*_raw` companion. We interpret; we don't overwrite.
3. **Never drop the unrecognized** — unmapped vendor fields land in an `extra{}`
   bag. Models are `extra="forbid"`, so unknown keys can't slip in silently — the
   normalizer has to route them into `extra` on purpose.
4. **Vocabulary lives in data, not code** — the canonical stage/outcome lists and
   all vendor aliases live in [`data/mappings.yml`](data/mappings.yml). Teach it a
   new vendor string by editing YAML, no code change.

## Structure
```
Dataset
├── schema_version : str
├── applicant      : Applicant          # you, once
├── sources[]      : Source             # one per company dump (provenance)
└── applications[] : Application        # the core records, one per role
```

### Application (the core record)
| Field | Type | Normalization |
|---|---|---|
| `company` | str | **required** |
| `role_title` | str | **required**, kept **verbatim** (titles don't safely merge) |
| `requisition_id` | str? | as-is |
| `applied_date` | date? | ISO date; **required** that this or `applied_date_raw` is present |
| `applied_date_raw` | str? | original string |
| `dispositioned_date` / `_raw` | date? / str? | ISO date + original |
| `stage_reached` | str? | canonical stage (see below) |
| `stage_reached_raw` | str? | original |
| `outcome` | str? | canonical outcome (see below) |
| `disposition_raw` | str? | original disposition/status text |
| `screening` | Screening | automated telemetry, below |
| `inferences` | dict | freeform automated inferences (seniority, flagged gaps, ...) |
| `source_vendor` / `source_file` | str? | provenance — trace any field back to its file |
| `extra` | dict | **extension bag** — unmapped vendor fields, verbatim |

### Screening (the black-box output)
| Field | Type | Normalization |
|---|---|---|
| `match_score` | 0–100? | `0.63`→63, `"59 / 100"`→59, `"68%"`→68 |
| `match_score_raw` | any? | original value |
| `fit_tier_raw` | str? | vendor tier verbatim (`A`, `Gold`, ...) |
| `fit_quality` | 0.0–1.0? | our cross-vendor quality mapping (see mappings.yml) — **our** call, not the vendor's |
| `parsed_skills[]` | Skill | `name` lowercased, optional `confidence`/`baseline_match` |
| `auto_screened` | bool? | was an automated screen applied |
| `keyword_hits` / `keyword_misses` | int? | as-is |

### Applicant & Source
`Applicant`: `full_name`, `emails[]`, `phone`, `location`, `ca_resident`.
`Source`: `company`, `ats_vendor`, `source_files[]`, `request_date`, `received_date`,
`withholding_noted` (did they admit to withholding under trade-secret claims?).
Both also carry an `extra{}` bag.

## Canonical vocabularies
Defined in [`data/mappings.yml`](data/mappings.yml):

**Stages** (ordered — powers "how far did I get"):
`submitted → application_review → recruiter_screen → assessment →
hiring_manager_review → interview → offer → hired`

**Outcomes:**
`active`, `auto_rejected`, `rejected_after_review`, `rejected_after_interview`,
`withdrew`, `offer`, `hired`, `unknown`

Outcomes are derived from the raw disposition text via keyword rules; a generic
"rejected" is then refined by how far you got — at/after `interview` →
`rejected_after_interview`, else `rejected_after_review`.

**Fit tiers** map to a `fit_quality` 0.0–1.0 (`A`/`Gold`→0.9, `D`→0.2, ...). These
numbers are Appli-CAN!'s judgment for comparison, not a vendor claim. Tune them in
the mappings file, not in code.

## Extending it
- **New vendor string** (a stage/disposition we've never seen) → add an alias or
  keyword in `data/mappings.yml`.
- **New vendor field worth capturing as first-class** → add it to the relevant
  model in `applican/schema.py` (with a `*_raw` companion if it's normalized) and
  bump `SCHEMA_VERSION`.
- **Everything else** → it already survives in `extra{}`; promote it later if it
  proves useful.

## Why not SQLite yet?
This normalized JSON structure is the on-disk contract. Once there's enough data
to query — funnel stats, reasons, cross-company patterns — the same fields become
the table columns. The schema is designed so that migration is a mapping, not a
redesign.

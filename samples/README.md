# Sample ATS Data Dumps (Synthetic)

These are **fabricated** examples of the kind of data an Applicant Tracking
System (ATS) might hand back after a CCPA "Right to Know" request. They exist so
you can test the Appli-CAN! parsing scripts before your own real dumps arrive,
and so the documentation has concrete artifacts to point at.

Nothing here describes a real person, company, or applicant. Company names are
deliberately fictional ("ACME", "Globex", "Initech", "Umbrella").

Each subfolder / file mimics a different ATS "shape" on purpose — the whole point
of the normalize step is that no two vendors agree on field names or structure.

| Sample | Vendor style | Format | What it demonstrates |
|---|---|---|---|
| `workday_acme_corp/` | Workday-style | Multiple JSON files | Nested candidate profile + separate application history + screening telemetry |
| `greenhouse_globex/candidate_export.json` | Greenhouse-style | Single JSON | Flat-ish array of applications with scorecards |
| `initech_generic.csv` | Generic ATS | CSV | Spreadsheet dump, one row per application |
| `umbrella_flattened.txt` | Poorly-flattened PDF | Plain text | The "worst case" — a PDF export dumped to text with no structure |

The interesting fields (the ones the transcript and PDF guide tell you to hunt
for) are seeded throughout: `Fit_Tier`, `DispositionReason`, `StageReached`,
`Parsed_Skills`, match scores, and automated inferences.

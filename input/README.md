# `input/` — put your data dumps here

This is where you drop the raw data an ATS / employer sends back after your CCPA
"Right to Know" request. The pipeline reads from here.

## What goes here
- The `.zip` bundle a company emailed you, **or**
- Its already-extracted `.json` / `.csv` / `.txt` files, or a flattened PDF.

A tidy convention (optional, but it makes cross-referencing easier) is one
subfolder per company:

```
input/
├── acme_corp/          ← unzipped dump from ACME
│   ├── candidate_profile.json
│   └── application_history.json
├── globex/
│   └── candidate_export.json
└── globex_dump.zip     ← or just drop the raw .zip; the extract step handles it
```

## Privacy
**Everything you put in this folder is git-ignored** (except this README), so your
personal data will not be committed or pushed. Don't remove that rule in
`.gitignore` unless you really mean to.

Not sure what a dump looks like yet? See the synthetic examples in `../samples/`.

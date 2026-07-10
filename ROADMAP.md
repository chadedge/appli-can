# Appli-CAN! Roadmap

What V1 does today, and what's deliberately deferred. Ideas here are **not built
yet** — they're captured so they don't get lost.

## V1 — shipped
The core request→parse→report loop:
1. `request_template.md` + `tracker.md` — send CCPA requests and track them.
2. `scripts/extract_compressed_files.py` — unpack archive dumps.
3. `scripts/identify_json_schema.py` / `identify_pdf_schema.py` — discover fields.
4. `scripts/normalize.py` — map any vendor dump onto the master schema ([`SCHEMA.md`](SCHEMA.md)).
5. `scripts/report.py` — per-company funnel + automation-rejection flags.

---

## V2 — email cross-reference
Join your own "thanks but no thanks" / confirmation emails against the ATS
timestamps to (a) catch applications a company *omitted* from its dump, and
(b) sanity-check disposition timing.

**Deferred because:** it requires the user to export a mailbox (Google Takeout
`.mbox`, drag-exported `.eml`, or a manual CSV) — a lot of manual friction for
what is essentially optional timeline garnish. Explicitly **no live email API /
OAuth connector** — everything stays local and offline, parsed with the stdlib
`mailbox`/`email` modules.

---

## V2.5 — community contact directory
A growing, community-contributed list of **where to actually send a request** —
privacy portal URLs, emails, phone numbers — so nobody has to re-do the footer
detective work. Start with FAANG, expand from there.

### Why it matters
"Where do I send this?" is where most people give up. Crowd-maintaining it turns
everyone's one-off research into a shared asset.

### Design principles
- **Freshness is required, not optional.** Every entry carries `last_verified`
  (date) and `source` (where the contact was found). Contacts rot; stale entries
  must be *visible*, never silently wrong.
- **Machine-readable.** Structured YAML keyed by company so `request_template` and
  `tracker.md` can auto-fill from an entry — the directory feeds the pipeline.
- **Aliases / legacy entities are first-class.** A lookup for a merged company must
  surface predecessor names, or post-merger applicants search the wrong system
  (see the Paramount → Paramount Global / ViacomCBS / CBS / Viacom case).
- **Per-company gotchas.** Capture the traps: e.g. **Meta** — you must *have and
  authenticate an account* to even see whether data exists (no account = no
  visibility). **Amazon/Google** flows differ per business unit, etc.
- **Not legal advice.** Entries are pointers only; the disclaimer in the readme
  applies.

### Proposed entry shape
```yaml
- name: Paramount
  aliases: [Paramount Skydance, Paramount Global, ViacomCBS, CBS, Viacom]
  privacy_portal: https://privacy.paramount.com/privacyrightscenter
  privacy_email: null                      # portal-only at time of writing
  phone: "(888) 841-3343"
  mail: "Paramount Skydance Corp, Attn: Privacy Team, 1515 Broadway, NY 10036"
  applicant_data_notes: >
    Consumer policy makes no distinction for applicants/employees — you must
    self-select "Right to Know" and state you're a former employee AND a repeat
    applicant. Records may be siloed under legacy entity names (request all).
  gotchas:
    - "Publicly disclaims automated decisions with 'legal or similarly significant
       effect' — ask them to CONFIRM in writing whether any screening/scoring
       touched your applications."
  last_verified: 2026-07-09
  source: https://privacy.paramount.com/en/policy
```

### Contribution model
- One YAML file (e.g. `data/company_directory.yml`), edited via PR.
- A short `CONTRIBUTING.md`: how to add an entry, verify a contact, cite a source.
- Later: a validator/CI check that entries parse and `last_verified` isn't ancient.

---

## Later / unsorted
- `CLAUDE.md` or other LLM system training + tests around the mapping rules (the logic-dense part).
- Harden vendor adapters against real Workday/Greenhouse exports.
- A "withholding log" tracker — record what each company refused and why.

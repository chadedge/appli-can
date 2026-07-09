# Appli-CAN!

> "It's Appli-CAN, not AppliCAN'T!"

## Introduction
Yes, a dumb pun, but it makes sense to me (Chad Edge).  I'm frustrated - I'm assuming you are too if you found your way to this repository - when it comes to the _black box_ of submitting resume after resume (and often retyping) into an applicant tracking system.

How many nights have you sat around, reading Reddit threads or watching HR-expert videos on your favorite (or addicted) social media platfrm that include comments about "scoring systems," or "AI profiling," or the Mobley v Workday legal case?

How much time do you spend fretting about "what does this company / job board _know_ about me that they're not telling me?"

***Well, I have good news and bad news (and it likely differs depending on where you live).***
1. If you live in California (USA - and all focus of this repository is for us poor folks here in the USA) there are protections in place (CCPA, GDPR, [another]) that will help you, fair job-seeker, to retrieve much of the information applicant tracking systems store.
2. While there _are_ laws protecting your rights to access to data, a large portion of the truly useful stuff (inference, internal notes) are _not_ subject to data and identity requests.

***What this means for you***
1. Using the template script (request_template.md) you can very easily request _much_ of the data stored in most applicant tracking systems (with caveats like company size, location).
2. You are likely able to retrieve data _you_ entered (which position, dates and times, resume data or history you've provided).
3. With varying success, you _may_ be able to retrieve automated inference scores.
4. It is unlikely you will be able to retrieve _reasoning_ behind scoring or decisions (often these are protected behind walls like "company/trade secret"). I wouldn't expect you'll get access to something like "What is the _literal_ prompt or response used to have generated a decision or score?"

> ⚠️ **Not legal advice.** This project is a self-help toolkit, not a lawyer.
> Thresholds and exemptions vary by company size, your state of residence, and
> the specific facts. See California's official CCPA guidance at oag.ca.gov/privacy/ccpa.

## How to use this system

Appli-CAN! has two halves: **requesting** your data, and **parsing** what comes
back. The request half works today; the parsing half is being built (see the
scripts in `scripts/` and the synthetic examples in `samples/`).

### Step 1 — Build your target list
Make a list of the companies you've applied to. If you use Workday, Greenhouse,
Lever, or similar, you likely have a trail of "no reply" / "thanks but no thanks"
emails you can mine for company names, role titles, and dates. That list is both
your request queue *and* the seed for the funnel dashboard later.

Copy `tracker.md` to `input/tracker.md` and log each company there as you go — it's
a simple by-hand table for *who you asked, when, and whether they answered*. (When
you move on to parsing dumps for reasons and reports, the project graduates to a
SQLite database; the Markdown tracker is all you need until then.)

### Step 2 — Find each company's privacy channel
CCPA requests go to the **hiring company**, not to the ATS vendor — Workday and
friends are only "service providers" that host the data on the employer's behalf.
Look at the footer of the company's main website for:
- "Privacy Policy" / "Your Privacy Choices" / "California Privacy Rights", or
- "Do Not Sell or Share My Personal Information"

These pages are legally required to list a request email (often
`privacy@company.com`) or a web form.

### Step 3 — Send the request
Copy `request_template.md`, fill in the bracketed fields (`[Your Name]`,
`[Your Email]`, etc.), and send it. The template is worded deliberately to invoke
formal statutory terms (Request to Know, expired Employee Data Exemption,
automated screening scores, withholding log) so it routes to legal/compliance
instead of getting a lazy auto-reply.

### Step 4 — Survive identity verification
Expect a reply asking you to confirm who you are. Common asks: reply from the
exact email you applied with, or name the specific roles/dates you applied for.
This is why Step 1 matters — have your application list ready.

### Step 5 — Receive the data (≈45 days)
By law they should respond within a **45-day window** (extendable once). What
lands in your inbox is usually a **zipped bundle of `.json` / `.csv` files**, or
sometimes a flattened PDF. It will be raw and ugly — that's expected and, honestly,
the good case. Drop it into the parsing pipeline below.

### What you'll get vs. what stays hidden
| You can usually get | Usually withheld |
|---|---|
| The data you entered (roles, dates, resume fields) | The *reasoning* behind a score |
| Automated inferences, parsed skills, match tiers | The scoring formula / weights / prompt (trade secret) |
| Screening scores, fit ratings, disposition reasons | Subjective human recruiter notes, privileged work product |
| A withholding log (if you ask for one) | Third-party info (e.g. another employee's feedback) |

## How to parse your returned data

The goal of the parsing half is to turn each company's mismatched dump into **one
common structure**, then cross-reference it against your own application timeline
to build a funnel view. No two ATS vendors agree on field names — compare the
files in `samples/` to see the problem (`Fit_Tier` vs `match_tier` vs `fit_rating`,
`DispositionReason` vs `rejection_reason` vs `Final Disposition`, and so on).

### The pipeline
```
  your .zip dump
        │
        ▼
  1. extract_compressed_files.py   →  unpack the archive into a working folder
        │
        ▼
  2. identify_json_schema.py       →  discover the fields & types each vendor used
     identify_pdf_schema.py            (JSON/CSV vs. flattened-PDF text)
        │
        ▼
  3. normalize  (planned)          →  map vendor fields onto the common schema
        │
        ▼
  4. cross-reference emails (planned) → join ATS timestamps against your
        │                                "thanks but no thanks" email history
        ▼
  5. funnel dashboard / report     →  see the black box, per company
```

> **Status:** the `scripts/` files are currently stubs (docstrings only). Steps
> 3–5 are planned. Until they land, you can still eyeball your dumps — the field
> guide below tells you what to look for.

### What to hunt for in the raw data
Regardless of vendor, these are the high-value fields the guide and transcript
call out. Open your files and search for anything resembling:

| Concept | Field names seen across vendors |
|---|---|
| Automated fit tier | `Fit_Tier`, `match_tier`, `fit_rating`, `System Fit Tier` |
| Match score | `matchScorePercent`, `match_score`, `match_pct`, `Automated Match Score` |
| Disposition / rejection | `DispositionReason`, `rejection_reason`, `disposition`, `Final Disposition` |
| Furthest stage | `StageReached`, `current_stage`, `last_stage`, `Furthest Stage` |
| Parsed skills | `Parsed_Skills`, `parsed_keywords_matched`, `skills_parsed`, `Parsed Competencies` |
| Auto-screened flag | `autoAdvanced`, `auto_screened`, `Automation Screen Applied` |

**Tell-tale signs of a purely automated rejection:** a disposition timestamp only
seconds after you applied, an `autoAdvanced: false` next to a low `Fit_Tier`, or a
note like "minimum qualifications not met" with no human reviewer attached. The
ACME sample (`samples/workday_acme_corp/`) has a rejection dispositioned 118
seconds after submission — that's the kind of thing this project exists to surface.

### Try it against the samples
The `samples/` folder contains synthetic dumps in four different shapes (Workday-,
Greenhouse-, and generic-CSV-style, plus a flattened-PDF text file) so you can
develop and test the pipeline before your real data arrives. See
`samples/README.md` for the map.
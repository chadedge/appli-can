# Request Tracker

A dead-simple, copy-and-edit log of every CCPA request you send. No database, no
tooling — just a Markdown table you update by hand. It answers three questions at
a glance: **who did I ask, when, and did they answer?**

> This starts as plain Markdown on purpose. Once you have dumps to parse and want
> real reports on *reasons* and funnel stats, the project graduates to a SQLite
> database — but you don't need that just to keep track of who owes you a response.

## How to use it
1. Copy this file to your own working copy so your entries stay private.
   The `input/` folder is git-ignored, so a good home is `input/tracker.md`:
   ```
   cp tracker.md input/tracker.md
   ```
2. Add one row per company each time you send a request (from `request_template.md`).
3. Fill in **Requested** the day you send it. **Due** is that date **+ 45 days** —
   the statutory response window.
4. Update **Status** and **Received** as replies come in. When a dump arrives, drop
   it in `input/<company>/` and tick the **In `input/`?** column.

### Status legend
| Symbol | Meaning |
|---|---|
| 📤 | Request sent |
| 🪪 | They asked me to verify my identity |
| ⏳ | Verified / waiting on data (within 45-day window) |
| ✅ | Data received |
| 🚫 | Refused, or ignored past the deadline |

## Tracker

| Company | ATS | Roles / dates applied | Privacy contact | Requested | Due (+45d) | Status | Received | In `input/`? | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ACME Corp | Workday | Sr Backend Eng, Staff SWE — Feb–May 2024 | privacy@acme.example | 2026-07-09 | 2026-08-23 | ✅ | 2026-08-01 | yes | Dump had a rejection dispositioned 118s after applying |
| Globex | Greenhouse | Platform Eng — Mar 2024 | dsr@globex.example (web form) | 2026-07-09 | 2026-08-23 | ⏳ | — | no | Verified via applied-from email |
| Initech | (unknown) | SWE, Sr SWE, Eng Mgr — Jan–May 2024 | Found "CA Privacy Rights" in footer | 2026-07-09 | 2026-08-23 | 🪪 | — | no | Replied asking me to name the roles I applied for |
| Umbrella Corp | (unknown) | Cloud Infra, SRE — Mar–Jun 2024 | privacy@umbrella.example | 2026-07-09 | 2026-08-23 | 📤 | — | no | — |

_(The rows above are examples using the fictional companies from `samples/`.
Delete them and add your own.)_

# Reference — Tier 3: CORDIS & EU project-deliverable forensics

Copyright © 2026 Juliano Ramanantsoa. MIT License.

I added this tier because, in the European research-infrastructure world I work in, a dataset is very often *described* in a project deliverable, a Data Management Plan, or a work-package report long before it is registered in a catalogue — and sometimes it never reaches a catalogue at all. CORDIS, the EU's project portal, is where that paper trail starts. Treat what you find here as **forensic evidence** (`resourceRole: forensic_evidence`): it tells you the dataset's name, who owns it, where it should live, and under what conditions — not a direct download.

## When I reach for this tier
- The data are tied to a named EU project (Horizon Europe / H2020 — e.g. Geo-INQUIRE, EPOS-related actions, ENVRI).
- Tiers 1–2 returned nothing, or returned only a service with no obvious dataset.
- I need to know the *responsible partner* or *work-package owner* to ask the right person (this then feeds the dark-data steward step).

## What deliverables typically reveal
Dataset and service names; the responsible partner and work-package owner; the intended repository; embargo and access conditions; the data manager; and links to Zenodo communities or institutional project pages. Any one of these turns a dead end into a precise next action.

## Query templates
Replace the bracketed parts. The engine emits these as Tier-3 leads when run with `--cordis --acronym <ACRONYM>`.

```text
site:cordis.europa.eu "[project acronym]" dataset
site:cordis.europa.eu "[variable]" "[region]"
"[project acronym]" "deliverable" "data"
"[project acronym]" "Data Management Plan"
"[project acronym]" "DMP"
"[project acronym]" "repository"
"[project acronym]" "Zenodo"
"[project acronym]" "work package" "data"
"[project acronym]" "FAIR" "data"
"[project acronym]" "access" "dataset"
```

## How I turn a Tier-3 hit into data
1. **Read the deliverable / DMP** for the dataset name, the repository, the responsible partner and the access conditions.
2. **Jump back to Tier 1–2** with the exact dataset or repository name (often a Zenodo community or an institutional node) and run the verification gate on whatever direct link you find.
3. **If it is restricted**, record `FOUND_RESTRICTED`, name the work-package owner / data manager as the steward (from the deliverable, an authoritative public source), and route through the project's official contact — never a guessed personal address (see the dark-data playbook and DISCLAIMER.md).
4. **If there is genuinely no access**, propose a proxy and record `PROXY_RECOMMENDED`, describing the scientific loss.

## Honesty rules (same as the rest of the method)
A CORDIS page or deliverable is evidence, not data. Do not promote it to `actual_data`. Do not state that a dataset is available because a project *says* it produced it — only a verified, resolving direct link earns `DATA_AVAILABLE`.

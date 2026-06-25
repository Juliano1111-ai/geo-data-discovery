---
name: geo-data-discovery
description: >-
  Find directly-downloadable geoscience data with VERIFIED access links and
  machine-ingestible (schema.org / DCAT) metadata, and — when data is not in standard infrastructures — run a "dark
  data" forensic trail to prove it exists, name the human steward, and find a
  proxy. Use WHENEVER the user wants to locate, discover or source scientific
  data (GNSS / ground motion, seismic waveforms or catalogs, reanalysis /
  climate / atmosphere, ocean, bathymetry, satellite / EO), asks where a dataset
  "lives" or how to download it, wants to check that data URLs or DOIs actually
  resolve, needs a dataset catalogue as JSON-LD for a data cube or map, or can't
  find data and needs the academic-trail / steward / proxy pathway. Trigger even
  if they just say "find me data on X", "where can I get Y", "is dataset Z
  available", "who has the … data", or paste a variable + region + timeframe. It
  enforces a verification gate that stops hallucinated download links — prefer it
  over answering data-location questions from memory.
---

# Geoscience Data Discovery (with a verification gate)

This skill turns "find me data" into a disciplined pipeline. The core idea: **a
language model is not a search engine and must never emit a download link it has
not resolved.** The model here is an *orchestrator* — it expands the query,
routes each part to the correct machine endpoint, and synthesises results — but
every access link passes a Verification Gate before it reaches the user.

It has two modes. Pick the mode first, then follow that mode's reference file.

| Mode | Use when | Reference to read |
|---|---|---|
| **DISCOVERY** | The data probably exists in a known infrastructure and the job is to find the downloadable product. | `references/discovery_playbook.md` |
| **DARK DATA** | Standard catalogues return nothing, or the data is restricted / embargoed / buried in a thesis / committed in code. | `references/dark_data_playbook.md` |

Many requests start in DISCOVERY and fall through to DARK DATA when the open
product isn't there (e.g. a registered seismic network whose waveforms are
mostly restricted). That hand-off is normal — say so and switch.

For data tied to an EU project (Horizon Europe / H2020 — e.g. Geo-INQUIRE, EPOS,
ENVRI), also work **Tier 3: CORDIS & project deliverables**
(`references/cordis_project_deliverables_playbook.md`): in European RIs the data
are often described in a deliverable or Data Management Plan before they reach any
catalogue. Treat those hits as `forensic_evidence`, not data.

## THE NON-NEGOTIABLE RULE — the Verification Gate (v1.0.0)

A link reaching the output is necessary but **not sufficient**. Resolve every
DOI/URL this run (DOIs via `https://doi.org/<doi>`), record the HTTP status and a
UTC timestamp — then apply these v1.0.0 rules so nothing overclaims:

- **HTTP 200 = resolved, not verified data.** Record a *validation level*:
  0 unresolved · 1 service responded · 2 content type/structure correct ·
  3 data non-empty · 4 content matches the target (non-zero miniSEED bytes; a
  non-empty FDSN station list; a DOI that resolves to access metadata; JSON that
  parses; a CSV with rows). HTML landing pages stop at level 1 — they are not data.
- **Tag every record with a `resourceRole`** — `actual_data`, `metadata_evidence`,
  `availability_evidence`, `catalogue_record`, `forensic_evidence`, `proxy_data`,
  `restricted_lead`, `unresolved_lead`, `test_fixture`. A station inventory is
  `metadata_evidence`; the waveforms are `actual_data`. Never conflate them.
- **Split the outputs.** Only resources actually reached (`DATA_AVAILABLE` or
  verified `METADATA_ONLY`) go to `verified_catalog.jsonld`. Restricted resources
  (HTTP 401/403) → `restricted_leads.json`; everything else → `unresolved_leads.json`;
  every check → `access_validation_log.csv`.
- **End with one machine-readable status:** `FOUND_AVAILABLE`, `FOUND_RESTRICTED`,
  `DARK_TRACE`, `PROXY_RECOMMENDED`, or `NOT_FOUND_AFTER_PROTOCOL`. Do not invent
  endpoints, availability, contacts or access conditions; if the full protocol
  finds nothing, the answer is `NOT_FOUND_AFTER_PROTOCOL`.

The `scripts/discovery_orchestrator.py` engine implements all of the above; run it
rather than reproducing this logic by hand, then narrate the result.

### Original gate principle (still holds)
No DOI or URL goes into any output unless it was **resolved this run**. Resolve
DOIs through `https://doi.org/<doi>`; do an HTTP HEAD (fall back to a ranged GET
on 403/405/501); record the status and a UTC timestamp. Links that resolve
(200–399) go in the main answer; links that fail are quarantined into a clearly
separate "UNRESOLVED LEADS" block with the reason — never silently dropped, never
silently promoted. This single rule is the difference between a demo and a tool:
it is what stops the model from confidently handing over plausible-looking
endpoints that resolve to nothing.

If you have **no retrieval tool at all**, do not pretend to search. Produce a
labelled *plan* — the exact queries, endpoints and parameters to run — and mark
every URL "UNVERIFIED — template only".

## The workflow (both modes)

1. **Build a QueryPlan first** (auditable, reproducible). Decompose the target
   into: expanded controlled-vocabulary TERMS (synonyms — hook a real thesaurus
   such as GCMD / GEMET / an EPOS-SKOS vocabulary where available); a SPATIAL
   bounding box `[West, South, East, North]` plus gazetteer name and ISO country
   code; a TEMPORAL ISO-8601 interval `start/end`; and the expected TYPE / data
   velocity (archive vs near-real-time vs reanalysis-model) and distribution
   format (miniSEED, RINEX/tenv3, NetCDF/GRIB, GeoTIFF, CSV). Emit this block
   before retrieving anything.
2. **Route, don't guess the homepage.** Use the routing table in
   `references/endpoints.md` to send each query to a real API. A homepage with no
   listed endpoint → first hit a catalogue API (DataCite / re3data / OpenAIRE /
   B2FIND) to *discover* the endpoint, then query it.
3. **Retrieve** with parallel expanded queries. One miss on one phrasing must not
   end the search. Don't stop until every clause of the target is grounded or
   explicitly marked unretrievable with a reason.
4. **Pass everything through the Verification Gate** (above).
5. **Rank** high→low: Tier 1 global/continental core infrastructure > Tier 2
   national agency / certified repository > Tier 3 individual paper / local node;
   +verified-this-run; +has-DOI; consult CoreTrustSeal / re3data certification.
6. **Emit the output contract** for the mode (below).

## Running the orchestrator

`scripts/discovery_orchestrator.py` is the executable backbone for DISCOVERY: it
expands a query, calls real backends, runs the Verification Gate, ranks, and
writes valid `schema.org/Dataset` JSON-LD. Pure standard library — no installs.

```bash
# Demo mode — exercises the full path (expand → gate → emit) with reachable links
python scripts/discovery_orchestrator.py \
  --query "Ground motion GNSS tectonic displacement Andalusia" \
  --bbox "-7.6,36.0,-1.6,38.8" --start 2020-01-01 --end 2026-12-31

# Live mode — hits DataCite / Zenodo / re3data for real (needs open network)
python scripts/discovery_orchestrator.py --query "..." --bbox "..." --live --out catalogue.jsonld
```

Confirm it prints `Verified (resolved) links: N/M` — only the verified rows are
safe to publish as "Direct Access Link". It writes a JSON-LD array ready to drop
into a Spatial Data Cube or map. For **seismic waveforms**, the right backend is
FDSN web services, not a generic catalogue — drive them with ObsPy and let
EIDA/IRIS routing resolve the rest:

```python
from obspy.clients.fdsn import Client
inv = Client("GEOFON").get_stations(network="CP", starttime="2024-01-01",
                                    endtime="2024-12-31", level="station")
# then Client(...).get_waveforms(...) for the open stations
```

Extend the `BACKEND` clients and the routing table as services evolve — that file
is the part most likely to need maintenance (endpoints move; see `endpoints.md`).

## Output contracts

**DISCOVERY** → two artifacts, no preamble: (1) an EXECUTIVE SUMMARY TABLE sorted
high→low reliability with columns `# | Tier | Reliability | Verified
(status+UTC) | Velocity | Source Node | Dataset | bbox [W,S,E,N] | Temporal
(ISO) | Access Protocol | Direct Access Link`, plus an UNRESOLVED LEADS block;
(2) a valid `schema.org/Dataset` JSON-LD array (see playbook for required keys).

**DARK DATA** → an INVESTIGATION DOSSIER: classify the kind of darkness, then
(1) FORENSIC EVIDENCE TABLE, (2) HUMAN CONTACT & STEWARDSHIP INDEX, (3)
ALTERNATIVE PROXY PATHS — ending in a chase-vs-proxy routing recommendation. The
dark-data playbook carries a hard anti-fabrication rule: **never invent a
person's email/phone/address**; surface only contacts from authoritative public
sources and label each `verified-from-source` or `inferred`.

## A note on scope (don't over-use the model)

If you already know exactly where the data lives — FDSN for waveforms, the Nevada
Geodetic Lab or EPOS-GNSS for processed GNSS, the Copernicus CDS (`cdsapi`) for
ERA5, the `copernicusmarine` toolbox for ocean physics — **just call that API
directly.** The LLM-orchestrated discovery earns its cost only when the *where*
is genuinely open, when synthesising across many heterogeneous catalogues, or for
the dark-data forensic trail. Use the cheap path when the cheap path works.

## Worked examples and maintenance

`references/endpoints.md` holds the machine-endpoint routing table, current
stale-seed flags (e.g. the Copernicus CDS API migration; OpenGrey being
discontinued), and two fully worked targets — Andalusia GNSS ground motion and
Azores 2024 seismic waveforms — to copy from.

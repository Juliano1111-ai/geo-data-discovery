# Reference — DARK DATA forensics playbook

Read this when standard catalogues return nothing, or the data is restricted /
embargoed / buried in a thesis / committed inside code. The Verification Gate
still applies to every cited link.

## First, classify the kind of darkness — it dictates the method
- **Linked-but-unindexed** — a dataset DOI exists and is *cited by* a paper, but
  no catalogue surfaced it. → Walk the relatedIdentifier graph (machine-tractable).
- **Exists-but-restricted/embargoed** — provably exists (a registered network,
  an instrument, a DOI) but the bytes are gated. → Prove existence, enumerate it,
  identify the operator, find the access pathway (semi-machine).
- **Supplementary / "available upon request"** — thesis appendix, journal
  supplement, a researcher's drive. → Academic trail + human steward.
- **Code-embedded** — a CSV/NetCDF committed inside a research repo. → Code search.
- **Truly offline** — paper archives, never digitised. → Human steward only.

State which kind you are chasing at the top of the dossier.

## Anti-fabrication guardrail — non-negotiable
- Surface ONLY contact pathways that appear in an authoritative public source:
  the dataset/network DOI metadata's contact field, the repository's official
  contact / data-access page, an institutional lab page, a corresponding-author
  block, or a public ORCID record. Link the source.
- Label every contact `provenance: verified-from-source` or `provenance:
  inferred`. If inferred, give the stewardship *role* and official *route*, not a
  guessed personal email. Do not assemble personal dossiers.
- A wrong invented contact is worse than an honest "operator is X; use their
  official data-request form: <link>".

## The forensic trail, step by step
1. **Prove existence first.** A registered network/instrument, a minted DOI, a
   named dataset in a paper's Data Availability statement, or an enumerable
   inventory (FDSN availability, an ERDDAP `info` page). State the evidence.
2. **Walk the graph.** Paper DOI → Crossref/OpenAlex → DataCite/OpenAIRE for
   *related* dataset & software PIDs → resolve them. Author → ORCID → full dataset
   output. Region/instrument → re3data subject+country → the local node.
3. **Enumerate the restricted.** List exactly what exists (stations, variables,
   time windows, granule counts) so the request to the steward is precise and the
   proxy decision is informed.
4. **Name the steward + real pathway.** Operating institution / lab / PI role and
   the official access route. Apply the anti-fabrication rule.
5. **Build the proxy ladder.** Ranked openly-downloadable substitutes covering the
   same variable/region/period, each itself passed through the Verification Gate.
   Proxy logic examples:
   - Local GNSS RINEX gated → Nevada Geodetic Lab global PPP position time series
     (`http://geodesy.unr.edu/`) for the same station codes; and/or EPOS-GNSS /
     EUREF chain (Spain node: CNIG/IGN).
   - Specific waveform network embargoed → the open subset on EIDA/GEOFON + the
     nearest open national network (e.g. Portuguese IPMA stations for the Azores
     region) via FDSN.
   - Regional reanalysis gated → ERA5 from the Copernicus CDS as a baseline.

## Forensic seed registry — with machine endpoints and health flags
| Lead type | Where / how |
|---|---|
| Dataset↔paper↔project graph | OpenAIRE Graph API; DataCite record `relatedIdentifiers` (IsSupplementTo / IsSourceOf / Cites / IsPartOf) |
| Literature cross-ref | Crossref REST `api.crossref.org/works`; OpenAlex `api.openalex.org/works`; Semantic Scholar |
| Researcher → steward | ORCID Public API `pub.orcid.org/v3.0/<id>/works` → datasets, affiliations |
| Theses / hidden appendices | WorldCat dissertations; DART-Europe, theses.fr, DiVA, NDLTD; university DSpace OAI |
| Code-embedded data | GitHub code search API `api.github.com/search/code?q=...+extension:csv|nc|h5`; GitLab; Software Heritage |
| Seismic existence/enumeration | FDSN network registry `fdsn.org/networks/`; `station/1/query` + `availability/1/query` reveal stations/time-windows even when waveforms are restricted |
| Gray literature (EU, historical) | OpenGrey — **discontinued / no longer updated; the DANS archive holds the legacy corpus** — verify, don't assume live |
| US federal deep web | Science.gov; USGS ScienceBase; NOAA NCEI |
| Repository trust / obscure archives | CoreTrustSeal registry; re3data (subject + country filter for hyper-local nodes) |
| Researcher networks (last resort) | ResearchGate / Academia.edu — to *locate* a person/preprint, then route to the official channel; low-trust |
| Scholar advanced syntax | Google Scholar with `"supplementary data"`, `"data available upon request"`, `site:`, `filetype:` |

## Output contract — DARK DATA INVESTIGATION DOSSIER, no preamble
Classify the dark-data type, then three sections:
1. **FORENSIC EVIDENCE TABLE** — `# | Evidence type | Title/ID | DOI/PID |
   Resolves? (status+UTC) | What it proves about the hidden data | Link`
2. **HUMAN CONTACT & STEWARDSHIP INDEX** — `# | Stewardship role | Institution |
   Official access pathway | provenance: verified-from-source | inferred | Source`
3. **ALTERNATIVE PROXY PATHS** — `# | Proxy dataset | Covers (variable/region/
   period) | Why it substitutes | Openly downloadable? | Resolves? (status+UTC) |
   Direct Access Link`

End with a one-line ROUTING RECOMMENDATION: chase-the-restricted vs use-the-proxy,
with the reason.

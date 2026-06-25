# Changelog

All notable changes to this project are documented here. Copyright © 2026 Juliano Ramanantsoa. MIT License.

## [1.0.1] - 2026-06-25

Patch release fixing query-type routing and the output contract for non-Claude assistants.

### Added
- **Earthquake-catalogue routing.** A magnitude / event / seismicity query now routes to the FDSN **event** service and recomputed catalogues (USGS ComCat, ISC Bulletin, ISC-GEM `10.31905/D808B825`, NOAA NCEI `10.7289/V5TD9V7K`) instead of waveform endpoints. Added `is_event_catalog`, `build_event_url`, `extract_min_magnitude`, `fdsn_event_candidates`, and 5 routing tests (suite now 21 tests).
- Earthquake-catalogue sources in `endpoints.md`.
- Ready-to-run entry points: `quickstart.py` (zero-dependency), a Google Colab notebook (`notebooks/geo_data_discovery_colab.ipynb`), `requirements.txt`, and `DEPLOY.md` (full GitHub / Zenodo / ReadTheDocs guide) with a buildable `docs/` Jupyter Book.

### Changed
- **Hardened the discovery playbook output contract.** `discovery_playbook.md` now opens with a non-skippable "STOP — data table + JSON-LD only, no report" rule, so a model (e.g. Gemini) cannot default to producing a prose essay with the data buried at the end. JSON-LD contract updated to the v1.0.0 honesty fields.
- `USAGE.md`: explicit warning that Gemini defaults to essays, with the one-line "data-only" prompt suffix and the playbook-not-just-SKILL.md guidance.

### Fixed
- Magnitude/event queries no longer mis-route to FDSN `dataselect` (raw waveforms).

## [1.0.0] - 2026-06-25

First public release. This version hardens the prototype so that the implementation enforces the claims of the method.

### Added
- **Output separation.** Verified resources (`verified_catalog.jsonld`), restricted resources (`restricted_leads.json`), unresolved leads (`unresolved_leads.json`), a full `access_validation_log.csv`, and a machine-readable `workflow_status.json`. Only resources that were actually reached enter the verified catalogue.
- **Validation levels (0-4).** HTTP 200 is recorded as "resolved" only; data are confirmed by protocol-specific checks (non-zero miniSEED bytes, non-empty FDSN station list, DOI resolution, JSON/CSV parsing). HTTP 200 alone no longer counts as verified data.
- **`resourceRole` field** on every record (`actual_data`, `metadata_evidence`, `availability_evidence`, `catalogue_record`, `forensic_evidence`, `proxy_data`, `restricted_lead`, `unresolved_lead`, `test_fixture`) so metadata is never mistaken for data.
- **Formal workflow statuses:** `FOUND_AVAILABLE`, `FOUND_RESTRICTED`, `DARK_TRACE`, `PROXY_RECOMMENDED`, `NOT_FOUND_AFTER_PROTOCOL`.
- **Tier 3 - CORDIS & EU project deliverables** routing, with a dedicated playbook and query templates (CORDIS, DMPs, work packages, Zenodo communities).
- **Tests** (`tests/`) and **continuous integration** (`.github/workflows/ci.yml`): compile check, pytest, and JSON-Schema validation of the examples.
- **JSON Schema** for the verified catalogue (`schemas/discovery_output.schema.json`).
- **Copyright headers, LICENSE, and DISCLAIMER.md.**

### Changed
- Documentation rewritten to state plainly what the tool can and cannot prove.
- Example JSON-LD catalogues extended with `resourceRole`, `dataStatus`, `accessProtocol`, `isAccessibleForFree` and a verification block.

### Removed
- Misleading demo stand-ins. Synthetic test fixtures are now labelled `test_fixture` and never carry a real provider's name; a reachable URL is no longer presented as a scientific data source.

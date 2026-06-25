# Reference — machine endpoints, maintenance flags, worked examples

The single most maintenance-prone part of this skill. Endpoints move; verify
before trusting. When one changes, fix it here and in
`scripts/discovery_orchestrator.py`'s `BACKEND` clients.

## Routing table — homepage → MACHINE endpoint (parameterise from the QueryPlan)

| Domain / node | Machine endpoint to call (not the homepage) |
|---|---|
| Cross-domain DOI graph | DataCite REST `https://api.datacite.org/dois?query=...&resource-type-id=dataset` |
| Repository discovery | re3data API `https://www.re3data.org/api/v1/repositories?query=...&country=...` |
| Publication↔data graph | OpenAIRE Graph API (`https://api.openaire.eu/...`) |
| EU harvester | B2FIND (CKAN) `https://b2find.eudat.eu/api/3/action/package_search?q=...` |
| Generalist repo | Zenodo `https://zenodo.org/api/records?q=...&type=dataset` |
| Generalist repo | Harvard Dataverse `/api/search?q=...&type=dataset` |
| **Seismic waveforms/metadata** | **FDSN web services**: `dataselect/1/query` (waveforms), `station/1/query` (inventory), `availability/1/query` (what exists). Federate via IRIS fedcatalog / EIDA routing. Drive with **ObsPy** `obspy.clients.fdsn`. |
| Earthquake catalogs | FDSN `event/1/query`; USGS ComCat `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| Earth-environmental data | PANGAEA: OAI-PMH `https://ws.pangaea.de/oai/`, or the `pangaeapy` client; record DOIs resolve to tabular/NetCDF |
| Ocean physics / NRT + reanalysis | Copernicus Marine — **`copernicusmarine` Python toolbox** (old MOTU/subset servers retired) |
| Marine in-situ / bathymetry | EMODnet — **ERDDAP** (`/erddap/griddap|tabledap`), WMS/WFS/WCS |
| Climate / atmosphere | Copernicus **CDS** `https://cds.climate.copernicus.eu/api` via `cdsapi` (ECMWF Personal Access Token; syntax changed in 2024) |
| Gridded model/obs | Any **ERDDAP** or **THREDDS/OPeNDAP** server; **STAC** catalogues for EO imagery |
| Argo floats | Argo GDAC (Ifremer/US) + the `argopy` client |

## Earthquake catalogues / event lists (magnitude & event queries)
A magnitude / event / seismicity query wants an event **catalogue**, not waveforms.
Route to the FDSN **event** service or a recomputed catalogue (these return the data):

| Source | Where / how |
|---|---|
| USGS ANSS ComCat | `https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=&endtime=&minmagnitude=&minlatitude=&maxlatitude=&minlongitude=&maxlongitude=` |
| ISC Bulletin | `http://www.isc.ac.uk/fdsnws/event/1/query?...` (also EMSC `seismicportal.eu`, ESM `esm-db.eu`) |
| ISC-GEM (instrumental, 1904–, recomputed Mw) | DOI `10.31905/D808B825` (CSV) |
| NOAA NCEI Significant Earthquakes (2150 BC–present, historical) | DOI `10.7289/V5TD9V7K` (TSV) — use for pre-instrumental events |

## Tier 3 — CORDIS & EU project deliverables (added v1.0.0)
In European RIs the data are often described in a deliverable, a Data Management
Plan or a work-package report before they reach a catalogue. Search these as
`forensic_evidence` (leads, not data); see `cordis_project_deliverables_playbook.md`.

| Lead | Where / how |
|---|---|
| EU project portal | CORDIS `https://cordis.europa.eu/` (search by acronym, variable, region) |
| Deliverables / DMPs | `site:cordis.europa.eu "[acronym]" dataset` · `"[acronym]" "Data Management Plan"` |
| Project outputs | `"[acronym]" Zenodo community` · `"[acronym]" "work package" data` · institutional project pages |

## Stale-seed flags (known as of mid-2026 — re-verify periodically)
- **Copernicus Climate Data Store**: the legacy CDS was decommissioned on
  2024-09-26 and all legacy-API requests fail. The live API is
  `https://cds.climate.copernicus.eu/api`, needs an ECMWF account + Personal
  Access Token, and the `cdsapi` request syntax changed. Old credentials and old
  scripts will silently fail. Use the dataset page's "Show API request" button to
  get current syntax.
- **Copernicus Marine**: the old MOTU / subsetter endpoints were retired in favour
  of the `copernicusmarine` Python toolbox. Scripts targeting the old service break.
- **OpenGrey**: discontinued / no longer updated. The DANS-KNAW archive holds the
  legacy corpus. Treat as historical, not a live search.

## Worked example A — Andalusia GNSS ground motion (DISCOVERY)
QueryPlan: TERMS {ground motion, crustal deformation, GNSS position time series,
geodetic time series, tectonic displacement}; bbox ≈ `[-7.6, 36.0, -1.6, 38.8]`
(ES); temporal `2020-01-01/2026-12-31`; type archive, format tenv3/RINEX.

Where it actually lives (route here; don't invent a portal):
- **Nevada Geodetic Laboratory** (`http://geodesy.unr.edu/`) — processed daily PPP
  position time series for >17,000 global stations in the IGS14 frame; the de-facto
  ready-made product other deformation studies build on. Best first stop for a
  ready time series.
- **EPOS-GNSS / EUREF** product chain — for the authoritative European product;
  the Spain national node is **CNIG** (National Centre for Geographic
  Information); consortium contact `general@gnss-epos.eu`.
- **IGN Spain** (`ign.es`) — national network operator; **SONEL** also redistributes
  NGL solutions.

Run: `python scripts/discovery_orchestrator.py --query "Ground motion GNSS
tectonic displacement Andalusia" --bbox "-7.6,36.0,-1.6,38.8" --start 2020-01-01
--end 2026-12-31 --live`.

## Worked example B — Azores 2024 seismic waveforms (DISCOVERY → DARK DATA)
This one starts in DISCOVERY and falls through to DARK DATA — a textbook
exists-but-restricted case.
- The Azores network is **CIVISA**, FDSN network code **CP**, DOI
  `10.14470/PC311625`. It is registered and real.
- BUT only ~2 of its stations are openly available at GEOFON; the rest are
  restricted → DARK DATA, exists-but-restricted.
- Correct retrieval is **FDSN web services** (not a generic catalogue):
  `station/1/query` to enumerate, `availability/1/query` to see what exists,
  `dataselect/1/query` for the open waveforms — drive with ObsPy and let
  EIDA/IRIS routing resolve nodes.
- **Proxy ladder**: the open CP subset on EIDA/GEOFON + the nearest open national
  network — the regional stations are integrated into Portugal's **IPMA** national
  network — gives broader open coverage for the same region/period.
- **Steward**: route to the operator (CIVISA / IVAR, Univ. of the Azores, and
  IPMA) via their official data-access channels — use the contact in the network
  DOI metadata; mark provenance `verified-from-source`. Never invent an address.

ObsPy starting point:
```python
from obspy.clients.fdsn import Client
inv = Client("GEOFON").get_stations(network="CP", starttime="2024-01-01",
                                    endtime="2024-12-31", level="channel")
```

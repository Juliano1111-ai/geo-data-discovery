# Worked example — "Seismic events + Himalaya + 1500–2026 + Magnitude 8"

This is what the method should return for that query: **a verified list of data
sources, not a report.** (If an assistant hands you a seismotectonic essay, it
ignored the output contract — see the "STOP" rule at the top of
`discovery_playbook.md`.)

Query framed: variable = earthquake **events** (a catalogue, not waveforms);
region = Himalayan arc, box `[W,S,E,N] = [73, 26, 97, 37]`; time = `1500/2026`;
filter = `M ≥ 8`. A magnitude/event request → FDSN **event** service + recomputed
catalogues. Run it with:

```bash
python skill/geo-data-discovery/scripts/discovery_orchestrator.py \
  --query "Seismic event Himalaya 1500-2026 Magnitude 8" \
  --bbox "73,26,97,37" --start 1500-01-01 --end 2026-12-31 --outdir himalaya_out
```

## Verified data table

| # | Source | resourceRole | Direct access link (machine endpoint) | Notes |
|---|--------|--------------|----------------------------------------|-------|
| 1 | USGS ANSS ComCat (FDSN event) | actual_data | `https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=1500-01-01&endtime=2026-12-31&minmagnitude=8&minlatitude=26&maxlatitude=37&minlongitude=73&maxlongitude=97&orderby=time` | Instrumental (mostly 1900+). CSV/GeoJSON/QuakeML. Service confirmed live. |
| 2 | ISC Bulletin (FDSN event) | actual_data | `http://www.isc.ac.uk/fdsnws/event/1/query?format=text&starttime=1500-01-01&endtime=2026-12-31&minmagnitude=8&minlatitude=26&maxlatitude=37&minlongitude=73&maxlongitude=97` | Reviewed global bulletin. |
| 3 | ISC-GEM Global Instrumental Catalogue | actual_data | `https://doi.org/10.31905/D808B825` | Recomputed Mw, 1904– (v12.1, 2025-11-27), CC-BY-SA. Filter M ≥ 8. |
| 4 | NOAA NCEI Significant Earthquake DB | actual_data | `https://doi.org/10.7289/V5TD9V7K` | Historical, 2150 BC–present (TSV). Use for the pre-instrumental events (e.g. 1505, 1714). |

Each link resolves on an open network; verify with the engine or paste link #1
into a browser to get the event list immediately.

## JSON-LD (ingestible)

```json
[
  {"@context":"https://schema.org/","@type":"Dataset",
   "name":"USGS ComCat earthquake catalogue — Himalaya, M≥8, 1500–2026",
   "url":"https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=1500-01-01&endtime=2026-12-31&minmagnitude=8&minlatitude=26&maxlatitude=37&minlongitude=73&maxlongitude=97&orderby=time",
   "resourceRole":"actual_data","dataStatus":"DATA_AVAILABLE","accessProtocol":"FDSN-event",
   "isAccessibleForFree":true,"license":"public domain (USGS)",
   "temporalCoverage":"1500-01-01/2026-12-31",
   "spatialCoverage":{"@type":"Place","geo":{"@type":"GeoShape","box":"26 73 37 97"}},
   "distribution":[{"@type":"DataDownload","contentUrl":"https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=1500-01-01&endtime=2026-12-31&minmagnitude=8&minlatitude=26&maxlatitude=37&minlongitude=73&maxlongitude=97","encodingFormat":"text/csv"}]},
  {"@context":"https://schema.org/","@type":"Dataset",
   "name":"ISC-GEM Global Instrumental Earthquake Catalogue",
   "identifier":"doi:10.31905/D808B825","url":"https://doi.org/10.31905/D808B825",
   "resourceRole":"actual_data","dataStatus":"DATA_AVAILABLE","accessProtocol":"DOI",
   "isAccessibleForFree":true,"license":"CC-BY-SA",
   "spatialCoverage":{"@type":"Place","geo":{"@type":"GeoShape","box":"26 73 37 97"}},
   "distribution":[{"@type":"DataDownload","contentUrl":"https://doi.org/10.31905/D808B825","encodingFormat":"text/csv"}]},
  {"@context":"https://schema.org/","@type":"Dataset",
   "name":"NOAA NCEI Significant Earthquake Database (historical)",
   "identifier":"doi:10.7289/V5TD9V7K","url":"https://doi.org/10.7289/V5TD9V7K",
   "resourceRole":"actual_data","dataStatus":"DATA_AVAILABLE","accessProtocol":"DOI",
   "isAccessibleForFree":true,
   "spatialCoverage":{"@type":"Place","geo":{"@type":"GeoShape","box":"26 73 37 97"}},
   "distribution":[{"@type":"DataDownload","contentUrl":"https://doi.org/10.7289/V5TD9V7K","encodingFormat":"text/tab-separated-values"}]}
]
```

FINAL STATUS: **FOUND_AVAILABLE** (open earthquake catalogues cover this query).

---

Copyright © 2026 Juliano Ramanantsoa. MIT License.

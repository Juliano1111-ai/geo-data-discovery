# Reference — DISCOVERY mode playbook

Read this when the data probably exists in a known infrastructure and the task is
to find the directly-downloadable product with a verified link. The SKILL.md
workflow and the Verification Gate still apply; this file adds the detail.

## STOP — HARD OUTPUT RULE (read before anything else)

**This is a data-finding task, not an essay.** Your entire response is two things
and nothing else: (1) a **verified data table** (one row per dataset, each with a
resolvable Direct Access Link), and (2) a **JSON-LD array**.

You are **NOT** writing a report. Do **NOT** output background, geological or
tectonic history, descriptions of past events, casualty figures, an introduction,
a conclusion, or narrative prose. If you have written more than one sentence of
context before the table, you have **failed** — delete it and return the table.

A research-sounding query is still a **data** request. For example
"Seismic events + Himalaya + 1500–2026 + Magnitude 8" must return the *catalogues
and services that deliver that event list* — the **FDSN event service**
(`fdsnws/event/1/query` with `minmagnitude`, bbox, time), **ISC-GEM**, **USGS
ComCat**, **NOAA NCEI** — each with a verified link. Never an article about the
earthquakes. (Magnitude/event query → earthquake **catalogue**; "waveform / raw /
miniSEED" query → FDSN **dataselect**. Do not confuse the two.)

If you cannot run the verification yourself (e.g. you are a chat model with no code
execution), still output only the table + JSON-LD, mark each link "unverified —
resolve before use", and point to `scripts/discovery_orchestrator.py` /
`examples/test_etna_pipeline.py` to verify.


## Operating principles
1. **Seed = prior, not truth.** Treat any catalogue/homepage as a node to
   re-resolve, not a guaranteed-live endpoint. If a documented access pattern
   looks outdated, flag it and find the current one (`endpoints.md` tracks known
   moves).
2. **Expand before you search.** Fire parallel queries per backend from the
   QueryPlan's synonym set. A single "[Variable]+[Area]+[Time]+[Type]" string is
   brittle.
3. **Right endpoint, not homepage.** Use the routing table. For a homepage with
   no API, discover the endpoint via a catalogue API first.
4. **Metadata over guessing.** Read velocity, access protocol, licence and
   coverage from the record. Never infer a bounding box or a protocol you did not
   read.
5. **Don't stop early.** Continue until every clause of the target is grounded or
   explicitly marked unretrievable with a reason.

## Query expansion protocol
Produce, before retrieving:
- **TERMS** — controlled-vocabulary synonyms. Prefer NASA GCMD, GEMET, EPOS/EPOS-
  DCAT SKOS vocabularies, or a domain CGV over ad-hoc words. e.g. "ground motion"
  → {crustal deformation, surface displacement, GNSS position time series,
  geodetic time series, strain rate, tectonic displacement}.
- **SPATIAL** — `[West, South, East, North]` decimal degrees + gazetteer name +
  ISO-3166 country code.
- **TEMPORAL** — strict ISO-8601 interval `start/end`.
- **TYPE / VELOCITY** — archive vs NRT vs reanalysis/model; expected distribution
  format.

## Reliability ranking
Tier 1 continental/global core infrastructure (base 0.90) > Tier 2 national
agency / certified repository (0.70) > Tier 3 individual paper / local node
(0.45). Add +0.07 if the link verified this run; +0.03 if a DOI is present;
consult CoreTrustSeal / re3data certification and explicit FAIR signals. Show the
score.

## Output contract — exactly two artifacts, no preamble

### 1. EXECUTIVE SUMMARY TABLE
Columns, in order: `# | Tier | Reliability | Verified (status+UTC) | Data
Velocity | Source Node | Dataset | Spatial bbox [W,S,E,N] | Temporal (ISO) |
Access Protocol | Direct Access Link`. Verified rows only. Then an `UNRESOLVED
LEADS` block for gate failures (with reasons), and a `SEED HEALTH` note for any
node whose access pattern looks stale.

### 2. JSON-LD ARRAY (schema.org/Dataset, valid + ingestible)
One object per verified dataset. Required keys: `@context`(https://schema.org/),
`@type`("Dataset"), `name`, `description`, `identifier`("doi:..."), `url`(resolved
final URL), `keywords`[], `creator`/`publisher`{Organization},
`temporalCoverage`("start/end"), `spatialCoverage`{Place→GeoShape.box "minLat
minLong maxLat maxLong"}, `distribution`[{`@type`:"DataDownload", `contentUrl`,
`encodingFormat`}], plus the v1.0.0 honesty fields `resourceRole`
(actual_data | metadata_evidence | catalogue_record | …), `dataStatus`
(DATA_AVAILABLE | METADATA_ONLY | RESTRICTED | …), `accessProtocol`,
`isAccessibleForFree`, and `verification`{ok, http_status, validation_level,
validation_method, checked_at}. Must `json.loads()` cleanly. End with one status:
FOUND_AVAILABLE | FOUND_RESTRICTED | DARK_TRACE | PROXY_RECOMMENDED |
NOT_FOUND_AFTER_PROTOCOL. DCAT-AP / GeoDCAT-AP is an acceptable alternative target
if the ingestion engine requires it.

The `scripts/discovery_orchestrator.py` script implements this contract directly —
run it rather than assembling the JSON-LD by hand, then narrate the result.

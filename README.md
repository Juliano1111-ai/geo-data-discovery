# geo-data-discovery

*Find Earth-science data, verify it actually exists, and — when it doesn't sit in a public archive — track it down. With a step that stops fabricated links cold.*

**Juliano Ramanantsoa** — Department of Earth Science, University of Bergen / Bjerknes Centre for Climate Research · ORCID [0000-0003-0831-2802](https://orcid.org/0000-0003-0831-2802)
**Version 1.0.1** · **License [MIT](LICENSE)** · **[DISCLAIMER](DISCLAIMER.md)** · Copyright © 2026 Juliano Ramanantsoa

---

## Motive and narrative

I have spent years working with data and research-data infrastructure across European geoscience, and one frustration is constant: the data you need is real, but finding the downloadable product means crossing a dozen archives — and sometimes the data isn't openly published at all. When I ask a language model where to download something, it answers with clean, confident links that don't resolve. That is not a small annoyance. For a paper, a proposal, or a course, a plausible-looking dead link is worse than no answer.

So I wrote down the method I actually trust, and I made the part that must never fail deterministic. A model is good at expanding a query, routing it to the right infrastructure, and reasoning over a forensic trail — and I let it do exactly that. What I never let it do is decide that a link is good. **A link reaches the output only after a script has resolved it and confirmed the response is the data I asked for.** That single boundary is what turns a clever demo into something I am willing to put my name on.

This repository is that method. It runs as plain Python, as a Colab notebook, and as a Claude Skill (compatible to other GAI), so it fits whatever you already use.

## Install and run

You do not need to install anything to use the core engine — it is pure Python 3.9+ standard library. Pick the path that suits you.

### Option 1 — Plain Python (local)

```bash
git clone https://github.com/Juliano1111-ai/geo-data-discovery.git
cd geo-data-discovery

# the simplest start — runs three worked examples, writes verified outputs
python quickstart.py
# on an open network, also query the cross-domain catalogues:
python quickstart.py --live
```

Optional extras (waveform download, plotting, tests, schema validation):

```bash
pip install -r requirements.txt
```

### Option 2 — Google Colab (nothing to install)

Open `notebooks/geo_data_discovery_colab.ipynb` in Google Colab and choose **Runtime → Run all**. Colab has open internet, so the links resolve live and you get real data — verified seismic waveforms, a real earthquake catalogue, and an ObsPy waveform plot, end to end.

### Run a single target directly

```bash
python skill/geo-data-discovery/scripts/discovery_orchestrator.py \
  --query "Seismic waveforms Etna 2024 raw data" \
  --bbox "14.8,37.6,15.2,37.9" --start 2024-01-01 --end 2024-12-31 \
  --network IV --outdir out
# results: out/verified_catalog.jsonld and out/workflow_status.json
```

## What is in here

| Path | What it is |
|------|------------|
| `quickstart.py` | The simplest entry point — no dependencies, runs three examples |
| `notebooks/geo_data_discovery_colab.ipynb` | Ready-to-run Colab notebook with live data |
| `skill/geo-data-discovery/scripts/discovery_orchestrator.py` | The engine: resolve → validate → classify → split outputs |
| `skill/geo-data-discovery/SKILL.md` + `references/` | The method and the discovery / dark-data / CORDIS playbooks + routing table |
| `examples/` | Worked, verified examples (GNSS/Andalusia, seismic/Etna, Himalaya M≥8) + a zero-dependency test |
| `docs/finding_geoscience_data.md` | A complete, tested walk-through |
| `tests/`, `.github/workflows/ci.yml`, `schemas/` | Test suite, CI, and the output JSON Schema |
| `requirements.txt`, `DEPLOY.md` | Optional dependencies and the full deployment guide |

## What this tool proves — and what it does not

I am precise about this, because the credibility of the method depends on it.

- **HTTP 200 means a link resolved. It does not mean the data are usable.** The engine records a *validation level* (0–4), not a yes/no: 0 unresolved, 1 the service responded, 2 the content type is right, 3 the data are non-empty, 4 the content matches the target (non-zero miniSEED bytes, a non-empty FDSN station list, a DOI that resolves to access metadata, JSON that parses, a CSV with rows).
- **Metadata is not data.** Every record carries a `resourceRole`. A station inventory is `metadata_evidence`; the waveforms are `actual_data`. They are never conflated.
- **Verified data, restricted resources and dead leads go to different files.** Only resources actually reached land in `verified_catalog.jsonld`; restricted ones (HTTP 401/403) go to `restricted_leads.json`; everything else to `unresolved_leads.json`; every check is logged to `access_validation_log.csv`. Each run ends with one status: `FOUND_AVAILABLE`, `FOUND_RESTRICTED`, `DARK_TRACE`, `PROXY_RECOMMENDED`, or `NOT_FOUND_AFTER_PROTOCOL`.
- **I do not invent endpoints, availability, contacts, or access conditions.** If the full protocol finds nothing, the honest answer is `NOT_FOUND_AFTER_PROTOCOL`.

This is research tooling to locate and verify data. It is not a guarantee of fitness for a particular scientific use, and it does not replace each provider's own terms. See [DISCLAIMER.md](DISCLAIMER.md).

## The search tiers

The router works through five tiers. Tier 3 is the one I built specifically for European infrastructures, where data are often described in a deliverable or a Data Management Plan before they reach any catalogue:

1. Core domain infrastructures (FDSN, Copernicus, EPOS, …)
2. Cross-domain catalogues (DataCite, re3data, Zenodo, B2FIND)
3. **CORDIS & EU project deliverables** (Geo-INQUIRE, EPOS, ENVRI, DMPs, work packages)
4. Literature & code trail (Crossref, OpenAlex, GitHub)
5. Human stewards & proxy datasets

A magnitude/event query routes to earthquake **catalogues** (FDSN event service, ISC-GEM, USGS ComCat, NOAA NCEI); a waveform query routes to FDSN **dataselect**. See `references/` for the playbooks and `references/endpoints.md` for the routing table.

## Tests

```bash
pip install pytest
pytest tests/ -q          # 21 tests
```

CI runs the compile check, the tests, and JSON-Schema validation on every push (`.github/workflows/ci.yml`).

## Deploy

The full step-by-step for GitHub, Zenodo (DOI) and ReadTheDocs is in **[DEPLOY.md](DEPLOY.md)**.

## Citing

Please cite it if it helps your work — see [`CITATION.cff`](CITATION.cff). A tagged release wired to Zenodo mints a DOI for the exact version you used.

## License and disclaimer

Released under the [MIT License](LICENSE), for research and educational use, **as is, without warranty of any kind**. Access to any third-party data referenced by the tool is governed solely by that provider's terms. Please read [DISCLAIMER.md](DISCLAIMER.md) before relying on any output.

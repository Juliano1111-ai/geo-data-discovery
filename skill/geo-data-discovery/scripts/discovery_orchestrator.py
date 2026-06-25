#!/usr/bin/env python3
# Copyright (c) 2026 Juliano Ramanantsoa.
# Licensed under the MIT License (see LICENSE). Provided "as is" without
# warranty; see DISCLAIMER.md. This tool locates and verifies links to
# third-party data; it does not redistribute data and is not affiliated with
# any data provider.
"""
discovery_orchestrator.py  (v1.0.0)
===================================
The deterministic engine behind my data-discovery method. It does the parts a
language model must NOT be trusted to do: it resolves and validates every
candidate link, separates real data from metadata evidence and from unverified
leads, and writes machine-readable outputs.

Two principles drive the v1.0.0 hardening:

1. HTTP 200 means a link RESOLVED, not that usable data exist. Confirmation needs
   a protocol-specific check (a non-empty FDSN station list; non-zero miniSEED
   bytes; a DOI that resolves to access metadata; JSON that parses; a CSV with
   rows). I record a validation LEVEL (0-4), not a boolean.

2. Verified data, metadata evidence, restricted resources and dead leads go to
   SEPARATE outputs. Only resources that are actually downloadable land in the
   primary catalogue; nothing else can masquerade as data.

Pure standard library. Run `python discovery_orchestrator.py --help`.
"""
from __future__ import annotations

import argparse
import csv
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

UA = "geo-data-discovery/1.0 (research; FAIR data discovery)"
TIMEOUT = 25
_SSL = ssl.create_default_context()

# --- controlled taxonomies (kept small and explicit on purpose) ------------- #
RESOURCE_ROLES = (
    "actual_data", "metadata_evidence", "availability_evidence",
    "catalogue_record", "forensic_evidence", "proxy_data",
    "restricted_lead", "unresolved_lead", "test_fixture",
)
DATA_STATUSES = ("DATA_AVAILABLE", "METADATA_ONLY", "RESTRICTED",
                 "LINK_ONLY", "UNRESOLVED")
WORKFLOW_STATUSES = ("FOUND_AVAILABLE", "FOUND_RESTRICTED", "DARK_TRACE",
                     "PROXY_RECOMMENDED", "NOT_FOUND_AFTER_PROTOCOL")
# Search tiers. Tier 3 (CORDIS / EU project deliverables) is added in v1.0.0
# because in European RIs the data often surface first in deliverables and DMPs.
SEARCH_TIERS = {
    1: "Core domain infrastructures (FDSN, Copernicus, EPOS, ...)",
    2: "Cross-domain data catalogues (DataCite, re3data, Zenodo, B2FIND)",
    3: "CORDIS & EU project deliverables (Geo-INQUIRE, EPOS, ENVRI, DMPs, WPs)",
    4: "Literature & code trail (Crossref, OpenAlex, GitHub)",
    5: "Human stewards & proxy datasets",
}


# --------------------------------------------------------------------------- #
# QUERY MODEL + EXPANSION
# --------------------------------------------------------------------------- #
@dataclass
class QueryPlan:
    raw: str
    terms: list[str]
    bbox: Optional[tuple[float, float, float, float]] = None  # (W, S, E, N)
    time_start: Optional[str] = None
    time_end: Optional[str] = None

    @property
    def temporal_iso(self) -> Optional[str]:
        return f"{self.time_start}/{self.time_end}" if self.time_start and self.time_end else None

    @property
    def box_schema_org(self) -> Optional[str]:
        if not self.bbox:
            return None
        w, s, e, n = self.bbox
        return f"{s} {w} {n} {e}"          # schema.org box = "minLat minLon maxLat maxLon"


SYNONYMS = {
    "ground motion": ["ground motion", "crustal deformation", "surface displacement",
                      "GNSS position time series", "geodetic time series",
                      "tectonic displacement", "strain rate"],
    "gnss": ["GNSS", "GPS", "geodetic", "RINEX", "position time series"],
    "seismic waveforms": ["seismic waveforms", "miniSEED", "raw waveform",
                          "broadband seismometer", "continuous waveform data", "seismogram"],
    "seismicity": ["seismicity", "earthquake catalog", "hypocenter", "event catalog"],
    "sea surface temperature": ["sea surface temperature", "SST"],
    "reanalysis": ["reanalysis", "ERA5", "model simulation", "hindcast"],
    "bathymetry": ["bathymetry", "seafloor topography", "depth grid"],
}


def expand_query(raw, bbox=None, start=None, end=None) -> QueryPlan:
    low = raw.lower()
    terms: list[str] = []
    for key, syns in SYNONYMS.items():
        if key in low:
            terms.extend(syns)
    if raw not in terms:
        terms.append(raw)
    seen, ordered = set(), []
    for t in terms:
        if t.lower() not in seen:
            seen.add(t.lower())
            ordered.append(t)
    return QueryPlan(raw=raw, terms=ordered, bbox=bbox, time_start=start, time_end=end)


# --------------------------------------------------------------------------- #
# CANDIDATE + VERIFICATION MODEL
# --------------------------------------------------------------------------- #
@dataclass
class Verification:
    ok: bool                       # link resolved (2xx-3xx)
    http_status: Optional[int]
    final_url: Optional[str]
    checked_at: str
    validation_level: int = 0      # 0 unresolved .. 4 content matches target
    validation_method: str = ""
    note: str = ""


@dataclass
class Candidate:
    title: str
    source_node: str
    tier: int
    resource_role: str                       # one of RESOURCE_ROLES
    access_url: str
    identifier: Optional[str] = None
    fmt: Optional[str] = None
    access_protocol: Optional[str] = None
    velocity: str = "unknown"
    license: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    spatial_box: Optional[str] = None
    temporal: Optional[str] = None
    publisher: Optional[str] = None
    verification: Optional[Verification] = None
    data_status: str = "UNRESOLVED"          # one of DATA_STATUSES

    @property
    def reliability(self) -> float:
        base = {1: 0.9, 2: 0.7, 3: 0.6, 4: 0.45, 5: 0.4}.get(self.tier, 0.3)
        if self.verification and self.verification.ok:
            base += 0.05
        if self.identifier and self.identifier.lstrip("doi:").startswith("10."):
            base += 0.03
        return round(min(base, 0.99), 3)

    @property
    def access_score(self) -> float:
        # transparent heuristic: how directly usable is this resource right now?
        if self.data_status == "DATA_AVAILABLE":
            return 1.0
        if self.data_status == "METADATA_ONLY":
            return 0.6
        if self.data_status == "RESTRICTED":
            return 0.3
        if self.data_status == "LINK_ONLY":
            return 0.4
        return 0.0


# --------------------------------------------------------------------------- #
# VALIDATION (the heart of the v1.0.0 hardening)
# --------------------------------------------------------------------------- #
def _looks_like_miniseed(body: bytes) -> bool:
    # miniSEED record: 6 ASCII digits (sequence no.) + data-header indicator.
    return len(body) > 64 and body[:6].isdigit() and body[6:7] in (b"D", b"R", b"Q", b"M")


def validate_payload(role: str, content_type: str, body: bytes) -> tuple[int, str]:
    """Return (validation_level, method). Level 0 unresolved, 1 service responded,
    2 content type/structure correct, 3 data non-empty, 4 matches target type."""
    if body is None:
        return 0, "no-response"
    head = body[:8192]
    ct = (content_type or "").lower()
    try:
        text = head.decode("utf-8", "replace")
    except Exception:                                    # noqa: BLE001
        text = ""

    if role in ("actual_data",) and ("mseed" in ct or _looks_like_miniseed(head)):
        return (4, "miniseed-nonzero-bytes") if _looks_like_miniseed(head) else (3, "mseed-content-type")
    if role in ("metadata_evidence", "availability_evidence"):
        rows = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
        if "<station" in text.lower() or "<channel" in text.lower():
            return 3, "stationxml-nonempty"
        if rows:
            return 3, "fdsn-text-nonempty"
        return 1, "fdsn-empty-response"
    if "json" in ct or text.strip().startswith(("{", "[")):
        try:
            json.loads(body.decode("utf-8", "replace"))
            return 3, "json-parsed-nonempty"
        except Exception:                                # noqa: BLE001
            return 1, "json-parse-failed"
    if "csv" in ct or (text.count(",") > 3 and "\n" in text):
        rows = [r for r in text.splitlines() if r.strip()]
        return (3, "csv-rows-nonempty") if len(rows) > 1 else (1, "csv-empty")
    if "html" in ct or text.lstrip().lower().startswith("<!doctype html") or "<html" in text.lower():
        return 1, "html-landing-page"          # resolved, but NOT data
    return 2, "resolved-content-present"


def _http(url: str, method: str = "GET"):
    """Resolve a URL and capture a small body slice for validation."""
    ts = datetime.now(timezone.utc).isoformat()
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as r:
            body = r.read(16384)
            ct = r.headers.get("Content-Type", "")
            return Verification(ok=200 <= r.status < 400, http_status=r.status,
                                final_url=r.url, checked_at=ts), ct, body
    except urllib.error.HTTPError as e:
        return Verification(ok=False, http_status=e.code, final_url=url, checked_at=ts,
                            note=f"HTTPError {e.code}"), "", b""
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ValueError) as e:
        return Verification(ok=False, http_status=None, final_url=url, checked_at=ts,
                            note=f"{type(e).__name__}: {e}"), "", b""


def verify_and_validate(c: Candidate) -> Candidate:
    """Resolve (Level 0/1), then run a protocol-specific check (Level 2-4), then
    set data_status. DOIs are resolved through doi.org."""
    url = c.access_url
    if c.identifier and c.identifier.lstrip("doi:").startswith("10."):
        url = f"https://doi.org/{c.identifier.split(':')[-1]}"
    v, ct, body = _http(url)
    if v.ok:
        v.validation_level, v.validation_method = validate_payload(c.resource_role, ct, body)
    c.verification = v

    # derive an honest data_status from role + validation level + http status
    if v.http_status in (401, 403):
        c.data_status, c.resource_role = "RESTRICTED", "restricted_lead"
    elif not v.ok:
        c.data_status = "UNRESOLVED"
    elif c.resource_role == "actual_data" and v.validation_level >= 3:
        c.data_status = "DATA_AVAILABLE"
    elif c.resource_role in ("metadata_evidence", "availability_evidence") and v.validation_level >= 3:
        c.data_status = "METADATA_ONLY"
    else:
        c.data_status = "LINK_ONLY"          # resolved but not confirmed as usable data
    return c


def classify_bucket(c: Candidate) -> str:
    """verified | restricted | unresolved."""
    if c.data_status == "RESTRICTED":
        return "restricted"
    if c.data_status in ("DATA_AVAILABLE", "METADATA_ONLY"):
        return "verified"
    return "unresolved"


def final_status(cands: list[Candidate]) -> str:
    roles = {c.data_status for c in cands}
    if "DATA_AVAILABLE" in roles:
        return "FOUND_AVAILABLE"
    if "RESTRICTED" in roles:
        return "FOUND_RESTRICTED"
    if any(c.resource_role == "proxy_data" and c.data_status in ("DATA_AVAILABLE", "METADATA_ONLY")
           for c in cands):
        return "PROXY_RECOMMENDED"
    if "METADATA_ONLY" in roles or any(c.resource_role == "forensic_evidence" for c in cands):
        return "DARK_TRACE"
    return "NOT_FOUND_AFTER_PROTOCOL"


# --------------------------------------------------------------------------- #
# BACKENDS
# --------------------------------------------------------------------------- #
def build_fdsn_urls(qp: QueryPlan, network="*",
                    node="https://federator.orfeus-eu.org") -> dict:
    """Pure, testable FDSN URL builder. Returns station + dataselect URLs for the
    QueryPlan's bbox and time window. (Drive with ObsPy in production.)"""
    w, s, e, n = qp.bbox
    geo = f"minlatitude={s}&maxlatitude={n}&minlongitude={w}&maxlongitude={e}"
    t0, t1 = qp.time_start or "2024-01-01", qp.time_end or "2024-12-31"
    return {
        "station": (f"{node}/fdsnws/station/1/query?network={network}&{geo}"
                    f"&starttime={t0}&endtime={t1}&level=station&format=text&nodata=404"),
        "dataselect": (f"{node}/fdsnws/dataselect/1/query?network={network}"
                       f"&station=*&channel=HH?&starttime={t0}T00:00:00"
                       f"&endtime={t0}T01:00:00&nodata=404"),
    }


import re

WAVEFORM_HINTS = ("waveform", "miniseed", "seismogram", "raw waveform", "dataselect",
                  "broadband", "seismometer", "continuous waveform")
EVENT_HINTS = ("event", "catalog", "catalogue", "magnitude", "seismicity",
               "hypocenter", "hypocentre", "epicenter", "epicentre", "earthquake")


def is_waveform(qp: QueryPlan) -> bool:
    blob = (qp.raw + " " + " ".join(qp.terms)).lower()
    return any(h in blob for h in WAVEFORM_HINTS)


def is_event_catalog(qp: QueryPlan) -> bool:
    """A magnitude / event / catalogue request -> earthquake CATALOGUE (FDSN event),
    not raw waveforms. Waveform hints win to avoid mis-routing."""
    if is_waveform(qp):
        return False
    blob = (qp.raw + " " + " ".join(qp.terms)).lower()
    return any(h in blob for h in EVENT_HINTS)


def is_seismic(qp: QueryPlan) -> bool:
    blob = (qp.raw + " " + " ".join(qp.terms)).lower()
    return is_waveform(qp) or is_event_catalog(qp) or "seismic" in blob


def extract_min_magnitude(raw: str) -> Optional[float]:
    m = re.search(r'(?:magnitude|mag|m[ww]?)\D{0,4}(\d(?:\.\d)?)', raw.lower())
    return float(m.group(1)) if m else None


def fdsn_candidates(qp: QueryPlan, network="*") -> list[Candidate]:
    if not qp.bbox:
        return []
    urls = build_fdsn_urls(qp, network=network)
    common = dict(source_node="FDSN/EIDA federator", tier=1,
                  spatial_box=qp.box_schema_org, temporal=qp.temporal_iso,
                  velocity="archive", access_protocol="FDSN",
                  license="varies by network (open data via EIDA)")
    return [
        Candidate(title=f"FDSN station inventory (network {network}) — what exists",
                  resource_role="metadata_evidence", access_url=urls["station"],
                  fmt="text/fdsn-station", keywords=["seismic", "FDSN", "station-metadata"],
                  **common),
        Candidate(title="FDSN dataselect raw waveforms (miniSEED)",
                  resource_role="actual_data", access_url=urls["dataselect"],
                  fmt="application/vnd.fdsn.mseed",
                  keywords=["seismic", "miniSEED", "raw waveform"], **common),
    ]


def build_event_url(qp: QueryPlan, node="https://earthquake.usgs.gov",
                    minmag: Optional[float] = None, fmt="csv") -> str:
    """FDSN event-service query -> an earthquake CATALOGUE (event list), the right
    product for a magnitude/event request. Works for USGS, ISC, EMSC, ESM nodes."""
    w, s, e, n = qp.bbox
    t0, t1 = qp.time_start or "1900-01-01", qp.time_end or "2026-12-31"
    mag = f"&minmagnitude={minmag}" if minmag else ""
    return (f"{node}/fdsnws/event/1/query?format={fmt}&starttime={t0}&endtime={t1}"
            f"&minlatitude={s}&maxlatitude={n}&minlongitude={w}&maxlongitude={e}"
            f"{mag}&orderby=time&nodata=404")


def fdsn_event_candidates(qp: QueryPlan) -> list[Candidate]:
    """Earthquake-catalogue sources for an event/magnitude query. The event-service
    query and the recomputed catalogues ARE the data (resource_role=actual_data)."""
    if not qp.bbox:
        return []
    minmag = extract_min_magnitude(qp.raw)
    box = qp.box_schema_org
    out = [
        Candidate(title=f"USGS ComCat earthquake catalogue (FDSN event, M>={minmag or 'any'})",
                  source_node="USGS / ANSS ComCat", tier=1, resource_role="actual_data",
                  access_url=build_event_url(qp, minmag=minmag, fmt="csv"),
                  fmt="text/csv", access_protocol="FDSN-event", velocity="archive",
                  license="public domain (USGS)", spatial_box=box, temporal=qp.temporal_iso,
                  keywords=["earthquake catalog", "FDSN event", "magnitude", "ComCat"]),
        Candidate(title="ISC Bulletin earthquake catalogue (FDSN event)",
                  source_node="ISC", tier=1, resource_role="actual_data",
                  access_url=build_event_url(qp, node="http://www.isc.ac.uk", minmag=minmag, fmt="text"),
                  fmt="text/plain", access_protocol="FDSN-event", velocity="archive",
                  spatial_box=box, temporal=qp.temporal_iso,
                  keywords=["earthquake catalog", "ISC Bulletin", "FDSN event"]),
        Candidate(title="ISC-GEM Global Instrumental Earthquake Catalogue (1904-, recomputed)",
                  source_node="ISC-GEM", tier=1, resource_role="actual_data",
                  identifier="10.31905/D808B825",
                  access_url="https://doi.org/10.31905/D808B825",
                  fmt="text/csv", access_protocol="DOI", velocity="archive",
                  license="CC-BY-SA", spatial_box=box, temporal=qp.temporal_iso,
                  keywords=["ISC-GEM", "instrumental catalogue", "recomputed", "Mw"]),
        Candidate(title="NOAA NCEI Significant Earthquake Database (2150 BC-present)",
                  source_node="NOAA NCEI", tier=2, resource_role="actual_data",
                  identifier="10.7289/V5TD9V7K",
                  access_url="https://doi.org/10.7289/V5TD9V7K",
                  fmt="text/tab-separated-values", access_protocol="DOI", velocity="archive",
                  spatial_box=box, temporal=qp.temporal_iso,
                  keywords=["significant earthquakes", "historical", "pre-instrumental"]),
    ]
    return out



    """Tier 3: surface EU project-deliverable search leads (CORDIS / DMPs / WPs).
    These are forensic leads, not data — they point to where data are described."""
    region = ""
    tag = acronym or "[project acronym]"
    queries = [
        f'site:cordis.europa.eu "{tag}" dataset',
        f'"{tag}" "Data Management Plan" OR "DMP"',
        f'"{tag}" deliverable data repository',
        f'"{tag}" Zenodo community',
    ]
    out = []
    for q in queries:
        out.append(Candidate(
            title=f"CORDIS / deliverable lead: {q}",
            source_node="CORDIS / EU project deliverables", tier=3,
            resource_role="forensic_evidence",
            access_url="https://cordis.europa.eu/search?q=" + urllib.parse.quote(q),
            keywords=["CORDIS", "deliverable", "DMP", "EU project"],
            spatial_box=qp.box_schema_org, temporal=qp.temporal_iso))
    return out


def datacite_search(qp: QueryPlan, rows=4) -> list[Candidate]:
    q = " ".join(f'"{t}"' for t in qp.terms[:4])
    url = "https://api.datacite.org/dois?" + urllib.parse.urlencode(
        {"query": q, "resource-type-id": "dataset", "page[size]": rows})
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": UA}), timeout=TIMEOUT, context=_SSL) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:                               # noqa: BLE001
        print(f"  [datacite] skipped: {e}", file=sys.stderr)
        return []
    out = []
    for item in data.get("data", []):
        a = item.get("attributes", {})
        out.append(Candidate(
            title=((a.get("titles") or [{}])[0].get("title") or "untitled")[:140],
            source_node="DataCite", tier=2, resource_role="catalogue_record",
            identifier=a.get("doi"), access_url=a.get("url") or f"https://doi.org/{a.get('doi')}",
            fmt=(a.get("formats") or [None])[0], access_protocol="DOI",
            publisher=a.get("publisher"), license=a.get("rightsList", [{}])[0].get("rights")
            if a.get("rightsList") else None,
            keywords=[s.get("subject") for s in (a.get("subjects") or []) if s.get("subject")][:8],
            temporal=qp.temporal_iso, spatial_box=qp.box_schema_org))
    return out


# --------------------------------------------------------------------------- #
# EMIT (schema.org JSON-LD with v1.0.0 fields) + WRITERS
# --------------------------------------------------------------------------- #
def to_schema_org(c: Candidate) -> dict:
    v = c.verification
    node = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "name": c.title,
        "identifier": (f"doi:{c.identifier}" if c.identifier else None),
        "url": (v.final_url if v else c.access_url),
        "keywords": c.keywords,
        "publisher": ({"@type": "Organization", "name": c.publisher} if c.publisher else None),
        "license": c.license,
        "isAccessibleForFree": (c.data_status == "DATA_AVAILABLE"),
        "temporalCoverage": c.temporal,
        "spatialCoverage": ({"@type": "Place", "geo": {"@type": "GeoShape", "box": c.spatial_box}}
                            if c.spatial_box else None),
        "distribution": [{
            "@type": "DataDownload",
            "contentUrl": (v.final_url if v else c.access_url),
            "encodingFormat": c.fmt or "application/octet-stream",
        }],
        # v1.0.0 honesty fields
        "resourceRole": c.resource_role,
        "dataStatus": c.data_status,
        "accessProtocol": c.access_protocol,
        "searchTier": c.tier,
        "reliabilityScore": c.reliability,
        "accessScore": c.access_score,
        "verification": (asdict(v) if v else {"ok": False, "validation_level": 0}),
    }
    return {k: val for k, val in node.items() if val is not None}


def write_outputs(cands, outdir, status):
    import os
    os.makedirs(outdir, exist_ok=True)
    buckets = {"verified": [], "restricted": [], "unresolved": []}
    for c in cands:
        buckets[classify_bucket(c)].append(c)

    with open(os.path.join(outdir, "verified_catalog.jsonld"), "w", encoding="utf-8") as f:
        json.dump([to_schema_org(c) for c in buckets["verified"]], f, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "restricted_leads.json"), "w", encoding="utf-8") as f:
        json.dump([to_schema_org(c) for c in buckets["restricted"]], f, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "unresolved_leads.json"), "w", encoding="utf-8") as f:
        json.dump([to_schema_org(c) for c in buckets["unresolved"]], f, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "access_validation_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "tier", "resource_role", "access_url", "http_status",
                    "resolved", "validation_level", "validation_method", "data_status",
                    "bucket", "checked_at"])
        for c in cands:
            v = c.verification
            w.writerow([c.title, c.tier, c.resource_role, c.access_url,
                        v.http_status if v else None, v.ok if v else False,
                        v.validation_level if v else 0, v.validation_method if v else "",
                        c.data_status, classify_bucket(c), v.checked_at if v else ""])
    with open(os.path.join(outdir, "workflow_status.json"), "w", encoding="utf-8") as f:
        json.dump({"final_status": status,
                   "counts": {k: len(v) for k, v in buckets.items()},
                   "generated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
    return buckets


def print_table(cands):
    print("\n" + "=" * 124)
    print("DISCOVERY RESULTS  (only DATA_AVAILABLE is downloadable data; METADATA_ONLY is evidence)")
    print("=" * 124)
    print(f"{'#':<3}{'Tier':<5}{'Role':<19}{'HTTP':<6}{'Lvl':<4}{'dataStatus':<15}{'Title':<40}Link")
    print("-" * 124)
    for i, c in enumerate(cands, 1):
        v = c.verification
        http = (str(v.http_status) if v and v.http_status else ("ERR" if v else "-"))
        lvl = (str(v.validation_level) if v else "0")
        link = (v.final_url if v and v.final_url else c.access_url)
        print(f"{i:<3}{c.tier:<5}{c.resource_role[:18]:<19}{http:<6}{lvl:<4}"
              f"{c.data_status:<15}{c.title[:39]:<40}{link[:40]}")
    print("=" * 124)


# --------------------------------------------------------------------------- #
# DEMO FIXTURES (honest: labelled test_fixture, never a real provider name)
# --------------------------------------------------------------------------- #
def demo_candidates(qp: QueryPlan) -> list[Candidate]:
    return [
        Candidate(title="Synthetic fixture — reachable URL (exercises the gate)",
                  source_node="SyntheticTestFixture", tier=5, resource_role="test_fixture",
                  access_url="https://github.com", fmt="text/html",
                  keywords=["fixture"], spatial_box=qp.box_schema_org),
        Candidate(title="Synthetic fixture — unreachable URL (must be quarantined)",
                  source_node="SyntheticTestFixture", tier=5, resource_role="test_fixture",
                  access_url="https://this-endpoint-does-not-resolve.invalid/x",
                  fmt="application/octet-stream", keywords=["fixture"]),
    ]


def run(qp: QueryPlan, live: bool, network="*", cordis=False,
        acronym: Optional[str] = None) -> list[Candidate]:
    print(f"\nTarget   : {qp.raw}")
    print(f"Terms    : {qp.terms}")
    print(f"BBox     : {qp.bbox}   Temporal: {qp.temporal_iso}")
    seismic = is_seismic(qp)
    catalog = is_event_catalog(qp)
    waveform = is_waveform(qp)
    kind = "event-catalogue" if catalog else ("waveform" if waveform else ("seismic" if seismic else "generic"))
    print(f"Seismic  : {seismic} (routing: {kind})  CORDIS Tier 3: {'ON' if cordis else 'off'}")

    cands: list[Candidate] = []
    if qp.bbox and catalog:
        cands += fdsn_event_candidates(qp)
    elif qp.bbox and (waveform or seismic):
        cands += fdsn_candidates(qp, network=network)
    if cordis:
        cands += cordis_leads(qp, acronym=acronym)
    if live:
        print("[live] querying DataCite ...")
        cands += datacite_search(qp)
    elif not (seismic or cordis):
        print("[demo] using synthetic fixtures to exercise the gate ...")
        cands += demo_candidates(qp)

    print(f"\nResolving + validating {len(cands)} candidate(s) ...")
    cands = [verify_and_validate(c) for c in cands]
    cands.sort(key=lambda c: (c.access_score, c.reliability), reverse=True)
    return cands


def main() -> int:
    ap = argparse.ArgumentParser(description="Hardened FAIR geoscience data discovery (v1.0.0)")
    ap.add_argument("--query", default="Ground motion GNSS tectonic displacement")
    ap.add_argument("--bbox", default="-7.6,36.0,-1.6,38.8", help="W,S,E,N")
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default="2026-12-31")
    ap.add_argument("--network", default="*", help="FDSN network code (e.g. IV for INGV)")
    ap.add_argument("--cordis", action="store_true", help="add Tier 3 CORDIS/deliverable leads")
    ap.add_argument("--acronym", default=None, help="EU project acronym for CORDIS leads")
    ap.add_argument("--live", action="store_true", help="query real catalogues (needs network)")
    ap.add_argument("--outdir", default="discovery_outputs")
    args = ap.parse_args()

    bbox = tuple(float(x) for x in args.bbox.split(",")) if args.bbox else None
    qp = expand_query(args.query, bbox=bbox, start=args.start, end=args.end)  # type: ignore[arg-type]
    cands = run(qp, live=args.live, network=args.network, cordis=args.cordis, acronym=args.acronym)
    print_table(cands)

    status = final_status(cands)
    buckets = write_outputs(cands, args.outdir, status)
    print(f"\nFINAL STATUS: {status}")
    print(f"verified(downloadable+evidence)={len(buckets['verified'])}  "
          f"restricted={len(buckets['restricted'])}  unresolved={len(buckets['unresolved'])}")
    print(f"Outputs written to: {args.outdir}/ "
          f"(verified_catalog.jsonld, restricted_leads.json, unresolved_leads.json, "
          f"access_validation_log.csv, workflow_status.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

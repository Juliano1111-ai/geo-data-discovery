# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import (expand_query, is_event_catalog, is_waveform,
                                    extract_min_magnitude, build_event_url, fdsn_event_candidates)

def _qp():
    return expand_query("Seismic event Himalaya 1500-2026 Magnitude 8",
                        bbox=(73,26,97,37), start="1500-01-01", end="2026-12-31")

def test_magnitude_query_routes_to_catalog_not_waveform():
    qp = _qp()
    assert is_event_catalog(qp) and not is_waveform(qp)

def test_waveform_query_routes_to_waveform():
    qp = expand_query("raw seismic waveforms Etna miniSEED", bbox=(14.8,37.6,15.2,37.9))
    assert is_waveform(qp) and not is_event_catalog(qp)

def test_min_magnitude_parsed():
    assert extract_min_magnitude("events Magnitude 8") == 8.0
    assert extract_min_magnitude("Mw 7.5 catalogue") == 7.5

def test_event_url_has_minmagnitude_and_bbox():
    url = build_event_url(_qp(), minmag=8.0, fmt="csv")
    assert "fdsnws/event/1/query" in url and "minmagnitude=8.0" in url
    assert "minlatitude=26" in url and "maxlongitude=97" in url

def test_event_candidates_are_actual_data_catalogues():
    cs = fdsn_event_candidates(_qp())
    nodes = {c.source_node for c in cs}
    assert "USGS / ANSS ComCat" in nodes and "ISC-GEM" in nodes and "NOAA NCEI" in nodes
    assert all(c.resource_role == "actual_data" for c in cs)

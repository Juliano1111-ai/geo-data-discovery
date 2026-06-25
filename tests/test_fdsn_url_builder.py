# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import expand_query, build_fdsn_urls, is_seismic

def test_fdsn_urls_have_required_params():
    qp = expand_query("seismic waveforms Etna", bbox=(14.8,37.6,15.2,37.9),
                      start="2024-01-01", end="2024-12-31")
    urls = build_fdsn_urls(qp, network="IV")
    assert "fdsnws/station/1/query" in urls["station"]
    assert "fdsnws/dataselect/1/query" in urls["dataselect"]
    # bbox constrains the STATION query; dataselect selects by network/station/time
    assert "minlatitude=37.6" in urls["station"] and "maxlongitude=15.2" in urls["station"]
    assert "network=IV" in urls["station"] and "network=IV" in urls["dataselect"]
    assert "2024-01-01" in urls["dataselect"]

def test_seismic_detection():
    assert is_seismic(expand_query("raw seismic waveforms"))
    assert not is_seismic(expand_query("sea surface temperature"))

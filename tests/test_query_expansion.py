# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import expand_query

def test_synonyms_expand():
    qp = expand_query("ground motion in Andalusia")
    assert "GNSS position time series" in qp.terms
    assert "tectonic displacement" in qp.terms

def test_raw_always_kept():
    qp = expand_query("totally novel variable xyz")
    assert "totally novel variable xyz" in qp.terms

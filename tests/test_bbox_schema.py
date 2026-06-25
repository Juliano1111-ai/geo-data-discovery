# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import expand_query

def test_box_is_minlat_minlon_maxlat_maxlon():
    qp = expand_query("x", bbox=(14.8, 37.6, 15.2, 37.9))  # W,S,E,N
    assert qp.box_schema_org == "37.6 14.8 37.9 15.2"      # S W N E

def test_no_bbox_returns_none():
    assert expand_query("x").box_schema_org is None

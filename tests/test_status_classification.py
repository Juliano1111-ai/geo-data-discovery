# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import Candidate, final_status

def _c(role, status):
    c = Candidate(title="t", source_node="s", tier=1, resource_role=role, access_url="https://x")
    c.data_status = status
    return c

def test_found_available_wins():
    assert final_status([_c("actual_data","DATA_AVAILABLE"),
                         _c("metadata_evidence","METADATA_ONLY")]) == "FOUND_AVAILABLE"

def test_restricted_when_no_data():
    assert final_status([_c("restricted_lead","RESTRICTED")]) == "FOUND_RESTRICTED"

def test_dark_trace_on_evidence_only():
    assert final_status([_c("metadata_evidence","METADATA_ONLY")]) == "DARK_TRACE"

def test_not_found_when_empty():
    assert final_status([_c("unresolved_lead","UNRESOLVED")]) == "NOT_FOUND_AFTER_PROTOCOL"

# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import Candidate, classify_bucket

def _c(status):
    c = Candidate(title="t", source_node="s", tier=1, resource_role="actual_data",
                  access_url="https://x")
    c.data_status = status
    return c

def test_split_routes_correctly():
    assert classify_bucket(_c("DATA_AVAILABLE")) == "verified"
    assert classify_bucket(_c("METADATA_ONLY")) == "verified"
    assert classify_bucket(_c("RESTRICTED")) == "restricted"
    assert classify_bucket(_c("LINK_ONLY")) == "unresolved"
    assert classify_bucket(_c("UNRESOLVED")) == "unresolved"

def test_link_only_never_verified():
    # HTTP 200 alone (LINK_ONLY) must NOT count as verified data
    assert classify_bucket(_c("LINK_ONLY")) != "verified"

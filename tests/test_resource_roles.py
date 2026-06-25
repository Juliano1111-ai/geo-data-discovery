# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
from discovery_orchestrator import (RESOURCE_ROLES, DATA_STATUSES, WORKFLOW_STATUSES,
                                    expand_query, fdsn_candidates)

def test_taxonomies_nonempty_and_known():
    assert "actual_data" in RESOURCE_ROLES and "metadata_evidence" in RESOURCE_ROLES
    assert "DATA_AVAILABLE" in DATA_STATUSES and "RESTRICTED" in DATA_STATUSES
    assert "FOUND_AVAILABLE" in WORKFLOW_STATUSES

def test_fdsn_roles_are_honest():
    qp = expand_query("seismic", bbox=(14.8,37.6,15.2,37.9), start="2024-01-01", end="2024-12-31")
    cs = fdsn_candidates(qp, network="IV")
    roles = {c.title.split()[1]: c.resource_role for c in cs}
    # the station inventory must be metadata_evidence, the waveforms actual_data
    assert any(c.resource_role == "metadata_evidence" for c in cs)
    assert any(c.resource_role == "actual_data" for c in cs)
    for c in cs:
        assert c.resource_role in RESOURCE_ROLES

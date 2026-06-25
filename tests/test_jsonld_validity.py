# Copyright (c) 2026 Juliano Ramanantsoa. MIT License.
import json, glob, os
from discovery_orchestrator import Candidate, to_schema_org, verify_and_validate

EX = os.path.join(os.path.dirname(__file__), "..", "examples")

def test_schema_org_has_required_fields():
    c = Candidate(title="t", source_node="s", tier=1, resource_role="actual_data",
                  access_url="https://x", spatial_box="37.6 14.8 37.9 15.2")
    c.data_status = "DATA_AVAILABLE"
    d = to_schema_org(c)
    for k in ("@context", "@type", "resourceRole", "dataStatus", "distribution"):
        assert k in d
    assert d["@type"] == "Dataset"

def test_example_jsonld_files_parse():
    files = glob.glob(os.path.join(EX, "*.jsonld"))
    assert files, "no example jsonld found"
    for f in files:
        with open(f, encoding="utf-8") as fh:
            arr = json.load(fh)
        assert isinstance(arr, list) and arr
        for rec in arr:
            assert rec["@type"] == "Dataset"

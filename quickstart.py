#!/usr/bin/env python3
# Copyright (c) 2026 Juliano Ramanantsoa. MIT License. See DISCLAIMER.md.
"""
quickstart.py — the simplest way to run geo-data-discovery.

No installation and no dependencies: Python 3.9+ standard library only.

    python quickstart.py            # builds + verifies links, writes outputs
    python quickstart.py --live     # on an open network, also queries catalogues

It runs three example discoveries and writes the split, verified outputs to
./discovery_outputs/<label>/ (verified_catalog.jsonld, restricted_leads.json,
unresolved_leads.json, access_validation_log.csv, workflow_status.json).
Edit the QUERIES list below to point it at your own targets.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "skill", "geo-data-discovery", "scripts"))
from discovery_orchestrator import (  # noqa: E402
    expand_query, run, print_table, final_status, write_outputs)

# label, query, bbox (W,S,E,N), start, end, FDSN network, CORDIS?, acronym
QUERIES = [
    ("etna_waveforms", "Seismic waveforms Etna 2024 raw data",
     (14.8, 37.6, 15.2, 37.9), "2024-01-01", "2024-12-31", "IV", False, None),
    ("himalaya_M8_events", "Seismic event Himalaya 1500-2026 Magnitude 8",
     (73, 26, 97, 37), "1500-01-01", "2026-12-31", "*", False, None),
    ("andalusia_gnss", "Ground motion GNSS Andalusia",
     (-7.6, 36.0, -1.6, 38.8), "2020-01-01", "2026-12-31", "*", False, None),
]

if __name__ == "__main__":
    live = "--live" in sys.argv
    for label, q, bbox, start, end, net, cordis, acro in QUERIES:
        print("\n" + "#" * 80 + f"\n# {label}\n" + "#" * 80)
        qp = expand_query(q, bbox=bbox, start=start, end=end)
        cands = run(qp, live=live, network=net, cordis=cordis, acronym=acro)
        print_table(cands)
        status = final_status(cands)
        write_outputs(cands, os.path.join("discovery_outputs", label), status)
        print(f"FINAL STATUS: {status}  ->  discovery_outputs/{label}/")

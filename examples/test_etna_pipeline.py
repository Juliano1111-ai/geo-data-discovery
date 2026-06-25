#!/usr/bin/env python3
# Copyright (c) 2026 Juliano Ramanantsoa. MIT License. See DISCLAIMER.md.
"""
test_etna_pipeline.py
=====================
Reproducible end-to-end TEST of the workflow on one example:

    Seismic waveforms  +  Mount Etna  +  2024  +  raw data

Pure standard library (no obspy, no pip). Run it on an open network:

    python test_etna_pipeline.py

What it does, and what "pass" looks like:
  STEP 1 — queries the FDSN *station* service and prints the INGV (network IV)
           seismic stations on Etna active in 2024.  PASS = a non-empty list.
  STEP 2 — downloads one hour of *raw miniSEED* (the actual waveform bytes) from
           a summit station via the FDSN *dataselect* service and saves it.
           PASS = a .mseed file of non-zero size is written.

Endpoints are the authoritative INGV FDSN web services (source: fdsn.org data
centres). The ORFEUS/EIDA federator is given as a one-line fallback. In
production you would normally drive these with ObsPy (snippet at the bottom),
which handles routing and response parsing for you.
"""
import sys
import urllib.request
import urllib.error

INGV = "https://webservices.ingv.it"                 # INGV FDSN node (authoritative)
FEDERATOR = "https://federator.orfeus-eu.org"         # EIDA federator (fallback, open data)

NETWORK = "IV"                                         # Italian Seismic Network (INGV)
BBOX = dict(minlat=37.6, maxlat=37.9, minlon=14.8, maxlon=15.2)  # Mount Etna summit box
YEAR_START, YEAR_END = "2024-01-01", "2024-12-31"
SUMMIT_STATION = "ESLN"                                # Serra La Nave (INGV-OE), active 2024
UA = {"User-Agent": "etna-workflow-test/1.0 (research)"}


def _get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def step1_list_stations(base=INGV):
    url = (f"{base}/fdsnws/station/1/query?network={NETWORK}"
           f"&minlatitude={BBOX['minlat']}&maxlatitude={BBOX['maxlat']}"
           f"&minlongitude={BBOX['minlon']}&maxlongitude={BBOX['maxlon']}"
           f"&starttime={YEAR_START}&endtime={YEAR_END}"
           f"&level=station&format=text&nodata=404")
    print("STEP 1  FDSN station query — what exists on Etna in 2024")
    print("        " + url)
    try:
        status, body = _get(url)
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP {e.code}: no stations matched (or service busy).")
        return []
    rows = [ln for ln in body.decode("utf-8", "replace").splitlines()
            if ln and not ln.startswith("#")]
    print(f"  -> HTTP {status} | {len(rows)} station(s) of network {NETWORK} in the box:")
    codes = []
    for ln in rows:
        c = ln.split("|")
        if len(c) >= 6:
            codes.append(c[1])
            print(f"       {c[1]:6}  {c[5][:34]:34}  ({c[2]}, {c[3]})")
    return codes


def step2_download_waveform(station=SUMMIT_STATION, base=INGV):
    # one hour of raw broadband (HH?) miniSEED on 1 Jan 2024
    url = (f"{base}/fdsnws/dataselect/1/query?network={NETWORK}"
           f"&station={station}&location=*&channel=HH?"
           f"&starttime={YEAR_START}T00:00:00&endtime={YEAR_START}T01:00:00&nodata=404")
    print(f"\nSTEP 2  FDSN dataselect — raw miniSEED from {NETWORK}.{station}")
    print("        " + url)
    try:
        status, body = _get(url)
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP {e.code}: no waveform for that station/channel/window "
              f"(try channel=* or another summit station).")
        return False
    out = f"etna_{NETWORK}_{station}_2024-01-01_00-01.mseed"
    with open(out, "wb") as fh:
        fh.write(body)
    print(f"  -> HTTP {status} | wrote {len(body):,} bytes of raw miniSEED -> {out}")
    return len(body) > 0


if __name__ == "__main__":
    print("=" * 78)
    print("WORKFLOW TEST — Seismic waveforms + Etna + 2024 + raw data")
    print("=" * 78)
    codes = step1_list_stations()
    if not codes:
        print("\nSTEP 1 returned nothing from INGV; retrying via the EIDA federator...")
        codes = step1_list_stations(base=FEDERATOR)
    ok2 = step2_download_waveform(station=(codes[0] if codes else SUMMIT_STATION))
    print("\n" + "-" * 78)
    print(f"RESULT: stations listed = {bool(codes)} | raw waveform downloaded = {ok2}")
    print("PASS" if (codes and ok2) else "CHECK NETWORK / ADJUST CHANNEL")
    sys.exit(0 if (codes and ok2) else 1)

# ---------------------------------------------------------------------------
# Production equivalent with ObsPy (handles routing + parsing automatically):
#
#   from obspy.clients.fdsn import Client
#   from obspy import UTCDateTime
#   cl = Client("http://webservices.ingv.it")
#   t0 = UTCDateTime("2024-01-01T00:00:00")
#   inv = cl.get_stations(network="IV", minlatitude=37.6, maxlatitude=37.9,
#                         minlongitude=14.8, maxlongitude=15.2,
#                         starttime=t0, level="station")
#   st  = cl.get_waveforms("IV", "ESLN", "*", "HH?", t0, t0 + 3600)
#   st.plot()
# ---------------------------------------------------------------------------

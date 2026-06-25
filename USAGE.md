# Usage Guide — find data, dig data, automate

A practical walkthrough for users. You have **three tools that do one job**:
locate downloadable geoscience data, dig for it when it's hidden, and do it
repeatably. Use whichever fits the moment.

| Tool | What it is | Best when | Needs |
|------|-----------|-----------|-------|
| **Prompts** (`references/*.md`) | Instructions you paste into any AI chat | You want an answer now, in whatever AI you have | An AI that can search the web |
| **Python** (`scripts/discovery_orchestrator.py`) | A runnable engine, no AI inside | You want automation, batch jobs, or guaranteed link-checking | Python 3.9+ |
| **Skill** (`dist/geo-data-discovery.skill`) | The prompts + engine packaged for Claude | You want to just ask in plain language, every day | Claude |

**Golden rule that makes all three trustworthy:** a download link is never shown
unless it was *resolved* (returned HTTP 200) during the run. You don't trust the
AI's memory — you trust a status code you can re-check.

---

## Part 1 — Use the PROMPTS (works in any AI)

The prompts are the fastest path and run in **any** assistant that can browse the
web (Claude, ChatGPT with browsing, Gemini, Perplexity…).

**Step 1.** Open `references/discovery_playbook.md`. Copy the whole file.

**Step 2.** Open a chat in an AI with web search **on**. Paste the playbook.

**Step 3.** Underneath it, type your target using the schema at the bottom of the
playbook:
```
USER DISCOVERY TARGET: [Variable] + [Geographic Area] + [Time Frame] + [Resolution/Type]
USER DISCOVERY TARGET: Ground motion + Southern Spain (Andalusia) + 2020–2026 + GNSS time-series + tectonic displacement
```

**Step 4.** Read the result. You get two things: a ranked table with a **Direct
Access Link** column (verified rows only), and a `schema.org/Dataset` JSON-LD block
you can drop into a data cube or map.

**Step 5 — data is hidden?** If standard catalogues return nothing, or the data is
restricted/embargoed/buried in a thesis, copy `references/dark_data_playbook.md`
instead and paste it with your target. You get a forensic **dossier**: evidence
that the data exists, the human steward to contact, and an openly-downloadable
proxy so your project isn't blocked.

> **The catch.** A plain chatbot can still occasionally invent a link. Treat the
> prompt as the fast first pass, then **verify the links** before you rely on them
> — which is exactly what the Python does automatically. That's why the next two
> tools exist.

---

## Part 2 — Use the PYTHON (automation, repeatable, no AI)

This is the part you run again and again. Pure standard library — nothing to
install for the core.

**Setup.**
```bash
# get the files (clone the repo or unzip it), then:
cd geo-data-discovery
```

**Run 1 — demo (see the verification gate work).**
```bash
python skill/geo-data-discovery/scripts/discovery_orchestrator.py \
  --query "Ground motion GNSS tectonic displacement Andalusia" \
  --bbox "-7.6,36.0,-1.6,38.8" --start 2020-01-01 --end 2026-12-31
```
You'll see reachable links marked `OK 200` and unreachable ones quarantined as
`FAIL`. That partition is the whole point.

**Run 2 — live (hit the real catalogues).**
```bash
python skill/geo-data-discovery/scripts/discovery_orchestrator.py \
  --query "..." --bbox "W,S,E,N" --start YYYY-MM-DD --end YYYY-MM-DD \
  --live --outdir catalogue_out
```
`--live` queries DataCite / Zenodo / re3data for real (needs an open network) and
writes a JSON-LD catalogue to `catalogue.jsonld`.

**Read the output.** The printed table is sorted most-reliable first; the line
`Verified (resolved) links: N/M` tells you how many are safe to publish. The
`.jsonld` file is the machine-readable catalogue.

### Automation recipes (the "again and again" part)

**A. Batch many targets.** Put targets in `targets.txt`, one per line, fields
separated by `|`:
```
Ground motion GNSS Andalusia|-7.6,36.0,-1.6,38.8|2020-01-01|2026-12-31
Seismic waveforms Azores|-31.3,36.9,-25.0,39.7|2024-01-01|2024-12-31
```
Then loop:
```bash
while IFS='|' read -r q bbox s e; do
  python skill/geo-data-discovery/scripts/discovery_orchestrator.py \
    --query "$q" --bbox "$bbox" --start "$s" --end "$e" --live \
    --outdir "out_$(echo "$q" | tr ' ' '_')"
done < targets.txt
```

**B. Scheduled link-health check.** Catalogues rot; re-verify weekly with cron
(`crontab -e`):
```
0 6 * * 1 cd /path/to/geo-data-discovery && python skill/geo-data-discovery/scripts/discovery_orchestrator.py --query "your standing query" --bbox "W,S,E,N" --live --outdir weekly_out
```

**C. Reuse the gate inside your own code.** Import the building blocks:
```python
import sys; sys.path.append("skill/geo-data-discovery/scripts")
from discovery_orchestrator import expand_query, verify, to_schema_org, Candidate

qp = expand_query("seismic waveforms Azores",
                  bbox=(-31.3, 36.9, -25.0, 39.7),
                  start="2024-01-01", end="2024-12-31")

# build Candidate objects from YOUR own source (a CSV, an API, a notebook), then:
checked = [verify(c) for c in my_candidates]        # the gate
jsonld  = to_schema_org(checked)                     # machine-ingestible output
```
This is how you bolt the verification gate onto a Streamlit dashboard, a notebook,
or an existing pipeline.

### Extend it
Add a new data source by writing one client function and registering it — see
`references/endpoints.md` for the routing table. For **seismic waveforms**, drive
FDSN with ObsPy and let EIDA/IRIS routing resolve nodes:
```python
from obspy.clients.fdsn import Client
inv = Client("GEOFON").get_stations(network="CP", starttime="2024-01-01",
                                    endtime="2024-12-31", level="channel")
```

---

## Part 3 — Use the SKILL (easiest, ask in plain language)

**Install (Claude).** Download `dist/geo-data-discovery.skill` and add it in
Claude's settings under Skills/Capabilities.

**Use.** Just ask, in any chat:
- *"Find me GNSS ground-motion data for Andalusia, 2020–2026."*
- *"Where can I download seismic waveforms for the Azores in 2024?"*
- *"I can't find the raw data behind this paper — trace it and suggest a proxy."*

The skill picks the mode (DISCOVERY vs DARK DATA), builds the search plan, routes
to the right APIs, runs the verification gate, and hands back the catalogue +
JSON-LD — without you pasting anything. This is the low-friction daily driver.

---

## Part 4 — Share with your users AND any AI (portability)

**Key idea:** the *skill* is a Claude convenience wrapper, but its **parts are
portable**. To deploy on whatever assistant a user has, you map the skill's
pieces into that assistant's container:

| Skill component | Claude | ChatGPT (Custom GPT / Project) | Gemini (Gem) | Plain chat (any) |
|---|---|---|---|---|
| `SKILL.md` (the procedure) | bundled | paste into **Instructions** | paste into Gem instructions | paste at top of the chat |
| `references/*.md` (playbooks, endpoints) | bundled | upload as **Knowledge** files | upload/attach files | paste the relevant one |
| `scripts/discovery_orchestrator.py` | runs inside the skill | run locally, or upload to **Code Interpreter** | run locally | run locally |

**How to set it up elsewhere (general steps — exact menu names vary, check the
platform's current docs):**
- **ChatGPT:** create a *Custom GPT* (or a *Project*) → paste `SKILL.md` into the
  instructions → upload the three `references/*.md` files as knowledge → enable web
  browsing. Users then chat with it like the Claude skill.
- **Gemini:** create a *Gem* → paste `SKILL.md` as the Gem's instructions → attach
  the reference files.

> **Watch out — Gemini's default is to write an essay.** If you ask
> "Seismic events + Himalaya + 1500–2026 + Magnitude 8", Gemini will happily hand
> you a long seismotectonic *report* with the actual data sources buried at the
> bottom. That is the model ignoring the output contract, not the method failing.
> Two fixes: (1) the `discovery_playbook.md` now opens with a hard "STOP — data
> table + JSON-LD only, no report" rule; paste that playbook, not just `SKILL.md`,
> into the Gem. (2) End your prompt with one line:
> *"Output ONLY the verified data table and the JSON-LD array — no background, no
> history, no prose."* For guaranteed verification + the real data list, run
> `discovery_orchestrator.py` (or `examples/test_etna_pipeline.py`) alongside the
> chat.

- **Any chatbot with no file support:** just paste a playbook + the target
  (Part 1). That always works.

**Important honesty for users:** only Claude *auto-runs* the bundled Python.
On other assistants, the prompts/playbooks port directly (paste + upload), but the
**Python is run separately** — it's a standalone tool that works next to any chat,
on any machine, with no AI at all. So the verification gate is always available to
everyone, regardless of which AI they use: if the chat can't verify links, run the
Python to do it.

---

## Part 5 — The repeatable operating procedure (find → dig → automate)

Teach users this loop:
1. **Frame** the target: variable + bounding box `[W,S,E,N]` + ISO dates + type.
2. **Find** (Part 1 or 3): run discovery; collect the verified links + JSON-LD.
3. **Verify** (always): if you used a plain chat, run the Python on the links
   before trusting them. Only HTTP-200 survives.
4. **Dig** (if needed): nothing open? switch to dark-data mode → dossier →
   contact the steward and/or take the proxy.
5. **Automate**: add the target to `targets.txt` (Part 2A) and/or a cron re-check
   (Part 2B) so the catalogue stays fresh without anyone re-doing the work.

---

## Part 6 — What to hand your users

Give them the **repo** (link or zip). Tell them:
- Read **this file** first.
- The 60-second proof is in `examples/DEMO_andalusia_gnss_discovery.md` — click the
  first link and a real GNSS time series for an Andalusia station downloads.
- Pick their path: paste a **playbook** (any AI), run the **Python** (automation),
  or install the **skill** (Claude).
- When a link stops resolving, the fix goes in `references/endpoints.md` — and a
  pull request is welcome.

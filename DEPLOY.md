# Deploying geo-data-discovery

This is the full path from this folder to a public, citable, documented tool:
**GitHub → Zenodo (DOI) → ReadTheDocs**. Copyright © 2026 Juliano Ramanantsoa. MIT License.

Before you start, confirm two things are how you want them to appear publicly: the
name and ORCID in `CITATION.cff`, and the GitHub username in the URLs below
(`Juliano1111-ai`). Change them once, here and in `CITATION.cff` / `README.md`,
before the history is public.

---

## Part 1 — GitHub

1. Create an empty repository on GitHub named `geo-data-discovery` (no README, no
   license — this folder already has them).

2. From inside this folder:

   ```bash
   git init -b main
   git add -A
   git commit -m "geo-data-discovery v1.0.1"
   git tag v1.0.1
   git remote add origin https://github.com/Juliano1111-ai/geo-data-discovery.git
   git push -u origin main --tags
   ```

3. Continuous integration runs automatically. The workflow in
   `.github/workflows/ci.yml` runs the compile check, the 21 tests, and
   JSON-Schema validation on every push. Confirm the green check on the
   repository's **Actions** tab.

4. (Recommended) In **Settings → General**, set the description and topics
   (`fair-data`, `geoscience`, `seismology`, `gnss`, `data-discovery`), and pin
   the repository to your profile.

---

## Part 2 — Zenodo (mint a DOI)

A DOI makes the tool citable and freezes the exact version.

1. Sign in at <https://zenodo.org> with your GitHub account.

2. Go to **Account → GitHub**, find `geo-data-discovery`, and flip the switch
   **On**. Zenodo now watches the repository for releases.

3. On GitHub, create a release from the tag: **Releases → Draft a new release →**
   choose tag `v1.0.1`, title `v1.0.1`, paste the `CHANGELOG.md` entry as the
   notes, **Publish release**.

4. Zenodo archives that release and issues a DOI within a minute or two. Copy the
   **concept DOI** (it always points to the latest version).

5. Add the badge to the top of `README.md` and commit:

   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/<your-concept-DOI>.svg)](https://doi.org/<your-concept-DOI>)
   ```

6. Put the same DOI into `CITATION.cff` as a `doi:` field so the citation is
   complete.

---

## Part 3 — ReadTheDocs

You have two clean options. Choose **A** if you want a dedicated documentation
site for this tool; choose **B** if you would rather fold the chapter into a book
you already maintain (for example a course book).

### Option A — Build this repo's `docs/` as its own site

This repository already ships a buildable Jupyter Book and a ReadTheDocs config:

- `.readthedocs.yaml` — tells ReadTheDocs how to build (it installs
  `docs/requirements.txt`, runs `jupyter-book build docs/`, and publishes the
  HTML).
- `docs/_config.yml`, `docs/_toc.yml`, `docs/intro.md`,
  `docs/finding_geoscience_data.md` — the book itself.

Steps:

1. Sign in at <https://readthedocs.org> with GitHub.
2. **Import a Project**, pick `geo-data-discovery`, and import it.
3. ReadTheDocs detects `.readthedocs.yaml` automatically. Trigger **Build
   version**. The first build takes a couple of minutes.
4. Your docs are live at `https://geo-data-discovery.readthedocs.io`. Every push
   to `main` rebuilds them.
5. Add the badge to `README.md`:

   ```markdown
   [![Docs](https://readthedocs.org/projects/geo-data-discovery/badge/?version=latest)](https://geo-data-discovery.readthedocs.io/en/latest/)
   ```

To add the worked examples as chapters later, copy them into `docs/` and list them
in `docs/_toc.yml`:

```yaml
format: jb-book
root: intro
chapters:
  - file: finding_geoscience_data
  - file: example_etna          # after copying examples/... into docs/
  - file: example_himalaya
```

Build locally first to check it:

```bash
pip install -r docs/requirements.txt
jupyter-book build docs/
# open docs/_build/html/index.html
```

### Option B — Add the chapter to an existing Jupyter Book

If you already publish a course/handbook book on ReadTheDocs:

1. Copy `docs/finding_geoscience_data.md` (and any example pages you want) into
   that book's source folder.
2. Add them to that book's `_toc.yml`.
3. Commit and push — ReadTheDocs rebuilds it. No extra configuration needed.

---

## Part 4 — Keeping it current

When you change the tool:

1. Update `CHANGELOG.md` with a new version section.
2. Bump `version:` in `CITATION.cff` and the version line in `README.md`.
3. Commit, then tag and push:

   ```bash
   git commit -am "describe the change"
   git tag vX.Y.Z
   git push origin main --tags
   ```

4. Draft a GitHub release from the new tag — Zenodo issues a fresh version DOI,
   and ReadTheDocs rebuilds, automatically.

That is the whole loop: edit → test (`pytest tests/ -q`) → tag → release. The
verification gate, the tests, and CI keep every published version honest.

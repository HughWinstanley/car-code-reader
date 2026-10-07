# Car Code Reader

A Mac app that reads and clears trouble codes through an OBD-II adapter (OBDLink EX recommended):
check-engine codes on any 1996+ vehicle, plus ABS, airbag and body modules on most Fords and GMs.

This repository is also where the app gets its updates. When it opens, the app reads
`release.json`, and if the version there is newer it offers **Update now** and downloads the
files in `app/`, checking each one against the SHA-256 listed in `release.json`.

- `release.json` - the current version, release notes and file fingerprints
- `app/` - the files the updater downloads
- `source/` - the starter, version file, release tool and Mac app launcher

To publish an update: change the code, run `python make_release.py <new version> "<what changed>" <repo folder>`,
then commit and push to `main`.

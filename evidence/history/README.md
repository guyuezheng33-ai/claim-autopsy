# Archived acceptance evidence

Earlier runs are kept here, unchanged, as a record of defects found and fixed.
They are not used as evidence for any current claim. In particular, early runs
contained literal `sk-` placeholder strings from an obsolete README example;
those strings are not credentials, but they are archived here so a repository
scan does not confuse them with live secrets.

`acceptance_*.json` files here are superseded run tags from earlier versions;
the single canonical result lives in `evidence/` at the project root. The
`screenshots_v5/` folder holds the previous English UI screenshots, replaced
in v6 by seven new captures that show the AI contrast panel, the anatomy
chain, the coverage boundary and the corpus browser. `screenshots_v6/` holds
the v6 captures (71-card numbers and the tightened refusal wording replaced
them in v7; every current screenshot is regenerated from the built page by
`tools/make_screenshots.py`, so they cannot drift from the data).
`check_language_gate.png` is the in-browser check that the "English only"
notice renders for unreadable input.

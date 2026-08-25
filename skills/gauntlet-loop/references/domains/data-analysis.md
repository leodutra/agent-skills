# Domain: Data Analysis - numbers that survive an independent recomputation

## Bars that work

- A published analysis with open data and code - a FiveThirtyEight story with its dataset repo. The LEAD saves article text, pinned commit and raw dataset under reference/; manifest: URL, commit, date. Measurable half: the headline number's interval - our recomputation must land inside it.
- The NIST Statistical Reference Datasets. The LEAD saves data file and certified values. Measurable half: certified values match to the stated digits.
- A pinned library implementation of the same method (statsmodels OLS, scipy ttest_ind). The LEAD saves version, call and printed output. Measurable half: coefficients agree within 1e-6.

## Floor

Command floors (LEAD, before any CRITIC):

- Recomputation from the metric definition matches the headline number within tolerance.
- Rerun from raw with the fixed seed gives the same output hash twice.
- Data-quality script (nulls, duplicates, units) exits 0.
- Sensitivity sweep across the declared range keeps the sign.

HELD-OUT: a raw slice and sweep parameters the BUILDER never sees.

Reading floors (CRITIC, both sides): the metric definition names numerator, denominator, window and filters; every reported number appears in the rerun output; every code filter appears in the report; no filter or feature uses information from after the moment being measured (leakage).

## What the critic physically does

It receives a/ and b/, each holding report, code and raw-data pointer. It reruns each from raw with the fixed seed, pasting headline number and output hash. It writes its own recomputation from the metric definition sentence, before reading either side's code, and compares. It runs the sensitivity sweep on both and pastes the range. Evidence: pasted command output, a quoted report line with path and line, a computed number.

The LEAD blinds the pair: same metric, reports taken at the same section, neither side truncated, notebooks converted by the LEAD to plain scripts so no cached output carries a BUILDER trace, directories renamed a/ and b/, git history and author lines stripped.

## How the LEAD splits this work

Pieces: ingestion and cleaning; one per metric; the sensitivity sweep; the findings. Cleaning feeds every metric, so it is serialised: the LEAD freezes the cleaned snapshot with a hash, then metric BUILDERS run in parallel worktrees. Findings wait for every metric to win. The assembled-whole gate reruns from raw, checks every report number against that output, and puts the whole report against the whole reference.

## A verdict, as evidence looks

```text
WINNER: A
GAP: B's headline lift excludes mobile sessions without saying so - seen by reading b/sql/conversion.sql against the metric definition, which names all sessions
FLOOR: every code filter appears in the report - A: pass (a/run.py filters on the 4-week window only; a/report.md line 8 names it) / B: fail (b/sql/conversion.sql line 9 `WHERE device = 'desktop'`; b/report.md never names device)
EVIDENCE:
- A: `python a/run.py --seed 42` prints `lift=0.061 ci=[0.032,0.090] n=184203`; a/report.md line 12 quotes the same three numbers
- A: recomputation from the definition sentence: 6.1%; weekly sweep 2.4% to 9.0%, sign holds, a/report.md line 31 states it
- B: `python b/run.py --seed 42` prints `lift=0.203 n=61877`; n is a third of the row count in raw/sessions.csv (184203)
- B: recomputation from the definition sentence: 6.1%; weekly sweep 14.9% to 26.1%, sign holds, not stated in b/report.md
- B: b/report.md line 12 states "+20% conversion" with no interval
- A and B: sha256 of out/results.csv identical across two seed-42 runs on each side
```

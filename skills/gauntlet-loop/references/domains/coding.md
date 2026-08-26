# Domain: Coding - code that beats a named reference

## Bars that work

- A reference implementation - `vercel/ms` for duration parsing, `ripgrep` for search. Frozen as a pinned commit and built package under reference/; manifest: URL, commit, date, runtime. Measurable half: its tests passed, or its benchmark number on the LEAD's machine.
- Suite-as-floor - a suite written by the LEAD or a third party (`toml-test`, CommonMark spec tests) beside a reference implementation that passes it; a suite is never B on its own, and if no implementation passes it, finding one is round zero's first job. The BUILDER never edits it. Kept as a compact table: one row per case, input, expected, required yes/no. The LEAD saves it as text plus a held-out subset. Measurable half: required tests 100% green.
- A performance budget as a number - p95 latency, bundle kB, allocations - the script saved beside the reference's number.

## Floor

Command floors, run by the LEAD on ours before any CRITIC: required tests green, existing suite green, linter clean, benchmark under budget, HELD-OUT tests green (edge cases the BUILDER never sees), and a hostile-input script (null, empty, negative, overflow, unicode, huge, concurrent, I/O failure) does not crash. Where inputs can be generated, one property-based or fuzz test sits in the held-out set. Red ends the round. Reading floors, run by the CRITIC on both sides: the code handles the case, not the literal test input; each thrown error names the bad input.

## What the critic physically does

It runs both suites, the benchmark and the hostile-input script from a clean checkout, pastes counts and numbers, then reads both sources for hardcoded test values. Evidence is pasted output, a measured number, or a quoted line with path:line.

Pair preparation: the LEAD copies both trees to `a/` and `b/`, same layout and runtime, git history stripped, comments and filenames naming a round or the CRITIC removed, one adapter so the same script calls each side; matched by function or feature, never by cutting either side. UI is rendered by the LEAD, never from BUILDER screenshots; a piece with a UI also takes its floors and pair preparation from design.md.

## How the LEAD splits this work

Pieces are public functions, modules, or endpoints, each with its own test group and held-out cases. Shared state - a schema, shared types, build config, the same file - means serialise or separate worktrees; pure functions run in parallel. The assembled-whole gate re-runs the full suite, held-out set and benchmark on the integrated build; the SMOOTHER merges duplicated helpers and aligns error-message style; a fresh CRITIC compares the whole build against the whole reference.

## A verdict, as evidence looks

```text
EVIDENCE:
- A: `npm test` in a/ - 6 passed, 0 failed; "" throws, "1h1h" returns 7200
- B: `npm test` in b/ - 4 passed, 2 failed (cases 4 and 6, negative and invalid input)
- B: b/src/parse.js:3 regex `/(\d+)([hms])/g` skips the sign, so "-5m" parses as 5m
- B: "999999999999h" returns 3.6e15 with no error; A throws `duration too large`
- A: hyperfine, 1e6 calls: 412 ms; budget 500 ms
- B: hyperfine, 1e6 calls: 388 ms; budget 500 ms
WINNER: A
GAP: B returns 0 for input it cannot parse instead of throwing; seen by running b/run.js on "abc" and "-5m", both print 0 with exit code 0.
FLOOR: thrown error names the bad input - A: pass, `Error: invalid duration: "abc"` / B: fail, no error thrown
```

# rust-style-guide rewrite: what is left after the branch

Written 2026-11-14 on `rust-style-guide-rewrite` (HEAD e194f20, two commits ahead of `main` at
56829ee). The rewrite of `SKILL.md`, `references/fundamentals.md` and `assets/lints.toml` is
committed, with the conversion-trait and tag evals (`review-conversion-traits`,
`review-reservations-ids`) and the graders aligned with it.

Rules for every item: nested `claude -p` runs spend the user's claude.ai usage, so say the cost
and when a run starts. Bench workspaces go in `.bench/`, not the scratchpad.

## 1. Compare against Google's Rust style guide

- [x] Compared Google's guide (saved locally, gitignored, as `dev/rust-style-guide/google-style.guide.md`;
  never inside `skills/`, which the benchmark copies and installs ship) with `SKILL.md` and
  `fundamentals.md`. Adopted: extension traits (`…Ext`) as a reason for a trait; no
  `impl Into<Newtype>` parameters; operators only for their meaning; std accessor names; no
  obscure abbreviations or ambiguous one-letter lifetimes and generics; `Copy` errors where the
  fields allow; poisoned locks never read (`PoisonError` accessors in `disallowed-methods`). The
  rest is recorded in fundamentals' Google section as already here, held by clippy's defaults, or
  not taken.

## 2. Benchmark the rewrite

- [x] `python3 dev/rust-style-guide/bench.py --all --ref main`. `--ref HEAD` refuses: the rewrite
  is committed, so the working tree's skill equals HEAD's; `main` holds the pre-rewrite skill.
  12 cases × 2 arms = 24 runs + 24 grading calls (Sonnet).
- [x] The nested `claude` CLI can't reach the API from the sandbox: the first attempt
  (2026-11-14) failed every call with `connection_failed` before any run finished, so nothing was
  spent. Runs go outside the sandbox (or from the user's own shell, `! python3 …`).

## 3. Adversarial evals with a no-skill arm

- [x] `bench.py --no-skill` adds an arm with no skill loaded (no system prompt added; code cases
  get no `--add-dir`); the unblinded table prints a column per arm. Dry-run checked with and
  without `--new-only`.
- [x] Eight review cases written in `evals/`, each with controls that must not be flagged:
  - `review-cli-format-flag` (ValueEnum CLI): a closed set as a validated `String` refinement with
    a custom `value_parser` and a silent `_ =>` fallback; anyhow and the print `#[expect]` in
    `main` are controls.
  - `review-route-distances` (finite f64): hand-written `Eq` on a finite-float refinement is fine;
    `Eq` on raw `f64` fields isn't; `-0.0` breaks `Hash`/`Ord` agreement; `Add` can overflow to
    infinity.
  - `review-invoice-archive` (io::Result adapter): the filesystem adapter's `io::Result`, the
    error without `Clone`/`Eq` and the trait with a test double are controls; the domain `load`
    returns `serde_json::Error` raw and turns a store failure into `Ok(None)`.
  - `review-parcel-weights` (unit that travels): grams and ounces travel as bare `u32` and `fits`
    compares them (a live bug); `from_grams` at the scale and the rounding `grams_to_ounces` stay
    named.
  - `review-metrics-exporter` (extensible trait): a published crate's public `Exporter` trait and
    `#[non_exhaustive]` error are controls; the crate-private `FlushPolicy` trait isn't needed.
  - `review-ledger-writer` (async-write cancellation): `select!` can tear a ledger line and lose
    the entry; the balance moves before the write; a dropped `JoinHandle`; a best-effort access
    log that documents accepting a partial write is the control.
  - `review-team-summary` (proportionality): one real defect (`split_at` on a byte offset);
    no newtypes, traits, error types or layers asked for.
  - `review-match-roster` (bug versus error): an error variant and an `unwrap_or_default` for
    states the constructor rules out; real input errors and an `Option` lookup are controls.
- [x] Run them: `bench.py --cases <the eight> --ref main --no-skill` (8 × 3 = 24 tool-less review
  calls + 24 grading calls). Read each run's review.md before trusting a grader: a case whose
  no-skill arm passes everything tests nothing, and a control that every arm fails may be a grader
  problem.

## Results (2026-11-15, Sonnet, one run per arm)

The benchmark ran on the skill as of 5e3c617 (before the unsafe, derive and ctor additions).
`bench.py` gained `--resume` and a retry-then-skip per call after one grading call was refused by
Sonnet's safety filter and one review came back empty.

- 12 original cases (`.bench/rsg-20261114-234541-gocqx7tb`): new 92/94, main 98/100. The new
  arm's `review-conversion-traits` grading is refused by the filter on every attempt, so it is
  unscored; on the 11 comparable cases, new 92/94 against main 93/94: a tie at one sample. The
  new arm missed a private `AccountNumber` without `Debug` (settlement-boundaries) and the generic
  `CaptureService` name (capture-service); main missed the JSON DTO (cli-json-recipients).
- 8 adversarial cases (`.bench/rsg-20261114-235302-42fkfrhf`): new 31/31, main 30/31, no-skill
  30/31. They don't separate the arms: Sonnet without the skill passes nearly all of them.
- Two graders were wrong, not the runs, and were fixed: `review-orders-store` 06 now accepts a
  finite-float refinement whose constructor rejects NaN (the rewrite's own fix), and
  `review-cli-format-flag` 04 accepts `writeln!` with its error handled in place of `println!`.

## 4. Follow-ups

- [ ] Harden the adversarial cases until the no-skill arm fails some: subtler controls (the
  traps the skill's own wording would trip a careless reader into), fewer self-evident defects.
- [ ] Score `review-conversion-traits` for the new arm: its grading call trips Sonnet's filter
  (`reasoning_extraction`); try rewording the grading prompt, or grade it with another model.
- [ ] Watch the two misses on a second sample before changing anything: private-type `Debug`
  and catch-all names.
- [x] Re-run the benchmark on the skill with the unsafe, derive and ctor additions:
  `bench.py --all --ref main`, all 20 cases, 72bfa04's skill, finished 2026-11-15 with `--resume`
  after the usage limit (`.bench/rsg-20261115-000044-ia3ulb76`). New 128/131, main 126/131. One
  new-arm review (inventory-module) came back as imitation tool calls instead of a review; that
  run was discarded and rerun (7/7). Misses: new proposed `From<Grams> for Ounces` for a rounding
  conversion (parcel-weights); main flagged the finite-float `Eq` on Kilometres
  (route-distances), missed `TryFrom` on Quantity (conversion-traits) and the JSON DTO
  (cli-json-recipients); both arms missed the `CaptureService` name and called a real input error
  in match-roster a bug. That workspace's grading.json files were later overwritten with empty
  placeholders by a `--regrade --dry-run` (a bug, since fixed: `--dry-run` now refuses an existing
  workspace); the scores above stand, the runs and reviews are intact, and 40 grading calls would
  restore the per-assertion evidence.
- [ ] Watch the rounding-conversion miss: SKILL.md already says a conversion that rounds is no
  trait; see whether a second sample repeats it before rewording.

## 5. Commit

- [ ] Commit `bench.py`, the eight cases and this file; then the benchmark results, if they
  change anything.

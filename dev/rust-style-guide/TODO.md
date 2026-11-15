# rust-style-guide rewrite: what is left after the branch

Written 2026-11-14 on `rust-style-guide-rewrite` (HEAD e194f20, two commits ahead of `main` at
56829ee). The rewrite of `SKILL.md`, `references/fundamentals.md` and `assets/lints.toml` is
committed, with the conversion-trait and tag evals (`review-conversion-traits`,
`review-reservations-ids`) and the graders aligned with it.

Rules for every item: nested `claude -p` runs spend the user's claude.ai usage, so say the cost
and when a run starts. Bench workspaces go in `.bench/`, not the scratchpad.

## 1. Compare against Google's Rust style guide

- [ ] Read <https://google.github.io/styleguide/rustguide.html> and list the details and rules it
  has that `references/fundamentals.md` (its section "What came from Google's Rust style guide":
  adopted, already here, kept against Google, not taken) and `SKILL.md` don't. Decide per item:
  adopt (replicating into SKILL.md where it is a rule), already covered, or rejected with a reason.
  Do this before the benchmark, so the benchmark measures the final skill.

## 2. Benchmark the rewrite

- [ ] `python3 dev/rust-style-guide/bench.py --all --ref main`. `--ref HEAD` refuses: the rewrite
  is committed, so the working tree's skill equals HEAD's; `main` holds the pre-rewrite skill.
  12 cases × 2 arms = 24 runs + 24 grading calls (Sonnet).
- [ ] The nested `claude` CLI can't reach the API from the sandbox: the first attempt
  (2026-11-14) failed every call with `connection_failed` before any run finished, so nothing was
  spent. Run it outside the sandbox, or from the user's own shell (`! python3 …`).

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
- [ ] Run them: `bench.py --cases <the eight> --ref main --no-skill` (8 × 3 = 24 tool-less review
  calls + 24 grading calls). Read each run's review.md before trusting a grader: a case whose
  no-skill arm passes everything tests nothing, and a control that every arm fails may be a grader
  problem.

## 4. Commit

- [ ] Commit `bench.py`, the eight cases and this file; then the benchmark results, if they
  change anything.

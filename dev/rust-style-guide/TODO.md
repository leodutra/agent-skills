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

## Discriminating run (2026-11-15, Sonnet, 2 samples, b1fa458's skill)

`bench.py --new-only --no-skill --samples 2` on the 2 new code cases and the 8 hardened review
cases (`.bench/rsg-20261115-064514-hqh1zgag`): skill 101/101, no skill 93/106 (per sample: skill
53/53 and 48/48, no skill 45/53 and 48/53). One skill-arm grading of review-match-roster is
refused by the safety filter under both Sonnet and Opus, so it is unscored.

- What separates the arms: the code cases (rate-limit-config 14 vs 7: validate-after-deserialize,
  shared error enum, public fields; ticket-reassign 14 vs 10: no FromStr round-trip proptest,
  clippy under the lint set) and review-ledger-writer's error messages (10 vs 8).
- The other seven hardening traps don't: Sonnet without the skill flags them too. Review cases
  with planted defects stay near the ceiling; writing tasks expose the defaults.
- route-distances grader 01 was too strict once the serde trap existed (the review rightly said
  the bypass undermines Eq, and asked to derive the hand-written PartialEq): fixed and regraded.

- [ ] More code cases, fewer review cases: the next ones should exercise today's additions (an
  unsafe FFI wrapper, a type whose Default or Ord tempts a hand-written impl, shared state across
  spawned tasks), since no current case tests them.
- [ ] Only then the A/B against the skill before the Google additions (0e5d632): on today's cases
  both skill versions sit at the ceiling, so a tie would say nothing about the additions.

## Validity (2026-11-15)

- Every grader says its kind: `correctness` (48: a bug any Rust reviewer would agree on) or
  `convention` (105: this skill's own rule). The table reports them apart. Recomputed from saved
  gradings: discriminating run correctness skill 30/30, no skill 30/30, convention 71/71 against
  63/76; the 12-case run against main correctness 33/33 both, convention 59/61 against 65/67. So
  far every gap is convention: the evals show the skill is followed, not that the code is better.
  The classification is the skill author's judgment; a second reader should check it.
- Graders are frozen per workspace (graders.json); a change needs `--grader-change "<reason>"`,
  regrades every arm and lands in grader-changes.md (the four earlier changes are backfilled there).
- `--validate` grades each case's reference/ and mainstream/ answers. Both code cases pass it: the
  first pass caught a weak test in the rate-limit reference (a zero limit asserted only as some
  load error), fixed. Review cases have no reference/mainstream review yet.

- [x] Correctness evidence: hidden behavioral tests (`hidden/tests/hidden.rs`, run by grade_cargo.py,
  never shown to a run, one correctness point per test) in rate-limit-config (11, prompt now pins the
  JSON shape and `load`'s signature) and in three bug-trap code cases.
- [x] reference/ and mainstream/ review.md (+ expected-fails) for all 16 review cases.
- [x] At least 3 samples on the cases that disagree (below).
- [x] Cases written by someone who hasn't read the skill: split-payout (money in f64), mask-email
  (UTF-8 byte slicing), rate-window (window math near t=0), by a subagent barred from skills/, dev/
  and .bench/. Graded by cargo test and hidden tests only; mainstream fails 3/11, 5/11, 2/10 hidden.

## Correctness run (2026-11-15, Sonnet, 3 samples, b1fa458's skill + this session's cases)

- `--validate` (`.bench/rsg-validate-20261115-173113-49q4a9_v`, plus a rerun of inventory-module whose
  reference grading returned broken JSON twice): 42 answers (16 review + 5 code cases, reference and
  mainstream each), 0 misgraded. Every grader tells the correct answer from the common one, including
  the four labels the authors called borderline (payments 03, published-crate 02, inventory 05,
  invoice-archive 02).
- `--new-only --no-skill --samples 3` on rate-limit-config, ticket-reassign, review-ledger-writer and
  the three blind cases (`.bench/rsg-20261115-173121-l92wr2cx`, 4.0M input tokens): skill 204/204,
  no skill 179/204; per sample skill 68/68 ×3, no skill 59, 60, 60 /68.
  - correctness 156/156 both arms; hidden tests 129/129 both. No run in either arm used f64 for money,
    sliced the email by bytes, or dropped the t=0 request: Sonnet avoids these traps without the skill.
  - convention 48/48 against 23/48, a gap far outside the per-sample spread: the skill reliably
    changes design (refinement types, serde through constructors, per-constructor errors, FromStr +
    proptest, no #[non_exhaustive], error-message style, its lint set).
- Conclusion so far: the skill is followed and shifts conventions; no evidence yet that it improves
  correctness, because the no-skill arm made no correctness error to fix. A correctness gain needs
  traps the bare model actually falls into (harder ones, or a weaker model).
- [x] Harder blind traps, screened on the bare model first (`--screen`: no-skill arm only, so case
  selection never reuses the samples it would be compared on). Five round-2 cases by the same blind
  author, bugs in how steps combine: volume-discount (u32 quantity overflow across lines),
  ledger-batch (partial write before an error), layered-config (early return hides a later invalid
  layer), text-edits (tie order at one position), timesheet-billing (rounding per entry instead of on
  the total). Mainstream fails 2/14, 5/13, 4/15, 2/14, 3/13 hidden; references pass all.
  - Sonnet, no skill, 2 samples (`.bench/rsg-20261115-174840-mhgxsw_8`): hidden 138/138.
  - Haiku 5.5, no skill, all 8 blind cases, 2 samples (`.bench/rsg-20261115-175010-95ditixj`):
    hidden 202/202.
  - No case survived screening, so no comparison run followed: there is no correctness deficit for
    the skill to close. Across 3 rounds and 2 models the bare model failed 0 of 469 hidden tests.
- Result: the goal's first item ("evidence the skill improves correctness") is not supported. What is
  supported: the skill changes conventions reliably (48/48 vs 23/48, outside the spread) and costs no
  correctness. Further trap hunting risks fishing for a win; a correctness claim would need traps
  drawn from real bugs that current models are documented to make, not invented ones.

## 5. Commit

- [ ] Commit `bench.py`, the eight cases and this file; then the benchmark results, if they
  change anything.

## Round 3 (in progress, stopped by the usage limit 2026-11-15)

- `bench.py` code cases may carry `starter/` (an existing crate copied into the run): maintenance
  tasks, where look-alike plain values must be threaded through existing helpers.
- The blind author stopped partway (5-hour limit) with 2 of 4 cases drafted. Both verified with
  cargo and imported into evals/ (night-premium: local-clock night premium; partial-refunds: refunds
  drift from the charged amount): starter 0/13 hidden, reference 13/13, mainstream 8/13 and 10/13.
  The lead wrote their case.yaml and expected-fails from the diff. Plan, fixed in advance: verify, import, `--screen` on Sonnet, then a fresh
  3-sample skill vs no-skill run on any case the bare model fails; report the result either way and
  stop there.
- Bias caveat (from a side review): the briefs to the blind author named trap families (money
  rounding, swappable ids, lookups hiding failures) that overlap the skill's rules. The author never
  read the skill, but the choice of traps leaned toward it, which would favour the skill. That
  doesn't weaken the null result above; any skill win on such a case must be weighed against it,
  and generic traps (UTF-8 slicing, overflow, partial writes, tie ordering) are the stronger evidence.
- Round 3 screen (2026-11-15 23:22, Sonnet, no skill, 2 samples, `.bench/rsg-20261115-232258-rhzao6oo`):
  night-premium and partial-refunds hidden 52/52. No case survived, so no comparison run. Round 3
  closes as planned: across 3 rounds, 10 blind cases and 2 models the bare model failed 0 of 521
  hidden tests. The skill's correctness benefit is not measurable with tasks like these; the
  measured benefit is convention.

## Dropped (2026-11-15, the user)

Only cases that separate the skill from no skill stay: rate-limit-config and ticket-reassign (3
samples: 54/54 vs 42/54, 21/21 vs 14/21). Dropped: the 16 review cases (7 run without the skill and
didn't separate, review-ledger-writer only on one grader, 8 never run without it), the 4 original code
cases (never run without the skill, no reference/mainstream) and the 10 blind correctness cases (not a
style-guide question). Tracked files are in git history; today's untracked work (blind cases,
reference/mainstream reviews) is in `.bench/dropped-evals-20261115/`. `--screen` and `starter/`
support went with them. The review-case code path in bench.py (place-files.sh, inputs) has no case now.
Next: the per-rule good/bad suite (static where possible) per the plan above.

## Per-rule suite (2026-11-16)

Three tiers check the guide's own claims rather than model behavior. Tiers 1–2 are static and make no model calls.

- Tier 1, `static_eval.py` (rewritten; samples in `rules/lints/`): 70 bad samples each raise their
  lint and nothing else they don't declare; 56 good samples (the guide's fix, plus the Allowed entries
  the lints touch: test unwrap, `literal`'s panic, `main` expect/exit/print, local non-`Send` future)
  are clean. Coverage runs three ways: every lint and `disallowed-*` path has a bad sample, every
  lint has a good one, and SKILL.md's "The lints hold:" list matches `PROMISES` item for item (an
  unmapped promise or an unpromised lint fails).
  - Found: clippy.toml's `ctor::dtor` was dead (ctor 0.13 moved `#[dtor]` to the `dtor` crate, and
    `allow-invalid` hid it); now `dtor::dtor`. ctor's expansion also can't compile under
    `forbid(unsafe_code)` (E0453), so the macro samples live in the unsafe probe.
  - In edition 2024 `unsafe_op_in_unsafe_fn` reports as E0133; the script maps it back through the
    "requested on the command line" note.
- Tier 2, `fixtures/template` doctests (run by `verify.py`): 11 `compile_fail` claims (swapped ids, a
  bare `u64` for a tag, building `Port`/`Email`/`Span` around the constructor, `Port::default()`,
  mutating `Span`, `&mut` into `Email`, a tracking number missing or read off a non-shipped order),
  each with a twin that differs in the misuse line and compiles. Stable rustdoc ignores
  `compile_fail,E0xxx` codes (checked), so the twin is the guard. Plus serde-bypass doctests for
  `Port` and `Span`.
- Tier 3, `rules.py` (samples in `rules/judgment/`, 19 rules, 55 samples):
  - static default: every sample compiles and passes the lint set. Bad samples included, since a bad
    sample a lint catches belongs in tier 1. It found two: `matches!(r, Err(_))` is held by
    `redundant_pattern_matching` and then `assertions_on_result_states`, and `Err(_) => Ok(None)` in
    a function with no other failure by `unnecessary_wraps`. Both samples now carry a review-only form.
  - The 8 patterns static_eval's old `--audit-gaps` kept inline (a private `Result<_, ()>`, an error
    turned to text, a `Result` or future bound to `_name` or `drop`ped, `assert!` on input, a hash
    iterator chain, a private type without `Debug`) are all tier 3 bad samples now, so this static
    check is the gap audit and `--audit-gaps` is gone.
  - `--judgment`: 55 grading calls (~0.22M tokens). Each rule's grader must flag bad and pass good
    and allowed. **Not run yet.**
  - `--fix`: bad and allowed samples, skill vs no-skill arm, "fix what needs fixing", graded by the
    same grader (allowed: the construct must survive), lint verdict reported apart. 72 runs + 72
    gradings (~1.15M tokens). **Not run yet; only after --judgment validates the graders.**
- rules.py checks each file as its own crate (one workspace, shared lockfile and target dir): in
  `--fix` a model's file that doesn't compile can't be fixed without changing the result, and in one
  shared crate it would stop the lint pass for every other run's file. A file counts as lint-clean only
  when cargo reports its crate and tests checked with no diagnostic; otherwise broken, lints or
  unknown. A fix run passes only if its rule passes and it is lint-clean.
- `claude()` moved to `claude_cli.py`, shared by bench.py and rules.py.
- The probes need crates.io once (`cargo fetch` in `$TMPDIR/rsg-static-eval` and `$TMPDIR/rsg-rules`
  outside the sandbox); after that they run offline.

### Tier 3 runs (2026-11-16, Sonnet)

- `--judgment` (`.bench/rsg-rules-20261116-005353`, 155k input tokens): 55/55. Every grader flags its
  bad samples and passes good and allowed, quoting the deciding lines. Caveat: several rule.md files
  name their allowed case outright, so this proves the graders on clear cases, not subtle ones.
- `--fix --arms none` screen (`.bench/rsg-rules-20261116-005448`, 330k): the bare model fixed 21/23 bad
  samples by the rule (20/23 lint-clean) and left 12/13 allowed constructs alone.
  - Real miss: on `constructor/allowed-open`, asked to "fix" correct code, it added an error enum that
    `open` shares with `sync`, so `open`'s error holds a failure it can't produce (the guide's
    constructor rule).
  - Lint-only: `map_err(|_| …)` (overflow) and a manual modulo clippy flags (ext-trait). The bare model
    doesn't know the lint set.
  - Eval flaws: option-vs-result/bad-ok-none's own second failure (an empty draft as an error) was
    arguably absence; now a size limit. cancellation is borderline: the fix dropped the `select!` but
    its doc promised "never a partial line", which a dropped future breaks.
- Conclusion: same as the code cases. Single-defect judgment rules don't separate the arms, because
  Sonnet fixes them without the skill. What separated were the guide's conventions (error shape) and
  its lint set. The `--fix` skill arm is worth running only on what survived: constructor, the lint
  set, cancellation and option-vs-result after the fix (3 samples).
- Skill-arm pilot (`.bench/rsg-rules-20261116-010545`, 124k fresh + 166k cached; no-skill results
  reused, plus one rerun of the changed ok-none sample): bad samples the bare model missed, skill 3/3
  (cancellation and overflow closed; ok-none passes in both arms now). Allowed left alone and
  lint-clean: skill 9/13 against no skill 11/13. One sample each, so leads:
  - **Guide gap:** the skill removed a reasoned `let _ = tx.send(…)` under `#[expect]` and made the
    function return an error. Dropping where it's right is allowed only in lints.toml's comments and
    fundamentals.md; SKILL.md, the one file the skill run reads, only says "no `.ok()` dropping an
    error". The bare model left it alone.
  - Sample flaw: `from_ratio` was neither a parse that chooses nor a name beside the same
    conversion's trait, so the skill was right to rename it `with_ratio`. Now `const fn from_u8`
    beside `TryFrom<u8>`.
  - Lint misses: a skill-written test used `assert!(r.is_err())` (unit-error); both arms wrote a
    manual `% 60` (ext-trait).
- SKILL.md's Allowed list now has the reasoned `Result` drop. Rerun (`.bench/rsg-rules-20261116-012703`):
  the skill arm keeps the `#[expect]`'d `let _ = tx.send(…)`.
- `from_u8` beside `TryFrom<u8>`: the grader passes it (`…012700`), but both arms rename it to `try_new`,
  the guide's default, which is no over-fix. Its `// keep:` line is dropped: an allowed sample without
  one only must not be flagged.
- **Open, guide gap:** both skill-arm lint misses are `assert!(serde_json::from_str::<T>(…).is_err())`.
  `serde_json::Error` has no `PartialEq`, so "assert the exact error" has no sanctioned form for a
  serde rejection: the lint bans `is_err()`, and a message substring is what exact-error-test calls a
  defect. The tier 2 doctests do the same (clippy doesn't lint doctests). SKILL.md needs to name a form.

## Evals for every skill-home rule (2026-11-16)

- The trace ledger has an eval column. trace.py fails when an S rule has no eval, a listed file is
  missing, a doctest link's fragment isn't in its file, or a tier 3 sample is claimed by no rule.
  All 98 S rules have evals (M rules exempt).
- 12 new tier 3 families, 67 samples, every bad one lint-clean. Tier 2 adds `Km`, whose `a + b`
  doesn't compile (`try_add` instead). Static gate: rules.py 122 samples, static_eval, trace and
  verify all pass.
- `--judgment` on the new families (`.bench/rsg-rules-20261116-151009`, 201k fresh input): 65/67.
  - `unsafe-placement/good.rs` was rightly flagged: `get_unchecked(7)` on a `[u8; 8]` is avoidable.
    The family was rewritten around FFI to a vendor C driver, where unsafe is unavoidable.
  - `refinement-ways-in/bad-borrow.rs` passed as clean, under a literal reading of SKILL.md's
    "`Borrow<str>` only if those agree with `str`'s". A normalized type does agree with its stored
    text; the problem is the text callers look up with. rule.md was reworded. **SKILL.md's wording
    stays ambiguous: open.**
  - Rerun of the 9 changed samples (`…151228`, 27k): 9/9.
  - Every passing bad sample's evidence cites its own rule, not just another in its family.
- **Open:** clippy's `not_unsafe_ptr_arg_deref` (deny by default) holds part of S3: a safe fn
  dereferencing a raw-pointer argument. Under "default lints are still listed" it belongs in lints.toml.
- Both opens resolved (60923cd): SKILL.md's `Borrow<str>` wording now names the text callers look up
  with; `not_unsafe_ptr_arg_deref` is listed (fundamentals L51, lints.toml, tier 1 pair).

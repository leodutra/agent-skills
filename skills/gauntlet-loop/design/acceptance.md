# Acceptance record: gauntlet-loop, 2026-09-18

Every criterion in `spec.md` §13, with how it was checked on branch `gauntlet-loop/next`. "Test" is `python3 -m unittest discover -s skills/gauntlet-loop/tests` (111 tests, all passing); "eval" is `eval/run.sh` and `eval/run_critic.sh` against `eval/baseline.json`; "live" is a run in a scratch repository with real subagents, recorded in `references/harness-claude-code.md`. Claude Code 2.1.274.

## Not done, and why

| Item | State |
| --- | --- |
| Spike S1 (agent-frontmatter hooks) | Not run. Frontmatter hooks are skipped in a folder whose trust dialog was never accepted, and accepting it is the operator's decision. The design no longer depends on them: every hook is registered in settings (spec A9) |
| AC-11.2, second half: branch protection on `main` requiring the workflow's `gate` job; the `ANTHROPIC_API_KEY` repository secret (optional since 2026-09-18, the user's call: without it CI skips the paid suites and they are run by hand, so FR-11.3 is enforced in CI for the free checks only) | The operator's: `gh` is not authenticated in the environment this was built in, and both change the repository's settings |
| AC-15.4, the sandboxed `freeze-verify` run by hand | Not done. It is covered with detection stubbed both ways (tests). The scratch repository lives under the sandbox's own temp root, where the isolation probe rightly fails (S14); a real check needs a repository elsewhere with the sandbox on |
| The pull request itself (plan, phase 20.5) | Not opened: pushing a branch and opening a pull request are the operator's to authorise. This file is its description's acceptance section |
| Global mirror refresh (`config/stack-init.sh global`), install into target repositories | After the merge, from the main checkout, by the operator (plan §1.1) |
| Three measured runs to replace the bootstrap envelope and the README's cost estimate | Needs real runs. The policy marks its proportions `bootstrap` |

## Criteria

| Id | Result | How |
| --- | --- | --- |
| AC-NN.1 | pass | test: `test_no_piece_before_the_reference_is_frozen` |
| AC-NN.5 | pass | test: `test_confirmation_needs_the_other_reader_on_another_model` |
| AC-NN.10 | pass | `eval/wordcount.py`: template 195 words; examples 248, 257, 266; the example run's pasted prompt 268 (test) |
| AC-1.1 | pass | live: a reader listed its tools (Read, Glob, Grep, Bash), no roster, no `CLAUDE.md` canary; denied everything outside its pair |
| AC-1.2 | pass | test and live: the workbench read denied, `BLIND_BLOCK` logged with agent id |
| AC-1.3 | pass | test: installed but not checked in is Tier 3; a Tier 2 status, workbench and report never say "isolated" or "cannot reach" |
| AC-1.4 | pass | README, "Why each rule is there", last row |
| AC-1.5 | pass | eval: the shipped `reader`, given a pair path and nothing else, files a verdict that begins with the pair id; live on Fable and Opus 3 of 3, on the eval model about 4 in 5 (the rest open with their conclusion and are discarded) |
| AC-2.1, AC-8.1 | pass | eval: the motivating run is refused as a manufactured bar with per-piece referents offered; a suite alone refused by name |
| AC-2.2 | pass | `SKILL.md`, the Bespoke example: "judge it champion against challenger" |
| AC-2.3 | pass | test: the report reads "converged against reference/ms", never "beat the bar" |
| AC-3.1 | pass | test and live: a held-out edit, a read of it, `git push`, a package install denied and logged as `BOUNDARY_BLOCK` |
| AC-3.2 | pass | the BUILDER dispatch in `running-the-loop.md` and the `editor` definition carry the boundary and `BLOCKED:` |
| AC-3.3 | pass | test: `## Parked` in the workbench; `parked: n` in status |
| AC-4.1 | pass | README D19 |
| AC-4.2 | pass | test: `test_parked_leaves_only_by_a_human` |
| AC-5.1 | pass | test: the example log holds the plan commit before any builder, a DERIVED floor, a finding converted through `floor add --from`, an accepted `NOT REPRODUCED` |
| AC-6.1 | pass | README D25 to D36, each with its quality cost |
| AC-6.2 | pass | test: one `CRITIC_DISPATCHED` per `CRITIC_RESULT` in the example; `pair --prepare` and floor outputs as files in the document |
| AC-6.3 | pass | `SKILL.md` flow step 4 |
| AC-6b.1 | pass | `eval/sizes.sh`: `SKILL.md` 6.7 KB, `running-the-loop.md` 10.2 KB, `controller.md` 6.0 KB, a two-line description; write mode loads `SKILL.md` alone (spec A11), a third of the baseline |
| AC-6b.2 | pass, against the baseline | eval: `run.sh --skill-only`, 8/11 before the cut, 9/11 and 10/11 after, 10/11 with the third example in |
| AC-7.1 | pass | `eval/harness_tokens.sh`; `SKILL.md` keeps `/goal` and `/effort xhigh`, the paste prompt's own text (spec A11) |
| AC-7.2 | pass | test: `test_a_fresh_clone_reaches_tier_2_from_the_harness_files_steps_alone` |
| AC-8.2, AC-14.1 | pass | the template's first line; test on the example's pasted prompt and the slash command |
| AC-9.1 | pass, as amended | README "Attribution" credits Matt Shumer only; fifteen alternatives decided against are listed unnamed, each with its entry (C1, settled by the user 2026-09-19) |
| AC-10.1, AC-10.2 | pass | `domains/design.md`; no deck row in `what-breaks.md` |
| AC-10.3 | pass | test: the example's gate turn shows `gauntletctl gate` output |
| AC-11.1 | pass | 12 write-mode cases, 21 critic pairs. Three consecutive runs: write mode 11/12, 11/12, 12/12; critic picks 21/21 three times, shape 33/42, 33/42, 35/42 |
| AC-11.2 | pass for the file; open for branch protection | `.github/workflows/gauntlet-eval.yml`: free checks and both suites on every pull request that touches the skill, failing below the baseline |
| AC-12.1 | pass | eval: `spec-input` 3/3 after the wording change (0/2 before) |
| AC-12.2 | pass | test: the example's pull request description links the manifest, workbench and whole-gate verdicts |
| AC-12.3 | pass | README D37 |
| AC-13.1 | pass | test: every metric line in the example is the controller's; `running-the-loop.md` lists the report's fields |
| AC-13.2 | pass | README "Reading the numbers" |
| AC-14.2 | pass | test: the workbench's envelope line and per-piece Spent column; status lines carry the spend |
| AC-14.3 | pass | test: `test_an_unreachable_bar_ends_on_its_own_with_the_gate_reserve_untouched` |
| AC-15.1 | pass | test: freeze strips `CLAUDE.md`, `.env`, `.cursor/` and the manifest names them |
| AC-15.2 | pass | test and live: `pair` refuses a tree with a `.env` (exit 3) |
| AC-15.3 | pass | the example names the shipped allowlist; the report has a containment line (test) |
| AC-15.4 | pass by test; the by-hand run is open | tests: `freeze` executes nothing, `freeze-verify` exits 3 without isolation and when the probe escapes, `floors` records `PIECE_BLOCKED` (execution) and proceeds when isolation is present |
| AC-16.1 | pass | test: the example's classes are 8 artifact, 2 evaluation, 2 execution, 1 scope; `metrics` counts by class |
| AC-17.1 | pass | `references/controller.md`, 5,993 bytes |
| AC-17.2, AC-17.6 | pass | tests: every rejected transition; every fact name through `event` |
| AC-17.3, AC-17.4 | pass | test: the example is an event log and its status lines are `status` output verbatim |
| AC-17.5 | pass | test: `pair` twice gives identical trees, mapping, and one attempt |
| AC-17.7 | pass | tests: unregistered, unknown, closed, wrong type; a confirmation from `reader` rejected |
| AC-17.8 | pass | tests, both tiers: refused without the key; a forged attestation collides, everything after it leaves the fold, the report lists the conflict first |
| AC-17.9 | pass | test: `init` refuses equal or missing reader pins |
| AC-M.1 | pass | README mechanism table; bounds and exits in `running-the-loop.md`; test lists every metric name |

## Spec amendments carried

A1 to A8 as planned, plus A9 (hooks in settings, not frontmatter), A10 (rows and event names the draft omitted), A11 (examples as slot fills; write mode's default load; the two harness tokens `SKILL.md` keeps). Spike S3 overturned one assumption: `SubagentStop` does not fire at the `maxTurns` cap, so a capped reader's attempt is closed by its lease (in A6).

## Defaults taken

P1 `.claude/hooks/gauntlet/`; P2 `.gauntlet/wt/<piece>/`; C1 was settled by the user on 2026-09-19 (credit Matt Shumer only; name no other implementation); C2 Python stdlib, one file; C4 GitHub Actions plus the local runners; C6 remove the deck row; C7 the bootstrap envelope; C10 regenerate the slash command from the template; C12 keep the block. C13 was decided by the user before the work began.

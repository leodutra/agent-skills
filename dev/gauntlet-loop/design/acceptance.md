# Acceptance record: gauntlet-loop, 2026-09-18

Every criterion in `spec.md` §13, with how it was checked on branch `gauntlet-loop/next`. "Test" is `python3 -m unittest discover -s skills/gauntlet-loop/tests` (111 tests, all passing); "eval" is `eval/run.sh` and `eval/run_critic.sh` against `eval/baseline.json`; "live" is a run in a scratch repository with real subagents, recorded in `references/harness-claude-code.md`. Claude Code 2.1.274.

## 2026-09-23: what the first real run exposed, fixed

Claude Code 2.1.280 installed. 153 tests, all passing, with `sizes.sh`, `harness_tokens.sh` and `wordcount.py`. Each fix below came test-first; `dev/gauntlet-loop/TODO.md` holds the plan these rows close, and spec amendments A15 to A38 record the changes to the spec.

| Finding | Result | How |
| --- | --- | --- |
| F5. `attest` read `last_assistant_message`, but on 2.1.277 agents hand back through a tool; the parse builder's `BLOCKED:` was filed as a build | fixed (A16) | `final_text()` reads the last handback from the agent's transcript and falls back to the last message; tests: `test_a_verdict_handed_back_through_the_tool_is_the_verdict`, `test_a_builder_that_hands_back_blocked_parks`. Spike S11 marked overturned in the harness file |
| F6. A `>` inside a builder's quoted `node -e` script read as a redirect, and the call was denied | fixed (A17) | redirects are matched on shell text only; here-document bodies are data; tests: `test_a_greater_than_inside_a_quoted_script_is_not_a_redirect`, and the `ProtectFloors` shell cases |
| A revision path (`git show HEAD:heldout/x`) hid a held-out file from `builder_boundary` | fixed (A17) | `path_tokens` splits on `:`; test: `test_held_out_material_and_run_state_are_unreadable` |
| F1. Nothing told a critic not to execute code when the reference was never verified | fixed (A18) | `pair` adds `READ_ONLY_LINE` to `PROMPT.md`; tests: `test_a_critic_executes_nothing_unless_the_reference_was_verified`, `test_a_verified_reference_lets_the_critic_run_both_sides` |
| F4. A builder could not run its required suite: auto mode refused the env-prefixed command | fixed by convention (A19); proof owed live | floor files fall back to the working directory; the BUILDER and AUTHOR lines say so; tests: `test_a_builder_runs_its_required_suite_without_an_env_prefix`. Only a live run shows the permission layer accepts the new command |
| F8. The pull request carried no tests | fixed (A15) | the final `commit` stages the floors; test: `test_the_final_commit_carries_the_floors_and_the_plan_commit_does_not` |
| F7. A human's `status` recorded a lead turn and ended an overdue run (the bytesize run, 2026-09-23) | fixed (A20) | `status --peek`; test: `test_peek_is_the_same_line_and_changes_nothing` |
| FR-13.1: no lead tokens | fixed (A21) | recorded at each registration from the lead's transcript; tests: `test_lead_tokens_come_from_the_transcript_the_start_hook_names`, the example's metrics block |
| The freeze offload counted files the lead cannot count before freezing | fixed (A22) | the lead always runs the freeze; README D33 rewritten; tests: `test_the_freeze_is_the_leads_own_command`, `test_the_freeze_is_never_offloaded` |
| F9. With the sandbox on, the controller could not read its own files: the allowlist's `.gauntlet` denies became `/dev/null` mounts (the bytesize-2 run) | fixed (A23), verified live | no `.gauntlet` permission rule; `controller_only` denies tools `private/`; the start hook makes the attestation key. Tests: `test_second_run_changes_nothing_and_keeps_what_was_there`, `test_private_storage_is_unreadable_by_every_tool`, `test_the_first_registration_makes_the_key_outside_the_sandbox`, `test_init_writes_the_run_and_nothing_a_plain_git_add_could_stage`. Live: a sandboxed `claude -p` in `~/Work/gauntlet-sandbox-check` (Tier 2, isolated, attestation tier-1) ran `init`, `status` and `next`, was denied three reads of `private/`, and could not write outside the project; $0.05 |
| F10. The controller's `PermissionError` was a traceback | fixed (A24) | `main()` refuses with the path; test: `test_an_unreadable_file_is_a_refusal_that_names_it` |
| F11. The lead met that traceback and went on by hand at Tier 3 | fixed (A24) | the By hand section: an installed controller that errors stops the run; test: `test_an_installed_controller_that_errors_stops_the_run` |
| F12. The coarse matcher denied `ls .gauntlet` chained to a staging write, and an `init` chained to a cleanup | message fixed (A25); coarse by design | test: `test_a_chained_controller_call_is_told_to_stand_alone` |
| F13. `protect_floors` denied `freeze-verify reference/bytes --cmd "npm install ..."` (the bytesize-3 run): the write verb inside the quoted argument and the reference path, with no exemption for the controller | fixed (A26); deployed after that run ends | test: `test_the_controller_alone_on_its_line_passes` |
| F14. Writes judged by every path-looking token: six author commands denied over `sed` scripts and `$A/test` paths | fixed (A27) | `write_targets()`; tests: `test_only_what_a_command_writes_must_stay_inside`, `test_a_script_argument_is_not_a_write_target` |
| F15. A reader's first shell command denied as unbound | fixed (A28) | bind on a first command inside one pair; test: `test_a_first_shell_command_inside_one_pair_binds_the_reader` |
| F16. `pair` left the reference's name in its files (FR-6.5 unmet) | fixed (A29) | `anonymise()`, both sides alike; test: `test_a_pair_carries_no_name_on_either_side` |
| F17. The builder returned a file where the floors needed its directory | fixed (A30) | the editor definition; test: `test_a_builder_returns_its_directory_for_code` |
| F18. `freeze-verify` refused: the parent directory was writable inside that session's sandbox | fixed (A35), 2026-09-24; first recorded as not a defect, which was wrong | the parent was a throwaway tmpfs (checked live, $0.035): the write vanished, so the runs were isolated and the probe misjudged them. A write escapes only on the project's own filesystem; test: `test_a_write_that_lands_off_the_projects_filesystem_is_not_an_escape` |
| F19. Tokens summed per transcript line and with cache reads: 23.8 million for the lead of a 0.9-hour run | fixed (A31) | once per message, cache reads left out, about 270 thousand; tests: `test_tokens_count_each_message_once_and_leave_out_cache_reads`, `test_tokens_are_read_from_the_transcript_the_stop_hook_names` |
| F21. `controller_only` denied the units lead's `freeze-verify`, alone on its line, over a `;` inside a quoted `--cmd` (2026-09-24) | fixed (A32); deployed after that run ends | test: `test_quoted_arguments_do_not_make_the_controller_chained` |
| F22. `freeze` wrote a frozen copy outside `reference/` (`reference-whole/`, the units run) | fixed (A33); deployed after that run ends | test: `test_a_frozen_copy_lives_under_reference` |
| F23. The lead could not file a question where the user looks: only a blocked piece filled the open questions (the units run) | fixed (A34); deployed after that run ends | `QUESTION_FILED`; tests: `test_a_question_for_the_user_is_filed_where_they_look`, `test_the_lead_can_file_a_question` |
| F24. A builder's scratch file in the harness's scratchpad was denied; it returned `BLOCKED` as told and its piece parked with its suite green (the units run) | fixed (A36); deployed after that run ends | tests: `test_the_harness_scratchpad_is_writable_and_nothing_else_outside`, `test_the_author_may_use_the_harness_scratchpad` |
| F25. With every remaining piece parked, the run did not end when the last active piece finished, and `next` offered a whole gate over a parked piece (the units run) | fixed (A37); deployed after that run ends | test: `test_every_remaining_piece_parked_ends_the_run_however_it_got_there` |
| F26. `controller_only` denied staging a piece's own worktree for its merge: any `git add` naming `.gauntlet` (the units run) | fixed (A38); deployed after that run ends | test: `test_committing_a_pieces_worktree_is_allowed` |

The bytesize-3 run, 2026-09-23: the lead a Claude Code session opened in `~/Work/bytesize-3` with the prompt pasted under `/goal`; Tier 2, attestation tier-1, the sandbox on in strict mode. It ended on a win with one piece, the lead's coarsest split, so a whole gate over two pieces is still owed (TODO, C3). A fable reader picked ours, and an opus reader-alt picked ours again with the sides swapped. Every agent returned through the handback tool, so without A16 both verdicts would have been discarded. Both critics judged by reading, since no reference was verified. `gauntletctl status --peek`, then `gate`, from the run's own controller:

```text
confirmed 1/1 pieces, whole: yes (2/2) | parked: 0 | blocked: 0 | spent: 5/40 inv, 1.1/3 h | ended: win
.gauntlet/verdicts/bytesize-r1-1.md: WINNER: B
.gauntlet/verdicts/bytesize-r1-2.md: WINNER: A
```

`metrics`, the lines that carry a value. The two token lines were computed before A31, with every line and every cache read counted; recounted under A31, the lead's is about 270 thousand:

```text
rounds per confirmed piece                       1.0
red floor share                                  0.67
confirmation flip rate                           0.0
discarded verdict rate                           0.0
invocations per confirmed piece                  5.0
lead turns per confirmed piece                   7.0
lead tokens per confirmed piece                  23820651.0
controller operations per confirmed piece        51.0
worker minutes per confirmed piece               10.1
tokens per confirmed piece                       2128340.0
spend                                            {'local': '5/24', 'escalation': '0/10', 'gate': '0/6'}
unused reserve                                   {'escalation': 10, 'gate': 6}
ended                                            win
ceiling hit                                      False
by class                                         {'artifact': 2, 'evaluation': 5, 'execution': 0, 'scope': 0}
attestation conflicts                            0
```

The five `evaluation` entries are the lead's own floor corrections before any critic: one held-out case was wrong, and the floors pointed at a file (F17).

The bytesize run, closed on 2026-09-23 with its own installed controller (`report --notes`, then `commit`: `a48b45b` in that repository; no remote, so promotion was not applied). It ended on its ceiling with no verdict: the lead's session stopped after both builders returned, and the overdue turn was recorded by a `status` call four days later (F7). The status line, from the report:

```text
confirmed 0/2 pieces, whole: no | parked: 0 | blocked: 0 | spent: 3/40 inv, 108.4/3 h | ended: ceiling
```

`metrics`, the lines that carry a value:

```text
parked pieces                                    0
spend                                            {'local': '3/24', 'escalation': '0/10', 'gate': '0/6'}
unused reserve                                   {'escalation': 10, 'gate': 6}
ended                                            ceiling
ceiling hit                                      True
by class                                         {'artifact': 0, 'evaluation': 0, 'execution': 0, 'scope': 0}
attestation conflicts                            0
```

It proves the stop: a stalled run ended on its own ceiling with the whole-gate reserve untouched (AC-14.3, live). It proves nothing about critics.

Still open on this date: one real run done the way a user runs it (a session opened in the target repository, under `/goal`); the spikes re-run on 2.1.280; spike S1; AC-15.4; the ponytail audit after the live run. The plan is in `dev/gauntlet-loop/TODO.md`.

## 2026-09-19: the plan's thin spots, and the first real run (in progress)

Tests now live in `dev/gauntlet-loop/tests` (122, all passing, with `sizes.sh`, `harness_tokens.sh` and `wordcount.py`). Claude Code 2.1.277.

| Gap | Result | How |
| --- | --- | --- |
| a. Phase 9h: three hooks carried their own path lists | closed | `policy/v1.json` holds `critic_blind`, `author_scope` and `controller_only`; test: `PolicyDriven` runs each hook from a copy with an edited policy. The version stays `v1`: the values are the ones the hooks carried, and no run was in flight |
| b. Phase 9c: `pair` refuses where the plan says strip | closed, decided | What is not the deliverable never enters a pair; a trace inside it, a line or a filename, is refused. README D40, spec A13; test: `test_history_is_stripped_and_a_trace_in_a_filename_is_refused` |
| c. Spec 8.4.1: `piece referent` and `piece mode` | spec amended (A13) | The judgment events are the interface; `MODE_SELECTED` takes two values; both are rejected for an open piece. Test: `test_referent_and_mode_are_judgments_recorded_before_the_piece_opens` |
| d. `shared_by_rule` and `offload` read by nothing | closed | `next` names them at the freeze, the split and the referent step; the runbook points at `next` instead of repeating the numbers. Tests: `Next`, `NextBeforeTheFreeze` |
| e. An author's shell writes unchecked | closed | `author_scope` matches `Bash`; test: `test_an_authors_shell_writes_are_held_to_the_same_trees`; the installer test checks the wiring |
| f. Harness file, S1 row | closed | The line now says `detect` never reads the folder's trust; test: `test_docs.py` |
| g. No path without the controller | closed | `## By hand` in `running-the-loop.md`, 10,236 of 10,239 bytes; test: `test_docs.py` |

Found along the way, each with a test: the shared shell matcher ignored bare words, so `rm -rf heldout` passed every hook (`_paths.path_tokens`; `test_shell_writes_are_denied_and_shell_reads_are_not`); floor outputs entered a pair on our side only, under the lead's floor names and with `$GAUNTLET_OURS` on the command line (spec A14; `test_floor_outputs_enter_a_pair_on_both_sides_or_on_neither_and_name_no_side`).

The first real run: `~/Work/bytesize` (installed, checked in, `detect` tier 2 before the run), goal a zero-dependency byte-size library, bar `visionmedia/bytes.js` 3.1.2, two pieces plus the whole, envelope 40 invocations and 3 hours. The lead is a session in another checkout, so every role agent is spawned by a relay: `claude -p` inside the target repository in auto mode, one Agent call with the real definition. Lead-side hooks therefore do not fire on the lead; role-side hooks and the start and stop hooks do. Round zero is done and committed (`commit --plan`); the author and both builders were registered by the start hook. NOT FINISHED at the time of this record: no verdict yet.

| Finding | State |
| --- | --- |
| F1. Nothing says what a critic may execute in a pair when the reference was never verified under isolation; FR-15.7 blocks such a pair on paper, `pair` does not know. The lead wrote read-only critic steps by hand | open: test and fix owed |
| F2. In a folder whose trust dialog was never accepted the harness ignores `permissions.allow` from project settings ("Ignoring 18 permissions.allow entries"), so the shipped allowlist does nothing there; hooks still fire. The operator accepted trust for this folder mid-run | recorded in the harness file, in the "No stalled prompts" row and under "Checks by hand" |
| F3. A hook's first run left `__pycache__/` beside it, `git status` was no longer clean and `detect` fell to tier 3 for the next run | fixed: the installer writes a `.gitignore` there; the fresh-clone test runs every wired hook, then `detect` |
| The offload rule for `freeze` counts reference files the lead cannot know before freezing, and `freeze` is one command that prints only the manifest | open: wording |

Still open: AC-15.4 (the sandbox is off in the target repository), spike S1 (trust is now accepted there; not run yet), the mirror refresh.

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

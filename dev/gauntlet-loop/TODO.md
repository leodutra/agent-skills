# gauntlet-loop v2: what is still missing, and the plan to finish it

Written 2026-09-23 against `design/intent.md`, `design/spec.md` and `design/plan.md`, after the 2026-09-19 section of `design/acceptance.md`. State then: `main` at dbb074d, one commit ahead of `origin`; 122 tests and the three free checks pass; Claude Code 2.1.280, while the spikes in `skills/gauntlet-loop/references/harness-claude-code.md` were observed on 2.1.274 and 2.1.277.

The first real run (`~/Work/bytesize`, 2026-09-19) never filed a verdict. It ended on `ceiling` on 2026-09-23, when a `status` call recorded a lead turn 107 hours into its 3-hour envelope.

Rules for every item: a failing test first, the smallest root-cause fix, then docs, and a spec amendment when the spec was the hole (plan §1.2). No new dependencies. Development files stay out of `skills/gauntlet-loop/`. Credit Matt Shumer only. Nested `claude -p` runs spend the user's usage: say the cost and wait for a yes. Never edit `~/.claude.json`. No push. Never write or reinstall a run's tooling during that run.

Decided by the user on 2026-09-23: the final commit carries every floor (A5); `status --peek` for humans (A7); the lead always runs the freeze itself (A9); a ponytail audit after the live run (D5).

## Stage A: code fixes (free, test-first)

- [x] **A1. F5: `attest` reads the handback message.** On 2.1.277 both builders returned through a `SubagentHandback` tool call (`tool_input.message`); `last_assistant_message`, the field `attest` reads, held only the chatter after it. So the parse builder's `BLOCKED:` was filed as a normal `BUILDER_DONE`, and a reader that hands back the same way would have every verdict discarded. Spike S11 said the opposite on 2.1.274. Evidence: `~/.claude/projects/-home-leo-Work-bytesize/49550e34-8372-4ed5-8455-a546235fcddf/subagents/agent-ac9d8a2ead1aff783.jsonl`. Fix: `final_text(p)` beside `transcript_tokens()` returns the last handback message from `agent_transcript_path`, else `last_assistant_message`; the tool name goes in the `HARNESS` table and the harness file. Tests: a handback verdict with chatter after it yields a valid `CRITIC_RESULT`; a handback `BLOCKED:` parks the piece; the old tests pass through the fallback.
- [x] **A2. F6: redirects are matched on shell text only.** A builder's `node --input-type=module -e "... h.length > 50 ..."` was denied "outside your directory": `WRITES` matched the `>` inside the quoted script, then the whole script counted as one path. Fix in `hooks/_paths.py`: look for redirects with quoted strings and quoted-heredoc bodies removed; the write-verb check stays on the raw string. Tests: the exact bytesize command is allowed; `echo "a > b"` is not a write; `echo x > heldout/y` and `cat > heldout/x <<'EOF'` are still denied.
- [x] **A3. F1: a critic executes nothing when nothing was verified.** FR-15.7 forbids executing reference code without isolation, but `pair` never said so and the domain files tell critics to run both sides. Fix: when no `REFERENCE_VERIFIED` covers the piece's referent, `pair` appends a controller line to `PROMPT.md`: compare by reading, execute neither side. `swap` carries it. Tests: present by default, absent once the reference is verified.
- [x] **A4. F4: a builder runs its required suite with no env prefix.** Auto mode refused `GAUNTLET_OURS=... node --test ...` in both spellings, and the shipped allowlist's `Bash(node *)` does not cover it. Fix: floor files resolve ours as `$GAUNTLET_OURS`, else the working directory; the builder runs `cd <worktree> && node --test <root>/tests/required/<piece>/`. The AUTHOR and BUILDER lines in `running-the-loop.md` say so. Tests: `builder_boundary` allows that command; `test_docs.py` checks both lines.
- [x] **A5. F8: the pull request carries the floors.** Worktrees are cut before the floors exist, and neither `commit --plan` nor the final `commit` stages `tests/required/`, `heldout/` or `bench/`, so the pull request has no tests. Fix: the final `commit` adds all three after the secret scan; nothing floor-related is committed during a run. Test: in the tree after `commit`, not after `commit --plan`. Spec FR-12.2 amended.
- [x] **A6. A revision path hides a held-out file.** `git show HEAD:heldout/x.mjs` resolves as an ordinary path outside `heldout/`. Fix: `path_tokens` splits on `:` as well as `=`, after skipping URLs whole. Test: `builder_boundary` denies it.
- [x] **A7. F7: `status --peek`.** Every `status` records `LEAD_TURN`, expires leases and can derive `BUDGET_EXHAUSTED`, so a human who checks a run changes it. Fix: `--peek` prints the same line from the fold, writing nothing; the runbook and the harness file say humans use it. Test: `--peek` on an overdue run leaves the log byte-identical.
- [x] **A8. FR-13.1: lead tokens per confirmed piece.** `metrics` counts subagent tokens only, though every `SubagentStart` payload carries the lead's transcript path (S2). Fix: `attest --start` records it on `AGENT_REGISTERED`; `metrics` adds `lead_tokens_per_confirmed_piece`. Test: a fixture transcript gives the expected sum.
- [x] **A9. The lead always runs the freeze.** `next` said an author freezes "a reference beyond 12 files", a count the lead cannot know before freezing, and `freeze` already returns only the manifest, so the lead never holds the bytes. Fix: drop the freeze offload and `offload.reference_files` from the policy and `next`; the author offload stays for floors beyond 60 lines. README D33, spec FR-6.13 and FR-6.14 amended. Test: `next` names no author for the freeze.

Done 2026-09-23: 132 tests; `running-the-loop.md` at 10,207 of 10,239 bytes. A4 still needs the live run to show the permission layer accepts the new command.

## Stage A2: what the bytesize-2 run exposed (2026-09-23)

The user turned the sandbox on in `~/Work/bytesize-2` (`/sandbox`, `settings.local.json`). The lead's `gauntletctl init` crashed with `PermissionError` on `.gauntlet/events.jsonl`: inside the sandbox, `events.jsonl`, `state.json` and `private/` were `/dev/null` mounts. The sandbox docs (fetched 2026-09-23) say `Edit` permission rules and `Read` deny rules are merged into the sandbox configuration, so the shipped allowlist's `.gauntlet` denies mask the controller's own files from the controller, which runs inside the lead's sandboxed shell. The lead then fell back to "by hand" at Tier 3, where no pair can be built and no reader can work. I recommended stopping that run; its files stay as evidence.

- [x] **F9. The controller cannot run with the sandbox on.** Fix: the shipped allowlist carries no permission deny on `.gauntlet/`; `hooks/controller_only.py` also matches `Read|Glob|Grep` and denies every agent and the lead reads of `.gauntlet/private/` (by path for file tools; a string match for the shell, the controller alone on its line excepted); `init` no longer creates the attestation key, and the start hook creates it on first use, outside the sandbox (S4). Tests: the installed settings carry no `.gauntlet` deny; the hook denies private reads; `init` makes no key and the first registration does. Live: a sandboxed `init`, `status` and `pair` in a scratch repository (a few cents, one `claude -p`). Spec FR-1.4 amended; README D22 and the ledger; the harness file's S5 row and settings table.
- [x] **F10. A controller I/O error is a traceback.** Fix: `main()` turns an `OSError` into a refusal (exit 3) that names the path and points at the harness file. Test: an unreadable event log exits 3 with its path.
- [x] **F11. An installed controller that errors made the lead go "by hand".** Fix: the runbook's By hand section says it is for a run with no controller, and an installed controller that errors stops the run: report the error, never continue by hand. Test: `test_docs.py`.
- [x] **F12. The coarse shell matcher denied `ls .gauntlet` chained to a staging write, and an `init` chained to a cleanup.** Fail-closed stays (spec: coarse by design); the denial now says to run the controller alone on its line and each write as its own command. Test: the reason names it.
- [x] **F13. `protect_floors` denied `freeze-verify` with an install step** (the bytesize-3 run): the write verb inside the quoted `--cmd` and the reference path, and no exemption for the controller alone on its line. Fixed test-first (A26). Deploy only after bytesize-3 ends: its lead reads the deployed runbook, and a run's tooling never changes mid-run.
- [x] **Retry C2 in a fresh `~/Work/bytesize-3`** once F9 to F12 are committed and deployed; `bytesize-2` keeps what that run left, as evidence. Prepared 2026-09-23: F9 to F12 committed as `d4a0eb0` and deployed (mirror diff empty); `~/Work/bytesize-3` has the skeleton (`38c9f5a`) and the fixed skill (`5d1b909`), `detect` Tier 2, no `.gauntlet` permission deny. The prompt is the one under C2. Waiting on the user to open `claude` there, accept trust, optionally `/sandbox` strict, and paste it.

## Stage B: records, commit, deploy (free)

- [x] **B1. Records.** Spec amendments A15 onward; README entries in place; the harness file (S11 overturned with the 2.1.277 evidence, the handback tool, 2.1.280 installed); `acceptance.md` rows for F4 to F8, dated; this file ticked.
- [x] **B2. Gate.** `python3 -W error -m unittest discover -s dev/gauntlet-loop/tests`, `sizes.sh`, `harness_tokens.sh`, `wordcount.py`.
- [x] **B3. Commit.** One `fix:` commit on `main`, no bytecode or scratch files, with this file. No push.
- [x] **B4. Deploy.** `config/stack-init.sh global` (the whole stack installer: it also re-checks Serena, codegraph, npm tools and settings env vars), then `diff -rq -x __pycache__ skills/gauntlet-loop ~/.claude/skills/gauntlet-loop` prints nothing. Done 2026-09-23 from `00f2b5b`: the diff printed nothing.
- [x] **B5. Close out bytesize** with its own installed controller: `report --notes <file>`, `commit` (no remote: promotion not applied), `status` and `metrics` pasted into `acceptance.md`.

## Stage C: proof (paid; needs the user)

- [ ] **C1. Cheap spikes, about $2; ask first.** S1 in `~/Work/bytesize` (trust accepted 2026-09-19); S3 (`maxTurns`); plan 20.3, one prompt from `SKILL.md` alone: `dev/gauntlet-loop/eval/run.sh --skill-only --only <case>`.
- [ ] **C2. A real run, the way a user runs it.** I prepare `~/Work/bytesize-2` from the bytesize skeleton, install the fixed skill, commit, check `detect` says tier 2, and write the paste prompt from `SKILL.md` (same goal, 40 invocations, 3 hours). The user opens `claude` there, accepts trust, sets `/effort xhigh` and auto mode, optionally `/sandbox` strict (which enables `freeze-verify`, lets critics execute, and covers AC-15.4 and S14), and pastes it. Cost: the user's usage, at most 40 subagent spawns; tens of dollars. It must show for the first time on v2: verdicts attested through the handback, a builder's green suite line, no false boundary blocks, hooks on the lead, the `/goal` evaluator reading the status line, a swapped confirmation, a wave, the whole gate over two pieces, and a routed loss with a resumed builder if a loss occurs.
  - Prepared 2026-09-23: `~/Work/bytesize-2` (skeleton `4ed100b`, the fixed skill installed and committed as `424edf8`; `detect` says tier 2, and still does after a hook leaves bytecode behind, which proves F3 live). The prompt, written from `SKILL.md`'s template (267 words; GOAL and BAR 68):

    ```text
    /goal Ours beats the bar blind: two fresh critics in a row, the second with A and B swapped on a different model, pick ours on every piece and on the whole library, or 40 invocations or 3 hours are spent. Until then, run a gauntlet loop:

    Build bytesize, a JavaScript library that parses byte sizes like "1.5 GB" to bytes and formats bytes back.

    The bar is visionmedia/bytes.js at tag 3.1.2. Clone it and freeze the copy first; judge against the copy, never a description. It must survive a hostile-input script without crashing. Never add a runtime dependency. Write the required tests and a held-out set before any builder starts; no builder edits them.

    Split it into the coarsest pieces that can be judged alone; each gets a builder and a fresh critic every round. Only you fetch the bar. The critic gets ours and the bar as A and B in random order and hears the goal, never the bar's name, which is which, or who made either. It opens both, writes what it sees in each, picks one and names the biggest thing the loser lacks. No ties; a hedge is a loss. The builder closes that gap; repeat.

    If the same gap comes back, split that piece, then change builders, then fan out variants; never mark it done. When every piece wins, judge the whole the same way.

    Update a progress page after every verdict: piece, round, winner, gap. End every turn with pieces confirmed and what is spent. Questions go there, not to me. Only I end this earlier.

    Fan out subagents.
    ```

  - Waiting on the user: open `claude` in `~/Work/bytesize-2`, accept trust, `/effort xhigh`, auto mode, optionally `/sandbox` strict, paste. Humans check the run with `gauntletctl status --peek`, never plain `status`.

## Stage D: after the run

The bytesize-3 run, 2026-09-23: `ended: win`, 5 of 40 invocations, 0.9 hours, Tier 2, attestation tier-1, the sandbox on in strict mode. One piece: the lead split the whole library into a single piece, which the prompt allows (coarsest first), so the wave and a whole gate over two pieces were not seen. Proven live: `init` under the sandbox (F9); verdicts attested through the handback on 2.1.280, by every agent (A1, S11); the builder's own suite with no env prefix, 21/21 (A4); a fable reader's win confirmed by an opus reader-alt on the swapped pair; `rerun` on the win; `RUN_ENDED win` derived. Friction, as findings:

- [x] **F14. An author's and a builder's shell writes are judged by every path-looking token.** Six author commands were denied: `sed 's/…/…/'` scripts and `$A/test` paths counted as write paths outside its trees. The rule "writes stay inside X" should look at write targets only (redirect targets, operands of write verbs), and deny a target it cannot resolve. Test first.
- [x] **F15. A reader's first shell command is denied until a file tool binds it.** Both readers lost a turn: `cd <pair> && cat PAIR_ID` and `cat <pair>/PAIR_ID` were denied as unbound. Bind on a shell command whose paths all lie in one pair. Test first.
- [x] **F16. `pair` leaves the reference's name in its files.** FR-6.5 says names are stripped at prepare; they are not. The lead had an author make an anonymised copy by hand, and the first critic still recognised the reference from its code. Fix, symmetric on both sides: drop identity files from a side that is a directory (README, LICENSE, CHANGELOG, HISTORY, AUTHORS, NOTICE), blank a package manifest's identity fields, and drop comment-only lines that carry a copyright or the reference's name. Code that names it stays: recognition from the code itself is D8's residual risk. Test first.
- [x] **F17. The builder returned a file where the floors needed its directory.** It returned `src/index.js`, the floors got a file path, and the lead amended all four floors with a directory walk. Fix: the editor definition says to return its directory for code, the file only for a single document. Test: `test_docs.py`.
- [x] **F19. Token counts were inflated.** Usage repeats on each line of a message and cache reads dominate; the lead of a 0.9-hour run read 23.8 million. Fixed test-first: once per message, cache reads left out (about 270 thousand).
- [x] **F18. `freeze-verify` refused because the parent folder looked writable inside the session's sandbox.** First called not a defect; wrong. Checked live on 2026-09-24: the sandbox lays a throwaway tmpfs over `/home/leo` and binds the project in, so the write succeeded and vanished. Both bytesize-3 and units were isolated, and their critics lost execution to the probe. Fixed test-first (A35): a write escapes only on the project's own filesystem. Deploy after the units run.
- [x] **F21. A quoted `;` made the controller look chained.** The units lead's `freeze-verify`, alone on its line, was denied over `--cmd '... ; echo "exit $?"'`: `controller_alone()` read operators in the raw string. Fixed test-first (A32): operators on shell text only; a substitution inside double quotes still counts. The live run was told to drop the `; echo`. Deploy after the units run.
- [x] **F22. `freeze` wrote outside `reference/`.** The units lead froze a combined copy into `reference-whole/`, where no floor hook guards it. Fixed test-first (A33): `freeze` refuses a destination outside `reference/`. Deploy after the units run.
- [x] **F23. The lead could not file a question.** The prompt, the runbook and FR-5.5 send questions and unattended DERIVED items to the open questions, but only a blocked piece filled them; the units lead wrote its five open decisions to a staging file. Fixed test-first (A34): `QUESTION_FILED` (note, piece optional), shown in the workbench and the report. Deploy after the units run.
- [x] **F24. The harness's scratchpad was out of bounds.** The harness sends every agent there for temporary files; `builder_boundary` denied the bytes builder's `check.mjs` there and told it to return `BLOCKED`, so a piece with its suite green parked (the author was denied twice too). Fixed test-first (A36). The user was advised to resume bytes and keep scratch files inside the worktree until the deploy.
- [x] **F25. Every remaining piece parked did not end the run.** Bytes parked while durations was active; when durations finished nothing re-checked, and `next` offered the whole gate over a parked piece. Fixed test-first (A37). Deploy after the units run.
- [x] **F26. Staging a piece's worktree was denied.** Any `git add` in a command that named `.gauntlet` was refused, and a piece's worktree lives under `.gauntlet/wt/`, so the units lead could not stage bytes for its merge (told to use `git commit -am` meanwhile). Fixed test-first (A38): denied only with `--force` or a path into `.gauntlet/` outside `wt/`. Deploy after the units run.
- [x] **F27. My F19 fix undercounted subagent output.** It kept a message's first transcript line, but a subagent's message streams and its usage grows (7, then 1,218 output tokens). Fixed test-first (A39): the last line per message.
- [x] **F28 to F30, from the units run's end.** `ms`'s lowercase `license.md` passed the identity filter; the whole gate's side of ours held empty `reference/` folders; the lead ran the controller from a worktree and wrote to its stale `.gauntlet/`. Fixed test-first (A40 to A42).
- [ ] **F20 (efficiency). The lead orients by hand.** The bytesize-3 lead read `--help` for nine commands and a hook's source; the units lead spent its first turn on `git log`, the hook folders and the settings, which `detect` already checks. Proposed: the runbook says `detect` checks the install and `next` names the first command with its flags, so neither is inspected by hand (test in `test_docs.py`, inside the byte ceiling). After the units run, with its log as the measure; never while a run is live.
- [x] **C3. A run with two pieces and a whole gate.** Done 2026-09-24: `ended: win`, 12 of 60 invocations, 1.1 of 4 hours; status, gate and metrics in `acceptance.md`. Coarse-first put this goal in one piece, as it should. A goal whose parts have different referents splits by itself; for example "a byte-size parser and a duration parser, one package", with `bytes.js` and `ms` as the bars. Prepared by me, started by the user, after F14 to F17 are deployed.
  - Prepared 2026-09-23: F13 to F19 committed (`c388692`) and deployed, mirror diff empty; `~/Work/units` has the skeleton (`e62a2e5`, `src/bytes.js` and `src/duration.js`) and the fixed skill (`0f40e0d`), `detect` Tier 2. The prompt, from `SKILL.md`'s template with per-piece bars (267 words; GOAL and BAR 68):

    ```text
    /goal Ours beats the bar blind: two fresh critics in a row, the second with A and B swapped on a different model, pick ours on every piece and on the whole package, or 60 invocations or 4 hours are spent. Until then, run a gauntlet loop:

    Build units, a JavaScript package parsing and formatting byte sizes ("1.5 GB") and durations ("2h 30m").

    The bars are per piece: byte sizes against visionmedia/bytes.js 3.1.2, durations against vercel/ms 2.1.3. Freeze each; judge against the copy, never a description. It must survive a hostile-input script without crashing. Never add a runtime dependency. Write the required tests and a held-out set before any builder starts; no builder edits them.

    Split it into the coarsest pieces that can be judged alone; each gets a builder and a fresh critic every round. Only you fetch the bars. The critic gets ours and the bar as A and B in random order and hears the goal, never the bar's name, which is which, or who made either. It opens both, writes what it sees in each, picks one and names the biggest thing the loser lacks. No ties; a hedge is a loss. The builder closes that gap; repeat.

    If the same gap comes back, split that piece, then change builders, then fan out variants; never mark it done. When every piece wins, judge the whole the same way.

    Update a progress page after every verdict: piece, round, winner, gap. End every turn with pieces confirmed and what is spent. Questions go there, not to me. Only I end this earlier.

    Fan out subagents.
    ```

  - Waiting on the user: open `claude` in `~/Work/units`, accept trust, `/effort xhigh`, auto mode, `/sandbox` strict if wanted, paste. Humans check it with `gauntletctl status --peek`.



- [ ] **D1. Findings.** Read the log, the report and the transcripts; each finding test-first, as in Stage A.
- [x] **D2. Spikes observed live.** Done 2026-09-23 from bytesize-3: S2, S6, S10, S11 (every agent handed back); S12, S3 and S14 not seen. S2, S6, S10, S11, S12, and S14 with the sandbox, dated with the version, in the harness file.
- [x] **D3. `acceptance.md`.** The run's `status`, `metrics` and, on a win, `gate`, pasted and dated, with what stays open.
- [x] **D4. Commit and re-mirror.** Done 2026-09-23 after bytesize-3: `c388692`, deployed, mirror diff empty; repeated 2026-09-24 after C3 from `f47df9e` (F18, F21 to F30 deployed), mirror diff empty. A second `fix:` commit on `main`; `config/stack-init.sh global`; the mirror diff prints nothing.
- [x] **D5. Ponytail audit.** Done 2026-09-24 on `skills/gauntlet-loop`; it only reported. Candidates, each test-first with its spec row, none touching a non-negotiable (about -92 lines, no dependencies):
  - [ ] one shell matcher: move `controller_only` and `protect_floors` onto `write_targets` (add `chmod`), drop `_Writes`, `_WRITE_VERBS`, `_REDIRECT` and `path_tokens`' bare-word branch (about -30)
  - [ ] the report and the workbench build their shared sections in one function (about -20)
  - [ ] drop the installer's `verify()` and `--verify`; `detect` checks the manifest, and the tests use it (about -16)
  - [ ] drop `hooks/register.py`: settings pass `attest.py --start` (about -9)
  - [ ] drop the `workbench` subcommand: every transaction rewrites the file (about -8)
  - [ ] drop the policy's unread `envelope.write_mode_default` and `envelope.bootstrap` (about -5)
  - [ ] drop the allowlist's unread `user_settings_recommended`; the harness file documents the credential denies (about -4)
  Declined: one critic per win (D7); random labels over the HMAC seed (D24, D29, AC-17.5); dropping conflict voiding (D24, AC-17.8); hooks as prompts (D16, D18); one budget counter (D21); removing the example run (D13).

## Stage E: tokens and speed, without touching a check (proposed 2026-09-24)

Measured on the two real runs (per-message usage, last line; cache reads counted separately):

| | bytesize-3, 55 min | units, 64 min so far |
| --- | --- | --- |
| lead: cache reads / output | 12.3 M / 76 k | 26.4 M / 100 k |
| all subagents: cache reads / output | 2.0 M / 34 k (5 agents) | 3.3 M / 45 k (11 agents) |

The lead is about 85 to 89 percent of every token processed, and the runs are lead-bound (17 subagent-minutes in 55). A run's cost is roughly lead calls times lead context, so the levers are fewer lead calls and a smaller lead context. None of the items below changes a critic, a confirmation, a floor or what a win is. Each is test-first, and each is measured on the next run with the numbers above, per confirmed piece.

- [ ] **E1. Every controller command ends with what is next.** A command that moves the run prints the `next` lines after its own output, so the lead stops calling `next` separately (12 calls in bytesize-3, 30 in units, each re-reading the whole context). `next` stays for a resume. The runbook's "after every event run `next`" becomes "read the next lines each command prints".
- [ ] **E2. Load less by default.** `example-run.md` is read only when the lead is stuck, never at round zero (every fresh session counted as "a first run", and it is 18 KB carried for a hundred calls). The harness file keeps what a run needs (the install, the needs-and-fallback table, the settings the controller reads); the dated spike and check rows move to `dev/gauntlet-loop/design/harness-evidence.md`, where humans read them. The runbook says the controller's and the hooks' source are never read in a run: `next`, `--help` and a denial's reason are the interface (the units lead read 28 KB of controller source; F20 folds in here). Sizes stay gated by `sizes.sh`.
- [ ] **E3. One command per mechanical round.** `gauntletctl round <piece>`: floors, then the pair if they are green, printing the reader's path or the red floor; the confirmation stays `swap`. Two lead calls per round become one, and the steps keep their order.
- [ ] **E4. Independent pieces in one turn.** The runbook says commands for different pieces go in one turn as parallel tool calls: one model call instead of one per piece.
- [ ] **E5. Effort where quality is bought, pinned.** `editor`, `reader` and `reader-alt` set `effort: xhigh` in their definitions (today they inherit the session's, so a forgotten `/effort` shortchanges them). With that pinned, the lead's own effort becomes a separate question: one measured run with the session at `high`, compared on lead output, rounds, flip rate and the verdicts, before any default changes (D36 stays until the numbers say otherwise).
- [ ] **E6. Floor review by case list (experiment).** The author returns one line per case beside the paths, and the lead reviews the list and the red run on the skeleton instead of reading every file (units: about 21 KB of test code in the lead's context). D14's custody holds: the lead can open any file. Measured against the floor corrections a run needs.

## Left to the operator on purpose

- Push `main`.
- Branch protection on `main` requiring the workflow's `gate` job; optionally the `ANTHROPIC_API_KEY` secret (FR-11.3).
- Three measured runs, to replace the bootstrap envelope, the README's cost estimate and the offload thresholds (FR-13.3, C7).

## Checked and not missing

The slash command is regenerated from the template (C10); the repository README lists the skill; the CI path filters cover `dev/gauntlet-loop/` and `slash-commands/gauntlet-goal.md`; plan gaps a to g are closed with tests; spec amendments run A1 to A14; the attribution credits Matt Shumer only.

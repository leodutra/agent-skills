# gauntlet-loop v2: what is still missing, and the plan to finish it

Written 2026-09-23 against `design/intent.md`, `design/spec.md` and `design/plan.md`, after the 2026-09-19 section of `design/acceptance.md`. State then: `main` at 2720757, one commit ahead of `origin`; 122 tests and the three free checks pass; Claude Code 2.1.280, while the spikes in `skills/gauntlet-loop/references/harness-claude-code.md` were observed on 2.1.274 and 2.1.277.

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

## Stage B: records, commit, deploy (free)

- [x] **B1. Records.** Spec amendments A15 onward; README entries in place; the harness file (S11 overturned with the 2.1.277 evidence, the handback tool, 2.1.280 installed); `acceptance.md` rows for F4 to F8, dated; this file ticked.
- [x] **B2. Gate.** `python3 -W error -m unittest discover -s dev/gauntlet-loop/tests`, `sizes.sh`, `harness_tokens.sh`, `wordcount.py`.
- [ ] **B3. Commit.** One `fix:` commit on `main`, no bytecode or scratch files, with this file. No push.
- [ ] **B4. Deploy.** `config/stack-init.sh global` (the whole stack installer: it also re-checks Serena, codegraph, npm tools and settings env vars), then `diff -rq -x __pycache__ skills/gauntlet-loop ~/.claude/skills/gauntlet-loop` prints nothing.
- [x] **B5. Close out bytesize** with its own installed controller: `report --notes <file>`, `commit` (no remote: promotion not applied), `status` and `metrics` pasted into `acceptance.md`.

## Stage C: proof (paid; needs the user)

- [ ] **C1. Cheap spikes, about $2; ask first.** S1 in `~/Work/bytesize` (trust accepted 2026-09-19); S3 (`maxTurns`); plan 20.3, one prompt from `SKILL.md` alone: `dev/gauntlet-loop/eval/run.sh --skill-only --only <case>`.
- [ ] **C2. A real run, the way a user runs it.** I prepare `~/Work/bytesize-2` from the bytesize skeleton, install the fixed skill, commit, check `detect` says tier 2, and write the paste prompt from `SKILL.md` (same goal, 40 invocations, 3 hours). The user opens `claude` there, accepts trust, sets `/effort xhigh` and auto mode, optionally `/sandbox` strict (which enables `freeze-verify`, lets critics execute, and covers AC-15.4 and S14), and pastes it. Cost: the user's usage, at most 40 subagent spawns; tens of dollars. It must show for the first time on v2: verdicts attested through the handback, a builder's green suite line, no false boundary blocks, hooks on the lead, the `/goal` evaluator reading the status line, a swapped confirmation, a wave, the whole gate over two pieces, and a routed loss with a resumed builder if a loss occurs.

## Stage D: after the run

- [ ] **D1. Findings.** Read the log, the report and the transcripts; each finding test-first, as in Stage A.
- [ ] **D2. Spikes observed live.** S2, S6, S10, S11, S12, and S14 with the sandbox, dated with the version, in the harness file.
- [ ] **D3. `acceptance.md`.** The run's `status`, `metrics` and, on a win, `gate`, pasted and dated, with what stays open.
- [ ] **D4. Commit and re-mirror.** A second `fix:` commit on `main`; `config/stack-init.sh global`; the mirror diff prints nothing.
- [ ] **D5. Ponytail audit.** `ponytail-audit` on `skills/gauntlet-loop`; it only reports. Check every finding against `intent.md`'s non-negotiables and the README D-entries. An accepted cut goes test-first with its own README entry; a finding that would weaken a non-negotiable (two critics, the swapped confirmation, blind pairs, attestation, the hooks) is recorded as declined, with the entry that argues for keeping it.

## Left to the operator on purpose

- Push `main`.
- Branch protection on `main` requiring the workflow's `gate` job; optionally the `ANTHROPIC_API_KEY` secret (FR-11.3).
- Three measured runs, to replace the bootstrap envelope, the README's cost estimate and the offload thresholds (FR-13.3, C7).

## Checked and not missing

The slash command is regenerated from the template (C10); the repository README lists the skill; the CI path filters cover `dev/gauntlet-loop/` and `slash-commands/gauntlet-goal.md`; plan gaps a to g are closed with tests; spec amendments run A1 to A14; the attribution credits Matt Shumer only.

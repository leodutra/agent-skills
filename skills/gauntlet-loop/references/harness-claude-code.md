# Harness facts: Claude Code

Minimum version: Claude Code 2.1.271. Every line below was observed on 2.1.274 (Linux, bubblewrap sandbox) on 2026-09-18 in a scratch repository, unless it says "docs" (the Claude Code docs as they read that day). A fact that backs an enforced rule is re-run before a release and re-dated. This is the only file that knows the harness: the method files name no harness command, and the controller calls no harness API.

## Install, before a run

1. `python3 <skill>/install/claude_code.py <repo>`: copies the controller, the hooks and the policy to `.claude/hooks/gauntlet/`, the five definitions to `.claude/agents/`, merges the hooks block and the allowlist into `.claude/settings.json`, writes `MANIFEST.sha256`. Idempotent.
2. Review the diff. The reader pins (`model:` in `reader.md` and `reader-alt.md`) must be two different models your plan offers, and must equal the policy's `confirmation` entry; changing them is a policy change, made here by a human, never mid-run.
3. Enable the sandbox (`/sandbox`, strict mode) if reference code has to execute or you want hook-authenticated attestation. Credential denies go in user or managed settings; the harness ignores them in project settings.
4. Check it in. A rule counts as enforced only when its hook was in checked-in or managed settings before the run started.
5. `.claude/hooks/gauntlet/gauntletctl detect` should report `"tier": 2`. The method files write `gauntletctl` for that path. A lead that installs at round zero instead runs at Tier 3 and says so.

## What the method needs, and the fallback

| Need | Here | Unavailable |
| --- | --- | --- |
| A loop the lead cannot end | `/goal` as the prompt's first token: the whole message is the condition (up to 4,000 characters); after every turn a small fast model reads the transcript only and restarts the lead until the condition holds; a turn that ends with subagents running is not judged until they report; the user ends it with `/goal clear`. The evaluator cannot run commands, so it reads the status line, and can clear a goal it judges impossible, which is why the lead never writes that the bar is out of reach (docs, 2026-08-25) | Hooks disabled: make `/loop` the first token instead, same body; the lead reschedules itself every turn (a minute or more apart, one 20-minute fallback, seven-day expiry). Any other agent: the Portability section of `what-breaks.md` |
| Effort that reaches builders and critics | `/effort xhigh` for the session, set before pasting. `ultracode` is `xhigh` plus workflow orchestration that competes with `next`; `max` is diminishing returns. `editor-fast` and `author` set `effort: high` in their definitions (docs) | Say so in the first turn and go on |
| Fresh subagents by definition | The Agent tool with `subagent_type` naming the definition (`reader`, `reader-alt`, `editor`, `editor-fast`, `author`); fresh context by default; never `fork`; `model` per call only for `editor`, whose definition pins none | No separate context: one self-review pass, and never call it a gauntlet |
| Resume a builder with its context | `SendMessage` to its agent id (S12). It belongs to the lead; no role definition lists it, which also keeps the roster away (S9) | Spawn a fresh `editor` with the artifact, the bar sentence, the matched reference, GAP and FLOOR |
| Parallel pieces | 20 concurrent subagents by default; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` raises it; at the cap a spawn fails, it does not queue (docs). Count what is running before a fan-out | Serialise |
| No stalled prompts | A subagent's permission prompt lands in the lead's session and stalls the run. Auto mode, or the shipped allowlist. Say which in the first turn, as a statement | - |
| A worktree per piece | The controller runs `git worktree add` under `.gauntlet/wt/`. Never the Agent tool's `isolation: worktree` (one per agent, from the default branch), never a sibling directory (S14, S5) | - |
| The pull request | `gh pr create` and `gh pr view`, through `promote` and `status`; branch protection on the target branch is what makes "no run merges its own result" hold | No remote that takes pull requests: report promotion as not applied |
| The progress page | `.gauntlet/workbench.md`. For visual work it may also be published as an Artifact redeployed to the same path; a script inlines screenshots as data URIs, under 16 MiB | The file alone |
| Hooks | Registered in settings, never in agent frontmatter (S1). `disableAllHooks` anywhere forces Tier 3. Hooks added mid-session count for the next run | Tier 3 |

The Workflow tool is not for the loop: its agents prompt for anything not allowlisted even in auto mode, and the loop needs a seeded pair and a user who can stop it.

## Spikes, 2026-09-18, Claude Code 2.1.274

| Spike | Observed | Decides |
| --- | --- | --- |
| S1 | NOT RUN. Hooks declared in a project agent's frontmatter are skipped, with an error in the debug log only, when the folder's trust dialog was never accepted; `claude -p` skips the dialog, and trust on a parent folder is not inherited. Accepting the dialog is the operator's decision, so the spike waits for one. Docs: agent-scoped `PreToolUse` hooks fire with `agent_id` and `agent_type` | Deny hooks are registered in settings and branch on `agent_type` (the path S10 verified); `detect` reads the folder's trust |
| S2 | Settings-level `SubagentStart` and `SubagentStop` fire for custom agents and match on agent type (`reader\|reader-alt\|editor`). Start carries `agent_id`, `agent_type`, `cwd`, `session_id`, `transcript_path`. Stop adds `last_assistant_message` (the full final text) and `agent_transcript_path` | attest input |
| S3 | `SubagentStop` does NOT fire when `maxTurns` is reached. The Agent tool result comes back marked "PARTIAL output" with the agent id and a note that `SendMessage` continues it | The collision guarantee holds only for agents that stop; a capped reader leaves an open attempt for the lease to close |
| S4 | A hook command runs outside the sandbox: it read a file under `sandbox.filesystem.denyRead` and wrote to the project's parent directory while sandboxed shell could do neither | The attestation key can live in a file only hook processes read |
| S5 | `permissions.deny` `Read(.gauntlet/private/**)` blocks the file tools for the lead and for subagents, and also denied `cat` of that path through the shell. `blockReadsOutsideWorkingDirectories: true` blocks file-tool reads outside the project for both | private storage sits behind permission denies |
| S6 | `PreToolUse` `updatedInput` rewriting works for the lead and inside subagents (`echo original` ran as `echo rewritten`) | a reader's shell command is rewritten to start in its pair. `updatedInput` alone, with no `permissionDecision`, rewrites without approving the command |
| S7 | `claude -p <goal> --append-system-prompt "$(cat SKILL.md)" --tools "" --setting-sources "" --strict-mcp-config --model <id> --output-format json` runs one write-mode case with no tools and no references: about $0.05 on `claude-sonnet-5`. `claude -p --agent reader` runs a definition as the main agent with its tool list: about $0.02 on `claude-haiku-4-5`. Frontmatter hooks under `--agent`: not run, same reason as S1 | eval runners; full suite under $3 a run |
| S8 | The subagent transcript (`agent_transcript_path`, JSONL) names the model and carries token usage on every assistant line | token metrics read from transcripts |
| S9 | A subagent whose tools omit `SendMessage` reports no other agents and no roster | no role lists `SendMessage` |
| S10 | A settings-level `PreToolUse` hook fires inside a subagent with `agent_id` and `agent_type`. The payload `cwd` is the project root even after the subagent ran `cd` into a worktree; the `cd` does not persist to its next call | a builder is bound to its worktree by its first write, not by `cwd` |
| S11 | A reader with a `tools:` allowlist delivers its final text in `last_assistant_message`; no handback tool was involved | attest reads `last_assistant_message` |
| S12 | A builder resumed with `SendMessage` keeps its `agent_id`; `SubagentStart` and `SubagentStop` both fire again on every resume | an editor stops once per round; re-registration is normal |
| S13 | A reader with `omitClaudeMd: true` could not quote a canary line from the repository's `CLAUDE.md`; the same definition without the field quoted it | readers set the field |
| S14 | Under the sandbox: `.gauntlet/wt/<piece>/` is writable from sandboxed shell; a path under `denyRead` reads as nonexistent to sandboxed shell, including a sandboxed controller; `excludedCommands` matches a subcommand prefix (`./gauntletctl pair *`); a compound command that starts with an excluded prefix runs unsandboxed in full (`./gauntletctl pair x && cat <denied file>` printed the file). A project under the sandbox's own temp root can write to its parent directory | No `excludedCommands` ship. The read deny names the attestation key only, so every lead-invoked command stays sandboxed and none needs the key |

## Settings the controller reads (`gauntletctl detect`)

Docs, 2026-09-18. This table mirrors the `HARNESS` table at the top of the controller's `freeze` section; the controller knows nothing else about the harness.

| What | Where |
| --- | --- |
| Settings scopes, low to high | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json` (where `/sandbox` saves), then managed: `/etc/claude-code/managed-settings.json` (Linux, WSL), `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS) |
| Sandbox keys | `sandbox.enabled`, `sandbox.allowUnsandboxedCommands` (false is strict mode), `sandbox.excludedCommands`, `sandbox.filesystem.denyRead`, `sandbox.network.allowedDomains` |
| Credential denies | `sandbox.credentials.files` and `.envVars`, applied from user and managed settings only; entries in project or local settings are ignored (2.1.246 and later) |
| Hooks off | `disableAllHooks` at any scope forces Tier 3 |
| Checked in | `.claude/settings.json`, `.claude/hooks/gauntlet/` and `.claude/agents/` tracked by git with a clean status |
| Tier 2 | the manifest verifies, every installed hook script is wired in checked-in or managed settings, checked in, readers set `omitClaudeMd`, hooks not disabled. Otherwise Tier 3 |
| Isolated (for `freeze-verify`) | sandbox enabled, strict mode, no excluded commands, a network allowlist; and the command's own probe cannot write to the project's parent directory. A project under the sandbox's temp root fails the probe (S14) and is treated as not isolated |
| Tier 1 | never reported: it needs a container per critic, which the controller cannot see. Attestation is `tier-1` when Tier 2 holds, the sandbox is strict, and `denyRead` names `.gauntlet/private/attest.key` |

## Decisions that rest on these facts

- Worktrees live at `.gauntlet/wt/<piece>/`, made with `git worktree add` (S14: writable from sandboxed shell; a sibling directory is not, and is unreadable under `blockReadsOutsideWorkingDirectories`, S5).
- A builder is bound to its worktree by its first write (S10), and a resumed builder keeps its binding because it keeps its `agent_id` (S12).

## Checks by hand

| Date | Version | Check | Observed |
| --- | --- | --- | --- |
| 2026-09-18 | 2.1.274 | AC-1.1, AC-1.2: install into the scratch repository (untrusted folder), spawn a `reader` on a pair | The shipped `reader` filed a shaped verdict starting `PAIR: parse-r1-7f3a` and refused by itself the out-of-pair steps planted in `PROMPT.md`. An obedient stand-in under the same agent type was denied `Read` of the workbench, `cat ../../state.json`, a rootless `Glob` and a `Grep` of `reference/`, each with "outside your working set" and a `BLIND_BLOCK` event (seq 1 to 4); its `ls` and `pwd` ran inside the pair |
| 2026-09-18 | 2.1.274 | End to end in the scratch repository, installed and checked in (`detect`: Tier 2), real subagents, the harness's own hooks attesting | `editor` (builder): the start hook recorded `AGENT_REGISTERED`, its first write bound it to the piece, the stop hook recorded `BUILDER_DONE`. `reader` (Fable): `CRITIC_RESULT` valid, `CRITIC_WIN` derived through the mapping, model recorded from the pin. `swap` dispatched and `reader-alt` registered, then the account's usage limit ended that agent mid-run: no stop hook fired, the attempt stayed open for its lease, and the confirmation was NOT observed live. Two mistaken dispatches with an empty path were each denied outside any pair and filed as `VERDICT_INVALID`, names no open attempt. Bugs this run found and the tests now cover: a worktree inherits tracked env files and `.claude/`; `>` in `=>` and `2>&1` read as a write; a reader's `./$s/` loop denied; a reader unable to write a scratch file in its own pair; `swap` inverting the live pair a reader had written in |
| 2026-09-18 | 2.1.274 | The same, a fresh run after the limit reset, through to the end | `editor` built; `floors` green; `pair`, `reader` (Fable): `CRITIC_WIN`; `swap`, `reader-alt` (Opus): `CONFIRMATION_WIN`; `RUN_ENDED` win derived; `gate` printed `parse-r1-1.md: WINNER: B` and `parse-r1-2.md: WINNER: A`, the inversion visible; `status` ended `win` at 3/30 invocations. Denied live and logged: the builder's `cat .gauntlet/workbench.md` (`BOUNDARY_BLOCK`), the confirming reader's `ls -la ../../..` (`BLIND_BLOCK`). In the paused first run the dead agent's lease expired to `BLOCKED` and the two-hour clock ended it on `ceiling`. Found and fixed: a reader's quoted-heredoc test driver was denied over JS template literals |

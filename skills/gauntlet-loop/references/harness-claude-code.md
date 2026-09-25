# Harness facts: Claude Code

Minimum version: Claude Code 2.1.271; last run against 2.1.280, 2026-09-24. Each fact here was observed on a named version, or says "docs" (the Claude Code docs as they read that day); a fact that backs an enforced rule is re-run before a release and re-dated. The observations behind them, spikes S1 to S14 and every check by hand, are the skill's development record (`dev/gauntlet-loop/design/harness-evidence.md` in its repository), not something a run reads. This is the only file that knows the harness: the method files name no harness command, and the controller calls no harness API.

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
| Effort per role | Pinned in the definitions, since a definition's `effort` overrides the session's: `editor`, `reader` and `reader-alt` at `xhigh`, `editor-fast` and `author` at `high`; a level a model lacks runs as the highest one below it (docs, 2.1.280). `/effort xhigh` for the session, set before pasting, now sets the lead's alone. `ultracode` is `xhigh` plus workflow orchestration that competes with `next`; `max` is diminishing returns. README D36 says when a pin comes out | Say so in the first turn and go on |
| Fresh subagents by definition | The Agent tool with `subagent_type` naming the definition (`reader`, `reader-alt`, `editor`, `editor-fast`, `author`); fresh context by default; never `fork`; `model` per call only for `editor`, whose definition pins none | No separate context: one self-review pass, and never call it a gauntlet |
| Resume a builder with its context | `SendMessage` to its agent id (S12). It belongs to the lead; no role definition lists it, which also keeps the roster away (S9) | Spawn a fresh `editor` with the artifact, the bar sentence, the matched reference, GAP and FLOOR |
| Parallel pieces | 20 concurrent subagents by default; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` raises it; at the cap a spawn fails, it does not queue (docs). Count what is running before a fan-out | Serialise |
| No stalled prompts | A subagent's permission prompt lands in the lead's session and stalls the run. Auto mode, or the shipped allowlist, which the harness applies only in a folder whose trust dialog the operator accepted (2026-09-19); the hooks fire either way. Say which in the first turn, as a statement | - |
| A worktree per piece | The controller runs `git worktree add` under `.gauntlet/wt/`. Never the Agent tool's `isolation: worktree` (one per agent, from the default branch), never a sibling directory (S14, S5) | - |
| The pull request | `gh pr create` and `gh pr view`, through `promote` and `status`; branch protection on the target branch is what makes "no run merges its own result" hold | No remote that takes pull requests: report promotion as not applied |
| The progress page | `.gauntlet/workbench.md`. For visual work it may also be published as an Artifact redeployed to the same path; a script inlines screenshots as data URIs, under 16 MiB | The file alone |
| Hooks | Registered in settings, never in agent frontmatter (S1). `disableAllHooks` anywhere forces Tier 3. Hooks added mid-session count for the next run | Tier 3 |

The Workflow tool is not for the loop: its agents prompt for anything not allowlisted even in auto mode, and the loop needs a seeded pair and a user who can stop it.

## Settings the controller reads (`gauntletctl detect`)

Docs, 2026-09-18. This table mirrors the `HARNESS` table at the top of the controller's `freeze` section; the controller knows nothing else about the harness.

| What | Where |
| --- | --- |
| Settings scopes, low to high | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json` (where `/sandbox` saves), then managed: `/etc/claude-code/managed-settings.json` (Linux, WSL), `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS) |
| Sandbox keys | `sandbox.enabled`, `sandbox.allowUnsandboxedCommands` (false is strict mode), `sandbox.excludedCommands`, `sandbox.filesystem.denyRead`, `sandbox.network.allowedDomains` |
| Credential denies | `sandbox.credentials.files` and `.envVars`, applied from user and managed settings only; entries in project or local settings are ignored (2.1.246 and later) |
| Hooks off | `disableAllHooks` at any scope forces Tier 3 |
| Checked in | `.claude/settings.json`, `.claude/hooks/gauntlet/` and `.claude/agents/` tracked by git with a clean status |
| Permission rules and the sandbox | `Read` deny and `Edit` permission rules are merged into the sandbox configuration, so a path they name is hidden or read-only for every sandboxed command, the controller included (docs, 2026-09-23). The installed settings name none of `.gauntlet/` |
| Scratch writes | the harness tells every agent to keep temporary files in its session scratchpad, `/tmp/claude-<uid>/<project>/<session>/scratchpad` (observed 2026-09-24); the policy's `scratch_writes` lets builders and authors write there, and no reader can read it |
| Agent returns | an agent's final return is the `message` input of its last `SubagentHandback` tool call in `agent_transcript_path`, when it made one (2.1.277); otherwise `last_assistant_message` |
| Tier 2 | the manifest verifies, every installed hook script is wired in checked-in or managed settings, checked in, readers set `omitClaudeMd`, hooks not disabled. Otherwise Tier 3 |
| Isolated (for `freeze-verify`) | sandbox enabled, strict mode, no excluded commands, a network allowlist; and the command's own probe cannot write to the project's parent directory on the project's own filesystem. Inside the sandbox of an interactive or `claude -p` session on Linux, `/home/<user>` is a throwaway tmpfs and the project is bind-mounted from disk: a write to the parent succeeds and never reaches the disk (2026-09-24, 2.1.280), so it is not an escape. A project under the sandbox's temp root fails the probe (S14) and is treated as not isolated |
| Tier 1 | never reported: it needs a container per critic, which the controller cannot see. Attestation is `tier-1` when Tier 2 holds, the sandbox is strict, and `denyRead` names `.gauntlet/private/attest.key` |

## Decisions that rest on these facts

- Worktrees live at `.gauntlet/wt/<piece>/`, made with `git worktree add` (S14: writable from sandboxed shell; a sibling directory is not, and is unreadable under `blockReadsOutsideWorkingDirectories`, S5).
- A builder is bound to its worktree by its first write (S10), and a resumed builder keeps its binding because it keeps its `agent_id` (S12).

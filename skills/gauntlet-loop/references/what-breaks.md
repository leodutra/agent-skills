# What breaks a gauntlet loop, and other harnesses

Rationale for write mode's rules. `SKILL.md` is complete without it; the decision ledger is the skill's `README.md`.

## What breaks a gauntlet loop

- **A vague bar.** The critic invents a comparison and approves everything. Most common failure by far. If no reference comes to mind, the first job of the loop is to find one; never let the agent start building against a vague target.
- **A manufactured bar.** A second build from the same spec, made to have something to compare against. Both builds share the spec's blind spots, and a floor that tests neither defect passes both. Refuse it by name; a held-out test written at round zero finds what it would have found.
- **The critic hearing the bar's name.** A critic told the reference is Nike finds the swoosh; told it is Julia Evans, finds the voice. It then judges the name, not the work. The lead fetches and freezes; the critic gets A, B and the goal with the name removed, nothing that says which is which.
- **The builder judging its own work.** The critic must be a separate agent with fresh context, and a new one every round: a reused critic conforms to its own earlier answer and, having seen which side changed, knows which side is ours. It never sees the builder's notes or how many rounds have run.
- **A soft critic.** Give it a binary job: which one is better, A or B. Scores out of 10 have no anchor, so a threshold gets crossed by noise; a list of ten gaps gets ten shallow fixes. Make it write what it sees before it picks, or it picks first and writes observations to match.
- **Labels the critic can decode.** Ours always handed over second, a file called hero-v4-final, a comment mentioning round three, a subagent named after a piece, round or role. Seeded order, clean names, no trace of the loop inside the artifact.
- **The builder editing the bar.** Tests, eval cases and criteria are fixed before building; a green test the builder rewrote is not a green test.
- **Named exit after N rounds.** Also "no improvement in two rounds, stop". The exit is winning the comparison, confirmed by a second critic with the order swapped on a different model; the only other ends are the user and the ceiling, which counts what was spent and grades nothing. A repeated gap is a reason to split further or change builders, never to stop.
- **Splitting too fine.** Every piece carries two confirmations and fixed per-agent overhead. Split coarse first, as fine as a piece can still be paired with a matching part of the bar and run without sharing an edge; a repeated gap splits further on its own.
- **Over-specifying.** Every extra instruction is one fewer decision the agent makes with its own judgment. Minimal wins.

## Bars by kind of work

| Goal | Bar that works |
| --- | --- |
| Website, app, UI | The live site of a specific best-in-class product, screenshotted at the same viewport |
| Game, 3D, visual | Real footage or screenshots from a named shipped title, same resolution |
| Writing | A specific published piece by a named author or publication, same length and format |
| Code, tooling | A named repo's implementation at a pinned commit, plus a test suite the builder did not write as the floor |
| Research, analysis | A named analyst report or a paper's methods section; every citation must open and say what is claimed |
| Data, metrics | A known result or standard method, recomputed independently from raw |
| Prompts, agents, skills | The current prompt as baseline on a frozen eval set with a held-out split |
| Detection rule | The MITRE ATT&CK technique's attack data, plus a benign log set it must stay silent on |

## Portability

The prompt's first word and the line under it are written for Claude Code; `harness-claude-code.md` has the facts behind them and what to do when a command is unavailable. Where the goal command is unavailable, the harness file names the fallback first word; the body stays the same.

For any other agent, replace the first line with "Keep looping until two fresh critics in a row, the second with A and B swapped on a different model, pick ours on every piece and the whole, or [N] subagent runs or [T] hours are spent. Run a gauntlet loop:" and the last line with "Run the builders and critics as parallel subagents with their own context." The structure carries over unchanged. Without the controller and its hooks every rule is advisory, and the run says "blind by instruction".

Method: Matt Shumer, ["How to Run a Gauntlet Loop"](https://somethingbig.ai/gauntlet-loop). This skill is an independent adaptation.

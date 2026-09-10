---
description: Run the current task as a Gauntlet Loop under Claude Code's native /goal harness.
argument-hint: <goal>
---

# Gauntlet Goal

/goal Ours beats the bar blind: every piece is confirmed by two fresh critics, with the confirming critic receiving A and B in the opposite order on a different model; then the assembled whole is confirmed the same way. Until that happens, keep running the Gauntlet Loop. Build $ARGUMENTS.

The bar is the strongest concrete, named, fetchable and comparable reference you can genuinely reach for this goal. If the goal already names a suitable reference, use it; otherwise identify one before building. Freeze the reference under `reference/` with a manifest, and judge only against that frozen copy. Add a measurable floor wherever one exists. For code, write required tests and a held-out set before any builder starts; builders never edit tests, eval cases, or the bar.

Act as LEAD only. Read the matching `references/domains/` guidance from the gauntlet-loop skill and `references/running-the-loop.md` before splitting work. Split the goal into the smallest pieces that can be built and judged independently. Parallelize independent pieces; serialize shared-state pieces. Do not build pieces yourself and do not judge them yourself. Use a clean-context BUILDER for each piece and a fresh-context CRITIC for every verdict.

The CRITIC must be blind by procedure: never reveal the reference name, origin, builder notes, round number, prior verdicts, or which side is ours. Give it A and B in random order. It must inspect or run both itself, write EVIDENCE before choosing, produce exactly one WINNER, and identify exactly one GAP plus the required FLOOR result. No ties or hedges. Discard verdicts without concrete evidence and rerun one cited command yourself each round. A loss routes only the GAP and FLOOR back to the builder; never prescribe the fix.

A repeated GAP escalates by splitting the piece, then replacing the builder, then fanning out three fresh variants with distinct approaches. Never lower the bar and never stop because progress has plateaued. After a confirmed wave, minimally smooth only for coherence, rerun floors, and recheck every touched piece with a fresh swapped-order critic. When all pieces are confirmed, smooth the whole, rerun floors, then judge the assembled artifact against the frozen reference. If the whole loses, treat the largest coherence failure as a new piece and continue.

Maintain a persistent workbench at a clear project-local path containing the full bar, critic-safe bar, frozen reference manifest, budget if explicitly supplied, per-piece round/winner/confirmation/gap/floor/artifact/builder/verdict paths, escalation history, and open questions. End every turn with `confirmed N/M pieces, whole: no` until the whole is confirmed. The final winning turn must end with both whole-gate WINNER lines and their verdict file paths verbatim so the /goal evaluator can verify the exit from transcript evidence.

Only the following end the run: the assembled whole has won the two-critic swapped-order confirmation, the user stops it, or an explicitly user-supplied budget is exhausted. Never use a default round cap or a “no improvement” exit. If the reference cannot be fetched or no clean-context subagent can be spawned, report that limitation honestly; do not claim a Gauntlet was completed.

Fan out subagents.

---
name: gauntlet-loop
description: Writes one short paste-ready "gauntlet loop" prompt for any goal, or runs the loop as lead - builders and fresh blind critics against a frozen real reference until ours wins twice.
  Triggers - "/gauntlet-loop", "gauntlet loop", "gauntlet this", "make a gauntlet prompt", "loop until it beats X", "builder critic loop", "run the gauntlet".
---

# Gauntlet Loop

The user gives a goal; you give back ONE short prompt to paste into a fresh agent session, which grinds until the work beats a real reference. Run mode (they say run it, or paste a gauntlet prompt at you): read `references/running-the-loop.md`, nothing here. Rationale, bar shapes, other harnesses: `references/what-breaks.md`.

## Flow

1. **Read the goal**, or the `spec.md` or `intent.md` it names.
2. **Set the bar.** A supplied bar that passes the three tests below is the bar. If it fails one, say which and offer 2 or 3 replacements; none supplied, offer 2 or 3 candidates, one line each. When offering, ask once for a budget (invocations, hours), then stop and wait for the pick.
3. **Write the prompt**: one fenced `text` block starting with `/goal` (unfenced, a client can swallow that word); nothing after it but step 4.
4. **One flat line under it**: "Paste it as is with `/effort xhigh`, in auto mode or with the skill's allowlist. Its hooks enforce the rules only if checked in before the run (`install/claude_code.py <repo>`)."

Refuse by name: the name in bold first, why in a sentence, then the offer.

- **Manufactured bar.** A second build from the same spec inherits its blind spots; a held-out test at round zero finds what it would have found.
- **Suite alone.** Tests with no implementation beside them: a floor, never B.
- After either, offer **per-piece referents**, in those words: each main piece gets a named, fetchable real thing of its kind; one with no match anywhere is judged champion against challenger beside the nearest real referent. Never a suite, expected outputs or a second build as B.
- **Not a gauntlet.** No referent exists for any piece. Say what a loop would need; write no prompt.
- **Too small.** One piece, no measurable half, no taste dimension (a rename, a one-line fix): offer to just do it.

## The bar

A bar is **named** (a specific thing, not a category), **fetchable** (the lead can freeze a copy with the tools it has) and **comparable** (it and ours can sit side by side as A and B before a judge who does not know which is which). Prefer the hardest bar the agent can reach; between two, the less iconic. Out of reach, the run ends on its ceiling: offer that only when the user wants the pull. A measurable half (load time, pass rate, word count) goes in the bar paragraph as a floor: a preference gets averaged into the A/B; a floor gates it.

## Template

Fill the slots and change nothing else: no added sentence, no list of pieces, nothing on what the critic should look for.

```text
/goal Ours beats the bar blind: two fresh critics in a row, the second with A and B swapped on a different model, pick ours on every piece and on [WHOLE], or [N] invocations or [T] hours are spent. Until then, run a gauntlet loop:

[GOAL]

[BAR]

Split it into the coarsest pieces that can be judged alone; each gets a [MAKER] and a fresh critic every round. [FETCH] The critic gets ours and the bar as A and B in random order and hears the goal, never the bar's name, which is which, or who made either. It opens both, writes what it sees in each, picks one and names the biggest thing the loser lacks. No ties; a hedge is a loss. The [MAKER] closes that gap; repeat.

If the same gap comes back, split that piece, then change [MAKER]s, then fan out variants; never mark it done. When every piece wins, judge the whole the same way.

Update a progress page after every verdict: piece, round, winner, gap. End every turn with pieces confirmed and what is spent. Questions go there, not to me. Only I end this earlier.

Fan out subagents.
```

- `[WHOLE]`: "the assembled whole", or its noun. `[MAKER]`: builder, or writer. `[N]`, `[T]`: the budget named, else 150 and 24; no other budget clause.
- `[GOAL]`: what perfect looks like, never how to build it. From a spec file: "Build what <path> specifies." and nothing more. GOAL and BAR together: 70 words at most.
- `[BAR]`: one paragraph: "The bar is X."; how the lead freezes it; "judge against the copy, never a description."; one measurable half ("It must ..."; from a spec, instead: "Its acceptance criteria are floors."); then each "never" or "must not" sentence of the goal or spec, copied whole and unmerged, up to three. A code goal's paragraph always ends: "Write the required tests and a held-out set before any builder starts; no builder edits them." A prompt goal's: "Freeze the eval set with a held-out split first." Per-piece bars: name each referent, and the piece that runs champion against challenger.
- `[FETCH]`: who fetches, renders or runs, one sentence. Default: "Only you fetch the bar."

No architecture, file layout, round count, stack or unneeded tool names. 270 words at most; the template is about 200. Count before you answer.

## Examples

**Visual.** No budget.

- WHOLE: `the whole page` N: `150` T: `24` MAKER: `builder`
- GOAL: `Build a landing page for a running brand: athletic, green and dark, alive.`
- BAR: `The bar is Nike's current running campaign page. Freeze screenshots of it at desktop and mobile first; judge against the copy, never a description. It must score 90 on mobile Lighthouse.`
- FETCH: `Only you render the pages, both at the same viewport.`

**Writing.** A budget.

- WHOLE: `the whole explainer` N: `60` T: `8` MAKER: `writer`
- GOAL: `Write a 2000-word explainer on vector databases for smart readers who are not engineers.`
- BAR: `The bar is Julia Evans' explainers on jvns.ca. Freeze three of her posts first; judge against the copy, never a description of her style. It must stay within 2000 words.`
- FETCH: `Only you pick, per piece, a passage of hers doing the same job at the same length, byline stripped.`

**Bespoke.** Per-piece bars, one champion-challenger piece, a human gate, a budget.

- WHOLE: `the whole service` N: `80` T: `12` MAKER: `builder`
- GOAL: `Rebuild the claims-routing service in spec.md.`
- BAR: `The bars are per piece: the router against Drools, the audit log against Stripe's events API; reconciliation has no counterpart, so judge it champion against challenger beside Drools. Freeze each; judge against the copy, never a description. Never touch production data; migrations park for me. Write the required tests and a held-out set before any builder starts; no builder edits them.`
- FETCH: `Only you fetch the bars.`

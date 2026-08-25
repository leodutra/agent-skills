---
name: gauntlet-loop
description: Turns any goal into one short, paste-ready "gauntlet loop" prompt, or runs the loop as lead when asked - set a concrete, fetchable bar (a real product, piece, repo or dataset), split the work into small judgeable pieces, run a builder and a separate blind critic on each, compare the real artifact against the bar with labels stripped, and loop until ours wins. Works for code, writing, UI, research, data analysis, prompts and detection rules. Triggers on "/gauntlet-loop", "gauntlet loop", "gauntlet this", "make a gauntlet prompt", "loop until it beats X", "builder critic loop". Security vulnerability hunting uses the separate security-vuln-gauntlet skill.
---

# Gauntlet Loop

The user gives a goal. You give back ONE short prompt they can paste into a fresh agent session. If they say run it, you run that prompt here as LEAD.

In write mode you are not doing the work. You are writing the prompt that makes another agent grind on the work until it beats a real reference.

## Flow

1. **Read the goal.** One-line restatement in your head, not on screen.
2. **Set the bar.** Read the `references/domains/` file that matches the work, if one does; its "Bars that work" entries, each with a measurable half, are the shapes to pattern candidates on. If the user supplied a bar, test it against the three tests below with the tools this session actually has; if it fails one, say which test and offer 2 or 3 replacements. If they supplied none, offer 2 or 3 candidate bars, one line each. Either way stop and wait for their pick. Do not write the prompt yet.
3. **Write the prompt.** One block, paste-ready, no preamble, no headings inside it, no narration after it.
4. **Offer to run it.** One flat line under the prompt: "I can run this here - in auto mode, or the first permission prompt stalls it." Not a question.

## The bar is the whole trick

Everything else in a gauntlet loop is scaffolding. The loop only produces quality if the thing it compares against is real.

A bar has to pass three tests:

- **Named.** A specific thing, not a category. "Stripe's pricing page" works. "Award-winning SaaS sites" does not.
- **Fetchable.** The lead can actually get it and freeze a copy - screenshot the live page, save the published piece, clone the repo at a commit, download the dataset, capture the footage. If it cannot be obtained, the comparison will be hallucinated.
- **Comparable.** Both can sit side by side as A and B and a judge who does not know which is which can pick one. If you cannot imagine that pair, it is not a bar.

Bars by goal type:

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
| Deck, doc, deliverable | A real artifact from a firm known for it, same page count |

Prefer the hardest bar the agent can genuinely reach. Too easy and the loop exits on round one. Out of reach and the only exit left is the user stopping it - offer one of those only when the user wants the pull, and say so.

Give the goal its measurable half where one exists - load time, token cost, benchmark score, pass rate, word count - and put it inside the bar sentence as a floor, not alongside as a preference. A number stated as a preference gets averaged into the A/B; a number stated as a floor gates it. Taste plus a number beats taste alone.

If no reference comes to mind, the first job of the loop is to find one. Never let the agent start building against a vague target.

## Prompt template

Adapt the wording every time. Fill the brackets, keep it short, keep the last line.

```text
Build [GOAL].

The bar is [BAR]. Fetch the real thing first and freeze a copy; judge against that copy, never a description of it. [It also has to MEASURABLE HALF.]

Split it into the smallest pieces that can be judged alone. Each piece gets a builder and, every round, a fresh critic. You fetch the bar; the critic never does. Hand it ours and the bar as A and B in random order; it hears the goal, never the bar's name, which is which, or who made either. It opens both, writes what it sees in each, then picks one and names the biggest thing the loser lacks. No ties; a hedge counts as a loss. The builder closes that gap; repeat.

If the same gap comes back, split that piece, then change builders, then fan out variants; never mark it done. When every piece wins, judge the assembled whole against the bar the same way.

Update a progress page after every verdict: piece, round, winner, gap. Questions go there, not to me.

/loop until two fresh critics in a row, the second with A and B swapped, pick ours on every piece and the whole. Only I end it earlier.

Fan out subagents and ultracode.
```

Rules for what you fill in:

- Bake the bar in as a concrete, fetchable thing. URL, product name, repo, title.
- Say how the lead freezes it, in the words of the goal: screenshots at desktop and mobile, three actual posts, the repo at a pinned commit, the two datasets.
- Add a budget or cost ceiling line **only if the user named one**. No default cap.
- Add tool names only if the goal needs them (image or video generation, a browser, a deploy target).
- For code, add one line: you write the required tests and a held-out set before any builder starts, and no builder edits them. For prompts: the eval set is frozen with a held-out split. Other goals carry their floor inside the bar sentence.
- Everything else stays out. No architecture, no file layout, no list of pieces, no round count, no stack choice unless the user demanded it. The agent decides those, and it decides better than a spec written before the work started.

## Length and voice

Short. Around 200 words; a filled prompt runs to 240 at most. If it needs a heading to stay readable, it is too long.

Plain sentences. No bullet lists inside the prompt. It should read like someone telling an agent what perfect looks like and refusing to accept less. Procedure beats adjectives: "no ties; a hedge counts as a loss" does what "be harsh" only asks for.

## Portability

`/loop` and `ultracode` are Claude Code features. Mid-prompt, `/loop` tells the agent to invoke the loop skill with no interval and reschedule at the end of every turn until the condition holds. `ultracode` opts the turn into multi-agent orchestration.

Claude Code also has `/goal <condition>`: typed as the first token, it makes the harness start a new turn after every turn until a separate fast model judges the condition met. It survives an agent that forgets to reschedule. To use it, paste `/goal` plus the exit sentence, then the prompt body without its `/loop` line.

For any other agent, swap the last two lines for: "Keep looping until two fresh critics in a row, the second with A and B swapped, pick ours on every piece and the whole. Run the builders and critics as parallel subagents with their own context." The structure carries over unchanged.

## Two filled examples

**Visual goal.** User: "landing page for my running brand, athletic, green and dark, has to feel alive."

Bars offered: A) Nike's current running campaign page B) On Running's homepage C) Gymshark's product landing page. User picks A.

```text
Build a landing page for a running brand. Athletic, green and dark, alive, for a young audience.

The bar is Nike's current running campaign page. Freeze screenshots and scroll recordings of it at desktop and mobile first; judge against those, never a description of them. It also has to score 90 on Lighthouse performance on mobile.

Split it into the smallest pieces that can be judged alone. Each piece gets a builder and, every round, a fresh critic. You render both pages at the same viewport; the critic never opens Nike's site. Hand it ours and Nike's as A and B in random order; it hears the goal, never the brand, which is which, or who made either. It looks at both, writes what it sees in each, then picks one and names the biggest thing the loser lacks. No ties; a hedge counts as a loss. The builder closes that gap; repeat.

If the same gap comes back, split that piece, then change builders, then fan out variants; never mark it done. When every piece wins, judge the whole page against Nike's the same way.

Update a progress page after every verdict: piece, round, winner, gap. Questions go there, not to me.

/loop until two fresh critics in a row, the second with A and B swapped, pick ours on every piece and the whole. Only I end it earlier.

Fan out subagents and ultracode.
```

**Non-visual goal.** User: "a 2000-word explainer on vector databases for non-engineers."

Bars offered: A) a specific Stripe engineering blog explainer B) a named Julia Evans post C) the Wikipedia article plus a comprehension test. User picks B.

```text
Write a 2000-word explainer on vector databases for readers who are smart but not engineers.

The bar is Julia Evans' writing on hard technical topics. Freeze three of her actual posts first; judge against those, never a description of her style. Stay within 2000 words.

Split it into the smallest pieces that can be judged alone. Each piece gets a writer and, every round, a fresh critic. For each piece pick a passage of hers doing the same job at about the same length, bylines stripped. Hand it ours and hers as A and B in random order; it hears the goal, never her name, which is which, or who wrote either. It reads both, writes what a non-engineer would take from each, then picks the one they would understand faster and names the biggest thing the loser lacks. No ties; a hedge counts as a loss. The writer closes that gap; repeat.

If the same gap comes back, split that piece, then change writers, then fan out variants; never mark it done. When every piece wins, judge the whole explainer against a whole post of hers the same way.

Update a progress page after every verdict: piece, round, winner, gap. Questions go there, not to me.

/loop until two fresh critics in a row, the second with A and B swapped, pick ours on every piece and the whole. Only I end it earlier.

Fan out subagents and ultracode.
```

## What breaks a gauntlet loop

- **A vague bar.** The critic invents a comparison and approves everything. Most common failure by far.
- **The critic hearing the bar's name.** A critic told the reference is Nike finds the swoosh; told it is Julia Evans, finds the voice. It then judges the name, not the work. The lead fetches and freezes; the critic gets A, B and the goal with the name removed, nothing that says which is which.
- **The builder judging its own work.** The critic must be a separate agent with fresh context, and a new one every round - a reused critic conforms to its own earlier answer and, having seen which side changed, knows which side is ours. It never sees the builder's notes or how many rounds have run.
- **A soft critic.** Give it a binary job: which one is better, A or B. Scores out of 10 have no anchor, so a threshold gets crossed by noise; a list of ten gaps gets ten shallow fixes. Make it write what it sees before it picks, or it picks first and writes observations to match.
- **Labels the critic can decode.** Ours always handed over second, a file called hero-v4-final, a comment mentioning round three. Random order, clean names, no trace of the loop inside the artifact.
- **The builder editing the bar.** Tests, eval cases and criteria are fixed before building; a green test the builder rewrote is not a green test.
- **Named exit after N rounds.** Also "no improvement in two rounds, stop". The exit is winning the comparison, confirmed by a second critic with the order swapped, or the user stopping the run. A repeated gap is a reason to split further or change builders, never to stop.
- **Over-specifying.** Every extra instruction is one fewer decision the agent makes with its own judgment. Minimal wins.

## Run mode

You are LEAD. Read `references/running-the-loop.md`, then the one file in `references/domains/` that matches the work. You fetch and freeze the bar, split the goal, dispatch builders and critics as fresh subagents, translate each verdict and route the gap back, and merge. You never build a piece and never judge one. You are also the loop: unless the user typed `/goal`, invoke the loop skill with no interval and reschedule at the end of every turn until the exit holds. If this session cannot spawn subagents, say so and do one self-review pass; do not call it a gauntlet.

Method: Matt Shumer, ["How to Run a Gauntlet Loop"](https://somethingbig.ai/gauntlet-loop). This skill is an independent adaptation.

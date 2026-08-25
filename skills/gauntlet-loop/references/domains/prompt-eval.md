# Domain: Prompt Eval - prompts that beat baseline on evals

## Bars that work

- The current production prompt, pinned at a commit. The LEAD saves prompt text, model id, temperature and harness config under reference/baseline/, commit hash in the manifest. Number: pass rate on the frozen eval set.
- A public benchmark slice - BFCL for tool descriptions, tau-bench for agents, GSM8K for reasoning. The LEAD samples 40 cases into reference/visible.jsonl and reference/heldout.jsonl, dataset version in the manifest. Number: the published score.
- Anthropic's published system prompts. The LEAD saves the text, URL and date. Number: token count, the ceiling for ours.

Every case has a checkable expectation - exact match, contains, schema-valid, or a judge model with a fixed rubric whose prompt and model id are in the manifest - and comes from real inputs, hard ones included, never from cases written to flatter the prompt.

## Floor

Command floors, LEAD runs on ours before any CRITIC: the visible set passes with zero schema-invalid outputs; every case the baseline passed still passes; tokens and p95 latency under the ceiling; `grep -F -f eval/inputs.txt` over the prompt returns no hits. HELD-OUT set: reference/heldout.jsonl, a quarter of the cases the LEAD keeps and never shows to the BUILDER.
Reading floors, CRITIC runs on both sides: each rule addresses a class of inputs, not one case; few-shot examples are not eval cases; the described output format matches what the harness checks.

## What the critic physically does

Runs the harness on A and B, one config, three runs per case, visible and held-out. Pastes per side: pass rate per run, schema-invalid count, mean tokens, per-case diff of which cases flip each way. The run-to-run spread is the noise band; a gap inside it is not a gap. Greps both prompts for eval inputs; quotes the line behind each flipped case. Evidence: pasted harness output, diff path, quoted lines, numbers.
Pair preparation: the LEAD saves both prompts as A.txt and B.txt, names, commit ids and comments stripped, neither cut (the token ceiling is a command floor), then hands over A.txt, B.txt, the critic's copy of the bar sentence and the inspection steps; one config, one seed list and the eval files sit in eval/ beside them.

## How the LEAD splits this work

Pieces: system prompt core, each tool description, few-shot block, output format section. The eval set is never a piece. Pieces sharing one prompt file score against one eval set: serialise them; tool descriptions in separate files run in parallel worktrees. Assembled-whole gate: full prompt against baseline on visible plus held-out, three runs, and the token ceiling on the whole file - pieces that each fit can sum over it.

## A verdict, as evidence looks

```text
WINNER: A
GAP: B lacks the held-out generalisation A has - held-out 6/10 vs 9/10, stable across 3 runs; opened B.txt and eval/visible.jsonl: B's two few-shot invoices are visible cases 07 and 12 copied verbatim, and the three held-out cases B loses are multi-currency layouts those examples never show
FLOOR: few-shot examples are not eval cases - A: pass (grep -F -f eval/inputs.txt A.txt: 0 hits) / B: fail (2 hits, B.txt lines 31-58 match cases 07 and 12)
FLOOR: described output format matches what the harness checks - A: pass (A.txt line 12 names the four JSON keys the schema requires) / B: pass (B.txt line 9, same four keys)
EVIDENCE:
- A: `promptfoo eval -c eval/config.yaml --prompts A.txt` x3 - visible 27/30, 28/30, 27/30; held-out 9/10, 9/10, 8/10; schema-invalid 0/40; mean 690 tokens
- B: same command with B.txt - visible 28/30, 28/30, 27/30; held-out 6/10, 6/10, 7/10; schema-invalid 0/40; mean 740 tokens
- runs/diff.jsonl: visible 03 and 19 flip between runs on both sides; B breaks held-out 33, 36, 38, all invoices carrying two currencies
- Noise band: visible moves by 1 case per side across runs; the 3-case held-out gap sits outside it
- B.txt line 31 quotes "Invoice #4471 ... Total EUR 1,240.00", the input of visible case 07
```

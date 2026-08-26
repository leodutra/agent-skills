# Domain: Writing - prose as tight as its model

## Bars that work

- Paul Graham, "Write Like You Talk" (paulgraham.com/talk.html) for essays and internal posts. LEAD saves the text under reference/ with URL and date. Measurable half: median sentence length (the essay runs near 15 words) and a word budget.
- George Orwell, "Politics and the English Language" (orwellfoundation.com) for argument and opinion. Saved as text. Measurable half: zero hits on a banned-phrase list built from his dead metaphors plus current AI-ese.
- One Stripe quickstart (docs.stripe.com/payments/quickstart) for technical writing. LEAD saves rendered text and a 1280px screenshot, dated. Measurable half: words per step and a readability grade from a script.

## Floor

Command floors, LEAD runs on ours before any CRITIC: `wc -w` within budget; banned-phrase grep returns zero; spellcheck clean; every number in the draft appears in sources.txt (a script extracts digits and greps). The banned-phrase list and a claim list (facts the piece must state correctly) are HELD-OUT - the BUILDER never sees them.

Reading floors, CRITIC runs on both sides: each cited source says what the sentence claims; no number without a source; the text addresses the named reader.

## What the critic physically does

It reads both excerpts in full. It strikes every word that can go without changing meaning and counts struck over total per side. It names the line where the main point lands. It opens every source named in either excerpt and quotes the supporting line, or writes "not found". Evidence is quoted lines and counts - never "feels tighter".

Pair preparation: the LEAD takes the same section from each (opening, one step, close), picks a reference passage doing the same job at about the same length - never cuts either side - strips titles, author names, URLs, dates and filenames, pastes both as plain text under coin-flipped labels, and puts both sides' sources in one sources.txt.

## How the LEAD splits this work

Pieces: the opening, each section or argument, the close; for docs, each step or page. Pieces share terminology and sources, so the LEAD keeps a terms file all BUILDERS read. The close depends on the body, so it is built last. Assembled-whole gate: SMOOTHER fixes transitions and words repeated across seams, floors re-run on the whole text, a fresh CRITIC judges the whole against the whole reference.

## A verdict, as evidence looks

```text
EVIDENCE:
- A: 81 words, 5 sentences, median 15 words; delete-the-word strikes 3 of 81 ("actually", "very", "in fact")
- B: 86 words, 3 sentences, median 29 words; delete-the-word strikes 27 of 86, including "in today's rapidly evolving landscape", "in order to", "the various issues relating to"
- A: line 1 names the reader's problem: "Our checkout times out under Friday traffic"
- B: line 1 is generic: "Choosing an infrastructure solution is an important consideration"
- B: "load" appears four times with no noun attached; the reader cannot tell load of what
WINNER: A
GAP: B buries its point - opened both excerpts; A states the decision in line 1, B reaches it in the last clause of line 4 after three sentences of setup.
FLOOR: source check - A: pass ("p99 rose to 4.1 s" matches sources.txt entry 2) / B: fail ("thousands of requests per second" has no entry; grep "requests\|rps" sources.txt returns 0 hits)
```

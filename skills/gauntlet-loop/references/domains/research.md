# Domain: Research - findings that survive a hostile fact-check

## Bars that work

- A Cochrane systematic review on the nearest question. The LEAD freezes the PDF and its included-studies table under reference/; manifest: URL, date. Measurable half: every included source has a date and design label; contrary findings sit in the results.
- A Wikipedia Featured Article on an adjacent subject, saved at its permalink (oldid) with references. Measurable half: citations per paragraph, and the share that open and contain the claim - 100 percent.
- An Our World in Data topic page, saved as text with its sources table. Measurable half: every number has a source and date; load-bearing sources within 24 months.

## Floor

Command floors (LEAD runs before any CRITIC):

- Link script: every cited URL returns 200 or has an archived copy.
- Grep for undated citations returns zero.
- Length within the limit.
- HELD-OUT: contrary sources the LEAD found before spawning BUILDERS; grep of the reference list must hit one.

Reading floors (CRITIC runs on both sides):

- Each citation says what is claimed.
- Each load-bearing claim rests on a primary or independent source; a vendor's statement about its own product is not evidence for it.
- Each claim table row is supported by its source.
- Inference is labeled.

## What the critic physically does

- Opens every citation and quotes the supporting passage with URL and paragraph; no passage found is a fail.
- Runs an independent counter-search: "evidence against {claim}", the strongest published objection, the failed trend; records query and dated results.
- Checks each load-bearing source's date against how the text presents it.
- Traces circular sourcing: three articles citing one press release count as one.
- Separates source claim from author inference.

Evidence: quoted passage with URL, dated search result, a count, pasted grep output.

Pair preparation: the LEAD takes the reference section on the same question, matched to about the same length by choice of section, never by cutting, strips titles, bylines, the document date, filenames and draft markers, renumbers citations from [1] in both, saves plain text A and B.

## How the LEAD splits this work

One piece per question: evidence for, known limitations, cost figures, the counter-case. Reference list and claim table are shared state - each BUILDER gets its own citation range; merges serialise. Pieces arguing opposite sides of one question share sources; serialise. Assembled-whole gate: SMOOTHER merges reference lists and aligns inference labels, floors re-run on the merge, a fresh CRITIC reads the whole brief against the whole reference for cross-section contradictions and one-sidedness.

## A verdict, as evidence looks

```text
EVIDENCE:
- A: [4] https://wiki.example.org/replication paragraph 3 reads "commits are replayed in the order they were committed on the primary"; matches A line 12
- B: [3] https://cloud.example.com/pricing opened 2026-08-25; the figure "USD 0.012 per GB" appears nowhere on the page (grep -c "0.012" page.html -> 0)
- B: [5] byline dated 2023-11-02, concludes "early, promising"; B line 9 presents it as current with no date
- B: [1], [2] and [6] each cite the same vendor launch post of 2024-03-14 - one source counted as three
- A: every source dated inline; oldest load-bearing source 2025-02
WINNER: A
GAP: B lacks the counter-case - its "known limitations" section names no contrary source; a search for "logical replication failover data loss" returns two 2025 practitioner write-ups on the ordering gap, neither cited in B; A cites both ([7], [8]) and addresses them.
FLOOR: every citation opens and contains the claim - A: pass, 11/11 / B: fail, 9/11
FLOOR: inference is labeled - A: pass (lines 14 and 20 carry "inference:") / B: fail (line 9 states [5]'s "early, promising" as settled)
```

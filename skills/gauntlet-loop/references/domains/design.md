# Domain: Design - pixels judged against a shipped product

## Bars that work

- Stripe's pricing page or Linear's settings screen. Frozen as PNGs at 1440x900 and 390x844 plus hover, focus and error states; manifest: URL, date, viewport, scale factor.
- Radix Themes at a pinned commit. Frozen as the commit hash, rendered by the LEAD at the same viewports.
- Games and 3D: real footage or screenshots from a named shipped title - Hades II, Alan Wake 2 - at the same resolution as ours. Frozen as PNG frames with source and timestamp.

Measurable half: contrast 4.5:1 or better (3:1 for large text), Lighthouse accessibility at or above the reference, no horizontal overflow at 390 px, frame time under 16.6 ms.

## Floor

Command floors, LEAD runs on ours first: axe-core contrast on every text pair, 4.5:1 minimum and 3:1 for large text; no horizontal overflow at 390 and 1440; Lighthouse accessibility at or above the reference; for games, p95 frame time under budget and capture at the reference's resolution.

Reading floors, CRITIC on both sides: primary action found in one glance; hover, focus, empty, loading and error states differ from default; no clipped text.

HELD-OUT: viewports and content the BUILDER never sees - 320 px, a 40-character label, an empty list.

## What the critic physically does

Opens a.png and b.png at 100 percent, then the state variants. Measures: samples hex pairs and computes the ratio, measures gutters and row heights in px, lays a ruler on baselines. For motion, steps through a.webm and b.webm frame by frame: what moves on scroll and hover, when, and how far. For games, steps through frames comparing edge softness, shadow direction and HUD scale. Evidence is a path, a px number, a hex pair, a ratio.

Pair preparation: the LEAD renders both sides with one Playwright script - same viewport and scale factor, same crop, browser chrome removed, filenames a and b, labels coin-flipped for every first CRITIC and swapped for the confirming one; for motion, the same script records a scripted scroll and hover on each side to a.webm and b.webm of equal length. For games, same resolution, matching framing and lighting hour, same frame count. BUILDER screenshots never reach a CRITIC.

## How the LEAD splits this work

Pieces are components or screens: a card, a nav bar, an empty state; for games a material, a lighting pass, a HUD overlay. Colour, spacing and type tokens are shared state: their own piece, judged first, then the rest build in parallel worktrees against them. The assembled-whole gate compares a full-page screenshot with the full reference page at each viewport; for games, a ten-second clip against the reference clip.

## A verdict, as evidence looks

```text
EVIDENCE:
- A: a-1440.png - gutters measure 16 and 24 px; feature rows 26 px tall on 16 px text
- A: a-390.png - card stacks to one column, button full width, no horizontal overflow
- B: b-1440.png - feature rows 19 px tall on 16 px text (line-height about 1.2); rows touch
- B: b-390.png - 12 px gutter against 16 px elsewhere; check icons sit 2 px above the text baseline
- B: b-1440.png - button fill #E5E7EB matches the card border tone; the button does not separate from the card
WINNER: A
GAP: B has no hierarchy - opened b-1440.png; price and plan name are both 16 px regular, so the eye has no first stop. In a-1440.png the price is 40 px bold and lands first.
FLOOR: primary action found in one glance - A: pass, one saturated button / B: fail, "Choose Pro" and "Compare plans" carry the same weight
FLOOR: focus state visible - A: pass, 2 px ring in a-1440-focus.png / B: fail, b-1440-focus.png is pixel-identical to b-1440.png
```

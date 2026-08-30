# good-readme — what this is and why it's here

`SKILL.md` is what the agent loads; `references/` is what it reads while working. This file is for humans.

## Origin

Vendored from [adewale/good-readme](https://github.com/adewale/good-readme) (MIT, author retained in the skill's `metadata`). Kept as-is rather than rewritten: it is a well-shaped skill already, and a fork that drifts from upstream is a fork that has to be maintained. Local edits should stay small enough to describe in one line here.

Local changes so far:

- `cloudflare.md` added to the frontmatter `references:` list — the skill body already linked it, so the manifest was simply incomplete.

## Why it earns a place in this repo

The other skills here are domain methods (Rust, architecture, macro analysis) or loops (gauntlet). This one covers a task every repo hits and nobody does well by default: a README that is accurate rather than plausible. Its **source-grounded API drift protocol** is the part that matters — the failure mode of an LLM writing a README is a confident example importing a function that no longer exists, and the protocol makes verification against manifests and exports a required step, not a nicety.

## Deployment

Domain skill, so it deploys per repo, never globally ([D48](../../config/DECISIONS.md#d48)):

```sh
cd /path/to/project && stack-init skills good-readme
```

Global would charge its description to every session in every project, including the ones that will never ask for a README. Its trigger is narrow by design — the description says "only when the user explicitly asks" — which makes it a poor fit for standing context and a good fit for an explicit per-repo opt-in.

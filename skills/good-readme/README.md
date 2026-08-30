# good-readme — what this is and why it's here

`SKILL.md` is what the agent loads; `references/` is what it reads while working. This file is for humans.

## Origin

Vendored from [adewale/good-readme](https://github.com/adewale/good-readme) (MIT, author retained in the skill's `metadata`). Kept as-is rather than rewritten: it is a well-shaped skill already, and a fork that drifts from upstream is a fork that has to be maintained. Local edits should stay small enough to describe in one line here.

Local changes so far:

- `cloudflare.md` added to the frontmatter `references:` list — the skill body already linked it, so the manifest was simply incomplete.

## Why it earns a place in this repo

The other skills here are domain methods (Rust, architecture, macro analysis) or loops (gauntlet). This one covers a task every repo hits and nobody does well by default: a README that is accurate rather than plausible. Its **source-grounded API drift protocol** is the part that matters — the failure mode of an LLM writing a README is a confident example importing a function that no longer exists, and the protocol makes verification against manifests and exports a required step, not a nicety.

## Deployment

Global, deployed by `config/stack-init.sh global` alongside gauntlet-loop, opensrc and worktrunk ([D58](../../config/DECISIONS.md#d58)):

```sh
config/stack-init.sh global     # mirrors this directory to ~/.claude/skills/good-readme
```

It is the first global skill fronting no installed tool. The reason it is not a per-repo domain skill ([D48](../../config/DECISIONS.md#d48)): every repo has a README, in every language, so none of the per-repo triggers domain skills rely on apply — deploying it per checkout would be a global install with extra steps. The cost is its description, ~85 tokens in every session, held down by a deliberately narrow trigger that names five exclusions.

The deployed copy is managed: overwritten on every `stack-init global` run, stale files removed. Edit here, not there.

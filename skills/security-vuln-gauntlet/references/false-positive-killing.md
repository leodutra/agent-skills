# False-Positive Killing — the VALIDATOR's technique

The validator's job: **treat every candidate as a false positive** until it clears three gates in order — **Reachability → Taint → PoC**. No PoC, no pass.

---

## Gate 1 — Reachability

*Can attacker-controlled input actually reach the suspicious point in a real execution path?*

- Trace the call chain from a **real entry point** (route handler, message consumer, CLI argument, deserializer) to the suspect function or line. No call path → **false positive** (dead code, unreachable).
- Check for **blocking conditions upstream**: is the feature flag off? is the route registered? does a guard or middleware stop it? does this code only run in debug mode?
- For binaries: is the function in a control-flow path reachable from input, or an unused symbol?
- For cloud/IaC: is the resource or permission actually attached and **effective** (not overridden by a deny at a higher level)?

Gate 1 output: the **specific path to reach it**, or a statement that it is unreachable.

## Gate 2 — Taint

*Does attacker-controlled data reach the dangerous sink intact?*

- Identify the **source** (where the data enters) and the **sink** (where it becomes dangerous: `exec`, SQL, template, deserializer, file path, redirect, HTTP client).
- Follow the variable through assignments and function calls. Record **every sanitizer or validator** on the path.
- For each sanitizer ask whether it is actually sufficient **for this sink**: HTML-escaping does not save SQL; escaping in the wrong context does not save XSS; length validation does not stop injection; deny-lists are routinely bypassed.
- Watch for **encoding/normalization mismatches**, **second-order** flows (stored then used later), and **context switches** across layers.

Gate 2 output: the source → sink chain and why the sanitizer (if any) is insufficient — or a statement that it is properly blocked.

## Gate 3 — PoC (mandatory)

*Can you build non-destructive evidence of exploitation under the target's real conditions?*

- The PoC must be **reproducible** and have the **least impact** that still proves the point (see `safety-and-scope.md`).
- Record the **reproduction steps**, the **payload**, the **observed result** (objective evidence: response, return value, observable side effect), and the **impact**.
- If no PoC can be built after reasonable effort → **UNCONFIRMED**. State exactly what is missing (needs role X, version Y, configuration Z) so it can be reassessed later.

### Proving impact without causing harm

- **Injection (SQLi / command):** harmless observable payloads — time-based (`SLEEP`) or constant-returning (`SELECT 1`), read-only commands like `id`.
- **XSS:** prove execution with a harmless signal (a DOM change, `console.log`) rather than stealing a real cookie.
- **IDOR/BOLA:** access a **canary or test record** belonging to another pentest-provided account — never real customer data.
- **SSRF:** point at a **collaborator or canary you control** and show the request went out — do not sweep the internal network.
- **Memory corruption:** show a **reproducible crash** plus an analysis of controllability (PC control, write-what-where) in the lab. Full weaponization is not required.

## Verdict table

| Verdict | Condition |
| --------- | ----------- |
| **CONFIRMED** | Clears all three gates, with a non-destructive PoC and objective evidence |
| **UNCONFIRMED** | Clears gates 1–2 but no PoC could be built, or exploitation preconditions are missing |
| **FALSE POSITIVE** | Fails gate 1 (unreachable) or gate 2 (adequately sanitized) |

## Bias controls for the validator

- The validator **does not read the hunter's reasoning** — only the claim plus a pointer to the real artifact.
- Try **at least two ways to refute** the candidate before accepting it.
- Prefer **objective evidence** (output, side effects) over plausible-sounding argument.
- Record both the reasons for confirming and the hypotheses that were ruled out, so the run is auditable.

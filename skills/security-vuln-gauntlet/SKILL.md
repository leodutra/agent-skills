---
name: security-vuln-gauntlet
description: >-
  Apply the Gauntlet Loop to security vulnerability hunting — a hunter (builder)
  proposes candidate vulnerabilities and a blind validator (critic) inspects the
  real artifact and MUST build a working non-destructive PoC before anything is
  confirmed. The bar is exploitability + CWE mapping + real vulnerability-class
  precedent; false positives are killed by reachability → taint → PoC gates.
  Use ONLY on assets you own or are authorized in writing to test; every PoC must
  be non-destructive. Covers web, API, binary/memory, and cloud/IaC. Trigger
  keywords: "find vulnerabilities", "security code review", "pentest", "kill
  false positives", "IDOR", "BOLA", "SQL injection", "SSRF", "path traversal",
  "exploit PoC", "CWE", "OWASP Top 10", "triage this scan". Use together with the
  core gauntlet-loop skill.
---

# Security Vuln Gauntlet

The Gauntlet Loop applied to **finding real vulnerabilities**: a **HUNTER** (builder) proposes candidates and a blind **VALIDATOR** (critic) demands a **working PoC** before anything counts. The bar is **exploitability + CWE mapping + real precedent**. Covers **web, API, binary/memory, and cloud/IaC**.

> Kept separate from the core `gauntlet-loop` skill because its **triggers and safety requirements differ**: written authorization (ROE) is mandatory and every PoC must be non-destructive. The method itself is the core loop.

## SCOPE AND AUTHORIZATION — mandatory

Use only on assets you **own or are authorized in writing to test**. If there is no ROE, **STOP** and ask the user for one. Read `references/safety-and-scope.md` first.

Every PoC must be **non-destructive**: no data destruction, no lateral movement, no exfiltration, no denial of service. This is a defensive/AppSec tool. Unauthorized access is a crime in most jurisdictions (CFAA in the US, the Computer Misuse Act in the UK, equivalent computer-crime statutes elsewhere) and the operator carries that responsibility.

## When to use it

Reviewing or pentesting an authorized codebase, service, binary, or cloud configuration — or triaging an existing scan down to what is actually exploitable.

## Role mapping

| Core role | Security role |
|-----------|---------------|
| LEAD | Split by trust boundary / entry point / high-value asset; maintain the coverage map |
| BUILDER | **HUNTER** (clean context): propose candidates with an exploitation hypothesis (source → sink) |
| CRITIC | **VALIDATOR** (blind): inspect the real artifact, check reachability and taint, **build the PoC**. No PoC, no pass |

## The bar (three axes, all required)

1. **Exploitability:** a **working PoC or equivalent evidence** under the target's actual conditions — not "theoretically possible".
2. **CWE mapping** (prefer the CWE Top 25): map to a meaningful weakness class, e.g. CWE-89, CWE-79, CWE-787, CWE-416, CWE-918, CWE-862, CWE-22, CWE-502.
3. **Real precedent (never fabricated):** point to the real-world vulnerability class or a genuine CVE to calibrate severity and credibility. If you cannot find a precedent, write "novel/uncertain" — **do not invent a CVE ID**.

## The loop

1. **Scope, bar, and budget.** Read the ROE first.
2. **LEAD split:** map trust boundaries, entry points (attacker-controlled input), dangerous sinks, and high-value assets (auth, money, PII, RCE surface). Divide into hunting units.
3. **HUNTER × N (parallel, clean contexts):** each returns `{location, source, sink, taint path, preconditions, confidence, PoC idea}`.
4. **VALIDATOR (blind):** for every candidate, run **Reachability → Taint → PoC** in order. PASS only with evidence. Techniques: `references/false-positive-killing.md`.
5. **Score against the bar:** CWE, CVSS, precedent. Drop anything below the bar.
6. **Repeat:** feed FAILs back to the hunters; chase chains and variants; run longer; record coverage gaps.
7. **Report:** confirmed findings (with PoC) kept strictly separate from unconfirmed ones, each with remediation.

## Source → sink checklists

Web, API, binary/memory, and cloud/IaC are covered in `references/checklists-by-domain.md`, with OWASP Top 10 / API Top 10 / ASVS / CWE / CIS mappings, sanitizer-bypass notes, and the per-domain bar signals.

## Worked examples

- Web (path traversal, with a PoC plus a killed false positive): `references/example-web-run.md`.
- IDOR/API, binary crash triage, and cloud IAM privilege escalation: inside `references/checklists-by-domain.md`.
- An end-to-end run across several hunting units: `../../examples/example-security-run.md`.

## Output

For every **CONFIRMED** finding: title, **CWE ID**, severity (with a suggested CVSS vector), the **non-destructive PoC or evidence**, the source → sink path, preconditions, and remediation. Findings without a PoC are reported as **UNCONFIRMED** in a separate section. Include the coverage map and a reference to the ROE.

## References
- `references/safety-and-scope.md` — ROE template, PoC constraints, logging.
- `references/false-positive-killing.md` — the reachability → taint → PoC gates.
- `references/checklists-by-domain.md` — web / API / binary / cloud (source → sink + bar + OWASP/CWE/CIS).
- `references/example-web-run.md` — one loop round with a PoC.

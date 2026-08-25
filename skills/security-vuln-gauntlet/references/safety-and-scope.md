# Safety and Scope — Rules of Engagement (ROE)

This is a **defensive / AppSec** tool. Use it only on assets you **own or are authorized in writing to test**. Unauthorized access or exploitation is a crime in most jurisdictions — the CFAA in the United States, the Computer Misuse Act in the United Kingdom, cybersecurity and computer-crime statutes elsewhere. The operator carries full responsibility.

## Non-negotiable rules for every PoC

1. **Non-destructive:** never delete, modify, encrypt, or corrupt data or services.
2. **No lateral movement:** never use a foothold to reach systems or accounts beyond the specific thing being demonstrated.
3. **No exfiltration:** never pull real data (PII, secrets, customer records) out. If you must prove readability, use a seeded canary record or extract a minimal indicator (a length, a hash) rather than the content.
4. **No denial of service:** never degrade or take down a service. Fuzzing and load testing belong in an approved lab or staging environment only.
5. **Least impact:** choose the smallest PoC that still proves the point — `id` rather than `whoami; rm`, `SELECT 1` rather than dumping a real table.
6. **Log everything and fail safe:** record every action (timestamp, target, payload, result). If a step risks real harm, **stop**, document it, and report it instead of executing it.

## Pre-flight checklist

- [ ] **Written authorization** covering exactly these targets and this time window.
- [ ] **Scope** is explicit: which domains, hosts, IPs, repos, and accounts are IN and which are OUT.
- [ ] Environment identified: production or staging? If production, what technical limits apply?
- [ ] Data: is real data or PII present? What is the handling rule if you touch it accidentally?
- [ ] Emergency contact for unintended disruption.
- [ ] Storage and destruction policy for sensitive findings and PoC material.

## ROE template

```
RULES OF ENGAGEMENT — VULN GAUNTLET
Effective: __________   Expires: __________
Authorizing party (asset owner): _______________________  Signed: __________
Testing party:                   _______________________  Signed: __________

IN SCOPE:
  - Hosts / domains / IPs:
  - Repos / artifacts:
  - Cloud accounts / subscriptions / projects:
  - Test accounts provided:
OUT OF SCOPE:
  - (e.g. third-party systems, real payments, real customer data, DoS)

ENVIRONMENT: [ ] Staging/Lab   [ ] Production (limits: __________)
PROHIBITED TECHNIQUES: [ ] DoS/stress outside the lab  [ ] real-data exfiltration
                       [ ] lateral movement  [ ] production config changes
                       [ ] social engineering of staff
TIME WINDOW: __________ (permitted hours/days)
INCIDENT HANDLING: emergency contact ____________  stop procedure: __________
RESULT STORAGE: location ________  encrypted? ____  destruction date: ______
```

## Handling sensitive data in findings

- Never commit real secrets or logs to the repository (`.gitignore` blocks `secrets/`, `*.key`, `.env` and similar, but check anyway).
- Redact tokens and PII in write-ups; keep only what is needed to reproduce inside the approved environment.
- Keep PoC binaries and crash artifacts in ignored directories (`crash-*/`, `poc/**/*.bin`).

## If you go out of scope by accident

Stop immediately. Do not continue exploiting. Record what was touched and when, and notify the authorizing party through the incident procedure in the ROE.

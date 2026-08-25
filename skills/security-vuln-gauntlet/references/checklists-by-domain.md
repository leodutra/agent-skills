# Checklists by domain — Web · API · Binary/Memory · Cloud/IaC

For the HUNTER while digging and the VALIDATOR while verifying. Each entry gives a concrete **source → sink** direction, the **bar signal**, and the shape of a **non-destructive PoC**. Always follow `safety-and-scope.md`.

---

## 1) WEB (mapped to OWASP Top 10 2021 / ASVS)

**Sources:** query and path parameters, body (JSON/form/multipart), headers (Host, Referer, X-Forwarded-*, Cookie), uploads, WebSocket messages, and stored-then-used data (second order).

| Vulnerability class | Typical sink | CWE | Non-destructive PoC |
|---|---|---|---|
| SQL Injection | string-concatenated SQL/ORM, `$where`, dynamic ORDER BY | CWE-89 | time-based `SLEEP`, `SELECT 1`; never read real tables |
| XSS (reflected/stored/DOM) | `innerHTML`, unescaped templates, `dangerouslySetInnerHTML` | CWE-79 | payload that triggers `console.log` or a DOM change, not cookie theft |
| OS Command Injection | `exec/system/child_process` | CWE-78 | read-only command such as `id` |
| SSRF | server-side HTTP fetch, importers, PDF/image loaders | CWE-918 | point at a canary/collaborator you control; show the request left |
| Path Traversal / LFI | `open/read/sendFile`, static handlers | CWE-22 | read a harmless marker file inside scope |
| Insecure Deserialization | `pickle` / `unserialize` / `ObjectInputStream` / `yaml.load` | CWE-502 | harmless gadget creating a marker file in the lab |
| SSTI | template engine receiving input | CWE-94 | harmless arithmetic (`{{7*7}}` → 49) |
| Open Redirect | redirect target taken from input | CWE-601 | redirect to a canary domain |
| CSRF | state-changing action with no token / SameSite | CWE-352 | cross-origin form against a test account |
| Auth/Session | JWT `alg:none` or weak signing, session not rotated | CWE-287/384/613 | forge a valid token / replay an old session |
| Access Control / IDOR | object accessed by id with no ownership check | CWE-862/639 | see the API section below |

### OWASP Top 10 (2021) → where to look

| OWASP | Topic | Where to hunt | Typical CWE |
|-------|-------|---------------|-------------|
| A01 | Broken Access Control | id-addressed endpoints, admin routes, IDOR/BOLA, forced browsing | CWE-862, CWE-639, CWE-284 |
| A02 | Cryptographic Failures | hardcoded secrets, weak algorithms, TLS disabled, guessable tokens | CWE-798, CWE-327, CWE-311 |
| A03 | Injection | SQL/NoSQL/OS command/LDAP/SSTI | CWE-89, CWE-78, CWE-79, CWE-94 |
| A04 | Insecure Design | missing rate limits, abusable business flows | (context dependent) |
| A05 | Security Misconfiguration | debug enabled, missing headers, loose CORS, default credentials | CWE-16, CWE-942 |
| A06 | Vulnerable & Outdated Components | dependencies with known CVEs | CWE-1035, CWE-1104 |
| A07 | Identification & Auth Failures | brute force, session fixation, JWT handling | CWE-287, CWE-384, CWE-613 |
| A08 | Software & Data Integrity Failures | deserialization, CI/CD, unsigned updates | CWE-502, CWE-345 |
| A09 | Logging & Monitoring Failures | security events not logged | CWE-778 |
| A10 | SSRF | HTTP client taking its URL from input | CWE-918 |

### Sanitizer bypasses the validator must check

- **SQLi (CWE-89):** quote-escaping that forgets numeric context; keyword deny-lists; ORDER BY cannot be parameterized → needs a column allow-list.
- **XSS (CWE-79):** escaping for the wrong context (HTML vs attribute vs JS vs URL); sanitizers that only strip `<script>`. Harmless PoC: `console.log` or a DOM change.
- **SSRF (CWE-918):** check bypasses via `127.0.0.1` alternates, IPv6, DNS rebinding, redirects, decimal/octal IPs. Correct fix: host/scheme allow-list, block internal and metadata ranges, validate **after** DNS resolution.
- **Path Traversal (CWE-22):** `../`, encoded `%2e%2e%2f`, absolute paths, null bytes (older languages), Windows `..\`. PoC: read a harmless in-scope marker file, never real secrets.
- **Deserialization (CWE-502):** `pickle.loads`, Java `ObjectInputStream`, PHP `unserialize`, non-safe `yaml.load`. PoC: a harmless gadget writing a marker file in the lab.
- **Auth/Session (CWE-287/384/613):** JWT `alg:none`, weak or unverified signatures, sessions not rotated after login, tokens that never expire. PoC: forge a valid token or replay an old session.

**ASVS depth:** L1 (basic), L2 (applications holding sensitive data — the recommended default), L3 (critical systems). Cite the relevant ASVS sections in the report (e.g. V2 Authentication, V3 Session, V4 Access Control, V5 Validation/Encoding).

**Web bar:** a reproducible HTTP PoC (request/response) + OWASP and CWE mapping + a real precedent. Impact ordering: RCE > SQLi/deserialization > auth bypass/IDOR > SSRF > stored XSS > reflected XSS/CSRF.

> Full web example (path traversal plus a killed false positive): `example-web-run.md`.

---

## 2) API / MICROSERVICES (mapped to OWASP API Security Top 10 2023)

**Sources:** path ids, JSON body (including extra fields), headers (Authorization, X-User-Id, tenant), GraphQL variables, gRPC messages.

| Vulnerability class | Hot spot | OWASP API / CWE | Non-destructive PoC |
|---|---|---|---|
| BOLA / IDOR | resource accessed by id **without an ownership check** | API1 / CWE-639, CWE-862 | **two test accounts**: A reads or modifies B's canary record |
| BFLA | admin/privileged endpoint with no role check | API5 / CWE-862 | a normal user invokes an admin function on a test resource |
| Mass Assignment | whole body bound to the model (`role`, `isAdmin`, `balance`) | API6 / CWE-915 | send an extra field, observe privilege change on a test account |
| Excessive Data Exposure | more fields returned than needed (client filters) | API3 / CWE-213 | show the response contains sensitive fields it should not |
| Unrestricted Resource Consumption | no rate limit or quota | API4 | send just enough requests to demonstrate it, in a lab — never DoS |
| Internal SSRF | service calls a service using an input URL | CWE-918 | an internal canary you control |
| Broken service-to-service auth | wrong JWT scope/audience, service does not authenticate | API2 / CWE-287 | a self-issued token is accepted |
| GraphQL | introspection enabled, deeply nested queries, missing field authz | (context dependent) | a nesting depth just sufficient to demonstrate it, without saturating the service |

**LEAD technique:** build a **{role} × {endpoint/action} matrix**; hunters compare responses between two accounts.

### Quick example — BOLA/IDOR (two-account PoC)

```
Endpoint: GET /api/v1/orders/{id}   (auth: regular user)
Code (abridged): return db.orders.find(id)   // NO check that order.ownerId == currentUser
HUNTER: suspects BOLA — sequential ids, no ownership check.
VALIDATOR (blind):
  1. Reachability: the route has auth (a valid regular user passes) but no ownership check. OK
  2. Taint/authz: the id reaches the query without an authorization check. OK
  3. PoC (two TEST accounts provided for the engagement):
     - userA (owns order #1001) requests GET /api/v1/orders/1002 (owned by test userB)
       → 200 plus userB's test order data ⇒ horizontal privilege boundary crossed.
     (Only test/canary records are touched — never real customer data.)
Verdict: CONFIRMED — CWE-639/862, OWASP API1. Severity High.
Fix: enforce ownership server side (order.ownerId == currentUser) or scope by tenant.
```

### Quick example — a killed false positive (mass assignment)

```
HUNTER: suspects mass assignment on PATCH /api/v1/profile (sending "role":"admin").
VALIDATOR: the serializer uses an allow-list DTO {name,email}; 'role' is dropped and never
  mapped onto the entity. PoC sending role=admin → role unchanged. ⇒ FALSE POSITIVE (blocked).
```

---

## 3) BINARY / MEMORY (fuzz → crash triage → exploitability)

**Sources:** file input, network packets, stdin/argv, IPC, environment.
**Sinks / bug classes:** out-of-bounds write (**CWE-787**), out-of-bounds read (**CWE-125**), use-after-free (**CWE-416**), double free, integer overflow leading to a bad allocation (**CWE-190**), format string (**CWE-134**), type confusion.

**Process**
1. **Fuzz** in an approved lab (AFL++, libFuzzer) and collect crashes. Fuzzing is a heavy load — approved environments only, never production.
2. **Triage the crash** with tooling (ASan output, exploitability heuristics): what kind of bug, read or write, is the address attacker-controlled?
3. **Assess exploitability (the bar):** does the crash lead to **PC control** or a **write-what-where** primitive? Which mitigations (ASLR, DEP, CFG, stack canary) stand in the way?

**Binary bar:** a **reproducible crash** plus a controllability analysis. Full weaponization is not required. Prioritize OOB write and UAF (commonly RCE) over NULL dereference (usually just DoS).

### Quick example — crash triage

```
Fuzzing an image parser (lab) → crash.
ASan: heap-buffer-overflow WRITE of size 4 at parse_chunk()+0x3c, past a 0x20 buffer,
  because chunk_len (attacker-controlled, from the file) is not validated before memcpy.
Assessment: out-of-bounds WRITE with attacker-controlled length and content → plausible
  write-what-where → potential RCE (CWE-787). A stack canary exists but this is the heap,
  so the canary does not help.
Verdict: CONFIRMED (likely exploitable) — PoC = the reproducing crash file plus the analysis.
  A full shell is NOT required. Fix: validate chunk_len <= buffer size before memcpy; use
  unsigned types with bounds checks.
Typical false positive: a NULL dereference from an uninitialized pointer — usually only DoS
  (CWE-476). Lower the severity; never claim RCE without demonstrating control.
```

---

## 4) CLOUD / IaC / KUBERNETES (mapped to CIS Benchmarks)

**Sources / artifacts:** Terraform, CloudFormation, Kubernetes manifests, IAM policies, buckets and ACLs, security groups, secret stores, container images.

**Bug classes and references**
- Overly broad IAM / privilege escalation (wildcard `*:*`, `iam:PassRole` plus role creation) → **CWE-269 / CWE-732**; CIS IAM.
- Public storage (S3/blob) or loose ACLs → **CWE-732**; CIS Storage.
- Secrets hardcoded in IaC, environment, or images → **CWE-798**; CIS Secrets.
- Security groups open to `0.0.0.0/0` on sensitive ports (22, 3389, database) → CIS Network.
- Kubernetes: privileged containers, `hostPath`, missing NetworkPolicy, overly broad RBAC, `allowPrivilegeEscalation`, running as root → CIS Kubernetes Benchmark.
- Logging and monitoring disabled (CloudTrail off) → CIS Logging.

**Cloud bar:** demonstrate the **effective permission or exposure**, not merely that a policy exists — check whether a higher-level deny (SCP, permission boundary) overrides it. Map to a CIS control and a CWE. Prioritize IAM privilege escalation and public data exposure.

### Quick example — IAM privilege escalation (safe PoC)

```
IaC grants the app role: { Action: ["iam:PassRole","lambda:CreateFunction",
  "lambda:InvokeFunction"], Resource:"*" }.
HUNTER: privesc chain — PassRole an admin role plus create a Lambda using it → execute with
  admin privileges.
VALIDATOR (blind), in the AUTHORIZED LAB ACCOUNT:
  1. Reachability: the policy is attached and effective (no SCP or permission boundary
     blocking it). OK
  2. Chain: create a Lambda with a test admin role, invoke it, print the identity
     (sts get-caller-identity) → it runs as the admin role.
     (No costly resources, no data deleted; everything cleaned up afterwards.)
Verdict: CONFIRMED — IAM privilege escalation (CWE-269), CIS IAM. Severity Critical.
Fix: remove the wildcard Resource; restrict PassRole to specific roles; set a permission
  boundary.
False positive: if a permission boundary or SCP denies PassRole, the chain breaks ⇒ do not
  confirm (record as UNCONFIRMED/mitigated).
```

---

## General notes for the VALIDATOR in every domain

- Default to skepticism: no PoC means no pass.
- Choose the **lowest-impact PoC** that still proves it; clean up afterwards, especially in cloud.
- **Never invent a CVE.** If there is no clear precedent, write "novel/uncertain".
- Give severity with a CVSS vector where possible, and always state the preconditions.

Sources: OWASP (https://owasp.org), OWASP API Security (https://owasp.org/API-Security/), CWE Top 25 (https://cwe.mitre.org/top25/), CIS Benchmarks (https://www.cisecurity.org/cis-benchmarks).

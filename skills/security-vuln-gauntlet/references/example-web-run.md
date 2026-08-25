# Worked example — one Gauntlet Loop round on a web endpoint

> **Hypothetical** target inside an authorized lab. Illustrates how LEAD, HUNTER, and VALIDATOR interact, and how a PoC both confirms one finding and kills another.

## Setting

An internal reporting app (lab). The suspicious endpoint:

```text
GET /api/report?path=<report file name>
Authorization: Bearer <regular user token>
```

Code (abridged, hypothetical Node/Express):

```js
app.get('/api/report', auth, (req, res) => {
  const p = req.query.path;                     // SOURCE
  const full = path.join('/srv/reports', p);    // path join
  return res.sendFile(full);                     // SINK: reads and returns a file
});
```

## Round 1

### LEAD — split

Relevant hunting unit: "file-serving endpoints". `/api/report` reaches the filesystem using input → suspect **path traversal (CWE-22)**. Assigned to HUNTER #3.

### HUNTER #3 (clean context) — candidate

```text
id: web-03
location: routes/report.js:12  (GET /api/report)
class: Path Traversal (CWE-22)
SOURCE: req.query.path
SINK: res.sendFile(path.join('/srv/reports', p))
taint hypothesis: path.join does not strip '../'; p='../../etc/passwd' escapes the root
preconditions: only a regular user token (auth passes but does not constrain the directory)
PoC idea: path=../../etc/passwd (read a file outside /srv/reports)
confidence: medium (unclear whether upstream middleware normalizes the path)
```

### VALIDATOR (blind) — receives the claim plus a pointer to `routes/report.js:12`

1. **Reachability:** the route is registered; `auth` only validates the token (a regular user passes) and there is no normalizing or `../`-denying middleware. Reachable.
2. **Taint:** `path.join('/srv/reports','../../etc/passwd')` resolves to `/etc/passwd`. `sendFile` is not root-constrained. No sanitizer.
3. **PoC (non-destructive — reads a harmless marker file placed by the lab, never a real secret):**

```text
GET /api/report?path=..%2f..%2fetc%2fhostname   HTTP/1.1
Authorization: Bearer <test user token>

→ HTTP 200
   <contents of /etc/hostname>   (harmless file, proves directory escape)
```

Observation: a file outside `/srv/reports` was read → escape confirmed. `/etc/shadow` and real data were not touched (least-impact rule).

#### Verdict: CONFIRMED

- CWE-22 (Path Traversal); OWASP A01 (Broken Access Control) / A05.
- Severity: High (arbitrary file read with the process's privileges; suggested CVSS ~7.5, AV:N/PR:L/UI:N).
- Precedent: path traversal in file-serving handlers is an extremely common, long-documented class — no need to cite a specific CVE, and never invent one.

### Recommended fix

```js
const p = path.basename(req.query.path);              // drop every directory component
const full = path.join('/srv/reports', p);
const resolved = path.resolve(full);
if (!resolved.startsWith(path.resolve('/srv/reports') + path.sep))
  return res.status(400).send('invalid path');         // block escapes
return res.sendFile(resolved);
```

Additionally: allow-list valid report names, and check report ownership so fixing traversal does not leave an IDOR behind.

## A false positive killed in the same round

HUNTER #3 also suspected XSS on `/api/health?fmt=`. The validator checked:

- **Reachability:** fine.
- **Taint:** `fmt` is only used in `switch(fmt){case 'json':...}` — it never reaches an HTML or JS sink, and unmatched values return 400. Tainted data does not reach a rendering sink.
- **PoC:** impossible to build (no HTML context exists).

**Verdict: FALSE POSITIVE** (fails the taint gate). Recorded so it is not re-reported.

## Round summary

LEAD merges: 1 CONFIRMED (path traversal), 1 false positive eliminated. Coverage: file-serving is covered; the export/PDF endpoints (suspected SSRF) go to round 2.

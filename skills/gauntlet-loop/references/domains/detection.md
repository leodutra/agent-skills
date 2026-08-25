# Domain: Detection - ATT&CK coverage with zero false positives

## Bars that work

- The SigmaHQ rule for the target technique (for T1053.005, `proc_creation_win_schtasks_create.yml`) - pinned commit, saved text.
- The Atomic Red Team test for the technique - pinned commit, test numbers run, its logs saved as the attack set.
- Elastic detection-rules for the same technique, pinned, when SigmaHQ has none.

LEAD freezes both datasets under reference/: that attack set and a benign set (30 days of the environment's own logs, or an OTRF Security Datasets capture), manifest: source, date, event count. Each rule maps to one ATT&CK technique ID. Measurable half: attack-set hits equal the variant count; benign-set hits are zero.

## Floor

Command floors (LEAD, on ours, first):

- Benign set: zero hits. One hit is red; no CRITIC this round.
- Attack set: fires on every variant in the manifest.
- Rule parses (`sigma check` or the platform's parser).
- The rule finishes over the benign set inside the platform's scheduled-search window; record the time.

Reading floors (CRITIC, both sides):

- Every exclusion names the benign log line that justifies it.
- The ATT&CK tag matches what the attack set exercises.
- The alert output carries host, user, parent image and command line.

HELD-OUT set: a benign slice and two Atomic variants the BUILDER never sees.

## What the critic physically does

- Runs both rules over both sets; pastes the command and hit counts.
- Opens every benign hit, quotes it, names the field that separates it (parent image, signer, user, path).
- Tries trivial evasion on both: casing, whitespace, another LOLBin, base64-encoded command; pastes what slips through.
- Checks each exclusion against a quoted benign line.

Evidence: command, count, quoted line, evasion variant.

LEAD hands over two rules in one format and field mapping, metadata (`title`, `id`, `author`, `references`) stripped, as `a.yml` and `b.yml`, and runs both itself on the same dataset copies; comments stripped from both, logic never cut. Sigma is the working format; `sigma convert` emits the same logic for Splunk SPL, Sentinel KQL and CrowdStrike.

## How the LEAD splits this work

One piece per technique per log source: schtasks.exe process creation and Event 4698 registration are separate pieces. Pieces sharing a field mapping or allow-list macro share state - serialise or use worktrees. Assembled-whole gate: SMOOTHER unifies field names, tags and allow-lists; the pack runs over the full benign set (zero hits), attack set and held-out slices; a fresh CRITIC judges it against the reference pack.

## A verdict, as evidence looks

```text
WINNER: A
GAP: B fires on benign scheduled-task creation by the endpoint management agent; A carries a parent-image filter for it. Seen by running both over benign/ and opening the 17 matched lines.
FLOOR: every exclusion cites a benign line - A: pass, filter names CcmExec.exe and benign line 20481 / B: pass, no exclusions
FLOOR: ATT&CK tag matches what the attack set exercises - A: pass (attack.t1053.005) / B: pass (attack.t1053.005)
EVIDENCE:
- A: `chainsaw hunt benign/ -s a.yml --mapping sigma-event-logs-all.yml` -> 0 detections over 412,880 process_creation events (30 days)
- B: same command -> 17 detections, all ParentImage=C:\Windows\CCM\CcmExec.exe, User=NT AUTHORITY\SYSTEM, CommandLine contains "/tn \Microsoft\Configuration Manager\"
- A and B: attack set (Atomic T1053.005 tests 1-3) - 3/3 fire on each side
- B: detection block is `selection` only - Image endswith \schtasks.exe, CommandLine contains /create; no suspicious clause, no parent filter
- A: `SCHTASKS  /Create /tn x /tr "powershell -enc ..."` (upper case, double space) still fires; B: same
- A and B: task registered through the ITaskService COM API, no schtasks.exe process, fires on neither
```

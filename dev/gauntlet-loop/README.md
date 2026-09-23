# gauntlet-loop: development material

Nothing here is deployed with the skill (`skills/gauntlet-loop/`); it is what keeps the skill honest.

- `tests/`: the controller, hook, installer and example tests. `python3 -W error -m unittest discover -s dev/gauntlet-loop/tests`
- `eval/`: free checks (`sizes.sh`, `harness_tokens.sh`, `wordcount.py`) and the two paid suites (`run.sh`, `run_critic.sh`) with their cases, pairs and `baseline.json`. The paid suites spend API or subscription usage; use `--only`.
- `TODO.md`: what is still missing against the design documents, by priority.
- `design/`: `intent.md`, `spec.md` with its amendments, `plan.md`, and `acceptance.md`, the record of what was checked and how. Paths inside them that read `tests/`, `eval/` or `design/` are relative to this folder.

CI: `.github/workflows/gauntlet-eval.yml`.

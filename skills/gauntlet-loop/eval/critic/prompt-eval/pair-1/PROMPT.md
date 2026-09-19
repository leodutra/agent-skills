The bar: a system prompt that extracts an invoice total as JSON; judged on the frozen harness results beside each prompt, visible and held-out.
On each side: read `prompt.txt` and `results.json` in `a/` and `b/`; compare visible and held-out pass rates and schema-invalid counts; run `grep -c -F -f inputs.txt a/prompt.txt` and `grep -c -F -f inputs.txt b/prompt.txt` to see whether eval inputs were pasted into a prompt.
Reading floors: no eval input appears in the prompt; zero schema-invalid outputs.

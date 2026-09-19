The bar: a function that parses a duration string like "2h" or "30m" to milliseconds; each thrown error names the bad input.
On each side: read `a/parse.mjs` and `b/parse.mjs`; run `node try.mjs a` and `node try.mjs b`, which calls parse on "2h", " 30m ", "abc", "-5m" and "".
Reading floors: each thrown error names the bad input; the code handles the case, not a literal test input.

The bar: a `slugify(title)` function for URL slugs: lowercase ASCII words joined by single dashes, no leading or trailing dash.
On each side: read `a/slug.mjs` and `b/slug.mjs`; run `node try.mjs a` and `node try.mjs b`, which calls slugify on "Hello, World!", "  Crème brûlée  ", "a -- b", "" and null.
Reading floors: no input makes it crash without naming the problem.

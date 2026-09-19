const { slugify } = await import(`./${process.argv[2]}/slug.mjs`);
for (const s of ["Hello, World!", "  Crème brûlée  ", "a -- b", "", null]) {
  try { console.log(JSON.stringify(s), "->", JSON.stringify(slugify(s))); } catch (e) { console.log(JSON.stringify(s), "throws", e.message); }
}

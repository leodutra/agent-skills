const { clamp } = await import(`./${process.argv[2]}/clamp.mjs`);
for (const a of [[5, 0, 10], [-1, 0, 10], [11, 0, 10], [1, 3, 2]]) {
  try { console.log(a, "->", clamp(...a)); } catch (e) { console.log(a, "throws", e.message); }
}

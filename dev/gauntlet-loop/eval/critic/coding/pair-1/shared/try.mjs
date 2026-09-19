const { parse } = await import(`./${process.argv[2]}/parse.mjs`);
for (const s of ["2h", " 30m ", "abc", "-5m", ""]) {
  try { console.log(JSON.stringify(s), "->", parse(s)); } catch (e) { console.log(JSON.stringify(s), "throws", e.message); }
}

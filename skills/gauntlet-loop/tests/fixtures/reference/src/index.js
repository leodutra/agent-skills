export function parse(s) {
  const m = /^(\d+)(ms|s|m|h)$/.exec(String(s).trim());
  if (!m) throw new Error(`invalid duration: "${s}"`);
  return Number(m[1]) * { ms: 1, s: 1e3, m: 6e4, h: 36e5 }[m[2]];
}

export function format(ms) {
  for (const [unit, n] of [["h", 36e5], ["m", 6e4], ["s", 1e3]]) if (ms >= n) return Math.round(ms / n) + unit;
  return ms + "ms";
}

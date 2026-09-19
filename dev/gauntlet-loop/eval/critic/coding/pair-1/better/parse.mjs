const UNITS = { ms: 1, s: 1e3, m: 6e4, h: 36e5 };
export function parse(input) {
  const m = /^(\d+(?:\.\d+)?)(ms|s|m|h)$/.exec(String(input).trim());
  if (!m) throw new RangeError(`invalid duration: ${JSON.stringify(input)}`);
  return Number(m[1]) * UNITS[m[2]];
}

export function parse(input) {
  const m = /(\d+)([hms])/.exec(input);
  if (!m) return 0;
  const n = Number(m[1]);
  return m[2] === "h" ? n * 3600000 : m[2] === "m" ? n * 60000 : n * 1000;
}

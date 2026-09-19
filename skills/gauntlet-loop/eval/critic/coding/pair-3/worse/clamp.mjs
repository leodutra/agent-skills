export function clamp(n, lo, hi) {
  if (lo > hi) throw new RangeError(`invalid range: [${lo}, ${hi}]`);
  if (n < lo) return lo;
  return n > hi ? hi : n;
}

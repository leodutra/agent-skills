export function clamp(n, lo, hi) {
  if (lo > hi) throw new RangeError(`clamp: lo (${lo}) is greater than hi (${hi})`);
  return Math.min(Math.max(n, lo), hi);
}

export function slugify(title) {
  if (typeof title !== "string") throw new TypeError(`slugify expects a string, got ${title === null ? "null" : typeof title}`);
  return title.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

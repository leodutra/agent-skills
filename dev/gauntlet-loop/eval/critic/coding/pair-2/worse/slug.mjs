export function slugify(title) {
  return title.toLowerCase().replace(/ /g, "-").replace(/[^a-z0-9-]/g, "");
}

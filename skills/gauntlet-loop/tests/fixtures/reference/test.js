import assert from "node:assert";
import { format, parse } from "./src/index.js";

assert.equal(parse("2h"), 7200000);
assert.equal(format(7200000), "2h");
console.log("2 passed");

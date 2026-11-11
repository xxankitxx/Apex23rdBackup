const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
const a = src.indexOf("function forecastHeadline("), b = src.indexOf("function renderForecast(");
const forecastHeadline = new Function(src.slice(a, b) + "; return forecastHeadline;")();
const assert = require("assert");
const row = (side, tag, up, down, above) => ({ side, tag, up, down, edge: up - down, above_line: !!above });
// reviewer case 1: call 40 % favourable, put 60 % favourable, but the call's up-minus-down is the larger
let t = forecastHeadline([row("CE", "exe", 0.40, 0.10), row("PE", "exe", 0.60, 0.55)], 5, "5");
assert(t.startsWith("The put has the higher chance of gaining 5% before losing 5% within 5 minutes: 60% against 40%."), t);
assert(!/more likely to rise|Strong enough/i.test(t), t);
assert(t.endsWith("Raw entry level not reached."), t);
// reviewer case 2: held contracts only, nothing buyable
t = forecastHeadline([row("CE", "held", 0.5, 0.2)], 5, "5");
assert(/^No contract the engine could buy has a forecast/.test(t) && /held contracts only/.test(t), t);
// one buyable side
t = forecastHeadline([row("PE", "exe", 0.33, 0.3), row("CE", "held", 0.5, 0.2)], 5, "5");
assert(/^Only the put side has a buyable contract/.test(t) && /33%/.test(t), t);
// two sides, near equal, one at the raw level
t = forecastHeadline([row("CE", "exe", 0.31, 0.3, true), row("PE", "exe", 0.30, 0.3)], 5, "5");
assert(/about the same chance/.test(t) && /Raw entry level reached on the call\.$/.test(t), t);
assert.strictEqual(forecastHeadline([], 5, "5"), "");
console.log("headline checks passed: 5");

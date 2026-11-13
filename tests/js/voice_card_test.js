// 13 Nov: the "What I would do now" card (apex/static/voice.js) renders every voice payload the engine writes
// (fixtures from tests/fixtures/voice/make_payloads.py) without throwing, with the pill, headline and the right body.
//   node tests/js/voice_card_test.js apex/static/voice.js tests/fixtures/voice
const fs = require("fs"), path = require("path"), vm = require("vm");
const [src, dir] = process.argv.slice(2);
const el = { hidden: true, className: "", innerHTML: "", textContent: "" };
const ctx = { $: (id) => (id === "voicecard" ? el : null),
              inr: (x) => (x === null || x === undefined) ? "—" : "Rs " + Math.round(x) };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(src, "utf8") + "\nthis.renderVoice = renderVoice;", ctx);
let n = 0, bad = 0;
const want = { waiting: ["WAIT", "I am flat"], armed: ["GET READY", "pullback"], zone: ["READY TO BUY", "turn back"],
               impulse: ["WATCHING THE IMPULSE", "impulse"], holding: ["HOLD", "v-ladder"] };
for (const f of fs.readdirSync(dir).filter(f => f.endsWith(".json") && !f.startsWith("stand"))) {
  const v = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
  const k = f.replace(".json", "");
  try {
    ctx.renderVoice({ voice: v });
    const h = el.innerHTML;
    for (const w of want[k] || []) if (!h.includes(w)) { bad++; console.log(`FAIL ${k}: missing "${w}"`); }
    if (el.hidden || !h.includes("What I would do now") || h.includes("undefined") || h.includes("NaN")) { bad++; console.log(`FAIL ${k}: bad render`); }
    n++;
  } catch (e) { bad++; console.log(`FAIL ${k}: ${e.message}`); }
}
ctx.renderVoice({});
if (!el.hidden) { bad++; console.log("FAIL: no voice should hide the card"); }
console.log(`${n} payloads rendered, ${bad} failures`);
if (bad) process.exit(1);
// 13 Nov: the stand banner (labStand) on a stand payload and on a Lab that is still warming up
{
  const st = { className: "", innerHTML: "" };
  ctx.$ = (id) => (id === "labstand" ? st : id === "voicecard" ? el : null);
  vm.runInContext("this.labStand = labStand;", ctx);
  const p = JSON.parse(fs.readFileSync(path.join(dir, "stand_payload.json"), "utf8"));
  let b = 0;
  ctx.labStand(p);
  for (const w of ["MY STAND", "BULLISH", "+64", "HOW THE MARKET IS BEHAVING", "BANKNIFTY", "HOW SURE I AM", "50 %", "st-fact pro", "st-fact con"])
    if (!st.innerHTML.includes(w)) { b++; console.log(`FAIL stand: missing "${w}"`); }
  if (!st.className.includes("st-bull")) { b++; console.log("FAIL stand: class"); }
  ctx.labStand({ stand: { ok: false, why: "needs 20 minutes of futures quotes" } });
  if (!st.innerHTML.includes("needs 20 minutes")) { b++; console.log("FAIL stand: warming text"); }
  ctx.labStand(null);
  if (!st.innerHTML.includes("waiting")) { b++; console.log("FAIL stand: null payload"); }
  console.log(`stand banner checks: ${b} failures`);
  if (b) process.exit(1);
}

// Forecast Lab panel contract test: the page's Lab code (apex/static/app.js) run in a vm sandbox with a minimal fake
// DOM, over payloads built by tests/fixtures/forecast_lab/make_payloads.py from real Lab output.
//   node tests/js/lab_payload_contract_test.js apex/static/app.js [fixture_dir]
// Checks: no part fails to draw; no 'Flat' while holding; '(80 %)' only where that horizon's range is on target; an
// old, previous-day or faulted file dims the panel and says so; the held contract comes first; table skeletons and
// unchanged SVGs are not rewritten; fmt builds one formatter per decimal count; the poll slows when stopped or hidden.
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm"), assert = require("assert");
const src = fs.readFileSync(process.argv[2] || "apex/static/app.js", "utf8").replace(/\r\n/g, "\n");
const dir = process.argv[3] || path.join(__dirname, "..", "fixtures", "forecast_lab", "gen");
if (!fs.existsSync(path.join(dir, "manifest.json"))) {
  console.error(`no fixtures in ${dir}: run py -3.13 tests/fixtures/forecast_lab/make_payloads.py first`);
  process.exit(2);
}
const html = fs.readFileSync(path.join(path.dirname(process.argv[2] || "apex/static/app.js"), "index.html"), "utf8");
const IDS = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]));

// ── the pieces of app.js the Lab uses: its shared one-line helpers, then the Lab section to the end of the file
const NEED = ["$", "nil", "NFC", "NF", "fmt", "inr", "MON", "dmy", "sinr", "put", "idEsc"];
const lines = src.split("\n");
const helpers = NEED.map((n) => {
  const l = lines.find((x) => x.startsWith(`const ${n} = `));
  assert(l, `helper ${n} not found in app.js`);
  return l;
}).join("\n");
const start = src.indexOf("// ── 11 Nov: Forecast Lab panel.");
assert(start > 0, "Lab section marker not found");
const lab = src.slice(start);

// ── a minimal DOM: enough for innerHTML / textContent writes, classes, attributes and createElement
let writes = 0;
class El {
  constructor(tag, id) { this.tagName = tag.toUpperCase(); this.id = id || ""; this.children = []; this._html = ""; this._text = "";
    this.className = ""; this.dataset = {}; this.attrs = {}; this.style = { setProperty: (k, v) => { this.style[k] = v; } };
    this.scrollLeft = 0; this.clientWidth = 0; this.open = undefined; this.listeners = {};
    const me = this;
    this.classList = {
      contains: (c) => me.className.split(/\s+/).includes(c),
      add: (c) => { if (!me.classList.contains(c)) me.className = (me.className + " " + c).trim(); },
      remove: (c) => { me.className = me.className.split(/\s+/).filter((x) => x && x !== c).join(" "); },
      toggle: (c, on) => { on = on === undefined ? !me.classList.contains(c) : !!on; on ? me.classList.add(c) : me.classList.remove(c); return on; },
    };
  }
  set innerHTML(h) { this._html = String(h); this._text = ""; this.children = []; writes++; }
  get innerHTML() { return this._html; }
  set textContent(t) { this._text = String(t); this._html = ""; this.children = []; writes++; }
  get textContent() { return this.children.length ? this.children.map((c) => c.textContent).join("") : this._text || this._html.replace(/<[^>]*>/g, ""); }
  appendChild(c) { this.children.push(c); return c; }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(k, f) { (this.listeners[k] = this.listeners[k] || []).push(f); }
  closest() { return null; }
}
const visible = (el) => (el ? el.textContent : "");

function sandbox(opts = {}) {
  const els = {};
  const body = new El("body");
  for (const c of opts.body || []) body.classList.add(c);
  const document = {
    body, visibilityState: opts.hidden ? "hidden" : "visible", listeners: {},
    getElementById: (id) => IDS.has(id) ? (els[id] = els[id] || Object.assign(new El(id === "labfut" || id === "labopt" ? "svg" : id === "labdetail" ? "details" : "div", id), id === "labdetail" ? { open: true } : {})) : null,
    createElement: (t) => new El(t),
    addEventListener: (k, f) => { (document.listeners[k] = document.listeners[k] || []).push(f); },
  };
  let nowMs = (opts.now || 0) * 1000;
  class FakeDate extends Date { static now() { return nowMs; } }
  let built = 0;
  const RealNF = Intl.NumberFormat;
  const FakeIntl = Object.create(Intl);
  FakeIntl.NumberFormat = function (...a) { built++; return new RealNF(...a); };
  const errors = [], warns = [];
  const store = opts.storage === "throws" ? { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } }
    : (() => { const m = new Map(Object.entries(opts.storage || {})); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), m }; })();
  const timers = [];
  const ctx = {
    document, window: { addEventListener() {} }, localStorage: store, Date: FakeDate, Intl: FakeIntl, Math, JSON, Number, String, Object, Array, Set, Map, Promise, Error,
    performance: { now: () => 0 }, console: { error: (...a) => errors.push(a.map(String).join(" ")), warn: (...a) => warns.push(a.join(" ")), log() {} },
    setTimeout: (f, ms) => { timers.push(ms); return timers.length; }, clearTimeout() {},
    fetch: () => new Promise(() => {}), AbortController: class { constructor() { this.signal = {}; } abort() {} },
  };
  vm.createContext(ctx);
  vm.runInContext(`${helpers}\n${lab}\n;globalThis.__t = { LAB, labTake, labDelay, labStaleOf, NFC, fmt, labRs, renderLab };`, ctx, { filename: "app.js (Lab section)" });
  return { t: ctx.__t, els, body, errors, warns, timers, store, setNow: (s) => { nowMs = s * 1000; }, built: () => built, doc: document };
}

const man = JSON.parse(fs.readFileSync(path.join(dir, "manifest.json"), "utf8"));
const P = Object.fromEntries(man.map((c) => [c.name, JSON.parse(fs.readFileSync(path.join(dir, c.file), "utf8"))]));
const C = Object.fromEntries(man.map((c) => [c.name, c]));
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks++; };
const statusOk = (p, h) => ((((p.earned || {}).range_h || {}).fut || {})[String(h)] || {}).status === "ok";

function run(name, opts = {}) {
  const c = C[name];
  const S = sandbox(Object.assign({ now: c.now, body: c.body }, opts));
  if (c.first) { S.setNow(P[c.first].t + 2); S.t.labTake(P[c.first]); S.setNow(c.now); }
  S.t.labTake(P[name]);
  ok(S.errors.length === 0, `${name}: a part failed to draw: ${S.errors.join(" | ")}`);
  return S;
}
const all = (S) => ["labsay", "labstrip", "labglance", "labnext", "labwhatif", "labdecay", "labscore", "labhint"].map((id) => visible(S.els[id])).join("\n");

// every case draws without a fault
for (const c of man) run(c.name);

// flat and live: not stale, detail open, the poll at 1 s
{
  const S = run("flat");
  ok(!S.els.fcsec.classList.contains("lab-stale"), "flat: marked stale");
  ok(S.els.labdetail.open === true, "flat: the detail should be open when flat");
  ok(S.t.labDelay() === 1000, `flat: poll ${S.t.labDelay()} ms, expected 1000`);
  ok(/Forecaster's view \(display only\)/.test(visible(S.els.labsay)), "flat: the view is not titled 'Forecaster's view (display only)'");
  ok(/Record by day/.test(visible(S.els.labscore)) && /fitted on itself/.test(visible(S.els.labscore)), "flat: no record-by-day table");
  ok(/vs plain clock/.test(visible(S.els.labscore)), "flat: volatility skill column missing");
  ok(/Nightly/.test(visible(S.els.labstrip)) && /1 failed/.test(visible(S.els.labstrip)), "flat: nightly chip missing");
  ok(/ask in, bid out/.test(visible(S.els.labnext)) && /last price/.test(visible(S.els.labnext)), "flat: the fill basis is not stated");
  ok(S.els.labglance.children.length === 5, `flat: glance has ${S.els.labglance.children.length} chips, expected 5`);
  // hidden page: 5 s
  const H = sandbox({ now: C.flat.now, hidden: true }); H.t.labTake(P.flat);
  ok(H.t.labDelay() === 5000, "hidden page: poll should be 5 s");
}

// '(80 %)' only on horizons whose range is on target today
for (const name of ["flat", "held", "unearned_horizons"]) {
  const S = run(name, { storage: { "apex.labdetail.holding": "1" } }), p = P[name];   // the detail open
  const futRow = S.els.labnext.children[0].children[0].children[1];   // wrap > table > row 1 (futures)
  const cells = futRow.children.slice(1);
  (p.path || []).forEach((f, i) => {
    const has = /\(80 %\)/.test(cells[i].textContent);
    ok(has === statusOk(p, f.h), `${name}: ${f.h} s column says '(80 %)' = ${has} while its status is ${(((p.earned.range_h || {}).fut || {})[String(f.h)] || {}).status}`);
    ok(!/80 % range/.test(cells[i].textContent), `${name}: the old '80 % range' label is still printed`);
  });
  const g = visible(S.els.labglance);
  ok(/\(80 %\)/.test(g) === (statusOk(p, 300) && !S.t.LAB.stale), `${name}: glance range chip '(80 %)' does not follow the 5-min status`);
}
{
  const S = run("unearned_horizons"), t = visible(S.els.labnext);
  ok(/being widened/.test(t) && /being narrowed/.test(t) && /unchecked/.test(t), "unearned: narrow, wide and unchecked labels missing");
}

// holding: no 'Flat' anywhere, detail closed by default, held contract first and selected, what-if from the entry
{
  const S = run("held");
  ok(!/\bFlat\b/.test(all(S)), "held: the word 'Flat' appears while holding");
  ok(S.els.labdetail.open === false, "held: the detail should be closed by default while holding");
  ok(S.t.LAB.dirty === true, "held: a closed detail should not be drawn");
  S.els.labdetail.open = true; S.els.labdetail.listeners.toggle.forEach((f) => f());
  ok(S.store.m.get("apex.labdetail.holding") === "1", "held: opening the detail while holding is not remembered");
  ok(S.t.LAB.sel === "25150CE", `held: chart shows ${S.t.LAB.sel}, expected the held 25150CE`);
  const wi = visible(S.els.labwhatif);
  ok(/from your entry at ₹230\.5/.test(wi), "held: what-if is not framed from the entry");
  ok(wi.indexOf("25,150 CE") >= 0 && (wi.indexOf("25,250 PE") < 0 || wi.indexOf("25,150 CE") < wi.indexOf("25,250 PE")), "held: the held what-if is not first");
  ok(/entry ₹230\.5/.test(S.els.labopt.innerHTML) && !/buy price now/.test(S.els.labopt.innerHTML), "held: the held fan should draw the entry, not the buy price");
  ok(/from your entry/.test(visible(S.els.labnext)), "held: the Next row has no P&L from the entry");
  ok(/not assessed: holding/.test(visible(S.els.labglance)), "held: buy chip should say not assessed");
  // a stored 'open' preference wins next time
  const S2 = sandbox({ now: C.held.now, body: C.held.body, storage: { "apex.labdetail.holding": "1" } }); S2.t.labTake(P.held);
  ok(S2.els.labdetail.open === true, "held: the viewer's stored choice is not applied");
  // storage that throws: defaults still apply, nothing fails
  const S3 = sandbox({ now: C.held.now, body: C.held.body, storage: "throws" }); S3.t.labTake(P.held);
  ok(S3.els.labdetail.open === false && S3.errors.length === 0, "held: blocked storage broke the panel");
}

// stopped, previous day, faulted: dimmed, said in words, no future drawn, slow poll
for (const name of ["stale", "previous_day", "ok_false"]) {
  const S = run(name);
  ok(S.els.fcsec.classList.contains("lab-stale") && S.els.labglance.classList.contains("lab-stale"), `${name}: .lab-stale not set`);
  const say = visible(S.els.labsay);
  ok(name === "ok_false" ? /No forecast at 15:15 on 11 Nov: shared table: not found\. The numbers below are from 15:14 on 11 Nov\./.test(say)
    : /Forecaster stopped at 15:14 on 11 Nov: the numbers below are from then\./.test(say), `${name}: stop line wrong: ${say}`);
  ok(!/lab-f80|lab-med/.test(S.els.labfut.innerHTML), `${name}: the future part of the futures fan is still drawn`);
  ok(!/Market|Options price/.test(visible(S.els.labstrip)), `${name}: forecast chips shown on an old file`);
  ok(S.t.labDelay() === 30000, `${name}: poll ${S.t.labDelay()} ms, expected 30000`);
  ok(/STOPPED|NO FORECAST/.test(visible(S.els.labglance)), `${name}: glance does not say stopped`);
}
// the file going quiet mid-session: fresh, then 11 s with the same t
{
  const S = run("flat");
  ok(!S.t.LAB.stale, "flat: should be live");
  S.setNow(P.flat.t + 11); S.t.labTake(P.flat);
  ok(S.els.fcsec.classList.contains("lab-stale"), "a file 11 s old should be stale");
  S.setNow(P.flat.t + 1e-3 + 12); const p2 = Object.assign({}, P.flat, { t: P.flat.t + 12 }); S.t.labTake(p2);
  ok(!S.els.fcsec.classList.contains("lab-stale") && /Right now/.test(visible(S.els.labsay)), "a fresh file after a stop should restore the panel");
}
// one failed read of a live file: still live, tried again in 1 s; failing for over 20 s: not reachable, 30 s
{
  const S = run("flat");
  S.t.LAB.last = (P.flat.t + 2) * 1000;
  S.setNow(P.flat.t + 3); S.t.labTake(null);
  ok(!S.t.LAB.stale && S.t.labDelay() === 1000, `one failed read: stale=${S.t.LAB.stale}, poll ${S.t.labDelay()} ms, expected live and 1000`);
  S.setNow(P.flat.t + 25); S.t.labTake(null);
  ok(S.t.LAB.staleKind === "gone" && S.els.fcsec.classList.contains("lab-stale"), "reads failing for 23 s: not marked as not reachable");
  ok(/NOT REACHABLE/.test(visible(S.els.labglance)) && S.t.labDelay() === 30000, "reads failing for 23 s: glance or poll wrong");
}
// a held contract that is not a buy candidate (the Lab appends it last): still first and selected
{
  const p = JSON.parse(JSON.stringify(P.held));
  const i = p.options.findIndex((o) => o.tag === "held"), h = p.options.splice(i, 1)[0];
  h.strike = 25100; p.options.push(h); p.held = Object.assign({}, p.held, { strike: 25100 });
  const S = sandbox({ now: C.held.now, body: C.held.body, storage: { "apex.labdetail.holding": "1" } }); S.t.labTake(p);
  ok(S.errors.length === 0, `held last: ${S.errors.join(" | ")}`);
  ok(S.t.LAB.sel === "25100CE", `held last: chart shows ${S.t.LAB.sel}, expected 25100CE`);
  const wi = visible(S.els.labwhatif), nx = visible(S.els.labnext);
  ok(wi.indexOf("25,100 CE") >= 0 && wi.indexOf("25,100 CE") < (wi.indexOf("25,250 PE") < 0 ? Infinity : wi.indexOf("25,250 PE")), "held last: the held what-if is not first");
  ok(nx.indexOf("25,100 CE · held") >= 0 && nx.indexOf("25,100 CE · held") < nx.indexOf("25,250 PE"), "held last: the held Next row is not first");
}
// the futures quote is old: the strip shows no forecast chips
{
  const S = run("quote_stale");
  ok(!/Market|Options price|Delivered/.test(visible(S.els.labstrip)) && /Forecast/.test(visible(S.els.labstrip)), "quote_stale: forecast chips shown");
}
// redraw only what changed: the same numbers a second time write nothing; one changed number writes one cell
{
  const S = run("flat");
  const wrap = S.els.labnext.children[0], before = S.t.LAB.wrote;
  S.setNow(P.flat.t + 3); S.t.labTake(Object.assign({}, P.flat, { t: P.flat.t + 1 }));
  ok(S.els.labnext.children[0] === wrap, "the Next table's wrapper was rebuilt: its scroll would reset");
  const again = S.t.LAB.wrote - before;
  ok(again < 400, `an unchanged second wrote ${again} characters of Lab HTML`);
  const p3 = JSON.parse(JSON.stringify(P.flat)); p3.t += 2; p3.F += 1.5;
  const b2 = S.t.LAB.wrote, f0 = S.els.labfut.innerHTML; S.t.labTake(p3);
  const svg = S.els.labfut.innerHTML !== f0 ? S.els.labfut.innerHTML.length : 0;   // the fan itself moves with the price
  ok(S.els.labnext.children[0] === wrap && S.t.LAB.wrote - b2 - svg < 800, `one changed price wrote ${S.t.LAB.wrote - b2 - svg} characters besides the fan`);
}
// fmt and labRs keep one formatter per decimal count
{
  const S = sandbox({ now: 0 }), n0 = S.built();
  for (let i = 0; i < 500; i++) { S.t.fmt(i * 1.37, 2); S.t.fmt(i, 0); S.t.labRs(i, 1); }
  ok(S.built() - n0 <= 3, `fmt built ${S.built() - n0} formatters for 1500 calls`);
  ok(S.t.fmt(1234567.891, 2) === (1234567.891).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }), "fmt output changed");
  ok(S.t.fmt(null) === "—" && S.t.fmt(NaN, 1) === "—", "fmt of a missing value");
}
console.log(`lab payload contract checks passed: ${checks}`);

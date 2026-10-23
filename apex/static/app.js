// ApexOptions dashboard.
// Ticks arrive straight from the shared table (/ws/ticks) and are written to the
// page the moment they land; the engine's view arrives ~4 times a second
// (/ws/state). The Triangle is drawn every animation frame from both.
"use strict";

const $ = (id) => document.getElementById(id);
const nil = (x) => x === null || x === undefined || Number.isNaN(x);
const fmt = (x, d = 2) => nil(x) ? "—" : Number(x).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });
const sgn = (x, d = 2) => nil(x) ? "—" : (x > 0 ? "+" : x < 0 ? "−" : "") + fmt(Math.abs(x), d);
const inr = (x) => nil(x) ? "—" : (x < 0 ? "−" : "") + "₹" + Math.round(Math.abs(x)).toLocaleString("en-IN");
const tone = (x) => x > 0 ? "up" : x < 0 ? "down" : "";
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const C = { up: css("--up"), down: css("--down"), beacon: css("--beacon"), ink: css("--ink"), mist: css("--mist"),
            shelf: css("--shelf"), line: css("--line"), deep: css("--deep"), refill: css("--refill") };
const NUMF = '"Chakra Petch", "Segoe UI", sans-serif';

let INST = {}, REGV = -1, loading = false;
let S = null;
const last = {};            // id -> last ltp
const legs = {};            // id -> {el, px}
let heroSig = "";
const ages = [];
let sound = false, actx = null, lastEvKey = "", flashAt = -1e9, flashDir = 1;
const futBuf = [];          // [t_s, fut] from state, virtual clock
const pnlBuf = [];          // [t_s, pts] for the open position
let posKey = "";
const RM = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

// ── data in ─────────────────────────────────────────────────────────────────
async function loadInstruments() {
  try {
    const d = await (await fetch("/api/instruments")).json();
    INST = {}; for (const it of d.items) INST[it.id] = it;
    REGV = d.version;
  } catch (e) { /* retried on next version change */ }
}

// Reconnect with jittered backoff: 1 s × 1.3^n (±25 %), capped at 10 s; n resets on open.
const tries = { ticks: 0, state: 0 };
function retry(name, fn) {
  const base = Math.min(10000, 1000 * Math.pow(1.3, tries[name]++));
  setTimeout(fn, Math.min(10000, base * (0.75 + 0.5 * Math.random())));
}

function connectTicks() {
  const ws = new WebSocket(`ws://${location.host}/ws/ticks`);
  ws.onopen = () => { tries.ticks = 0; };
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (!d.r) return;
    if (d.v !== REGV && !loading) { loading = true; loadInstruments().finally(() => { loading = false; }); }
    for (const r of d.r) onTick(r);
  };
  ws.onclose = () => retry("ticks", connectTicks);
}

function onTick([id, ltp, bid, ask, bq, aq, ttq, oi, age]) {
  ages.push(age); if (ages.length > 500) ages.shift();
  if (ltp === null) return;
  const prev = last[id]; last[id] = ltp;
  const it = INST[id];
  if (it && it.key === "NIFTY|FUT") paintPx($("fut"), ltp, prev);
  if (it && it.key === "NIFTY|SPOT") hdrNum("spot", ltp);           // the Spot tile flashes on its own ticks
  const L = legs[id];
  if (L) {
    paintPx(L.px, ltp, prev, !!(S && S.pos && S.pos.id !== id));   // while holding, only the held leg flashes
    L.ba.textContent = `${fmt(bid)} / ${fmt(ask)}`;
  }
  if (S && S.pos && S.pos.id === id) livePos(ltp);
}

function paintPx(el, v, prev, quiet) {
  el.firstChild ? (el.firstChild.nodeValue = fmt(v)) : (el.textContent = fmt(v));
  if (prev === undefined || v === prev || quiet || RM.matches) return;
  el.classList.remove("flash-up", "flash-down"); void el.offsetWidth;
  el.classList.add(v > prev ? "flash-up" : "flash-down");
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("flash-up", "flash-down"), 320);
}

// Staleness (C-08). The gateway stamps every state frame with engine_age_ms, and sends a small
// {"hb":1, engine_age_ms, feed_age_ms} frame when the engine's state has not changed for 1 s.
const live = { at: Date.now(), engineAge: undefined, feedAge: undefined, open: false, everOpen: false };
function noteAges(d) {
  live.at = Date.now();
  live.engineAge = d.engine_age_ms; live.feedAge = d.feed_age_ms;
}

function connectState() {
  const ws = new WebSocket(`ws://${location.host}/ws/state`);
  ws.onopen = () => { tries.state = 0; live.open = live.everOpen = true; };
  ws.onmessage = (m) => {
    try {
      const d = JSON.parse(m.data);
      noteAges(d);
      if (d.hb) { checkStale(); return; }
      S = d; render(S); checkStale();
    } catch (e) { console.log(e); }
  };
  ws.onclose = () => { live.open = false; checkStale(); retry("state", connectState); };
}

const STALE_MS = 2000;
function checkStale() {
  const since = Date.now() - live.at;
  let msg = "";
  if (since > STALE_MS || (!live.open && live.everOpen)) msg = "DISCONNECTED — no data from the gateway, reconnecting";
  else if (live.engineAge === null) msg = "ENGINE STALE — no engine heartbeat yet";
  else if (!nil(live.engineAge) && live.engineAge + since > STALE_MS) msg = `ENGINE STALE ${Math.round((live.engineAge + since) / 1000)} s — verdict, position and stop are frozen`;
  const b = $("stale");
  if (b.textContent !== msg) b.textContent = msg;
  b.hidden = !msg;
  document.body.classList.toggle("stale", !!msg);
  const fz = $("pbfrozen");
  if (fz && msg) {
    const secs = since > STALE_MS || !live.open ? since : (live.engineAge ?? 0) + since;
    fz.textContent = `FROZEN ${Math.max(1, Math.round(secs / 1000))} s · last known`;
  }
  if (!nil(live.feedAge)) $("health").title = `feed health · feed heartbeat ${fmt(live.feedAge / 1000, 1)} s old`;
}
setInterval(checkStale, 250);

setInterval(() => {
  const el = $("lat"), dot = $("dot");
  if (!ages.length) { el.textContent = "no ticks"; dot.className = S && S.feed === "LIVE" ? "warn" : ""; return; }
  const a = [...ages].sort((x, y) => x - y); ages.length = 0;
  const p50 = a[a.length >> 1], mx = a[a.length - 1];
  el.textContent = `tick age ${fmt(p50, 0)} ms, worst ${fmt(mx, 0)} ms`;
  dot.className = mx > 3000 ? "bad" : p50 > 800 ? "warn" : "live";
}, 1000);

// D-103: data health from EXCHANGE stamps — the receive-time "tick age" could not see frozen quotes
function renderHealth(h) {
  const el = $("dhealth");
  if (!el) return;
  if (!h) { el.textContent = ""; el.className = "dhealth"; return; }
  const pct = (x) => (nil(x) ? "—" : `${Math.round(x * 100)}%`);
  const parts = [];
  if (!nil(h.ce_live) || !nil(h.pe_live)) parts.push(`calls ${pct(h.ce_live)} · puts ${pct(h.pe_live)} trading`);
  if (!nil(h.lag_s)) parts.push(`data ${fmt(h.lag_s, 1)} s behind`);
  const fr = (h.frozen || []);
  if (fr.length) parts.push(`FROZEN: ${fr.slice(0, 3).join(", ")}${fr.length > 3 ? " …" : ""}`);
  el.textContent = parts.join(" · ");
  const bad = fr.length || (!nil(h.ce_live) && h.ce_live < 0.5) || (!nil(h.pe_live) && h.pe_live < 0.5);
  const warn = !nil(h.lag_s) && h.lag_s > 3;
  el.className = "dhealth" + (bad ? " bad" : warn ? " warn" : "");
  el.title = "From exchange time stamps: share of this week's options that traded in the last minute, the hero contracts with no trade for 5+ minutes, and how far the feed runs behind the exchange.";
}

// ── T03 header: four tiles, one accent each ─────────────────────────────────
// Spot (gold), VIX (violet→magenta ladder), ATM IV (cyan), Clock (white on ink + phase ring).
// Display thresholds only (nothing here decides a trade): VIX_HOT, IV_JUMP, LATE = last 15 min.
const H = {
  vixBuf: [],              // [t_s, vix] last 5 min of engine time, for the VIX 5-min arrow
  spotOpen: undefined,     // first spot seen this session: fallback for s.spot_prev
  vixOpen: undefined,      // first VIX seen this session: fallback for s.vix_prev
  prev: {},                // id -> last rendered number, for the change flash
  VIX_HOT: 24,             // tile pulses at or above this
  IV_JUMP: 1.0,            // |iv5| in IV points that earns a POP / CRUSH tag
  FLATTEN: "15:35",        // fallback only — the engine's flatten_at field wins when present
};
const hms = (s) => { const t = (s || "").split(":").map(Number); return t.length >= 2 ? t[0] * 3600 + t[1] * 60 + (t[2] || 0) : NaN; };
const mins = (secs) => Math.max(0, Math.ceil(secs / 60));
const hhmm = (secs) => `${String(Math.floor(secs / 3600)).padStart(2, "0")}:${String(Math.floor(secs / 60) % 60).padStart(2, "0")}`;

// one flash rule for every header numeral: white for 300 ms, then back to the tile colour
function hdrNum(id, v, d = 2) {
  const el = $(id); if (!el) return;
  const txt = fmt(v, d), prev = H.prev[id];
  if (el.textContent !== txt) el.textContent = txt;
  H.prev[id] = v;
  if (prev === undefined || nil(v) || v === prev || RM.matches || isStale()) return;
  el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("flash"), 300);
}
const delta = (v, ref, d = 2, pct = false) => nil(v) || nil(ref) || !ref ? "" :
  `<b class="${tone(v - ref)}">${sgn(v - ref, d)}${pct ? ` (${sgn((v - ref) / ref * 100, 2)}%)` : ""}</b>`;
const setHTML = (el, h) => { if (el.dataset.h !== h) { el.innerHTML = h; el.dataset.h = h; } };

function renderHeader(s, now) {
  // ── Spot: gold numeral; sub-line = change vs previous close (green/red) ─────────────────
  const spot = spotNow(s) ?? s.spot;                       // live tick first, state second
  if (H.spotOpen === undefined && !nil(s.spot)) H.spotOpen = s.spot;
  const spotRef = !nil(s.spot_prev) ? s.spot_prev : H.spotOpen;   // engine field or session-first
  $("t-spot").classList.toggle("nodata", nil(spot));
  hdrNum("spot", spot);
  const r = s.spot_range || {};
  setHTML($("spotsub"), nil(spot) ? (nil(spotRef) ? (s.phase === "PRE" ? "waiting for the open" : "no index quote") : `<span class="mist">prev close</span> <b>${fmt(spotRef)}</b>`) :
    `${delta(spot, spotRef, 2, true)}<span class="mist">${!nil(s.spot_prev) ? "vs close" : "vs first"}</span>` +
    (nil(r.hi) || nil(r.lo) ? "" : `<span class="mist rng">12-min range ${fmt(r.lo, 0)} – ${fmt(r.hi, 0)}</span>`));

  // ── VIX: violet → magenta by level; sub-line = day change and 5-min arrow in the tile hue ──
  const vix = s.vix;
  if (H.vixOpen === undefined && !nil(vix)) H.vixOpen = vix;
  if (!nil(vix)) { H.vixBuf.push([now, vix]); while (H.vixBuf.length && now - H.vixBuf[0][0] > 300) H.vixBuf.shift(); }
  const v5 = H.vixBuf.length > 1 ? vix - H.vixBuf[0][1] : null;
  const lv = nil(vix) ? 2 : vix < 13 ? 1 : vix < 18 ? 2 : vix < H.VIX_HOT ? 3 : 4;
  const tv = $("t-vix"), tvc = `ht ht-vix lv${lv}${nil(vix) ? " nodata" : ""}`;
  if (tv.className !== tvc) tv.className = tvc;
  hdrNum("vix", vix);
  const vref = !nil(s.vix_prev) ? s.vix_prev : H.vixOpen;
  setHTML($("vixsub"), nil(vix) ? "no VIX yet" :
    `${delta(vix, vref)}<span class="mist">${!nil(s.vix_prev) ? "vs close" : "vs first"}</span>` +
    (nil(v5) || Math.abs(v5) < 0.05 ? "" : ` <b class="${v5 > 0 ? "vup" : "vdn"}">${v5 > 0 ? "▲" : "▼"} ${sgn(v5)} 5m</b>`) +
    (lv === 4 ? ` <b class="vup">FEAR</b>` : ""));

  // ── ATM IV: cyan; sub-line = 5-min change with arrow; POP / CRUSH tag at ±IV_JUMP ────────
  const iv = s.atm_iv, iv5 = s.iv5;
  const ti = $("t-iv");
  ti.classList.toggle("nodata", nil(iv));
  ti.classList.toggle("pop", !nil(iv5) && iv5 >= H.IV_JUMP);
  ti.classList.toggle("crush", !nil(iv5) && iv5 <= -H.IV_JUMP);
  hdrNum("atmiv", iv);
  const ivk = nil(s.atm) ? "" : `· ${fmt(s.atm, 0)}`;
  if ($("ivk").textContent !== ivk) $("ivk").textContent = ivk;
  setHTML($("ivsub"), nil(iv) ? (s.phase === "PRE" ? "chain after the open" : "no chain yet") :
    nil(iv5) ? `<span class="mist">5-min change soon</span>` :
    `<b class="${tone(iv5)}">${iv5 > 0 ? "▲" : iv5 < 0 ? "▼" : "•"} ${sgn(iv5)} · 5m</b>` +
    (iv5 >= H.IV_JUMP ? `<span class="tag">POP</span>` : iv5 <= -H.IV_JUMP ? `<span class="tag">CRUSH</span>` : ""));

  // ── Clock: white on ink; phase chip; ring = where we are in the entry window ─────────────
  const t = (s.now || "").slice(11);
  if ($("clock").textContent !== (t || "—")) $("clock").textContent = t || "—";
  const [w0, w1] = (s.entry_window || ENTRY_WINDOW).split("-");          // "09:25-15:29"
  const open = hms("09:15"), e0 = hms(w0), e1 = hms(w1);
  const flat = hms((s.pos && s.pos.time_exit) || s.flatten_at || H.FLATTEN);
  const close = hms("15:40");
  let ph, frac = 0, ringTxt = "", sub = "";
  if (s.phase === "PRE" || now < open)        { ph = "PRE";    frac = 0;                                ringTxt = `${mins(open - now)}m`; sub = `open 09:15`; }
  else if (now < e0)                          { ph = "PRE";    frac = (now - open) / (e0 - open);       ringTxt = `${mins(e0 - now)}m`;   sub = `entries ${w0}`; }
  else if (now < e1)                          { ph = "CTS";    frac = (now - e0) / (e1 - e0);           ringTxt = `${mins(e1 - now)}m`;   sub = `until ${w1}`; }
  else if (now < flat)                        { ph = "LATE";   frac = (now - e1) / (flat - e1);         ringTxt = `${mins(flat - now)}m`; sub = `flat by ${hhmm(flat)}`; }
  else if (s.phase === "CAS-ENTRY" || s.phase === "CAS-MATCH") { ph = "CAS"; frac = 1; ringTxt = "CAS"; sub = s.phase === "CAS-MATCH" ? "matching" : "stocks in auction"; }
  else if (now < close)                       { ph = "POST";   frac = 1;                                ringTxt = `${mins(close - now)}m`; sub = "F&O to 15:40"; }
  else                                        { ph = "CLOSED"; frac = 1;                                ringTxt = "—";                    sub = "session over"; }
  if (ph === "CTS" && e1 - now <= 15 * 60) ph = "LATE";          // last 15 min of entries: amber
  const tc = $("t-clock"), tcc = `ht ht-clock ph-${ph}`;
  if (tc.className !== tcc) tc.className = tcc;
  const chip = $("phase");
  const chipTxt = ({ PRE: "pre-open", CTS: "entries open", LATE: now < e1 ? "last entries" : "exits only", CAS: "auction", POST: "post", CLOSED: "closed" })[ph];
  if (ph !== "CAS" && /^CAS/.test(s.phase || "")) sub = `CAS · ${sub}`;   // CAS test: entries run into the auction; say so
  if (chip.textContent !== chipTxt) chip.textContent = chipTxt;
  tc.title = `Engine clock · phase ${s.phase}${s.cas_test ? " (CAS test)" : ""} · entries ${w0}–${w1} · flatten ${hhmm(flat)}`;
  chip.hidden = false;
  if ($("clocksub").textContent !== sub) $("clocksub").textContent = sub;
  const off = (119.4 * (1 - clamp(isNaN(frac) ? 0 : frac, 0, 1))).toFixed(1);
  if ($("ringarc").getAttribute("stroke-dashoffset") !== off) $("ringarc").setAttribute("stroke-dashoffset", off);
  if ($("ringtxt").textContent !== ringTxt) $("ringtxt").textContent = ringTxt;
}

// ── state → page ───────────────────────────────────────────────────────────
let ENTRY_WINDOW = "09:25-15:15";
const PHASE_TXT = { "CAS-ENTRY": "Closing auction · stocks not trading", "CAS-MATCH": "Closing auction · matching", POST: "Cash closed · F&O open" };
const clockSecs = (s) => { const t = (s || "").slice(11).split(":").map(Number); return t.length === 3 ? t[0] * 3600 + t[1] * 60 + t[2] : 0; };

function render(s) {
  const now = clockSecs(s.now);
  $("mode").textContent = s.mode === "live" ? "paper · live data" : s.mode === "sim" ? "paper · simulated market" : "paper · replay";
  if (!nil(s.fut_ltp)) $("fut").title = `Bid/ask midpoint (what the system trades on). Last traded: ${fmt(s.fut_ltp, 2)}`;
  renderHealth(s.health);
  if (s.entry_window) ENTRY_WINDOW = s.entry_window;
  renderHeader(s, now);                            // T03: spot / vix / atm iv / clock tiles
  const bo = s.blackout || {};
  $("feed").textContent = ({ LIVE: "Live", SIM: "Simulated", REPLAY: "Replay", RECONNECTING: "Reconnecting", DEAD: "Feed down", CONNECTING: "Connecting", DONE: "Session over" }[s.feed] || s.feed)
    + (bo.on ? ` · entries paused (${bo.why || "data gap"}${nil(bo.resume_in) ? "" : `, resume in ${fmt(bo.resume_in, 0)} s`})` : "")
    + (bo.gaps_today ? ` · ${bo.gaps_today} gap${bo.gaps_today > 1 ? "s" : ""} today` : "");
  $("feed").classList.toggle("gap", !!bo.on);
  $("feed").title = $("feed").textContent;
  $("dayrange").textContent = (nil(s.fut_hi) || nil(s.fut_lo)) ? "" : `H ${fmt(s.fut_hi, 2)}  ·  L ${fmt(s.fut_lo, 2)}`;
  if (!nil(s.fut) && last[idOf("NIFTY|FUT")] === undefined) $("fut").textContent = fmt(s.fut);
  if (!nil(s.fut_prev) && !nil(s.fut)) { const c = s.fut - s.fut_prev; $("futchg").textContent = `${sgn(c)} (${sgn(c / s.fut_prev * 100)}%)`; $("futchg").className = "q-chg " + tone(c); }
  if (s.book && !s.pos) {
    $("caplabel").textContent = "Paper capital";
    $("cap").textContent = inr(s.book.capital);
    const d = $("daypnl"); d.textContent = `${inr(s.book.pnl_rs)} today, ${sgn(s.book.pnl_pts)} points`; d.className = tone(s.book.pnl_rs); d.dataset.h = "";
  }
  if (!nil(s.fut)) { futBuf.push([now, s.fut]); while (futBuf.length && now - futBuf[0][0] > 300) futBuf.shift(); }
  renderVerdict(s); renderLadder(s); renderPos(s, now);
  if (typeof renderCommentary === "function") renderCommentary(s, now);   // commentary.js (T09)
  drawTrace(s); drawOI(s);
  renderStraddle(s, now); renderHeavy(s); renderTrades(s); renderBooks(s); renderTape(s);
}

const idOf = (key) => { for (const id in INST) if (INST[id].key === key) return +id; return -1; };

function isSpotMode(s) { return !!((s && s.params) || {}).spot_dc; }
function spotNow(s) {
  const id = idOf("NIFTY|SPOT");
  return (id >= 0 ? last[id] : undefined) ?? (s && s.pos && s.pos.on_spot && s.pos.fut_now) ?? (s && s.spot);
}
function spotCorners(s) {
  // D-124: the spot-breakout champion has three conditions — the break, a free swing, fresh data
  const r = s.spot_range || {}, sp = spotNow(s), p = s.params || {};
  if (nil(r.hi) || nil(r.lo) || nil(sp)) return { dir: 1, push: 0, crowd: 0, fresh: (nil(r.age) || r.age <= 5) ? 1 : 0, ep: false, closed: false, spot: true, warming: true };
  const W = Math.max(r.hi - r.lo, 1e-6), mid = (r.hi + r.lo) / 2;
  const dir = sp >= mid ? 1 : -1;
  const push = dir > 0 ? (sp - r.lo) / W : (r.hi - sp) / W;          // 1.0 = at the edge; beyond = a break
  const sl = r.swing_last, free = !(sl && sl.d === dir && (sp - sl.best) * dir <= 0);
  const fresh = (nil(r.age) || r.age <= 5) ? 1 : 0;
  return { dir, push, crowd: free ? 1 : Math.max(0.05, 1 - Math.min(1, Math.abs(sp - (sl ? sl.best : sp)) / Math.max(p.spot_trail || 12, 1))),
           fresh, ep: true, closed: push >= 1 && free && fresh >= 1, spot: true, hi: r.hi, lo: r.lo, sp, free, age: r.age };
}

function corners(s) {
  if (isSpotMode(s)) return spotCorners(s);
  const d0 = s.domino || {}, p = s.params || { m_star: 2, s_star: .5 };
  const ep = s.episode;
  const dir = ep ? ep.dir : (d0.dir || 1);
  const push = Math.max(0, (d0.z || 0) * dir) / p.m_star;
  const crowd = (dir > 0 ? d0.S_up : d0.S_dn) / p.s_star || 0;
  let fresh = 0.35;                                   // no move under way
  if (ep && !nil(s.late)) fresh = s.late < 1 ? 1 + 0.25 * (1 - s.late) : Math.max(0, 2 - s.late);
  return { dir, push, crowd, fresh, ep: !!ep, closed: push >= 1 && crowd >= 1 && ep && fresh >= 1 };
}

function humanReason(r, s) {
  const p = s.params || {};
  let m;
  if (!r) return "Waiting for data";
  if (r === "no episode") return "Calm. Waiting for a move to start.";
  if (r === "spot range warming") return nil(s.spot) ? "No Nifty index quote is arriving. The spot book cannot trade without it." : "Learning the 12-minute spot range. Ready about 12 minutes after the open or a restart.";
  if ((m = r.match(/^spot ([\d.]+) inside its (\d+)-min range ([\d.]+)-([\d.]+)/))) return `Nifty ${fmt(+m[1], 1)} is inside its ${m[2]}-minute range ${fmt(+m[3], 1)} – ${fmt(+m[4], 1)}. Waiting for a break either way.`;
  if ((m = r.match(/^same swing: spot must pass ([\d.]+) before another (CE|PE)/))) return `Already traded this swing. Another ${m[2]} needs Nifty past ${fmt(+m[1], 1)}.`;
  if ((m = r.match(/^spot quote (\d+) s old/))) return `The Nifty index quote is ${m[1]} s old. No entry until it is fresh.`;
  if (/^spot [\d.]+ broke its/.test(r)) return "Nifty broke its 12-minute range. Entering.";
  if (r.startsWith("KILL switch")) return "Kill switch is on (data\\KILL exists). No new entries in any book.";
  if (r.startsWith("expiry day")) return "Expiry day: " + r.replace(/^expiry day:\s*/, "") + ".";
  if (r === "in position") return "In a trade.";
  if (r.startsWith("DAILY STOP")) return "Stopped for the day: " + r.slice(12) + ".";
  if (r.startsWith("pause:")) return "Paused after three losses in a row (" + r.split(", ")[1] + ").";
  if (r.startsWith("gate regime")) return "Market regime says no: " + r.replace(/^gate regime:\s*/, "") + ".";
  if (r.startsWith("cool-down")) return "Cooling down after the last exit (" + r.split(": ")[1] + ").";
  if (r === "episode began in a data gap") return "This move started while the data was paused, so it can't be trusted. Waiting for the next one.";
  if (r.startsWith("DATA GAP")) return "Data paused: " + r.replace(/^DATA GAP:\s*/, "") + ". No entries until it is clean.";
  if (r === "outside entry window") return `Outside entry hours (${ENTRY_WINDOW.replace("-", " to ")}).`;
  if (r === "already traded this episode") return "Already traded this move. Waiting for the next one.";
  if (r === "impulse against the episode") return "Futures are pushing against the move that started.";
  if ((m = r.match(/^impulse z (-?[\d.]+) < ([\d.]+)/))) return `Push is ${m[1]} of the ${m[2]} needed.`;
  if ((m = r.match(/^synchrony ([\d.]+) < ([\d.]+)/))) return `${Math.round(m[1] * 100)}% of heavyweight weight is moving together; ${Math.round(m[2] * 100)}% needed.`;
  if ((m = r.match(/^LATE: futures already (\d+) pts/))) return `Too late: futures already ran ${m[1]} points since the move began.`;
  if ((m = r.match(/^LATE: ATM IV \+([\d.]+)/))) return `Too late: option IV already up ${m[1]} points since the move began.`;
  if ((m = r.match(/^gate (\w+): (.*)/))) return `Blocked by a learned rule (${ADV[m[1]] || m[1]}): ${m[2]}.`;
  if (/^no (CE|PE) in delta band/.test(r)) return "No contract in the right delta band right now.";
  if (/move (UP|DOWN)/.test(r)) return "All three corners met. Entering.";
  return r;
}

const ADV = { iv_late: "IV not stretched", room: "Room to the next wall", coherence: "Hero contracts agree",
              force: "Level not holding firm", episode: "Basket led the move", book: "Orders on the contract",
              premium: "Premium being bought", quiet: "Market awake", bank: "Bank Nifty agrees", event: "No event today",
              gamma_leg: "Straddle leg agrees", gex_room: "Dealer gamma allows it", regime: "Market state suits it" };

function renderVerdict(s) {
  const v = $("verdict"), c = corners(s);
  if (s.pos) {
    v.textContent = `In a trade (${s.pos.strike} ${s.pos.rr}). The position is at the top of the page.`;
    v.className = "verdict quiet";
  } else {
    v.textContent = humanReason(s.reason, s);
    v.className = "verdict" + (c.closed ? " fire" : "");
  }
  const ep = s.episode;
  $("episode").innerHTML = ep
    ? `Move <b class="${ep.dir > 0 ? "up" : "down"}">${ep.dir > 0 ? "up" : "down"}</b>, ${fmt(ep.age, 0)} s old. ${{ "BASKET-LED": "Heavyweights moved first", "FUTURES-LED": "Futures moved first", "SINGLE-NAME": "One stock is doing it alone", "CO-FIRST": "Heavyweights and futures moved together", "FORMING": "Still forming" }[ep.type] || ep.type}${ep.first ? `, first was <b>${ep.first}</b>` : ""}; ${ep.n_cross} ${ep.n_cross === 1 ? "name" : "names"} joined. IV ${s.iv_rise === null ? "—" : sgn(s.iv_rise)} since it began.`
    : "No move under way.";
  const a = s.advisors || {}, gates = s.gates || [];
  $("advisors").innerHTML = Object.keys(ADV).map(k => {
    const x = a[k];
    const cls = !x ? "idle" : x.veto ? "veto" : "";
    return `<li class="${cls}${gates.includes(k) ? " gate" : ""}" title="${x ? x.why.replace(/"/g, "'") : "waits for a move"}">${ADV[k]}${gates.includes(k) ? " (rule)" : ""}${x && x.veto ? ": no" : ""}</li>`;
  }).join("");
  const p = s.params || {};
  if (isSpotMode(s)) {
    const r = s.spot_range || {}, c2 = c;
    $("champ").textContent = `Lead book ${s.champion}: buys a CE when Nifty spot breaks above its ${Math.round(p.spot_dc / 60)}-minute high, a PE below its low; exits ${p.spot_trail} spot points off the best. ` +
      (c2.warming ? "Range not ready yet." : `Range now ${fmt(r.lo, 1)} – ${fmt(r.hi, 1)}${c2.free ? "" : " · same swing as the last trade"}${!nil(r.age) && r.age > 5 ? ` · spot quote ${fmt(r.age, 0)} s old` : ""}.`) +
      ` ${gates.length ? "Learned rules: " + gates.map(g => ADV[g]).join(", ") + "." : "No learned rules."}`;
  } else
  $("champ").textContent = `Lead book ${s.champion}: push ≥ ${p.m_star}, together ≥ ${Math.round((p.s_star || 0) * 100)}%, stop ${p.d_star} futures points. ${gates.length ? "Learned rules: " + gates.map(g => ADV[g]).join(", ") + "." : "No learned rules yet."}`;
}

function renderLadder(s) {
  const hs = s.heroes || [];
  const sig = hs.map(h => h.id).join(",") + "|" + s.atm;
  const by = {};
  for (const h of hs) (by[h.strike] = by[h.strike] || {})[h.rr] = h;
  const ks = Object.keys(by).map(Number).sort((a, b) => b - a);
  if (sig !== heroSig) {
    heroSig = sig;
    const box = $("lad"); box.innerHTML = "";
    for (const k in legs) delete legs[k];
    for (const k of ks) {
      for (const side of ["CE", "K", "PE"]) {
        const el = document.createElement("div");
        if (side === "K") { el.className = "k" + (k === s.atm ? " atm" : ""); el.textContent = k; box.appendChild(el); continue; }
        const h = by[k][side];
        el.className = "leg " + side.toLowerCase();
        el.innerHTML = `<div class="px">—<small></small></div><div class="tug"><i></i></div><div class="meta"></div><div class="meta ord"></div>`;
        box.appendChild(el);
        if (h) {
          const px = el.querySelector(".px");
          legs[h.id] = { el, px, ba: px.querySelector("small"), tug: el.querySelector(".tug i"), meta: el.querySelector(".meta"), ord: el.querySelector(".ord") };
          if (last[h.id] !== undefined) px.firstChild.nodeValue = fmt(last[h.id]);
        }
      }
    }
  }
  for (const h of hs) {
    const L = legs[h.id]; if (!L) continue;
    const b = h.sb || 0, a = h.ss || 0;
    L.tug.style.width = (b + a > 0 ? b / (b + a) * 100 : 50) + "%";
    L.meta.innerHTML = `<span>Δ <b>${fmt(h.delta, 2)}</b> IV <b>${fmt(h.iv, 1)}</b></span><span>${nil(h.vol_s) ? "—" : fmt(h.vol_s / 1000, 1) + "k/s"}</span><span>OI <b class="${tone(h.oi_chg)}">${nil(h.oi_chg) ? "—" : sgn(h.oi_chg / 1000, 0) + "k"}</b></span><span class="c-${h.cls_s}" title="sellers: ${h.cls_s}">${SH[h.cls_s] || "—"}</span>`;
    const oppO = h.rr === "CE" ? h.cls_so : h.cls_bo, oppOrd = h.rr === "CE" ? h.sso : h.sbo, forOrd = h.rr === "CE" ? h.sbo : h.sso;
    const leadCls = h.lead >= 0.3 ? "up" : h.lead <= -0.3 ? "down" : "mist";
    L.ord.innerHTML = `<span title="resting orders: buyers vs sellers">orders <b>${fmt(forOrd, 0)}</b> v <b>${fmt(oppOrd, 0)}</b></span><span class="c-${oppO}" title="opposing side's order count">${h.rr === "CE" ? "seller" : "buyer"} orders ${SH[oppO] || "—"}</span><span class="${leadCls}" title="does this contract's book lead its price? (−1 to +1)">book→px ${sgn(h.lead, 2)}</span>`;
    L.el.classList.toggle("hot", (h.run_up || 0) >= 0.3);
    L.el.classList.toggle("held", !!(s.pos && s.pos.id === h.id));
  }
  const st = s.straddle || {};
  $("expiry").innerHTML = `expiry ${s.w0 || "—"}, ATM ${s.atm ?? "—"} · straddle <b>${fmt(st.px, 1)}</b>${st.vwap ? ` vs VWAP ${fmt(st.vwap, 1)} <b class="${/EXPAND|ABOVE/.test(st.state) ? "up" : "down"}">${(st.state || "").toLowerCase()}</b>` : ""} · together up ${pct(s.K_up)} down ${pct(s.K_dn)}`;
}
const SH = { "REFILLING": "refill", "HOLDING": "hold", "DRAIN-SLOW": "drain", "DRAIN-FAST": "drain fast", "PULLED": "pulled" };
const pct = (x) => nil(x) ? "—" : Math.round(x * 100) + "%";

// ── the position band (design council RESOLVED.md; v2 per T04) ─────────────
// One full-width band under the sticky bar. Flat: one quiet mist line. Open: the loudest thing on
// the page (56 px P&L with a glow, stop rail, premium path, ten tiles). Exit: a 60 s receipt.
// One data-state drives one colour variable: fresh ice, profit green, loss red, locked gold,
// near-stop amber, pending violet, stale mist. Display only, no trading logic.
const sinr = (x) => nil(x) ? "—" : (x > 0 ? "+" : "") + inr(x);
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dmy = (d) => { const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(d || ""); return m ? `${+m[3]} ${MON[+m[2] - 1]}` : (d || "—"); };
const dur = (s) => nil(s) ? "—" : s < 60 ? `${Math.round(s)}s` : s < 3600 ? `${Math.floor(s / 60)}m ${String(Math.round(s % 60)).padStart(2, "0")}s` : `${Math.floor(s / 3600)}h ${String(Math.floor(s % 3600 / 60)).padStart(2, "0")}m`;
const code = (r) => (r || "").split(" ")[0];
const isStale = () => document.body.classList.contains("stale");
let futId = -1, receipt = null, prevHad = null, bandMode = "";
const tz = { cur: "", cand: "", since: 0 };          // P&L tone with hysteresis (D4): 3 s beyond ±0.5 pt
const LOT = 65;                                      // config.LOT_SIZE (display only; qty from the blob wins)
const E = {};                                        // cached element refs of the open template (bindBand)
const st = { state: "", nearSince: 0, nearOff: 0, peakSeen: -1e9, bestSeen: -1e9, rail: null };   // band state machine (view only)
const hm = (s) => { const t = (s || "").split(":").map(Number); return t.length >= 2 ? t[0] * 3600 + t[1] * 60 + (t[2] || 0) : 0; };
const mmss = (s) => s <= 0 ? "now" : s < 3600 ? `${Math.floor(s / 60)}m ${String(Math.floor(s % 60)).padStart(2, "0")}s` : `${Math.floor(s / 3600)}h ${String(Math.floor(s % 3600 / 60)).padStart(2, "0")}m`;
const put = (el, txt) => { if (el && el.textContent !== txt) el.textContent = txt; };
const pop = (el) => { if (!el || RM.matches) return; el.classList.remove("pop"); void el.offsetWidth; el.classList.add("pop"); };
function futNow(s) {
  if (!INST[futId] || INST[futId].key !== "NIFTY|FUT") futId = idOf("NIFTY|FUT");
  return last[futId] ?? (s && s.pos && s.pos.fut_now) ?? (s && s.fut);
}
function setBand(mode, html) {
  const band = $("posband"), box = $("pos");
  if (bandMode !== mode || box.dataset.h !== html) { box.innerHTML = html; box.dataset.h = html; }
  bandMode = mode;
  band.classList.toggle("is-flat", mode === "flat");
  band.classList.toggle("is-receipt", mode === "receipt");
  band.classList.toggle("is-open", mode === "open");
  if (mode !== "open") band.classList.remove("t-up", "t-down", "near");
}
function announce(t) { $("posann").textContent = t; }
function pulseBand() {
  const band = $("posband"), cls = RM.matches ? "enter-rm" : "enter";
  band.classList.remove("enter", "enter-rm"); void band.offsetWidth; band.classList.add(cls);
  clearTimeout(band._t); band._t = setTimeout(() => band.classList.remove(cls), RM.matches ? 5000 : 1300);
}

// ── template ────────────────────────────────────────────────────────────────
function bandTemplate(p, b) {
  const qty = p.qty || p.lots * LOT, dep = p.entry * qty, cap = nil(b.capital) ? 100000 : b.capital;
  const mid = (!nil(p.entry_bid) && !nil(p.entry_ask)) ? (p.entry_bid + p.entry_ask) / 2 : null;
  const fill = mid === null ? "" : `paid <b>${fmt(p.entry)}</b> vs mid ${fmt(mid)} (<b>${sgn(p.entry - mid)}</b> over mid, spread ${fmt(p.entry_ask - p.entry_bid)}) · `;
  const more = Math.max(0, Math.floor((cap - dep) / (p.entry * LOT)));
  return `<div class="pb-open">
  <div class="pb-id">
    <div class="row"><span class="side">LONG</span><span class="k">${p.strike} ${p.rr}</span><span class="rr">${p.rr === "CE" ? "CALLS ▲" : "PUTS ▼"}</span></div>
    <div class="row"><span class="pb-tag" id="pbtag">FRESH ●</span><span class="exp">expiry <b>${dmy(p.expiry)}</b>${p.expiry === (S && S.now || "").slice(0, 10) ? " · <b>0DTE</b>" : ""}</span><span class="pb-frozen" id="pbfrozen"></span></div>
    <div class="pb-fill">${fill}in at <b>${p.time_in}</b>${nil(p.spot_in) ? "" : ` · spot <b>${fmt(p.spot_in, 1)}</b>`}${p.why ? ` · ${(p.why || "").replace(/^spot /, "")}` : ""}</div>
  </div>
  <div class="pb-pnl">
    <span class="lbl">Unrealised P&amp;L · ${p.lots} lots × ${qty} qty</span>
    <b class="pb-big" id="pospnl">—</b>
    <span class="pb-sec" id="pospts">—</span><span class="pb-sec" id="posret">—</span>
  </div>
  <div class="pb-rail">
    <div class="pb-cap" id="railcap">—</div>
    <div class="rail" id="rail"><i class="seg" id="railseg"></i><i class="mk stop"></i><i class="mk mid" id="railmid"></i><i class="mk arm" id="railarm"></i><i class="now" id="railnow"></i></div>
    <div class="rail-lab"><span class="l" id="raill"></span><span class="m" id="railm"></span><span class="r" id="railr"></span></div>
    <div class="pb-lock" id="pblock" hidden></div>
    <div class="pb-chips" id="pbchips"></div>
  </div>
  <div class="pb-path">
    <div class="trip"><span>Entry<b>${fmt(p.entry)}</b></span><i>→</i><span class="now">Now<b id="poslast">—</b></span><i>→</i><span class="best">Best<b id="pospeak">—</b></span></div>
    <canvas id="posline" height="72"></canvas>
  </div>
  <div class="tiles pb-size">
    <div class="tile hi"><span class="l">Lots</span><b>${p.lots}</b><small>× ${LOT} per lot</small></div>
    <div class="tile hi"><span class="l">Quantity</span><b>${qty.toLocaleString("en-IN")}</b><small>${p.slices > 1 ? `${p.slices} freeze slices` : "one order"}</small></div>
    <div class="tile"><span class="l">Capital deployed</span><b>${inr(dep)}</b><small>${Math.round(dep / cap * 100)}% of ${inr(cap)}</small><div class="util"><i style="width:${clamp(dep / cap * 100, 0, 100)}%"></i></div></div>
    <div class="tile"><span class="l">Cash left</span><b>${inr(cap - dep)}</b><small>${more} more lot${more === 1 ? "" : "s"} affordable</small></div>
  </div>
  <div class="tiles pb-greeks">
    <div class="tile"><span class="l">Delta</span><b id="gdelta">—</b><small id="gdelta2">at entry ${fmt(p.delta_in, 2)}</small></div>
    <div class="tile"><span class="l">Theta / min</span><b id="gtheta">—</b><small id="gtheta2">—</small></div>
    <div class="tile"><span class="l">IV</span><b id="giv">—</b><small id="giv2">at entry ${fmt(p.iv_in, 1)}</small></div>
  </div>
  <div class="tiles pb-clock">
    <div class="tile"><span class="l">In trade</span><b id="poshold">—</b><small id="poshold2">since ${p.time_in}</small></div>
    <div class="tile" id="exittile"><span class="l">Exit clock</span><b id="posexit">—</b><small>flat at ${p.time_exit || (S && S.flatten_at) || "15:35"}</small></div>
  </div></div>`;
}
function bindBand() {
  for (const id of ["pbtag", "pbfrozen", "pospnl", "pospts", "posret", "railcap", "rail", "railseg", "railmid", "railarm", "railnow", "raill", "railm", "railr",
                    "pblock", "pbchips", "poslast", "pospeak", "posline", "gdelta", "gdelta2", "gtheta", "gtheta2", "giv", "giv2", "poshold", "poshold2", "posexit", "exittile"]) E[id] = $(id);
}

// ── per state frame (4 Hz) ─────────────────────────────────────────────────
function renderPos(s, now) {
  const p = s.pos;
  document.body.classList.toggle("holding", !!p);
  if (!p) {
    if (prevHad && (s.trades || []).length) {
      const t = s.trades[0];
      receipt = { t, until: Date.now() + 60000 };
      announce(`Sold ${t.lots} × ${t.strike} ${t.rr} at ${fmt(t.exit)}. ${code(t.reason)}. ${sinr(t.pnl_rs)}.`);
    }
    prevHad = false; posKey = ""; pnlBuf.length = 0; tz.cur = tz.cand = ""; st.state = ""; st.rail = null;
    if (receipt && Date.now() < receipt.until) {
      const t = receipt.t, qty = t.qty || t.lots * LOT, hold = nil(t.hold_s) ? hm(t.time_out) - hm(t.time_in) : t.hold_s;
      setBand("receipt", `<div class="pb-receipt"><span class="lbl">CLOSED</span><span class="chip ink">${code(t.reason)}</span>
        <span>${t.strike} ${t.rr} · ${t.lots} lots · ${qty} qty · ${inr(t.entry * qty)} deployed</span><b class="rs ${tone(t.pnl_rs)}">${sinr(t.pnl_rs)}</b>
        <span>${sgn(t.pnl_pts)} pts · ${sgn(nil(t.ret_pct) ? t.pnl_pts / t.entry * 100 : t.ret_pct, 1)}%</span><span class="mist">${t.time_in} → ${t.time_out} (${dur(hold)} held)</span>
        ${t.reason !== code(t.reason) ? `<span class="mist">${t.reason}</span>` : ""}</div>`);
      $("posband").dataset.state = "";
      return;
    }
    receipt = null;
    const b = s.book || {}, bo = s.blackout || {}, lt = (s.trades || [])[0];
    setBand("flat", `<div class="pb-flat"><span class="lbl">FLAT</span><span>${inr(nil(b.capital) ? 100000 : b.capital)} ready</span>
      <span>${b.trades ? `${b.trades} trade${b.trades > 1 ? "s" : ""} today, ${b.wins} won` : "No trades yet today"}</span>
      <span class="sp">${bo.on ? `<span class="chip">entries paused · ${bo.why || "data gap"}</span> ` : ""}${lt ? `Last: ${code(lt.reason)} ${sinr(lt.pnl_rs)} at ${lt.time_out}` : ""}</span></div>`);
    $("posband").dataset.state = "";
    return;
  }
  const key = p.key + p.time_in;
  const ltp = last[p.id] ?? p.last;
  if (key !== posKey) {
    const fresh = prevHad === false;               // we saw it flat, then saw it open: a real entry
    posKey = key; pnlBuf.length = 0; receipt = null; tz.cur = tz.cand = ""; bandMode = "";
    st.state = "fresh"; st.nearSince = 0; st.nearOff = 0; st.peakSeen = -1e9; st.bestSeen = -1e9; st.rail = null;
    setBand("open", bandTemplate(p, s.book || {}));
    bindBand();
    $("posband").dataset.state = "fresh";
    if (fresh) { pulseBand(); announce(`Bought ${p.lots} lots, ${p.qty || p.lots * LOT} quantity, of ${p.strike} ${p.rr} at ${fmt(p.entry)}, ${inr(p.entry * (p.qty || p.lots * LOT))} deployed.`); }
  }
  prevHad = true;
  if (isStale()) { $("posband").dataset.state = "stale"; return; }     // frozen: keep the last good picture (D4)
  pnlBuf.push([now, ltp - p.entry]);
  if (pnlBuf.length > 3000) pnlBuf.splice(0, pnlBuf.length - 3000);
  // best premium since entry (peak_pts from the engine; pop the tile when it improves)
  const best = Math.max(p.entry + (p.peak_pts || 0), p.best_prem || 0, ltp);
  put(E.pospeak, fmt(best));
  if ((p.peak_pts || 0) > st.peakSeen + 1e-9) { if (st.peakSeen > -1e9) pop(E.pospeak); st.peakSeen = p.peak_pts || 0; }
  put(E.poshold, dur(p.hold_s));
  // exit clock: seconds to time_exit on the engine's clock
  const tx = hm(p.time_exit || s.flatten_at || "15:35"), left = tx - now;
  put(E.posexit, left <= 0 ? "closing" : mmss(left));
  const ec = "tile" + (left <= 120 ? " red" : left <= 600 ? " amber" : "");
  if (E.exittile.className !== ec) E.exittile.className = ec;
  // greeks now vs entry
  const g = p.g || {}, qty = p.qty || p.lots * LOT;
  put(E.gdelta, nil(g.delta) ? "—" : fmt(Math.abs(g.delta), 2));
  put(E.gdelta2, nil(g.delta) || nil(p.delta_in) ? `at entry ${fmt(Math.abs(p.delta_in || 0), 2)}` : `${sgn(Math.abs(g.delta) - Math.abs(p.delta_in), 2)} since entry (${fmt(Math.abs(p.delta_in), 2)})`);
  put(E.gtheta, nil(g.theta_min) ? "—" : `${sgn(g.theta_min, 3)}`);
  put(E.gtheta2, nil(g.theta_min) ? "—" : `${inr(g.theta_min * qty)}/min · ${inr(g.theta_min * qty * 60)}/hr at this size`);
  put(E.giv, nil(g.iv) ? "—" : fmt(g.iv, 1));
  put(E.giv2, nil(g.iv) || nil(p.iv_in) ? `at entry ${fmt(p.iv_in, 1)}` : `${sgn(g.iv - p.iv_in, 1)} pts since entry (${fmt(p.iv_in, 1)})`);
  E.giv.className = nil(g.iv) || nil(p.iv_in) ? "" : tone(g.iv - p.iv_in);           // IV up helps a long option
  E.gdelta.className = nil(g.delta) || nil(p.delta_in) ? "" : tone(Math.abs(g.delta) - Math.abs(p.delta_in));
  const rl = renderRail(s, p);                   // {near, locked, lock}
  // the profit lock (engine lock_* fields): one gold row under the rail
  let lk = "";
  if (p.lock_armed) {
    lk = `<span class="lk">LOCK ${sgn(p.lock_pct, 0)} %${nil(p.lock_floor) ? "" : ` <small>· floor ${fmt(p.lock_floor)}</small>`}</span>` +
      `<span>${nil(p.lock_trail_pct) ? "" : `trails ${fmt(p.lock_trail_pct, 0)} % off the best`}${nil(p.best_prem) ? "" : ` ${fmt(p.best_prem)}`}${p.lock_armed_at ? ` · armed ${p.lock_armed_at}` : ""}</span>`;
  } else if (!nil(p.lock_pct)) {
    lk = `<span class="lk armed-not">LOCK ARMS AT ${sgn(p.lock_pct, 0)} %</span><span>${nil(p.ret_pct) ? "" : `premium ${sgn(p.ret_pct, 1)} % now`}</span>`;
  }
  if (E.pblock.dataset.h !== lk) { E.pblock.innerHTML = lk; E.pblock.dataset.h = lk; E.pblock.hidden = !lk; }
  const bo = s.blackout || {}, chips = [];
  if (p.pending) chips.push(`<span class="chip warn">exit pending · ${code(p.pending.reason)} · waiting for a fresh quote</span>`);
  if (p.gap) chips.push(`<span class="chip">held contract had no quote for a while</span>`);
  if (bo.on) chips.push(`<span class="chip">entries paused · ${bo.why || "data gap"}${bo.exits_ok ? "" : " · stops wait for clean data"}</span>`);
  const ch = chips.join("");
  if (E.pbchips.dataset.h !== ch) { E.pbchips.innerHTML = ch; E.pbchips.dataset.h = ch; }
  st.rail = { near: rl.near, locked: rl.locked || !!p.lock_armed, lock: rl.lock };
  livePos(ltp, true);
}

// the rail: unchanged D-124 semantics (u = (spot − stop)·dir, r = u / trail); returns the rail verdict
function renderSpotRail(s, p) {
  const d = (s.params || {}).spot_trail || p.d_star, stop = p.stop_spot, dir = p.dir || (p.rr === "CE" ? 1 : -1);
  const sp = spotNow(s), rail = E.rail;
  if (nil(stop) || nil(d) || nil(sp) || d <= 0) { E.railcap.innerHTML = `<span class="lv">Stop not set yet</span>`; return { near: false, locked: false, lock: null }; }
  const best = nil(p.best_spot) ? p.spot_in : p.best_spot, trailing = (best - p.spot_in) * dir > 0;
  const u = (sp - stop) * dir, r = u / d, span = Math.max(d, (best - stop) * dir);
  put(E.raill, `${trailing ? "TRAIL" : "STOP"} ${fmt(stop, 1)}`); put(E.railm, ""); put(E.railr, `best spot ${fmt(best, 1)}`);
  const x = clamp(u / span, 0, 1) * 100;
  E.railseg.style.width = x + "%"; E.railnow.style.left = x + "%";
  E.railmid.style.display = "none"; E.railarm.style.display = "none";
  // near with hysteresis: on at r ≤ 0.25, off only at r ≥ 0.35 held for 1 s (a 1.2-pt dead band on a 12-pt trail)
  const nowMs = Date.now();
  if (r <= 0.25) { st.nearSince = st.nearSince || nowMs; st.nearOff = 0; }
  else if (r >= 0.35) { st.nearOff = st.nearOff || nowMs; if (nowMs - st.nearOff >= 1000) st.nearSince = 0; }
  const near = !!st.nearSince, warn = r <= 0.5;
  rail.classList.toggle("warn", warn);
  const lock = trailing ? (stop - p.spot_in) * dir : null, locked = lock !== null && lock >= 1;
  if (locked && lock > st.bestSeen + 1e-9) st.bestSeen = lock;
  const h = `${near ? `<span class="near-w">NEAR ${trailing ? "TRAIL" : "STOP"} ⚠</span>` : ""}<b>${fmt(Math.max(0, u), 1)}</b><span class="to">SPOT PTS TO ${trailing ? "TRAIL" : "STOP"}</span>
    <span class="lv">spot ${fmt(sp, 1)} · stop ${fmt(stop, 1)}${r < 1 ? ` · ${Math.round(Math.max(0, r) * 100)}% of the ${fmt(d, 0)}-pt trail left` : ""}</span>${lock === null ? `<span class="lv">trail arms once spot beats ${fmt(p.spot_in, 1)}</span>` : lock >= 1 ? `<span class="lock">locks ${sgn(lock, 1)} spot pts</span>` : lock > -1 ? `<span class="lv">stop at break-even</span>` : `<span class="lv risk">risks ${fmt(-lock, 1)} spot pts below entry</span>`}`;
  if (E.railcap.dataset.h !== h) { E.railcap.innerHTML = h; E.railcap.dataset.h = h; }
  return { near, locked, lock };
}
function renderRail(s, p) {
  if (p.on_spot) return renderSpotRail(s, p);
  // futures-stop books: same picture, futures points
  const d = !nil(p.d_star) ? p.d_star : (s.params || {}).d_star, stop = p.stop_fut, dir = p.dir || (p.rr === "CE" ? 1 : -1);
  const fut = futNow(s);
  if (nil(stop) || nil(d) || nil(fut) || d <= 0) { E.railcap.innerHTML = `<span class="lv">Stop not set yet</span>`; return { near: false, locked: false, lock: null }; }
  const u = (fut - stop) * dir, r = u / d;
  let span, mid = null;
  if (!p.trail) { span = 2 * d; mid = (p.fut_in - stop) * dir; put(E.raill, `STOP ${fmt(stop, 1)}`); put(E.railm, `entry ${fmt(p.fut_in, 1)}`); put(E.railr, `trail arms ${fmt(p.fut_in + dir * d, 1)}`); }
  else { span = Math.max(d, (p.best - stop) * dir); put(E.raill, `TRAIL ${fmt(stop, 1)}`); put(E.railm, ""); put(E.railr, `best ${fmt(p.best, 1)}`); }
  const x = clamp(u / span, 0, 1) * 100;
  E.railseg.style.width = x + "%"; E.railnow.style.left = x + "%";
  E.railmid.style.display = mid === null ? "none" : ""; if (mid !== null) { E.railmid.style.left = clamp(mid / span, 0, 1) * 100 + "%"; E.railm.style.left = E.railmid.style.left; }
  E.railarm.style.display = p.trail ? "none" : "";
  const nowMs = Date.now();
  if (r <= 0.25) { st.nearSince = st.nearSince || nowMs; st.nearOff = 0; }
  else if (r >= 0.35) { st.nearOff = st.nearOff || nowMs; if (nowMs - st.nearOff >= 1000) st.nearSince = 0; }
  const near = !!st.nearSince, lock = p.trail ? (stop - p.fut_in) * dir : null, locked = lock !== null && lock >= 1;
  E.rail.classList.toggle("warn", r <= 0.5);
  const h = `${near ? `<span class="near-w">NEAR ${p.trail ? "TRAIL" : "STOP"} ⚠</span>` : ""}<b>${fmt(Math.max(0, u), 1)}</b><span class="to">FUT PTS TO ${p.trail ? "TRAIL" : "STOP"}</span><span class="lv">futures ${fmt(fut, 1)} · stop ${fmt(stop, 1)}${r < 1 ? ` · ${Math.round(Math.max(0, r) * 100)}% of the ${fmt(d, 0)}-pt stop left` : ""}</span>${lock === null ? "" : lock >= 1 ? `<span class="lock">locks ${sgn(lock, 1)} fut pts</span>` : lock > -1 ? `<span class="lv">stop at break-even</span>` : `<span class="lv risk">risks ${fmt(-lock, 1)} fut pts below entry</span>`}`;
  if (E.railcap.dataset.h !== h) { E.railcap.innerHTML = h; E.railcap.dataset.h = h; }
  return { near, locked, lock };
}

// ── per tick (≤4 Hz) ───────────────────────────────────────────────────────
let liveAt = 0, liveQ = null, liveT = 0;
function livePos(ltp, force) {
  const p = S && S.pos; if (!p || !E.pospnl || !E.pospnl.isConnected || isStale()) return;
  const t = performance.now();
  if (!force && t - liveAt < 250) {                 // text changes at most 4× a second
    liveQ = ltp; if (!liveT) liveT = setTimeout(() => { liveT = 0; livePos(liveQ, true); }, 250); return;
  }
  liveAt = t;
  const qty = p.qty || p.lots * LOT, pts = ltp - p.entry, rs = pts * qty;
  put(E.pospnl, sinr(rs)); put(E.pospts, `${sgn(pts)} pts`); put(E.posret, p.entry ? `${sgn(pts / p.entry * 100, 1)}%` : "");
  put(E.poslast, fmt(ltp));
  // tone with hysteresis: the band takes a colour only after 3 s beyond ±0.5 pt, or at once beyond ±1.5 pt
  const side = pts > 0.5 ? "up" : pts < -0.5 ? "down" : "";
  const nowMs = Date.now();
  if (side !== tz.cand) { tz.cand = side; tz.since = nowMs; }
  if (tz.cand !== tz.cur && (nowMs - tz.since >= 3000 || Math.abs(pts) >= 1.5)) tz.cur = tz.cand;   // the 3 s wait only matters near breakeven
  if ((tz.cur === "up" && pts <= 0) || (tz.cur === "down" && pts >= 0)) tz.cur = "";   // never show a colour the sign contradicts
  // state of the trade, by priority: pending > near > locked > profit/loss > fresh
  const rl = st.rail || {}, fresh = (p.hold_s || 0) < 20 && tz.cur === "";
  const state = p.pending ? "pending" : rl.near ? "near" : rl.locked ? "locked" : tz.cur === "up" ? "profit" : tz.cur === "down" ? "loss" : fresh ? "fresh" : "flat";
  const band = $("posband");
  if (band.dataset.state !== state) { band.dataset.state = state; if (state === "locked" || state === "near") pop(E.pbtag); }
  band.classList.toggle("t-up", tz.cur === "up"); band.classList.toggle("t-down", tz.cur === "down"); band.classList.toggle("near", !!rl.near);
  const lockTag = p.lock_armed ? `LOCKED ${sgn(p.lock_pct, 0)} %${nil(p.lock_floor) ? "" : ` · FLOOR ${fmt(p.lock_floor)}`}` : `LOCKED ${sgn(rl.lock, 1)} ${p.on_spot === false ? "FUT" : "SPOT"} PTS`;
  put(E.pbtag, { pending: `EXIT PENDING · ${code((p.pending || {}).reason)}`, near: `NEAR ${rl.lock !== null && rl.lock !== undefined ? "TRAIL" : "STOP"} ⚠`,
                 locked: lockTag, profit: "IN PROFIT ▲", loss: "IN LOSS ▼", fresh: "FRESH ●", flat: "AT ENTRY ●" }[state]);
  // header: equity marked to market, one number with the band
  const b = (S && S.book) || {};
  $("caplabel").textContent = "Equity";
  $("cap").textContent = inr((b.capital || 0) + rs);
  const dp = `<span class="${tone(rs)}">${sinr(rs)} open</span><br><span class="mist">${sinr(b.pnl_rs || 0)} booked</span>`;
  if ($("daypnl").dataset.h !== dp) { $("daypnl").innerHTML = dp; $("daypnl").dataset.h = dp; }
  $("daypnl").className = "";
  drawPosLine(p);
}

// ── canvases ───────────────────────────────────────────────────────────────
function fit(cv) {
  const r = window.devicePixelRatio || 1, w = cv.clientWidth, h = cv.clientHeight || +cv.getAttribute("height");
  if (cv.width !== Math.round(w * r) || cv.height !== Math.round(h * r)) { cv.width = Math.round(w * r); cv.height = Math.round(h * r); }
  const g = cv.getContext("2d"); g.setTransform(r, 0, 0, r, 0, 0); return [g, w, h];
}
function alpha(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }

// premium path since entry: dashed zero line = entry, best marked gold, lock floor (if armed) dashed gold, last point lit
function drawPosLine(p) {
  const cv = E.posline; if (!cv || !cv.isConnected) return; const [g, w, h] = fit(cv); g.clearRect(0, 0, w, h);
  if (pnlBuf.length < 2) return;
  const t0 = pnlBuf[0][0], t1 = pnlBuf[pnlBuf.length - 1][0] || t0 + 1;
  let mx = 1, bi = 0; pnlBuf.forEach((x, i) => { if (Math.abs(x[1]) > mx) mx = Math.abs(x[1]); if (x[1] > pnlBuf[bi][1]) bi = i; });
  const floor = p && p.lock_armed && !nil(p.lock_floor) ? p.lock_floor - p.entry : null;
  if (floor !== null && Math.abs(floor) > mx) mx = Math.abs(floor);
  const X = (t) => (t - t0) / Math.max(t1 - t0, 1) * (w - 70) + 2, Y = (v) => h / 2 - v / mx * (h / 2 - 8);
  const lastV = pnlBuf[pnlBuf.length - 1][1], col = lastV >= 0 ? C.up : C.down;
  g.strokeStyle = C.line; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(0, h / 2); g.lineTo(w - 66, h / 2); g.stroke(); g.setLineDash([]);
  g.beginPath(); pnlBuf.forEach(([t, v], i) => i ? g.lineTo(X(t), Y(v)) : g.moveTo(X(t), Y(v)));
  g.strokeStyle = col; g.lineWidth = 2.5; g.stroke();
  g.lineTo(X(t1), h / 2); g.lineTo(X(t0), h / 2); g.closePath();
  const grad = g.createLinearGradient(0, 0, 0, h); grad.addColorStop(0, alpha(col, .35)); grad.addColorStop(1, alpha(col, .02)); g.fillStyle = grad; g.fill();
  if (floor !== null) {                             // the locked floor: a gold dashed line at lock_floor − entry
    g.strokeStyle = "#ffd166"; g.setLineDash([5, 4]); g.lineWidth = 1.5; g.beginPath(); g.moveTo(0, Y(floor)); g.lineTo(w - 66, Y(floor)); g.stroke(); g.setLineDash([]);
    g.fillStyle = "#ffd166"; g.font = `600 13px ${NUMF}`; g.fillText(`floor ${sgn(floor, 2)}`, w - 62, Y(floor) + 5);
  }
  const [bt, bv] = pnlBuf[bi];
  if (bv > 0.5) { g.fillStyle = "#ffd166"; g.beginPath(); g.arc(X(bt), Y(bv), 4, 0, 7); g.fill(); g.font = `600 13px ${NUMF}`; const lx = X(bt) > w - 150; g.textAlign = lx ? "right" : "left"; g.fillText(`best ${sgn(bv, 2)}`, X(bt) + (lx ? -7 : 7), Math.max(12, Y(bv) - 6)); g.textAlign = "left"; }
  g.fillStyle = col; g.beginPath(); g.arc(X(t1), Y(lastV), 4, 0, 7); g.fill();
  let ly = clamp(Y(lastV) + 5, 13, h - 4);
  if (floor !== null && Math.abs(Y(floor) + 5 - ly) < 14) ly = Y(floor) + 5 + (Y(lastV) <= Y(floor) ? -14 : 14);   // never on top of the floor label
  g.fillStyle = col; g.font = `700 14px ${NUMF}`; g.fillText(sgn(lastV, 2), w - 62, clamp(ly, 13, h - 4));
  g.fillStyle = C.mist; g.font = `500 13px ${NUMF}`; g.fillText("entry", w - 62, h / 2 + 16);
}

function drawTrace(s) {
  const cv = $("futline"); const [g, w, h] = fit(cv); g.clearRect(0, 0, w, h);
  if (futBuf.length < 2) { $("tracehint").textContent = ""; return; }
  const t1 = futBuf[futBuf.length - 1][0], t0 = t1 - 300;
  const lv = [];
  if (s.episode) lv.push([s.episode.fut0, C.beacon, "move began"]);
  if (s.pos) {
    lv.push([s.pos.fut_in, C.ink, "entry"]);
    if (!nil(s.pos.stop_fut)) lv.push([s.pos.stop_fut, C.down, "stop"]);
    // D-124: a spot book's stop is on spot; draw it on the futures trace at the same distance from the entry
    else if (s.pos.on_spot && !nil(s.pos.stop_spot) && !nil(s.pos.spot_in)) lv.push([s.pos.fut_in + (s.pos.stop_spot - s.pos.spot_in), C.down, "stop (spot)"]);
  }
  const ys = futBuf.map(x => x[1]).concat(lv.map(x => x[0]));
  let lo = Math.min(...ys), hi = Math.max(...ys); const pad = Math.max(2, (hi - lo) * .12); lo -= pad; hi += pad;
  const X = (t) => (t - t0) / 300 * (w - 84), Y = (v) => h - 14 - (v - lo) / (hi - lo) * (h - 24);
  if (s.episode) { const ta = t1 - s.episode.age; g.fillStyle = alpha(s.episode.dir > 0 ? C.up : C.down, .08); g.fillRect(X(ta), 0, X(t1) - X(ta), h - 12); }
  g.font = `12px ${NUMF}`;
  for (const [v, col, name] of lv) {
    g.strokeStyle = col; g.setLineDash([4, 4]); g.beginPath(); g.moveTo(0, Y(v)); g.lineTo(w - 84, Y(v)); g.stroke(); g.setLineDash([]);
    g.fillStyle = col; g.fillText(name, w - 80, Y(v) + 4);
  }
  g.beginPath(); futBuf.forEach(([t, v], i) => i ? g.lineTo(X(t), Y(v)) : g.moveTo(X(t), Y(v)));
  g.strokeStyle = C.ink; g.lineWidth = 1.6; g.stroke();
  const [tl, vl] = futBuf[futBuf.length - 1];
  g.fillStyle = C.ink; g.beginPath(); g.arc(X(tl), Y(vl), 3, 0, 7); g.fill();
  g.fillStyle = C.mist; g.fillText(fmt(hi, 0), w - 80, 12); g.fillText(fmt(lo, 0), w - 80, h - 16);
  const d = s.domino || {}, fb = s.fut_book || {}, lg = s.lag || {}, bk = s.bank || {};
  const rg = s.regime || {}, ld = s.ledger || {};
  const RW = { DIRECTIONAL: "a clean move the basket confirms", BREAKOUT: "escaping the recent range", EXHAUSTION: "stretched from VWAP and stalling — don't chase",
               RANGE: "back-and-forth, no progress", COMPRESSION: "quiet and contracting", UNCERTAIN: "progress without breadth, or mixed", WARMING: "learning today's scale" };
  $("regime").innerHTML = rg.state ? `Market: <b class="rg-${rg.state}">${rg.text}</b> — ${RW[rg.state] || ""}.${ld.today ? ` Candidates today ${ld.today} (${ld.followed} being followed).` : ""}` : "";
  $("tracehint").textContent = `15-s move ${sgn(d.r15, 1)} pts, normal ${fmt(d.sigma15, 1)} · Bank Nifty z ${sgn(bk.z, 1)} · lag today ${lg.median === null || lg.median === undefined ? "—" : fmt(lg.median, 1) + " s (" + lg.n + ")"}`;
  $("futbook").innerHTML = `Futures book: <b>${fmt(fb.sbo, 0)}</b> buy orders v <b>${fmt(fb.sso, 0)}</b> sell, order imbalance <b class="${tone(fb.imb_o)}">${sgn(fb.imb_o, 2)}</b>, whole book <b class="${tone(fb.imb_t)}">${sgn(fb.imb_t, 2)}</b> (${sgn(fb.imb_t_chg, 2)} in 30 s). Bid orders <span class="c-${fb.bid_ord_cls}">${SH[fb.bid_ord_cls] || "—"}</span>, ask orders <span class="c-${fb.ask_ord_cls}">${SH[fb.ask_ord_cls] || "—"}</span>. Book→price <b>${sgn(fb.lead, 2)}</b>.`;
}

function drawOI(s) {
  const cv = $("oi"); const rows = (s.chain || []).slice().sort((a, b) => b[0] - a[0]);
  cv.height = Math.max(220, rows.length * 22 + 20);
  const [g, w, h] = fit(cv); g.clearRect(0, 0, w, h);
  const pr = s.pressure || {};
  $("pcr").textContent = nil(pr.pcr) ? "" : `put/call ${fmt(pr.pcr, 2)}, chain ${fmt(pr.chain_age, 0)} s old`;
  if (!rows.length) { g.fillStyle = C.mist; g.font = `14px ${NUMF}`; g.fillText("Waiting for the option chain", 10, 24); return; }
  const mid = w / 2, half = mid - 34, mx = Math.max(...rows.map(r => Math.max(r[1], r[2])), 1);
  const rowH = (h - 20) / rows.length, top = 10;
  const walls = new Set([...(pr.walls_up || []), ...(pr.walls_dn || [])].map(x => x[0]));
  const Y = (k) => { // strike -> y by interpolation over the rows (rows are descending)
    if (k >= rows[0][0]) return top + rowH / 2; if (k <= rows[rows.length - 1][0]) return top + rowH * (rows.length - .5);
    for (let i = 0; i < rows.length - 1; i++) if (k <= rows[i][0] && k >= rows[i + 1][0]) return top + rowH * (i + .5 + (rows[i][0] - k) / (rows[i][0] - rows[i + 1][0]));
    return top; };
  g.font = `12px ${NUMF}`; g.textAlign = "center";
  rows.forEach(([k, ce, pe, cec, pec], i) => {
    const y = top + i * rowH, bh = Math.max(4, rowH - 7), isW = walls.has(k);
    g.fillStyle = alpha(C.down, isW ? .95 : .45); const pw = pe / mx * half; g.fillRect(mid - 30 - pw, y + 3, pw, bh);   // puts: PE colour
    g.fillStyle = alpha(C.up, isW ? .95 : .45); const cw = ce / mx * half; g.fillRect(mid + 30, y + 3, cw, bh);           // calls: CE colour
    g.fillStyle = C.ink; if (pec) { g.fillRect(mid - 30 - Math.abs(pec) / mx * half, y + rowH - 4, Math.abs(pec) / mx * half, 2); }
    if (cec) { g.fillRect(mid + 30, y + rowH - 4, Math.abs(cec) / mx * half, 2); }
    g.fillStyle = isW ? C.ink : C.mist; g.fillText(k, mid, y + rowH / 2 + 4);
  });
  const spot = s.spot || s.fut;
  if (!nil(spot)) {
    const y = Y(spot); g.strokeStyle = C.beacon; g.lineWidth = 1.5; g.beginPath(); g.moveTo(4, y); g.lineTo(w - 4, y); g.stroke();
    g.fillStyle = C.beacon; g.textAlign = "left"; g.fillText(`spot ${fmt(spot, 1)}`, 6, y - 4);
  }
  const gx = s.gex || {};
  if (gx.ok) {                                   // dealer-gamma markers: flip (dashed) and max pain (dotted)
    const mark = (k, dash, label, al) => { if (nil(k) || !rows.length) return; const y = Y(k);
      g.save(); g.setLineDash(dash); g.strokeStyle = C.ink; g.lineWidth = 1; g.beginPath(); g.moveTo(4, y); g.lineTo(w - 4, y); g.stroke(); g.restore();
      g.fillStyle = C.ink; g.textAlign = al; g.fillText(label, al === "right" ? w - 6 : 6, y - 3); };
    mark(gx.flip, [6, 4], `gamma flip ${fmt(gx.flip, 0)}`, "right"); mark(gx.max_pain, [2, 3], `max pain ${fmt(gx.max_pain, 0)}`, "left");
  }
  g.textAlign = "left"; g.fillStyle = C.mist; g.fillText("put OI: support", 4, h - 2); g.textAlign = "right"; g.fillText("call OI: resistance", w - 4, h - 2);
  const gw = { DAMPEN: "dealer hedging leans against moves, so spikes tend to fade", AMPLIFY: "dealer hedging leans with moves, so spikes can run", MIXED: "dealer hedging is balanced" };
  $("gex").innerHTML = gx.ok
    ? `Dealer gamma: <b class="${gx.regime === "AMPLIFY" ? "up" : gx.regime === "DAMPEN" ? "down" : ""}">${gx.regime.toLowerCase()}</b> (balance ${sgn(gx.balance, 2)}), ${gw[gx.regime]}. Flip ${nil(gx.flip) ? "none within 3%" : fmt(gx.flip, 0)}, call gamma wall ${nil(gx.call_wall) ? "—" : fmt(gx.call_wall, 0)}, put gamma wall ${nil(gx.put_wall) ? "—" : fmt(gx.put_wall, 0)}, max pain ${fmt(gx.max_pain, 0)}. <span class="c-0">Assumes dealers are long calls and short puts; shown as evidence only.</span>`
    : `Dealer gamma: ${gx.why || "warming"}.`;
  const f = s.force || {}, words = { "VACUUM": "sellers vanished, it should run", "BREAK-IMMINENT": "about to break", "WEAKENING": "weakening", "HOLD-STRONG": "holding firm", "TESTING": "being tested", "IDLE": "no level within 5 points", "BROKE": "broke", "REJECTED": "rejected the attack", "LEFT": "price left the level" };
  // colour = which way price should go: the attack wins (dir) or the level holds (−dir); dir +1 = resistance above
  const fwin = ["VACUUM", "BREAK-IMMINENT", "BROKE"].includes(f.verdict) ? 1 : ["HOLD-STRONG", "REJECTED"].includes(f.verdict) ? -1 : 0;
  const fcls = nil(f.dir) ? "" : tone(f.dir * fwin);
  $("force").innerHTML = f.name ? `Futures at <b>${f.name}</b> (${fmt(f.level, 0)}): <b class="${fcls}">${words[f.verdict] || f.verdict}</b>. Refill ${fmt(f.rho, 2)}, pulled ${fmt(f.pi, 2)}.`
    : `Level check: ${words[f.verdict] || f.verdict || "—"}.${f.last ? ` Last: ${f.last.name} ${words[f.last.outcome] || f.last.outcome} after ${fmt(f.last.dur, 0)} s.` : ""} Room up ${pr.dest_up ? fmt(pr.dest_up.room, 0) + " pts" : "open"}, down ${pr.dest_dn ? fmt(pr.dest_dn.room, 0) + " pts" : "open"}.`;
}

// ── the Triangle ───────────────────────────────────────────────────────────
const anim = { push: 0, crowd: 0, fresh: .35, rot: 0, glow: 0, t: performance.now(), beads: {} };

function frame(tms) {
  const dt = Math.min(.1, (tms - anim.t) / 1000); anim.t = tms;
  if (S) drawTriangle(dt, tms);
  requestAnimationFrame(frame);
}

function drawTriangle(dt, tms) {
  const cv = $("tri"); const [g, w, h] = fit(cv); g.clearRect(0, 0, w, h);
  const c = corners(S), k = 1 - Math.exp(-dt * 6);
  for (const n of ["push", "crowd", "fresh"]) anim[n] += (clamp(c[n], 0, 1.35) - anim[n]) * k;
  const near = clamp(Math.min(anim.push, anim.crowd, c.ep ? anim.fresh : 0), 0, 1.2);
  anim.glow += ((S.pos ? 0.1 : c.closed ? 1 : near * near) - anim.glow) * k;   // holding: the triangle is background
  anim.rot += dt * (0.04 + 0.9 * near * near);
  const col = c.dir > 0 ? C.up : C.down;
  const cx = w / 2, cy = h * .52, R = Math.min(w, h) * .21;
  const ang = [-Math.PI / 2, Math.PI * 5 / 6, Math.PI / 6];
  const P = (a, r) => [cx + Math.cos(a) * r, cy + Math.sin(a) * r];

  // the current: spiral arms that turn faster as the corners converge
  g.lineWidth = 1;
  for (let arm = 0; arm < 5; arm++) {
    g.beginPath();
    for (let i = 0; i <= 70; i++) {
      const r = R * 2.3 * Math.exp(-i * .035), a = anim.rot + arm * Math.PI * 2 / 5 + i * .085;
      const [x, y] = P(a, r); i ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.strokeStyle = alpha(anim.glow > .6 ? C.beacon : C.refill, .05 + .1 * near); g.stroke();
  }
  // sonar rings
  for (let i = 1; i <= 3; i++) { g.beginPath(); g.arc(cx, cy, R * (.55 * i), 0, 7); g.strokeStyle = alpha(C.line, .5); g.stroke(); }

  // the threshold triangle (dashed) and the market's triangle (filled)
  g.setLineDash([6, 6]); g.beginPath(); ang.forEach((a, i) => { const [x, y] = P(a, R); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath();
  g.strokeStyle = alpha(C.ink, .45); g.lineWidth = 1.2; g.stroke(); g.setLineDash([]);
  const fr = [anim.push, anim.crowd, anim.fresh];
  g.beginPath(); ang.forEach((a, i) => { const [x, y] = P(a, R * Math.max(.04, fr[i])); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath();
  const fillCol = anim.glow > .85 ? C.beacon : col;
  g.fillStyle = alpha(fillCol, .14 + .22 * near); g.fill(); g.strokeStyle = alpha(fillCol, .9); g.lineWidth = 2; g.stroke();

  // the eye
  const er = R * (.12 + .32 * anim.glow);
  const grd = g.createRadialGradient(cx, cy, 0, cx, cy, er * 2.2);
  grd.addColorStop(0, alpha(C.beacon, .2 + .75 * anim.glow)); grd.addColorStop(.45, alpha(C.beacon, .12 * anim.glow + .03)); grd.addColorStop(1, alpha(C.beacon, 0));
  g.fillStyle = grd; g.beginPath(); g.arc(cx, cy, er * 2.2, 0, 7); g.fill();

  // one orchestrated moment: the entry shock-wave
  const since = (tms - flashAt) / 1000;
  if (since < 1.6 && !RM.matches && !S.pos) { g.beginPath(); g.arc(cx, cy, R * (.3 + since * 1.4), 0, 7); g.strokeStyle = alpha(C.beacon, .8 * (1 - since / 1.6)); g.lineWidth = 3; g.stroke(); }

  // corner labels
  const d0 = S.domino || {}, p = S.params || { m_star: 2, s_star: .5 };
  const lab = c.spot ? [
    ["Break", c.warming ? "range warming" : `Nifty ${fmt(c.sp, 1)} vs ${c.dir > 0 ? "high " + fmt(c.hi, 1) : "low " + fmt(c.lo, 1)}`],
    ["Swing", c.warming ? "—" : c.free ? "free to trade" : "same swing as last trade"],
    ["Data", nil(c.age) ? "—" : c.age <= 5 ? `spot ${fmt(c.age, 1)} s fresh` : `spot ${fmt(c.age, 0)} s old`],
  ] : [
    ["Push", `futures ${sgn((d0.z || 0) * c.dir, 1)} of ${p.m_star}`],
    ["Together", `${pct(c.dir > 0 ? d0.S_up : d0.S_dn)} of ${Math.round(p.s_star * 100)}% weight`],
    ["Fresh", c.ep ? (nil(S.late) ? "—" : S.late < 1 ? `${Math.round((1 - S.late) * 100)}% of room left` : "too late") : "no move yet"],
  ];
  g.textAlign = "center";
  ang.forEach((a, i) => {
    const [x, y] = P(a, R + 30), ok = fr[i] >= 1 && (i < 2 || c.ep);
    g.font = `700 ${Math.max(14, R * .085)}px ${NUMF}`; g.fillStyle = ok ? C.beacon : C.ink; g.fillText(lab[i][0], x, y + (i === 0 ? -10 : 6));
    g.font = `500 ${Math.max(12, R * .06)}px ${NUMF}`; g.fillStyle = ok ? C.beacon : C.mist; g.fillText(lab[i][1], x, y + (i === 0 ? 8 : 24));
  });

  // the heavyweights orbit and are pulled in when they join the move
  const tiles = (S.tiles || []).slice().sort((a, b) => b.w - a.w), n = tiles.length;
  const first = S.episode && S.episode.first;
  tiles.forEach((t, j) => {
    const pull = clamp(((t.z || 0) * c.dir) / 2, 0, 1);
    const b = anim.beads[t.sym] || (anim.beads[t.sym] = { pull: 0 });
    b.pull += (pull - b.pull) * k;
    const a = anim.rot * .35 + j * Math.PI * 2 / n - Math.PI / 2;
    const [x, y] = P(a, R * (2.02 - .52 * b.pull));
    const rad = Math.max(3, Math.sqrt(t.w) * R * .032);
    const mv = t.m || 0, bc = mv > 0 ? C.up : mv < 0 ? C.down : C.mist;
    const strength = clamp(Math.abs(t.z || 0) / 2, .2, 1);
    if (b.pull > .3) { g.beginPath(); g.moveTo(x, y); const [x2, y2] = P(a, R * (2.02 - .52 * b.pull) + rad * 3); g.lineTo(x2, y2); g.strokeStyle = alpha(bc, .4 * b.pull); g.lineWidth = rad * .9; g.stroke(); }
    g.beginPath(); g.arc(x, y, rad, 0, 7); g.fillStyle = alpha(bc, .25 + .7 * strength); g.fill();
    if (t.sym === first) { g.strokeStyle = C.beacon; g.lineWidth = 2; g.stroke(); }
    if (t.w >= 3.3 || t.sym === first) { g.font = `600 ${Math.max(11, R * .05)}px ${NUMF}`; g.fillStyle = t.sym === first ? C.beacon : C.ink; g.fillText(t.sym, x, y - rad - 5); }
  });
  g.textAlign = "left";
}

// ── straddle watch ─────────────────────────────────────────────────────────
// A FIXED strike's CE+PE (the live ATM re-centres and makes the usual straddle chart jump).
// The chart: the straddle (ink), what theta alone would have done to it since the anchor
// (dashed), its VWAP, every spike (gold) and every ATM roll (blue). The leg that carries a
// spike — rising delta, price moving faster than theta — is the gamma leg.
let swSig = "";
function renderStraddle(s, now) {
  const w = s.straddle_watch;
  const hint = $("swhint"), stateEl = $("swstate"), legsEl = $("swlegs"), tb = $("swt").querySelector("tbody");
  if (!w || nil(w.K)) {
    hint.textContent = ""; stateEl.textContent = "Waiting for the ATM straddle"; legsEl.innerHTML = ""; tb.innerHTML = "";
    drawStraddle(null); return;
  }
  hint.innerHTML = `strike <b>${w.K}</b> since ${w.since || "—"}${s.atm !== w.K ? ` · live ATM ${s.atm}` : ""} · straddle <b>${fmt(w.px, 1)}</b> from ${fmt(w.open_px, 1)}${nil(w.vwap) ? "" : `, VWAP ${fmt(w.vwap, 1)}`}`;
  const L = w.legs || {}, sp = w.spike;
  legsEl.innerHTML = ["CE", "PE"].map(rr => {
    const l = L[rr] || {};
    const dd = l.ddelta, rising = !nil(dd) && dd >= 0.03;
    return `<div class="sw-leg ${rr.toLowerCase()}${w.leg === rr ? " gamma" : ""}">
      <div class="h"><b>${w.K} ${rr}</b><span class="px ${tone(l.chg5)}">${fmt(l.px, 2)}</span></div>
      <span>5 min <b class="${tone(l.chg5)}">${sgn(l.chg5, 1)}</b></span><span>1 min <b class="${tone(l.chg1)}">${sgn(l.chg1, 2)}</b>${nil(l.acc) ? "" : ` <small class="${tone(l.acc)}">${l.acc > 0 ? "faster" : l.acc < 0 ? "slower" : ""}</small>`}</span>
      <span>delta <b>${fmt(l.delta5, 2)}</b> → <b class="${rising ? "beacon" : ""}">${fmt(l.delta, 2)}</b></span><span>gamma <b>${nil(l.gamma) ? "—" : (l.gamma * 1000).toFixed(2) + "‰"}</b></span>
      <span>theta <b>${nil(l.theta) ? "—" : fmt(l.theta, 3)}</b>/min</span><span>${nil(l.theta) || nil(l.chg5) ? "" : `vs <b class="${tone(l.chg5 - l.theta * 5)}">${sgn(l.chg5 - l.theta * 5, 1)}</b> over theta`}</span>
    </div>`;
  }).join("");
  let txt, cls = "sw-state";
  if (sp) {
    cls += " spike";
    txt = `<b>SPIKE</b> on the ${sp.leg} leg, ${fmt(sp.age, 0)} s in: straddle ran <b>${sgn(sp.peak_excess, 1)}</b> over theta, the ${sp.leg} is <b>${sgn(sp.leg_move, 1)}</b> since it started (delta ${fmt(sp.delta0, 2)} → ${fmt(sp.delta_now, 2)}), futures <b>${sgn(sp.fut_move, 1)}</b> its way.`;
  } else if (w.state === "VOL-SPIKE") {
    txt = `Premium rising on <b>both</b> legs (${sgn(w.excess, 1)} over theta in 5 min): IV, not direction — no leg favoured.`;
  } else if (w.state === "WARMING") {
    txt = `Warming up: five minutes of this strike's prices needed before a spike can be measured.`;
  } else {
    txt = `${w.state === "DECAYING" ? "Decaying as a straddle should" : "Flat"}: <b>${sgn(w.drift_min, 2)}</b>/min over 10 min vs theta <b>${sgn(w.theta_min, 2)}</b>; 5-min change ${sgn(w.chg5, 1)} (${sgn(w.excess, 1)} over theta, spike at +${fmt(w.thr, 1)}).`;
  }
  stateEl.className = cls; stateEl.innerHTML = txt;
  const rows = (w.spikes || []).map(x => `<tr><td>${x.t0}</td><td class="${x.leg === "CE" ? "up" : "down"}">${x.K} ${x.leg}</td><td class="r">+${fmt(x.peak_excess, 1)}</td><td class="r ${tone(x.leg_move)}">${sgn(x.leg_move, 1)}</td><td class="r ${tone(x.fut_move)}">${sgn(x.fut_move, 1)}</td><td>${x.ended ? `${x.ended} · ${x.end_why}` : "<b class=\"beacon\">live</b>"}</td></tr>`)
    .concat((w.shifts || []).slice().reverse().map(x => `<tr class="mist"><td>${x.t}</td><td colspan="5">ATM rolled ${x.from} → ${x.to}: straddle ${fmt(x.s_before, 1)} → ${fmt(x.s_after, 1)}</td></tr>`));
  const sig = rows.join("|");
  if (sig !== swSig) { swSig = sig; tb.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="6" class="empty">No spike yet today. A spike is the straddle gaining more than theta should let it in 5 minutes.</td></tr>`; }
  drawStraddle(w, now);
}

function drawStraddle(w, now) {
  const cv = $("swline"); const [g, wd, h] = fit(cv); g.clearRect(0, 0, wd, h);
  const ser = (w && w.series) || [];
  if (ser.length < 2) { g.fillStyle = C.mist; g.font = `13px ${NUMF}`; g.fillText("Collecting the straddle's path", 10, 24); return; }
  const t1 = ser[ser.length - 1][0], span = Math.max(900, Math.min(7200, t1 - ser[0][0])), t0 = t1 - span;
  const pts = ser.filter(p => p[0] >= t0);
  const ys = [];
  for (const p of pts) { if (!nil(p[1])) ys.push(p[1]); if (!nil(p[4])) ys.push(p[4]); }
  if (w.vwap) ys.push(w.vwap);
  let lo = Math.min(...ys), hi = Math.max(...ys); const pad = Math.max(1, (hi - lo) * .15); lo -= pad; hi += pad;
  const RW = 56, X = (t) => (t - t0) / span * (wd - RW), Y = (v) => h - 16 - (v - lo) / (hi - lo) * (h - 28);
  g.font = `12px ${NUMF}`;
  // spike windows (engine clock, seconds — same clock as the series)
  for (const x of w.spikes || []) {
    if (nil(x.t_s)) continue;
    const xa = X(x.t_s), xb = X(nil(x.end_s) ? t1 : x.end_s);
    if (xb > 0 && xa < wd - RW) { g.fillStyle = alpha(C.beacon, .10); g.fillRect(Math.max(0, xa), 0, Math.min(wd - RW, xb) - Math.max(0, xa), h - 14); }
  }
  // ATM rolls
  for (const x of w.shifts || []) {
    if (nil(x.t_s) || x.t_s < t0) continue;
    g.strokeStyle = alpha(C.refill, .7); g.setLineDash([3, 4]); g.beginPath(); g.moveTo(X(x.t_s), 0); g.lineTo(X(x.t_s), h - 14); g.stroke(); g.setLineDash([]);
    g.fillStyle = C.refill; g.fillText(`${x.from}→${x.to}`, X(x.t_s) + 4, 12);
  }
  // theta-only path
  g.strokeStyle = alpha(C.mist, .8); g.setLineDash([5, 5]); g.lineWidth = 1; g.beginPath();
  let started = false;
  for (const p of pts) { if (nil(p[4])) continue; started ? g.lineTo(X(p[0]), Y(p[4])) : g.moveTo(X(p[0]), Y(p[4])); started = true; }
  g.stroke(); g.setLineDash([]);
  // VWAP
  if (w.vwap) { g.strokeStyle = alpha(C.refill, .55); g.beginPath(); g.moveTo(0, Y(w.vwap)); g.lineTo(wd - RW, Y(w.vwap)); g.stroke(); g.fillStyle = C.refill; g.fillText("vwap " + fmt(w.vwap, 1), wd - RW + 4, Y(w.vwap) + 4); }
  // the straddle
  g.strokeStyle = w.spike ? C.beacon : C.ink; g.lineWidth = 1.8; g.beginPath(); started = false;
  for (const p of pts) { if (nil(p[1])) continue; started ? g.lineTo(X(p[0]), Y(p[1])) : g.moveTo(X(p[0]), Y(p[1])); started = true; }
  g.stroke();
  const lp = pts[pts.length - 1];
  const taken = [];                                   // label rows already used on the right margin
  const place = (y) => { let yy = Math.min(h - 18, Math.max(14, y)); for (let i = 0; i < 4; i++) { if (taken.every(t => Math.abs(t - yy) >= 13)) break; yy += 13; } taken.push(yy); return yy; };
  if (w.vwap) taken.push(Y(w.vwap) + 4);
  if (!nil(lp[1])) { g.fillStyle = w.spike ? C.beacon : C.ink; g.beginPath(); g.arc(X(lp[0]), Y(lp[1]), 3, 0, 7); g.fill(); g.fillText(fmt(lp[1], 1), wd - RW + 4, place(Y(lp[1]) + 4)); }
  if (!nil(lp[4])) { g.fillStyle = C.mist; g.fillText("theta " + fmt(lp[4], 1), wd - RW + 4, place(Y(lp[4]) + 4)); }
  g.fillStyle = C.mist; g.fillText(`${Math.round(span / 60)} min`, 4, h - 3);
}

// ── lower panels ───────────────────────────────────────────────────────────
function renderHeavy(s) {
  const d = (s.episode && s.episode.dir) || (s.domino && s.domino.dir) || 1, first = s.episode && s.episode.first;
  const tiles = (s.tiles || []).slice().sort((a, b) => b.w - a.w);
  const fo = {}; for (const e of s.eq || []) fo[e.sym] = nil(e.fut_oi_chg) ? "—" : sgn(e.fut_oi_chg, 0);
  const mx = Math.max(3, ...tiles.map(t => Math.abs(t.m || 0)));
  $("hw").innerHTML = tiles.map(t => {
    const m = t.m || 0, wd = Math.abs(m) / mx * 50, join = (t.z || 0) * d >= 1;
    return `<div class="hrow"><span class="s ${t.sym === first ? "first" : ""}" title="z ${fmt(t.z, 1)}, volume ${fmt(t.act, 1)}× its normal, futures OI ${fo[t.sym] ?? "—"} in ~5 min">${t.sym}</span><span class="w">${fmt(t.w, 1)}%</span>
      <span class="track"><i class="${join ? "join" : ""}" style="left:${m >= 0 ? 50 : 50 - wd}%;width:${wd}%;background:${m >= 0 ? C.up : C.down};color:${m >= 0 ? C.up : C.down}"></i></span>
      <span class="v ${tone(m)}">${sgn(m, 2)}</span></div>`;
  }).join("");
  const dm = s.domino || {};
  $("hwhint").textContent = nil(dm.Mb) ? "in Nifty points" : `basket implies ${sgn(dm.Mb, 1)} pts, futures moved ${sgn(dm.Mf, 1)}, lag ${sgn(dm.gap, 1)}`;
  $("hw2").innerHTML = (s.eq || []).filter(e => !e.wn).map(e => `<span>${e.sym} <b class="${tone(e.chg)}">${sgn(e.chg)}%</b></span>`).join("") || "";
}

// closed trades (T04): Held / Qty / Deployed / Return columns, rupees at 20 px, rows coloured by exit reason
let tradesSig = "";
function renderTrades(s) {
  const b = s.book || {};
  const ts = b.trades ? `<span class="tsum">${b.trades} trades · ${b.wins} won · <span class="${tone(b.pnl_rs)}">${sinr(b.pnl_rs)}</span> · ${sgn(b.pnl_pts)} pts</span>` : "";
  if ($("tstats").dataset.h !== ts) { $("tstats").innerHTML = ts; $("tstats").dataset.h = ts; }
  const why = (r) => ({ TRAIL: "Trailing stop", STOP: "Stop loss" }[r] || (r || "").replace(/^TRAIL \(locked ([+\d]+) % at (\d\d:\d\d):\d\d\)/, "Trailing stop · locked $1 % at $2").replace(/^STOP \(locked ([+\d]+) % at (\d\d:\d\d):\d\d\)/, "Stop · locked $1 % at $2").replace(/^LOCK \(([\d.]+) fell ([\d.]+) % from best ([\d.]+); armed ([+\d]+) % at (\d\d:\d\d):\d\d\)/, "Profit lock · $2 % off the best $3").replace(/^STOP \(futures: spot quote (\d+) s old\)/, "Stop on futures · index frozen $1 s").replace("THESIS-VOID (synchrony flipped)", "Heavyweights turned against it").replace(/TIME \((\d\d:\d\d) flatten\)/, "$1 close").replace("TIME (0DTE 15:00)", "Expiry-day 15:00 close").replace(/^BOOK .*/, "Sellers refilled"));
  const html = (s.trades || []).length ? s.trades.map(t => {
    const qty = t.qty || t.lots * LOT, dep = t.entry * qty, hold = nil(t.hold_s) ? hm(t.time_out) - hm(t.time_in) : t.hold_s, ret = nil(t.ret_pct) ? t.pnl_pts / t.entry * 100 : t.ret_pct;
    return `<tr class="t r-${code(t.reason).replace(/[^A-Z-]/g, "")} ${t.pnl_rs > 0 ? "win" : t.pnl_rs < 0 ? "loss" : ""} ${(t.rr || "").toLowerCase()}">
      <td>${t.time_in}<small>→ ${t.time_out}</small></td><td class="r">${dur(hold)}</td><td class="ct">${t.strike} ${t.rr}</td>
      <td class="r">${t.lots} lots<small>${qty} qty</small></td><td class="r">${inr(dep)}</td><td class="r">${fmt(t.entry)}<small>→ ${fmt(t.exit)}</small></td>
      <td class="r rs ${tone(t.pnl_rs)}">${sinr(t.pnl_rs)}<small><span class="pts ${tone(t.pnl_pts)}">${sgn(t.pnl_pts)} pts</span> <span class="ret">· ${sgn(ret, 1)}%</span></small></td>
      <td class="why" title="${(t.reason || "").replace(/"/g, "'")}">${why(t.reason)}</td><td class="r">${inr(t.capital_after)}</td></tr>`; }).join("")
    : `<tr><td colspan="9" class="empty">No trades yet today. Entries appear here the moment the triangle closes.</td></tr>`;
  if (html !== tradesSig) { tradesSig = html; $("tt").querySelector("tbody").innerHTML = html; }
}

function renderBooks(s) {
  const vs = s.variants || [], mx = Math.max(1, ...vs.map(v => Math.abs(v.pnl_pts)));
  const CTRL = { futures_only: "control: futures only", random_entry: "control: random entry", premium_momentum: "control: premium momentum" };
  const name = (n) => CTRL[n] ? CTRL[n] : n.startsWith("gate:") ? `champion + gate ${ADV[n.slice(5)] || n.slice(5)}` : n === "RAW" ? "No rules (RAW)" : n === "straddle_spike" ? "straddle spike leg" : n === "spot_dual_lvl" ? "dual + range mode + level booking" : n === "spot_dual_rg" ? "dual + range mode" : n === "spot_orb45" ? "opening-range breakout, level booking" : n === "spot_ft_prem10" ? "first touch, ±10 % premium" : n === "spot_dual" ? "dual: retest on expiry day, pullback otherwise" : n === "spot_pb45" ? "pullback of a 45-min impulse" : n === "spot_dc12_t12" ? "spot breakout, retest entry" : n === "spot_dc12_t12_first" ? "spot breakout, first touch (old entry)" : n === "spot_dc12_t12_1130" ? "spot breakout, expiry entries to 11:30" : n === "fade_switch" ? "follow / fade switch" : n.startsWith("gap") ? n.replace(/^gap([\d.]+)_s([\d.]+)$/, (_, g, x) => `basket gap ${g}, ${Math.round(x * 100)}%`)
    : n.endsWith("_bookexit") ? "push 2.0, 50% + book exit" : n.replace(/^m([\d.]+)_s([\d.]+)$/, (_, m, x) => `push ${m}, ${Math.round(x * 100)}%`);
  $("books").innerHTML = vs.map(v => {
    const wd = Math.abs(v.pnl_pts) / mx * 50;
    return `<div class="book ${v.name === s.champion ? "champ" : ""} ${CTRL[v.name] || v.name.startsWith("gate:") ? "ctl" : ""}"><span class="n">${name(v.name)}${v.open ? " ●" : ""}</span>
      <span class="track"><i style="left:${v.pnl_pts >= 0 ? 50 : 50 - wd}%;width:${wd}%;background:${v.pnl_pts >= 0 ? C.up : C.down}"></i></span>
      <span class="v ${tone(v.pnl_rs)}">${inr(v.pnl_rs)}</span></div>`;
  }).join("");
  const l = s.learning || {}, sb = l.scoreboard || {};
  $("lstat").textContent = { COLLECTING: "collecting evidence", GO: "edge looks real", KILL: "lead book retired", "NO-EDGE": "no edge found" }[l.status] || "collecting evidence";
  $("sprt").textContent = `Lead book since ${l.champion_since || "—"}: ${sb.n ?? 0} trades, ${sgn(sb.sum ?? 0, 1)} points. Proven at ${fmt(sb.go_line, 1)}, retired at ${fmt(sb.kill_line, 1)}. Changes happen only after the close.`;
}

function renderTape(s) {
  const ev = s.events || [];
  const names = { ENTRY: "Bought", EXIT: "Sold", "RAW-ENTRY": "RAW bought", "RAW-EXIT": "RAW sold", SYSTEM: "System", LEARN: "Learned", ARMED: "Armed",
                  SPIKE: "Straddle spike", SHIFT: "ATM rolled", GAP: "Data gap" };
  $("ev").innerHTML = ev.map(e => `<li class="${e.k}"><span class="t">${e.t}</span><span class="k">${names[e.k] || e.k}</span><span>${e.x}</span></li>`).join("");
  const top = ev.find(e => e.k === "ENTRY" || e.k === "EXIT" || e.k === "ARMED" || e.k === "SPIKE");
  const key = top ? top.t + top.k + top.x : "";
  if (key && key !== lastEvKey) {
    if (lastEvKey) {
      // the entry moment now belongs to the position band (pulseBand), not the triangle
      if (sound) beep(top.k === "ENTRY" ? 880 : (top.k === "ARMED" || top.k === "SPIKE") ? 660 : 440);
    }
    lastEvKey = key;
  }
}

function beep(freq) {
  try {
    actx = actx || new AudioContext();
    const o = actx.createOscillator(), g = actx.createGain();
    o.frequency.value = freq; o.connect(g); g.connect(actx.destination);
    g.gain.setValueAtTime(.15, actx.currentTime); g.gain.exponentialRampToValueAtTime(.001, actx.currentTime + .4);
    o.start(); o.stop(actx.currentTime + .42);
  } catch (e) { }
}

$("snd").onclick = () => {
  sound = !sound; const b = $("snd");
  b.setAttribute("aria-pressed", sound); b.textContent = sound ? "Sound on" : "Sound off";
  if (sound) beep(660);
};
window.addEventListener("resize", () => S && render(S));

// One-time snapshot from /api/state so the page is painted before the first /ws/state frame lands
// (and still paints something useful if the socket is slow to come up). A ws frame always wins.
async function primeState() {
  try {
    const r = await fetch("/api/state", { cache: "no-store" }); if (!r.ok) return;
    const d = await r.json();
    if (S || !d || !d.now) return;
    noteAges(d); S = d; render(S); checkStale();
  } catch (e) { /* the socket will bring the state */ }
}
loadInstruments().then(() => { connectTicks(); connectState(); primeState(); requestAnimationFrame(frame); });

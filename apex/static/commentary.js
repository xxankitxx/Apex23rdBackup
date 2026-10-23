// ApexOptions — the live-trade commentary panel (council 5: T05 data contract, T09 visual design).
// Loaded after app.js; render() calls renderCommentary(s, now) right after renderPos(s, now).
// Uses app.js helpers: $, nil, fmt, sgn, sinr, tone, clamp, clockSecs, dur, RM, sound, beep, pnlBuf, isStale.
//
// State-blob contract (engine → gateway → page), everything optional, absent ⇒ panel hidden:
//   s.commentary = {trade_id, verdict: {level, state, score, reason, since}, items: [...], review: item|null,
//                   entry_card: {grade, lines[3], time}|null, review_card: {grade?, lines[3], pnl_rs, ret_pct, time, t}|null,
//                   n_today, eval_ms}
//   item = {t (engine clock s), time "hh:mm:ss", kind, tone, text, score, key, n, slots?: {stocks: {SYM: helping|hurting}}}
//   Items arrive newest FIRST; the DOM diff key is key|n|t (a template can fire more than once).
//   Tones: warning|caution|confidence|praise|lesson|information (a 'review' tone maps to the review card).
"use strict";

const CMT = {
  MAX_DOM: 40,            // li nodes kept in the feed (older ones are dropped; the footer counts them)
  ENTRY_CARD_S: 20,       // entry card visible for the first 20 s of a trade, then the verdict card takes the slot
  REVIEW_S: 60,           // review card + panel stay 60 s after the exit
  ANIM_MS: 350,           // .new class lifetime (≥ the 320 ms keyframe)
  FLASH_MS: 650,
  SYMS: ["HDFCBANK", "ICICIBANK", "RELIANCE", "BHARTIARTL", "LT", "SBIN", "AXISBANK", "INFY", "KOTAKBANK", "M&M", "TCS", "ITC", "BAJFINANCE", "HINDUNILVR"],
};
const TONES = new Set(["confidence", "caution", "warning", "information", "praise", "lesson", "review"]);
const VHUE = { "HOLD": "--v-hold", "WATCH": "--v-watch", "EXIT-SOON": "--v-exit" };
const cmt = { nodes: new Map(), state: "", posKey: "", lastWarnKey: "", closedAt: 0, shown: false, grade: "" };

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const NUM_RE = /(^|[\s(])([+\-−]?₹?\d[\d,]*(?:\.\d+)?\s?(?:%|pts?|s|x|×|lots?|k)?)(?=[\s,.;:)]|$)/g;
// one regex for all the heavyweight symbols, longest first ("M&M" is escaped; "&" is already "&amp;" after esc())
const SYM_RE = new RegExp("(^|[^A-Z0-9&;])(" + CMT.SYMS.slice().sort((a, b) => b.length - a.length).map(x => esc(x).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")(?![A-Z0-9])", "g");
const itemKey = (x) => `${x.key}|${x.n ?? 0}|${x.t ?? ""}`;

// text → HTML: escape, then stock chips (neutral unless slots.stocks says helping / hurting), then tinted numerals
function decorate(text, slots) {
  let h = esc(text || "");
  const stk = (slots && slots.stocks) || {};
  h = h.replace(SYM_RE, (m, pre, sym) => {
    const raw = sym.replace("&amp;", "&"), role = stk[raw] === "helping" ? " helping" : stk[raw] === "hurting" ? " hurting" : "";
    return `${pre}<span class="stk${role}">${sym}</span>`;
  });
  const nums = (slots && slots.nums) || {};
  h = h.replace(NUM_RE, (m, pre, n) => {
    const key = n.trim(), t = nums[key] || (/^[+]/.test(key) ? "up" : /^[\-−]/.test(key) ? "down" : "");
    return `${pre}<span class="n ${t}">${key}</span>`;
  });
  return h;
}
const setH = (el, h) => { if (el.dataset.h !== h) { el.innerHTML = h; el.dataset.h = h; } };

function cmtShow(on) {
  const sec = $("cmt"); if (!sec) return;
  if (on && !cmt.shown) { sec.hidden = false; if (!RM.matches) { sec.classList.remove("cmt-in"); void sec.offsetWidth; sec.classList.add("cmt-in"); } }
  if (!on && cmt.shown) { sec.hidden = true; sec.classList.remove("cmt-in"); }
  cmt.shown = on;
  document.body.classList.toggle("cmt-on", on);
}

function flashWarn() {
  const sec = $("cmt"), cls = RM.matches ? "flash-warn-rm" : "flash-warn";
  sec.classList.remove("flash-warn", "flash-warn-rm"); void sec.offsetWidth; sec.classList.add(cls);
  clearTimeout(sec._fw); sec._fw = setTimeout(() => sec.classList.remove(cls), RM.matches ? 4000 : CMT.FLASH_MS);
}

function setVerdict(v) {
  const lvl = v && (v.level || v.state);
  const state = VHUE[lvl] ? lvl : "HOLD";
  const sec = $("cmt"), pill = $("cmtstate"), head = sec.querySelector(".cmt-head");
  if (state !== cmt.state) {
    const first = !cmt.state;
    cmt.state = state;
    sec.dataset.state = state; pill.dataset.state = state;
    $("cmtstatetxt").textContent = state === "EXIT-SOON" ? "EXIT SOON" : state;
    if (!first && !RM.matches) {                       // one colour sweep in the new hue, 500 ms, never repeated
      head.style.setProperty("--sweep", `var(${VHUE[state]})`);
      head.classList.remove("sweep"); void head.offsetWidth; head.classList.add("sweep");
      clearTimeout(head._sw); head._sw = setTimeout(() => head.classList.remove("sweep"), 600);
    }
    if (!first && state === "EXIT-SOON" && sound) { beep(520); setTimeout(() => beep(440), 220); }
    $("cmtann").textContent = `Verdict ${state}. ${(v && v.reason) || ""}`;
  }
  setH($("cmtreason"), decorate((v && v.reason) || "Waiting for the first remark.", null));
  return state;
}

function renderFeed(list) {
  const feed = $("cmtfeed");
  const items = (list || []).filter(x => x && x.key && x.text).sort((a, b) => (b.t || 0) - (a.t || 0));
  const keep = items.slice(0, CMT.MAX_DOM), keys = new Set(keep.map(itemKey));
  for (const [k, li] of cmt.nodes) if (!keys.has(k)) { li.remove(); cmt.nodes.delete(k); }
  const bulk = keep.length - cmt.nodes.size > 3;      // first fill / reconnect: many new rows at once → no animation at all
  let ref = feed.firstChild, newest = null;
  for (const x of keep) {
    const k = itemKey(x);
    let li = cmt.nodes.get(k);
    const tn = TONES.has(x.tone) ? x.tone : "information";
    if (!li) {
      li = document.createElement("li");
      li.className = `rmk tone-${tn}`; li.dataset.key = k; li.dataset.t = x.t;
      li.innerHTML = `<i class="rmk-glyph" aria-hidden="true"></i><time class="rmk-time">${esc(x.time || "")}</time><p class="rmk-text"></p>`;
      cmt.nodes.set(k, li);
      if (!bulk && !RM.matches) { li.classList.add("new"); setTimeout(() => li.classList.remove("new"), CMT.ANIM_MS); }
      if (tn === "warning" && !bulk && k !== cmt.lastWarnKey) { cmt.lastWarnKey = k; flashWarn(); if (sound) beep(520); }
      newest = newest || x;
    } else if (!li.classList.contains(`tone-${tn}`)) { li.className = `rmk tone-${tn}`; }
    const p = li.lastElementChild; setH(p, decorate(x.text, x.slots));
    if (li !== ref) feed.insertBefore(li, ref);       // move into place (append when ref is null)
    else ref = ref.nextSibling;                        // already in place: advance
  }
  let wait = feed.querySelector(".cmt-wait");
  if (!keep.length) { if (!wait) { wait = document.createElement("li"); wait.className = "cmt-wait"; wait.textContent = "Watching the trade — the first remark prints as soon as there is something to say."; feed.appendChild(wait); } }
  else if (wait) wait.remove();
  const more = items.length - keep.length;
  $("cmtmore").hidden = more <= 0; $("cmtmoren").textContent = more;
  if (newest) $("cmtann").textContent = newest.text;
  return items.length;
}

function renderTimeline(s, p, now, list) {
  const t0 = clockSecs((s.now || "").slice(0, 11) + p.time_in), span = Math.max(30, now - t0);   // ≥ 30 s so the first seconds are not a blur
  const X = (t) => clamp((t - t0) / span, 0, 1) * 100 + "%";
  let bestT = t0, best = -Infinity;
  for (const [t, v] of pnlBuf) if (v > best) { best = v; bestT = t; }     // best time from the P&L buffer: no engine field needed
  if (!(best > -Infinity)) best = p.peak_pts || 0;
  const pts = pnlBuf.length ? pnlBuf[pnlBuf.length - 1][1] : (p.pnl_pts || 0);
  const line = $("cmtline");
  line.classList.toggle("t-up", pts > 0.5); line.classList.toggle("t-down", pts < -0.5);
  $("cmtfill").style.width = "100%";
  $("cmtmkbest").style.left = X(bestT); $("cmtmkbest").style.display = best > 0.5 ? "" : "none";
  $("cmtmknow").style.left = "100%";
  const dots = (list || []).filter(x => x.tone !== "information" && !nil(x.t)).slice(0, 24)
    .map(x => `<i class="tone-${x.tone}" style="left:${X(x.t)};--tone:var(--t-${TONES.has(x.tone) ? x.tone : "information"})" title="${esc(x.time)} ${esc(x.text)}"></i>`).join("");
  setH($("cmtdots"), dots);
  setH($("cmtlinel"), `entry <b>${esc(p.time_in)}</b> · ${fmt(p.entry)}`);
  setH($("cmtliner"), `best <b class="${best > 0.5 ? "up" : ""}">${sgn(Math.max(best, p.peak_pts || 0), 2)}</b> · now <b>${dur(nil(p.hold_s) ? now - t0 : p.hold_s)}</b>`);
}

function renderCard(id, card) {
  const el = $(id); if (!card) { el.hidden = true; return; }
  el.hidden = false;
  const lines = (card.lines || []).slice(0, 3).map(l => `<li>${decorate(l, card.slots)}</li>`).join("");
  setH(el.querySelector("ul"), lines);
  const lbl = el.querySelector(".cmt-card-lbl");
  if (card.grade) lbl.dataset.grade = card.grade; else delete lbl.dataset.grade;
}

function renderVerdictCard(c, state) {
  const el = $("cmtvcard"), v = c.verdict || {};
  el.hidden = false; el.dataset.state = state;
  const txt = state === "EXIT-SOON" ? "EXIT SOON" : state;
  if ($("cmtvstate").textContent !== txt) $("cmtvstate").textContent = txt;
  const since = v.since ? `since ${v.since}` : "";
  if ($("cmtvsince").textContent !== since) $("cmtvsince").textContent = since;
  $("cmtvscore").style.width = clamp((v.score ?? 0) * 100, 0, 100) + "%";
  const n = nil(c.n_today) ? "" : `${c.n_today} remark${c.n_today === 1 ? "" : "s"} today${nil(c.eval_ms) ? "" : ` · ${fmt(c.eval_ms, 1)} ms`}`;
  if ($("cmtvn").textContent !== n) $("cmtvn").textContent = n;
}

function renderCommentary(s, now) {
  const sec = $("cmt"); if (!sec) return;
  const c = s.commentary || null, p = s.pos;
  const list = (c && c.items) || [];
  if (p && c) {
    const key = p.key + p.time_in;
    if (key !== cmt.posKey) {                           // a new trade: wipe the feed, reset the verdict so the first paint does not sweep
      cmt.posKey = key; cmt.state = ""; cmt.lastWarnKey = ""; cmt.closedAt = 0; cmt.grade = "";
      for (const li of cmt.nodes.values()) li.remove(); cmt.nodes.clear();
      $("cmtreview").hidden = true; $("cmtstate").hidden = false;
    }
    cmtShow(true);
    const state = setVerdict(c.verdict);
    const g = $("cmtgrade"), grade = c.entry_card && c.entry_card.grade;
    if (grade) { g.hidden = false; if (cmt.grade !== grade) { g.dataset.grade = grade; $("cmtgradeltr").textContent = grade; cmt.grade = grade; } } else g.hidden = true;
    const clk = (s.now || "").slice(11); if ($("cmtclock").textContent !== clk) $("cmtclock").textContent = clk;
    if (isStale()) return;                              // frozen: keep the last good picture (D4)
    renderFeed(list);
    renderTimeline(s, p, now, list);
    const early = (nil(p.hold_s) ? now - clockSecs((s.now || "").slice(0, 11) + p.time_in) : p.hold_s) < CMT.ENTRY_CARD_S;
    const showEntry = early && c.entry_card && (c.entry_card.lines || []).length;
    renderCard("cmtentry", showEntry ? c.entry_card : null);
    $("cmtvcard").hidden = !!showEntry;
    if (!showEntry) renderVerdictCard(c, state);
    return;
  }
  // flat: a review card for 60 s after the exit, then the panel folds away
  if (cmt.posKey) { cmt.posKey = ""; cmt.closedAt = now; }
  const rc = c && c.review_card;
  const since = rc && !nil(rc.t) ? now - rc.t : cmt.closedAt ? now - cmt.closedAt : Infinity;
  if (rc && since >= 0 && since < CMT.REVIEW_S) {
    const t = (s.trades || [])[0] || {};
    cmtShow(true);
    cmt.state = "REVIEW"; sec.dataset.state = "REVIEW"; $("cmtstate").hidden = true; $("cmtgrade").hidden = true;
    setH($("cmtreason"), `Closed <b class="n">${esc(t.time_out || rc.time || "")}</b> · ${esc(t.reason || "")}${nil(t.pnl_pts) ? "" : ` · <span class="n ${tone(t.pnl_pts)}">${sgn(t.pnl_pts)} pts</span>`}`);
    const clk = (s.now || "").slice(11); if ($("cmtclock").textContent !== clk) $("cmtclock").textContent = clk;
    if (isStale()) return;
    // the post-mortem lines only: the review item plus lessons and praise from the trade
    const post = list.filter(x => x.tone === "review" || x.kind === "review" || x.tone === "lesson" || x.tone === "praise");
    if (c.review && !post.some(x => itemKey(x) === itemKey(c.review))) post.unshift(c.review);
    renderFeed(post);
    $("cmtentry").hidden = true; $("cmtvcard").hidden = true;
    renderCard("cmtreview", rc);
    const b = $("cmtreviewrs"); b.textContent = sinr(rc.pnl_rs ?? t.pnl_rs); b.className = "cmt-review-rs " + tone(rc.pnl_rs ?? t.pnl_rs);
    $("cmtreviewret").textContent = nil(rc.ret_pct ?? t.ret_pct) ? "" : `${sgn(rc.ret_pct ?? t.ret_pct, 1)} % on the premium${nil(t.hold_s) ? "" : ` · ${dur(t.hold_s)} held`}`;
    return;
  }
  if (cmt.shown) { cmt.state = ""; cmt.closedAt = 0; $("cmtstate").hidden = false; for (const li of cmt.nodes.values()) li.remove(); cmt.nodes.clear(); }
  cmtShow(false);                                       // flat: the panel does not exist
}

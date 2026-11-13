// ApexOptions: "What I would do now", the Conductor's own first-person voice (13 Nov, owner point 4).
// Loaded after app.js and commentary.js; render() calls renderVoice(s). Display only: nothing here trades.
// Contract: s.voice from apex/engine/voice.py (mode, headline, lines, trigger, books, would_buy, hold, day, recent).
"use strict";

const VOICE_PILL = {
  WAITING: ["WAIT", "v-wait"], IMPULSE: ["WATCHING THE IMPULSE", "v-near"], ARMED: ["GET READY", "v-near"],
  ZONE: ["READY TO BUY", "v-fire"], PENDING: ["BUYING", "v-fire"], HOLDING: ["HOLD", "v-hold"],
  EXITING: ["SELLING", "v-exit"], STOOD_DOWN: ["DONE FOR NOW", "v-wait"], PAUSED: ["PAUSED", "v-wait"], OFF: ["OFF", "v-wait"],
};
const HOLD_PILL = { HOLD: ["HOLD", "v-hold"], NEAR: ["CLOSE TO EXIT", "v-near"], PROTECTED: ["HOLD · PROTECTED", "v-hold"],
                    EXITING: ["SELLING", "v-exit"] };
const vesc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const vnum = (x, d = 0) => (x === null || x === undefined || Number.isNaN(+x)) ? "—" : (+x).toFixed(d);

function voiceGauge(label, now, need, max, note) {
  // one bar: filled to now/need; past need it glows; max (when given) marks where the idea is dropped
  if (now === null || now === undefined || !need) return "";
  const top = Math.max(need, max || 0) * 1.1;
  const w = Math.max(0, Math.min(100, 100 * Math.abs(now) / top)), nd = 100 * need / top;
  const mk = max ? `<i class="vg-max" style="left:${(100 * max / top).toFixed(1)}%" title="drop the idea past here"></i>` : "";
  return `<div class="vg${Math.abs(now) >= need ? " met" : ""}"><span class="vg-l">${vesc(label)}</span>` +
    `<span class="vg-bar"><b style="width:${w.toFixed(1)}%"></b><i class="vg-need" style="left:${nd.toFixed(1)}%"></i>${mk}</span>` +
    `<span class="vg-n">${vnum(Math.abs(now))} / ${vnum(need)}${note ? " " + vesc(note) : ""}</span></div>`;
}

function voiceTrigger(v) {
  const t = v.trigger || {}, a = t.arm;
  if (v.hold || !t || t.no_forward || t.warm) return "";
  if (a) {
    return voiceGauge("impulse", a.impulse_pts, t.need_pts, null, "pts") +
      voiceGauge("pullback", a.pullback_pts, a.need_pts, a.max_pts, `pts (${vnum(a.pullback_pct)} %)`) +
      (a.in_zone ? voiceGauge("turn back", Math.max(0, a.resume_pts || 0), a.resume_need, null, `pts · fires at ${vnum(a.fire_level, 1)}`) : "");
  }
  return voiceGauge(`move in ${t.vel_min} min`, t.move_pts, t.need_pts, null, "pts") +
    (t.range_pts !== null && t.range_pts !== undefined ? `<p class="vt-note">20-min range ${vnum(t.range_pts)} pts · ${vnum(t.gap_hi)} under the high · ${vnum(t.gap_lo)} over the low</p>` : "");
}

function voiceLadder(h) {
  const rows = (h.exits || []).map(x => {
    const away = x.away_px !== null && x.away_px !== undefined ? `${vnum(x.away_px, 2)} away` :
      x.left_s !== undefined ? `${Math.floor(x.left_s / 60)} min left` : x.at ? `at ${vesc(x.at)}` : "";
    const lvl = x.kind === "FWD_TRAIL" ? `forward ${vnum(x.fwd_level, 1)} (now ${vnum(x.fwd_now, 1)}, ${vnum(x.away_fwd)} pts)` :
      x.px !== undefined ? `bid ${vnum(x.px, 2)}` : "";
    return `<li class="${x.kind === h.nearest ? "nearest" : ""}"><span>${vesc(x.label)}</span><span>${lvl}</span><b>${away}</b></li>`;
  }).join("");
  return `<ul class="v-ladder">${rows}</ul>`;
}

function voiceBooks(bs) {
  if (!bs || !bs.length) return "";
  return `<div class="v-books">` + bs.map(b =>
    `<span class="v-book ${b.veto ? "veto" : b.ready ? "ready" : "busy"}" title="${vesc(b.text)}">${vesc(b.book)}${b.veto ? " · no" : ""}</span>`).join("") + `</div>`;
}

function renderVoice(s) {
  const el = $("voicecard");
  if (!el) return;
  const v = s.voice;
  if (!v) { el.hidden = true; return; }
  el.hidden = false;
  const h = v.hold;
  const [word, cls] = h ? (HOLD_PILL[h.level] || HOLD_PILL.HOLD) : (VOICE_PILL[v.mode] || VOICE_PILL.WAITING);
  const d = v.day || {};
  const side = h ? h.rr : v.trigger && v.trigger.arm ? v.trigger.arm.side : null;
  const wb = v.would_buy;
  el.className = "voicecard " + cls + (side === "CE" ? " side-ce" : side === "PE" ? " side-pe" : "");
  el.innerHTML =
    `<div class="v-head"><span class="v-pill">${word}</span><h2>What I would do now</h2>` +
    `<span class="v-day">today ${d.trades || 0} trade${d.trades === 1 ? "" : "s"}, ${d.won || 0} won, ${inr(d.pnl_rs)} · capital ${inr(v.capital)} · ${vesc(v.time || "")}</span></div>` +
    `<p class="v-headline">${vesc(v.headline)}</p>` +
    `<div class="v-body"><div class="v-left">` +
    (v.lines && v.lines.length ? `<ul class="v-lines">${v.lines.map(x => `<li>${vesc(x)}</li>`).join("")}</ul>` : "") +
    `</div><div class="v-right">` +
    (h ? voiceLadder(h) : voiceTrigger(v)) +
    (wb ? `<p class="v-buy">I would buy <b>${wb.strike} ${wb.rr}</b> @ ${vnum(wb.ask, 2)} · ${wb.lots} lots · ${inr(wb.cost_rs)}${wb.approx ? " (expiry picker: about)" : ""}</p>` : "") +
    voiceBooks(v.books) + `</div></div>` +
    (v.recent && v.recent.length ? `<p class="v-recent">Last: ${v.recent.slice(-3).reverse().map(r => `${vesc(r.time)} ${vesc(r.event)}${r.book ? " " + vesc(r.book) : ""}${r.ret_pct !== null && r.ret_pct !== undefined ? ` ${(+r.ret_pct).toFixed(1)} %` : ""}`).join(" · ")}</p>` : "");
}

// ── 13 Nov: the Forecast Lab's stand banner (core.stand): the word, the strength, how the market is behaving, and
// how sure I am, with the rule's measured record beside it. A description of who is in control, not a forecast.
function labStand(p) {
  const el = $("labstand");
  if (!el) return;
  const s = p && p.stand;
  if (!s || !s.ok) { el.className = "lab-stand st-none"; el.innerHTML = `<p class="st-wait">My stand: ${vesc((s && s.why) || (p && p.why) || "waiting for the forecaster")}.</p>`; return; }
  const cls = s.word === "BULLISH" ? "st-bull" : s.word === "BEARISH" ? "st-bear" : "st-side";
  const pos = Math.max(0, Math.min(100, 50 + s.strength / 2));
  const facts = (s.facts || []).map(f => `<span class="st-fact ${f.pro === true ? "pro" : f.pro === false ? "con" : ""}">${vesc(f.text)}</span>`).join("");
  const r = s.record || {};
  el.className = "lab-stand " + cls;
  el.innerHTML =
    `<div class="st-left"><small>MY STAND</small><b class="st-word">${vesc(s.word)}</b>` +
    `<span class="st-since">since ${vesc(s.since)} · held ${s.held_min} min${s.pending ? ` · turning ${vesc(s.pending.toLowerCase())}?` : ""}</span>` +
    `<span class="st-num">${s.strength > 0 ? "+" : ""}${s.strength}<small> strength out of 100 (how one-sided, not a chance)</small></span>` +
    `<span class="st-meter"><i style="left:${pos.toFixed(1)}%"></i><em class="l">sellers</em><em class="r">buyers</em></span></div>` +
    `<div class="st-mid"><small>HOW THE MARKET IS BEHAVING</small><p>${vesc(s.say)}</p><div class="st-facts">${facts}</div></div>` +
    `<div class="st-right"><small>HOW SURE I AM</small><p>Next 15 min: a coin toss. This stand was right ${vnum(r.hit15, 0)} % at 15 minutes (${r.days_better} of ${r.days} days better than half).</p>` +
    `<p>It describes who is in control now. It is not a reason to buy; the Conductor ignores it.</p></div>`;
}

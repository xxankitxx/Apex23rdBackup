import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, csv, os, re, collections
B = r"D:\ApexOptions\data\replay\batch"
RUN = {"2026-10-19":"g1","2026-10-21":"g1","2026-10-22":"g2","2026-10-23":"g2","2026-10-26":"g3","2026-10-27":"g3",
       "2026-10-28":"r1","2026-10-29":"g4","2026-10-30":"r2","2026-11-02":"r3","2026-11-03":"r4","2026-11-04":"g6",
       "2026-11-05":"g7","2026-11-06":"g7","2026-11-09":"g8","2026-11-11":"g8","2026-11-12":"g9"}
LIVE = {"2026-11-11","2026-11-12","2026-11-13"}
FP = re.compile(r"(^|[\s(])(I|I'm|I'd|I'll|my|me)([\s,.;:)]|$)")
out = []
for day in list(RUN) + ["L2026-11-11","L2026-11-12","L2026-11-13"]:
    live = day.startswith("L"); d = day[1:] if live else day
    pdir = r"D:\ApexOptions\data\paper" if live else os.path.join(B, "p44_" + RUN[d], "paper")
    cf, tf = os.path.join(pdir, f"commentary_{d}.jsonl"), os.path.join(pdir, f"trades_{d}.csv")
    if not os.path.exists(cf) or not os.path.exists(tf):
        print("missing", day); continue
    rows = [json.loads(l) for l in open(cf, encoding="utf-8")]
    trades = list(csv.DictReader(open(tf, encoding="utf-8")))
    by = collections.defaultdict(list)
    for r in rows: by[r.get("trade_id")].append(r)
    for t in trades:
        # trade_id = round(t_in); trades csv has time_in only -> match by first row time
        cand = [k for k, v in by.items() if k and v[0].get("time") == t["time_in"]]
        if not cand:
            cand = [k for k, v in by.items() if k and any(x.get("kind") == "entry_card" and x.get("time") == t["time_in"] for x in v)]
        if not cand: continue
        rs = sorted(by[cand[0]], key=lambda x: x["t"])
        t0 = rs[0]["t"]; hold = float(t["hold_s"]); t1 = t0 + hold
        rem = [x for x in rs if x.get("kind") not in ("verdict", "entry_card", "review_card") and x.get("text")]
        ver = [x for x in rs if x.get("kind") == "verdict"]
        # time share by verdict level
        share = collections.Counter(); first_exit = None
        for a, b in zip(ver, ver[1:] + [{"t": t1}]):
            share[a["level"]] += max(0.0, min(b["t"], t1) - a["t"])
            if a["level"] == "EXIT-SOON" and first_exit is None: first_exit = a["t"] - t0
        tot = sum(share.values()) or 1.0
        warn = sum(1 for x in rem if x.get("tone") == "warning")
        conf = [x["t"] for x in rem if x.get("tone") in ("confidence", "praise")]
        wt = [x["t"] for x in rem if x.get("tone") == "warning"]
        import bisect
        contra = sum(1 for w in wt if any(abs(c - w) <= 10 for c in conf[max(0, bisect.bisect_left(conf, w - 10)):bisect.bisect_right(conf, w + 10)]))
        dash = sum(1 for x in rem if " — " in x["text"] or "— pts" in x["text"] or "is — " in x["text"])
        oct19 = sum(1 for x in rem if "19 Oct" in x["text"])
        fp = sum(1 for x in rem if FP.search(x["text"]))
        you = sum(1 for x in rem if re.search(r"\b(you|your)\b", x["text"], re.I))
        out.append(dict(day=day, src=t.get("src") or "", time_in=t["time_in"], hold_s=round(hold), ret_pct=float(t["ret_pct"]),
                        reason=t["reason"], n_rem=len(rem), per_min=round(len(rem) / max(hold / 60, 1), 1), warn=warn,
                        n_verdict=len(ver), flips_per_10min=round(len(ver) / max(hold / 600, 0.1), 1),
                        hold_share=round(share["HOLD"] / tot, 2), watch_share=round(share["WATCH"] / tot, 2),
                        exit_share=round(share["EXIT-SOON"] / tot, 2), first_exit_s=None if first_exit is None else round(first_exit),
                        n_exit_episodes=sum(1 for x in ver if x["level"] == "EXIT-SOON"), contra_warn=contra, dash=dash,
                        oct19=oct19, first_person=fp, you=you))
json.dump(out, open(r"D:\ApexOptions\data\research\13nov\work\R12\s1_tape_audit.json", "w"), indent=1)
import statistics as st
def agg(sel, lab):
    if not sel: return
    n = len(sel); rem = sum(x["n_rem"] for x in sel)
    print(f"{lab}: trades {n}, held min {sum(x['hold_s'] for x in sel)/60:.0f}, remarks {rem}, per min {rem/ (sum(x['hold_s'] for x in sel)/60):.1f}, "
          f"warnings {sum(x['warn'] for x in sel)} ({100*sum(x['warn'] for x in sel)/max(rem,1):.0f}%), verdict changes {sum(x['n_verdict'] for x in sel)} "
          f"(median per 10 min {st.median(x['flips_per_10min'] for x in sel)}), trades with EXIT-SOON {sum(1 for x in sel if x['n_exit_episodes'])}, "
          f"EXIT-SOON share med {st.median(x['exit_share'] for x in sel)}, contra {sum(x['contra_warn'] for x in sel)}, dash {sum(x['dash'] for x in sel)}, "
          f"19Oct {sum(x['oct19'] for x in sel)}, first-person {sum(x['first_person'] for x in sel)}, you {sum(x['you'] for x in sel)}")
rep = [x for x in out if not x["day"].startswith("L")]; liv = [x for x in out if x["day"].startswith("L")]
agg(rep, "replay 17d"); agg(liv, "live 11-13 Nov")
# does EXIT-SOON separate winners from losers?
for lab, sel in (("replay", rep), ("live", liv)):
    w = [x for x in sel if x["ret_pct"] > 0]; l = [x for x in sel if x["ret_pct"] <= 0]
    for nm, g in (("win", w), ("loss", l)):
        if g:
            print(lab, nm, len(g), "with EXIT-SOON", sum(1 for x in g if x["n_exit_episodes"]), "median exit share", st.median(x["exit_share"] for x in g),
                  "median first EXIT-SOON s", st.median([x["first_exit_s"] for x in g if x["first_exit_s"] is not None] or [None]) if any(x["first_exit_s"] is not None for x in g) else None)
for x in liv: print(x)

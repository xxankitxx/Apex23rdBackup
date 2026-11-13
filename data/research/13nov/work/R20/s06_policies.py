"""R20: walk-forward meta-controller policies vs the static Conductor on the trade table (one account, all-in).
usage: py -3.13 s06_policies.py gate|ctx|switch|day"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import functools
import itertools
import time
from mc_lib import *

print = functools.partial(print, flush=True)
t0 = time.time()
SEC = sys.argv[1]
df = load()
cx = pd.read_pickle('ctx_bocpd.pkl')
df = df.join(cx)
df['c_none'] = 'all'
df['c_bocpd'] = df.fresh.map({True: 'F', False: 'S'}).fillna('S') + df.seg_with.map({True: 'w', False: 'a'}).fillna('a')
df['c_with'] = df.seg_with.map({True: 'w', False: 'a'}).fillna('a')
df['c_regime'] = df.wx_regime.fillna('NA').astype(str)
df['c_hmm'] = df.wx_hmm_state.fillna(-1).astype(int).astype(str)
CTXS = ('c_none', 'c_bocpd', 'c_with', 'c_regime', 'c_hmm')
df = df[['day', 'book', 'fam', 'trig', 't_in', 't_out', 'ret_pct', 'rr', 'win'] + list(CTXS)].copy()
DAYS = sorted(df.day.unique())
PRIO = {b: i for i, b in enumerate(POOL)}
FAMS = ['c20pool', 'c20ext', 't28', 'lvl', 'spotpb', 'spotdc', 'fade', 'edge', 'flow']
for _c in ['day', 'book', 'fam', 'rr'] + list(CTXS):
    df[_c] = df[_c].astype(object)
G = {d: g for d, g in df.groupby('day')}
static = {d: sim_day(G[d], books=POOL, prio=PRIO) for d in DAYS}
results = []
print("setup", time.time() - t0)

# per (day, fam, ctxcol, ctx) wins / n, for cross-day priors
DC = {}
for c in CTXS:
    for (d, f, v), x in df[df.fam.notna()].groupby(['day', 'fam', c]).win:
        DC[(d, f, c, v)] = (x.sum(), len(x))


def prior(f, c, v, day, gamma):
    a = b = 0.0
    prev = [d for d in DAYS if d < day]
    for age, d in enumerate(reversed(prev)):
        w, n = DC.get((d, f, c, v), (0, 0))
        a += gamma ** age * w
        b += gamma ** age * (n - w)
    return a, b


class Live:
    """Today's shadow trades, added as they close (t_out < trigger): counts by (fam, ctxcol value), plus a tape."""
    def __init__(self, g, ctxcol):
        g = g[g.fam.notna()].sort_values('t_out')
        self.t = g.t_out.to_numpy(float); self.f = g.fam.to_numpy(object).tolist(); self.w = g.win.to_numpy(int).tolist()
        self.rr = g.rr.to_numpy(object).tolist(); self.v = g[ctxcol].to_numpy(object).tolist()
        self.k = 0
        self.cnt = {}
        self.tape = {}          # (set name, rr or None) -> wins in closing order
        self.sets = {}

    def adv(self, trig):
        while self.k < len(self.t) and self.t[self.k] < trig:
            i = self.k
            key = (self.f[i], self.v[i])
            w, n = self.cnt.get(key, (0, 0))
            self.cnt[key] = (w + self.w[i], n + 1)
            for sn, fs in self.sets.items():
                if self.f[i] in fs:
                    self.tape.setdefault((sn, None), []).append(self.w[i])
                    self.tape.setdefault((sn, self.rr[i]), []).append(self.w[i])
            self.k += 1


def add(label, tk, params):
    sc = score(df, tk, label)
    sc['kept'], sc['top'] = top_kept(df, tk, static)
    sc.update(params)
    results.append(sc)
    return sc


if SEC == 'gate':
    SETS = {'pool': {'c20pool'}, 'c20all': {'c20pool', 'c20ext'}, 'all': set(FAMS)}
    for sname, N, th, dm in itertools.product(SETS, (6, 12, 999), (0.45, 0.55), (False, True)):
        fams = SETS[sname]
        tk = {}
        for d in DAYS:
            L = Live(G[d], 'c_none')
            L.sets = {sname: fams}

            def acc(r, L=L):
                L.adv(r.trig)
                w = L.tape.get((sname, r.rr if dm else None), [])[-N:]
                if len(w) < 3:
                    return True
                return (1 + sum(w)) / (2 + len(w)) >= th
            tk[d] = sim_day(G[d], acc, books=POOL, prio=PRIO)
        add(f"gate {sname} N{N} th{th} dir{int(dm)}", tk, {'cls': 'gate'})

if SEC == 'ctx':
    for ctxcol, gamma, th, w0 in itertools.product(sys.argv[2].split(','), (0.7, 0.9, 1.0), (0.5, 0.55, 0.6), (0.25, 1.0)):
        tk = {}
        for d in DAYS:
            L = Live(G[d], ctxcol)
            pc = {}

            def acc(r, L=L, pc=pc, d=d):
                L.adv(r.trig)
                v = getattr(r, ctxcol)
                if v not in pc:
                    pc[v] = prior('c20pool', ctxcol, v, d, gamma)
                a, b = pc[v]
                w, n = L.cnt.get(('c20pool', v), (0, 0))
                A = 1 + w0 * a + w
                B = 1 + w0 * b + n - w
                return A / (A + B) >= th
            tk[d] = sim_day(G[d], acc, books=POOL, prio=PRIO)
        add(f'ctx {ctxcol} g{gamma} th{th} w{w0}', tk, {'cls': 'ctx', 'ctxcol': ctxcol, 'gamma': gamma, 'th': th, 'w0': w0})

if SEC == 'switch':
    cand = df[df.fam.isin(FAMS)]
    CG = {d: g for d, g in cand.groupby('day')}
    famrank = {f: i for i, f in enumerate(FAMS)}
    cand_prio = {b: famrank[f] * 100 + PRIO.get(b, 50) for b, f in cand.groupby('book').fam.first().items()}
    for ctxcol, gamma, th, topk in itertools.product(sys.argv[2].split(','), (0.7, 1.0), (0.55, 0.6), (1, 2)):
        tk = {}
        for d in DAYS:
            L = Live(G[d], ctxcol)
            pc = {}

            def acc(r, L=L, pc=pc, d=d):
                L.adv(r.trig)
                v = getattr(r, ctxcol)
                post = {}
                for f in FAMS:
                    if (f, v) not in pc:
                        pc[(f, v)] = prior(f, ctxcol, v, d, gamma)
                    a, b = pc[(f, v)]
                    w, n = L.cnt.get((f, v), (0, 0))
                    A = 1 + 0.25 * a + w
                    B = 1 + 0.25 * b + n - w
                    post[f] = A / (A + B)
                best = sorted(post, key=lambda f: -post[f])[:topk]
                return r.fam in best and post[r.fam] >= th
            tk[d] = sim_day(CG[d], acc, prio=cand_prio)
        add(f'switch {ctxcol} g{gamma} th{th} top{topk}', tk, {'cls': 'switch'})

if SEC == 'day':
    ARMS = {'c20pool': POOL, 'c20all': POOL + sorted(df[df.fam == 'c20ext'].book.unique())}
    for f in FAMS[2:]:
        ARMS[f] = sorted(df[df.fam == f].book.unique())
    armret, armtk = {}, {}
    for an, bks in ARMS.items():
        for d in DAYS:
            pr = PRIO if an == 'c20pool' else {b: i for i, b in enumerate(bks)}
            armtk[(an, d)] = sim_day(G[d], books=bks, prio=pr)
            armret[(an, d)] = day_ret(df.loc[armtk[(an, d)]].ret_pct)
    AR = pd.Series(armret).unstack()
    AR.to_csv('arm_day_returns.csv')
    print(AR.round(1).to_string())
    for gamma, meth in itertools.product((0.6, 0.8, 1.0), ('mean', 'median', 'winrate')):
        tk, pick = {}, {}
        for i, d in enumerate(DAYS):
            arm = 'c20pool'
            if i >= 3:
                prev = DAYS[:i]
                wts = np.array([gamma ** (i - 1 - j) for j in range(i)])
                lr = np.log1p(AR[prev].clip(lower=-99) / 100)
                if meth == 'mean':
                    s = (lr * wts).sum(axis=1) / wts.sum()
                elif meth == 'median':
                    s = lr.median(axis=1)
                else:
                    s = ((lr > 0) * wts).sum(axis=1) / wts.sum() + 1e-3 * lr.mean(axis=1)
                arm = s.idxmax() if s.max() > 0 else None
            pick[d] = arm
            tk[d] = armtk[(arm, d)] if arm else []
        sc = add(f'day g{gamma} {meth}', tk, {'cls': 'day'})
        sc['picks'] = ' '.join(f"{d[5:]}:{pick[d]}" for d in DAYS[3:])
        print(sc['label'], sc['picks'])

base = add('static', static, {'cls': 'static'})
R = pd.DataFrame(results)
R.to_pickle(f'policy_{SEC}' + ('_' + sys.argv[2].replace(',', '_') if len(sys.argv) > 2 else '') + '.pkl')
cols = ['label', 'all_strike', 'all_n', 'all_sum', 'all_lose', 'all_worst', 'all_woBD', 'early_sum', 'late_strike',
        'late_n', 'late_sum', 'late_lose', 'late_worst', 'kept']
pd.set_option('display.width', 250)
g = R[R.cls != 'static']
print(SEC, len(g), 'variants; late_sum > static', int((g.late_sum > base['late_sum']).sum()),
      '; early_sum > static', int((g.early_sum > base['early_sum']).sum()),
      '; late strike > static', int((g.late_strike > base['late_strike']).sum()),
      '; all_sum > static', int((g.all_sum > base['all_sum']).sum()))
print(R.sort_values('early_sum', ascending=False)[cols].head(10).round(1).to_string())
print(R.sort_values('late_sum', ascending=False)[cols].head(5).round(1).to_string())
print('time', time.time() - t0)

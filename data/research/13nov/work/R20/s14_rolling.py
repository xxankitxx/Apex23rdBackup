import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
fr = []
for f in ('final_candidates.pkl', 'handoff_results.pkl', 'policy_gate.pkl', 'policy_ctx_c_bocpd_c_none.pkl', 'policy_ctx_c_with.pkl', 'policy_ctx_c_hmm.pkl', 'policy_switch_c_none.pkl', 'policy_switch_c_bocpd.pkl', 'policy_day.pkl'):
    try:
        R = pd.read_pickle(f)
    except Exception as e:
        print('skip', f, e); continue
    for _, r in R.iterrows():
        fr.append(pd.Series(r['_perday'], name=r['label']))
P = pd.DataFrame(fr)
P = P[~P.index.duplicated()]
days = list(P.columns)
st = P.loc['static']
print('variants in rolling pool', len(P) - 1)
for crit in ('sum', 'logsum'):
    out = []
    for i in range(4, len(days)):
        past = P[days[:i]]
        sc = past.sum(axis=1) if crit == 'sum' else np.log1p(past.clip(lower=-99) / 100).sum(axis=1)
        pick = sc.idxmax()
        out.append((days[i], pick, P.loc[pick, days[i]], st[days[i]]))
    O = pd.DataFrame(out, columns=['day', 'pick', 'ret', 'static'])
    print(crit); print(O.to_string())
    print('rolling sum', O.ret.sum().round(1), 'static', O.static.sum().round(1), 'losing days', (O.ret < 0).sum(), (O.static < 0).sum(),
          'better/worse days', (O.ret > O.static + 0.05).sum(), (O.ret < O.static - 0.05).sum())

"""R20: the side-loss lock applied to every book alone (gate tape = the book's own family, CE/PE side, last 12 closed)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import functools
import time
from mc_lib import *

print = functools.partial(print, flush=True)
t0 = time.time()
df = load()
df = df[['day', 'book', 'fam', 'trig', 't_in', 't_out', 'ret_pct', 'rr', 'win']].copy()
for c in ('day', 'book', 'fam', 'rr'):
    df[c] = df[c].astype(object)
df = df[df.fam.notna()]
DAYS = sorted(df.day.unique())
FAMSET = {'c20pool': {'c20pool', 'c20ext'}, 'c20ext': {'c20pool', 'c20ext'}}
rows = []
for (d, fam), g in df.groupby(['day', 'fam']):
    fs = FAMSET.get(fam, {fam})
    tape = df[(df.day == d) & df.fam.isin(fs)].sort_values('t_out')
    tt = tape.t_out.to_numpy(float); rr = tape.rr.tolist(); ww = tape.win.tolist()
    for b, gb in g.groupby('book'):
        gb = gb.sort_values('trig')
        k = 0; side = {'CE': [], 'PE': []}
        for r in gb.itertuples():
            while k < len(tt) and tt[k] < r.trig:
                side[rr[k]].append(ww[k]); k += 1
            w = side[r.rr][-12:]
            lock = len(w) >= 3 and (len(w) - sum(w)) > sum(w)
            rows.append((d, fam, b, r.ret_pct, lock))
T = pd.DataFrame(rows, columns=['day', 'fam', 'book', 'ret', 'lock'])
T['early'] = T.day <= EARLY_END
T['win'] = T.ret > 0
# a book's own trades are already one at a time, so removing locked trades is exact for the book's trade list
# (it does not re-open the trades the book skipped while holding a locked trade: approximate, conservative)
s = T.groupby(['fam', 'early', 'lock']).agg(n=('ret', 'size'), strike=('win', 'mean'), mean=('ret', 'mean')).round(3)
pd.set_option('display.width', 200)
print(s.to_string())
bd = T.groupby(['book', 'day']).apply(lambda x: pd.Series({'all': day_ret(x.ret), 'kept': day_ret(x.ret[~x.lock])}))
bd = bd.reset_index()
bd['fam'] = bd.book.map(family)
bd['early'] = bd.day <= EARLY_END
bd['better'] = bd.kept > bd['all'] + 1e-9
bd['worse'] = bd.kept < bd['all'] - 1e-9
print(bd.groupby(['fam', 'early']).agg(bookdays=('day', 'size'), better=('better', 'sum'), worse=('worse', 'sum'),
                                        d_mean=('kept', 'mean'), base_mean=('all', 'mean')).round(1).to_string())
T.to_pickle('sidelock_books.pkl')
print('time', time.time() - t0)

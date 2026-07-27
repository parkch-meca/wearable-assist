"""Analyze gait OFF/ON SO: ES(IL+LTpL+LTpT) peak per gait phase + reserve actuator check."""
import numpy as np, opensim as osim
from collections import defaultdict

def load(path):
    t = osim.TimeSeriesTable(path)
    T = np.array(list(t.getIndependentColumn()))
    labs = list(t.getColumnLabels())
    D = {c: np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]) for c in labs}
    return T, D, labs

R = '/data/gait_results'
Toff, Aoff, labs = load(R + '/gait_off/so_StaticOptimization_activation.sto')
Ton, Aon, _ = load(R + '/gait_on/so_StaticOptimization_activation.sto')
ES = [l for l in labs if l.startswith(('IL_', 'LTpL', 'LTpT'))]

def stack(D):
    return np.vstack([D[e] for e in ES])
pk_off = stack(Aoff).max(axis=0) * 100.0
pk_on = stack(Aon).max(axis=0) * 100.0
mn_off = stack(Aoff).mean(axis=0) * 100.0
mn_on = stack(Aon).mean(axis=0) * 100.0

PH = [('heel strike (R)', 0.62, 0.74), ('mid-stance (R)', 0.94, 1.06),
      ('toe-off (R)', 1.30, 1.42), ('whole cycle', 0.40, 1.60)]
print("=== ES peak (max muscle, IL+LTpL+LTpT) — gait phase별 OFF vs ON ===")
print(f"{'phase':18s} {'OFF%':>7s} {'ON%':>7s} {'Δ(ON-OFF)%p':>13s}  해석")
rows = []
for ph, a, b in PH:
    mo = (Toff >= a) & (Toff <= b)
    mnn = (Ton >= a) & (Ton <= b)
    o = pk_off[mo].max(); n = pk_on[mnn].max(); d = n - o
    itp = '슈트 보조(ES↓)' if d < -0.3 else ('슈트 방해(ES↑)' if d > 0.3 else '무영향(±0.3%p내)')
    print(f"{ph:18s} {o:7.2f} {n:7.2f} {d:+13.2f}  {itp}")
    rows.append((ph, round(o, 2), round(n, 2), round(d, 2)))
print(f"\nES mean(근육평균) whole peak: OFF {mn_off.max():.2f}% ON {mn_on.max():.2f}% "
      f"Δ{mn_on.max()-mn_off.max():+.2f}%p  [{len(ES)} ES 근육]")

# ---- reserve check ----
Tf, Foff, flabs = load(R + '/gait_off/so_StaticOptimization_force.sto')
_, Fon, _ = load(R + '/gait_on/so_StaticOptimization_force.sto')
res = [l for l in flabs if l.startswith('reserve_')]
def grp(nm):
    b = nm.replace('reserve_', '')
    if b.startswith('pelvis'): return 'pelvis(잔차흡수·예상)'
    if any(k in b for k in ['_FE', '_LB', '_AR', 'Abs_']): return 'spine(작아야=ES유효)'
    if any(k in b for k in ['shoulder', 'elv', 'elbow', 'wrist', 'pro_sup', 'clav']): return 'arm'
    if any(k in b for k in ['hip', 'knee', 'ankle', 'lumbar', 'subtalar', 'mtp']): return 'leg'
    return 'other(rib등)'
g = defaultdict(lambda: [0.0, ''])
for r in res:
    for tag, F in [('OFF', Foff), ('ON', Fon)]:
        mx = np.abs(F[r]).max(); G = grp(r)
        if mx > g[G][0]: g[G] = [mx, f"{r.replace('reserve_','')}({tag})"]
print("\n=== reserve actuator 점검 (force.sto |force| 최대, N 또는 N·m) ===")
print(f"{'group':24s} {'max|force|':>11s}   (actuator)")
for G in ['pelvis(잔차흡수·예상)', 'spine(작아야=ES유효)', 'arm', 'leg', 'other(rib등)']:
    if G in g: print(f"{G:24s} {g[G][0]:11.1f}   {g[G][1]}")
sp = g.get('spine(작아야=ES유효)', [0, ''])[0]
print(f"\n>>> spine reserve 최대 {sp:.1f} (임계 10N·m): "
      f"{'⚠️ ES 과소평가 가능' if sp > 10 else '✅ 작음 → ES 유효'}")
import json
json.dump({'rows': rows, 'es_mean_off': round(float(mn_off.max()),2), 'es_mean_on': round(float(mn_on.max()),2),
           'spine_res': round(float(sp),1),
           'reserves': {G: [round(float(g[G][0]),1), g[G][1]] for G in g}},
          open(R + '/gait_es_summary.json', 'w'), ensure_ascii=False)
print("WROTE gait_es_summary.json")

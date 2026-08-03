"""[4단계] 보행 결과 재해석 — 단일 수치가 아니라 근육별 부하 재분배로 분석.

지표 간 상반: 구간 peak 평균 +21.4 %(증가) vs ES_mean −11.9 %(감소).
평균은 줄고 최대는 늘었다면 이는 '부하 감소'가 아니라 '재분배'이다.
어느 근육군에서 늘고 어디서 줄었는지, gait phase별로 어떻게 다른지 정량화한다.

새 해석 실행 없음 — 기존 tight SO 산출물만 읽는다.
"""
import numpy as np, opensim as osim, json, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
_KFNAME = fm.FontProperties(fname=KF).get_name()
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [_KFNAME]
plt.rcParams['mathtext.fontset'] = 'dejavusans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9.5, 'axes.titlesize': 10,
                     'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
                     'legend.fontsize': 8.5, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})
CM = 1 / 2.54
OUT = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/paper_five_motion'
os.makedirs(OUT, exist_ok=True)

OFF = '/data/romfix_unified/gait_off/so_StaticOptimization_activation.sto'
ON = '/data/romfix_unified/gait_on/so_StaticOptimization_activation.sto'
PHASES = [('heel strike', 0.62, 0.74), ('mid-stance', 0.94, 1.06),
          ('toe-off', 1.30, 1.42)]


def load(p):
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn())); L = list(t.getColumnLabels())
    E = [l for l in L if l.startswith(('IL_', 'LTpL', 'LTpT'))]
    A = np.vstack([[float(t.getDependentColumn(e)[i]) for i in range(t.getNumRows())]
                   for e in E]) * 100
    return T, A, E


T, Ao, E = load(OFF)
_, An, E2 = load(ON)
assert E == E2, 'ES 근육 집합 불일치'
n = len(E)


def group(nm):
    if nm.startswith('IL_'):
        return 'Iliocostalis (IL)'
    if nm.startswith('LTpL'):
        return 'Longissimus pars lumborum (LTpL)'
    return 'Longissimus pars thoracis (LTpT)'


def side(nm):
    return '우측' if nm.endswith('_r') else ('좌측' if nm.endswith('_l') else '기타')


GR = sorted(set(group(e) for e in E))
res = {}

print('=' * 96)
print('[1] 전주기 요약 — 평균은 줄고 최대는 늘었는가')
print('=' * 96)
pk_o, pk_n = Ao.max(axis=0), An.max(axis=0)
mn_o, mn_n = Ao.mean(axis=0), An.mean(axis=0)
print(f"  ES peak (프레임별 최대근육) 전주기 평균 : OFF {pk_o.mean():6.2f} → ON {pk_n.mean():6.2f} "
      f"({100*(pk_n.mean()-pk_o.mean())/pk_o.mean():+6.1f} %)")
print(f"  ES mean (76근육 평균)      전주기 평균 : OFF {mn_o.mean():6.2f} → ON {mn_n.mean():6.2f} "
      f"({100*(mn_n.mean()-mn_o.mean())/mn_o.mean():+6.1f} %)")
print(f"  → 최대는 증가, 평균은 감소 ⇒ 총량 감소가 아니라 소수 근육으로의 집중(재분배)")

print('\n' + '=' * 96)
print('[2] 근육별 변화 분포 (전주기 평균 활성도 기준)')
print('=' * 96)
per_o = Ao.mean(axis=1); per_n = An.mean(axis=1)          # 근육별 시간평균
d = per_n - per_o
inc = (d > 0.05).sum(); dec = (d < -0.05).sum(); flat = n - inc - dec
print(f'  증가 근육 {inc}개 / 감소 근육 {dec}개 / 변화 없음 {flat}개  (역치 ±0.05 %p)')
print(f'  증가분 총합 {d[d>0].sum():+.2f} %p, 감소분 총합 {d[d<0].sum():+.2f} %p, 순변화 {d.sum():+.2f} %p')
order = np.argsort(d)
print('\n  가장 많이 감소한 5개:')
for i in order[:5]:
    print(f'    {E[i]:16s} {per_o[i]:6.2f} → {per_n[i]:6.2f}  ({d[i]:+6.2f} %p)  [{group(E[i])}]')
print('  가장 많이 증가한 5개:')
for i in order[::-1][:5]:
    print(f'    {E[i]:16s} {per_o[i]:6.2f} → {per_n[i]:6.2f}  ({d[i]:+6.2f} %p)  [{group(E[i])}]')

print('\n' + '=' * 96)
print('[3] 근육군별 재분배')
print('=' * 96)
grp_stat = {}
for g in GR:
    idx = [i for i, e in enumerate(E) if group(e) == g]
    o, v = per_o[idx].sum(), per_n[idx].sum()
    grp_stat[g] = (float(o), float(v), len(idx))
    print(f'  {g:38s} n={len(idx):2d}  합 {o:7.2f} → {v:7.2f}  ({v-o:+6.2f} %p, {100*(v-o)/o:+6.1f} %)')

print('\n' + '=' * 96)
print('[4] gait phase별 재분배')
print('=' * 96)
print(f"  {'구간':12s} {'ES peak OFF→ON':>22s} {'ES mean OFF→ON':>22s} {'집중도 변화':>14s}")
ph_rows = []
for nm, lo, hi in PHASES + [('전주기', T[0], T[-1])]:
    m = (T >= lo) & (T <= hi)
    po, pn = Ao[:, m].max(axis=0).mean(), An[:, m].max(axis=0).mean()
    mo, mnn = Ao[:, m].mean(), An[:, m].mean()
    # 집중도 = peak / mean (한 근육에 얼마나 몰려 있는가)
    co, cn = po / mo, pn / mnn
    print(f'  {nm:12s} {po:8.2f} → {pn:8.2f} ({100*(pn-po)/po:+5.1f}%) '
          f'{mo:8.2f} → {mnn:8.2f} ({100*(mnn-mo)/mo:+5.1f}%) {co:6.2f} → {cn:5.2f}')
    ph_rows.append(dict(phase=nm, peak_off=float(po), peak_on=float(pn),
                        mean_off=float(mo), mean_on=float(mnn),
                        conc_off=float(co), conc_on=float(cn)))

res = dict(peak_cycle_off=float(pk_o.mean()), peak_cycle_on=float(pk_n.mean()),
           mean_cycle_off=float(mn_o.mean()), mean_cycle_on=float(mn_n.mean()),
           n_inc=int(inc), n_dec=int(dec), n_flat=int(flat),
           sum_inc=float(d[d > 0].sum()), sum_dec=float(d[d < 0].sum()),
           net=float(d.sum()), groups=grp_stat, phases=ph_rows,
           top_dec=[(E[i], float(d[i])) for i in order[:5]],
           top_inc=[(E[i], float(d[i])) for i in order[::-1][:5]])
json.dump(res, open('/data/romfix_unified/gait_redistribution.json', 'w'),
          ensure_ascii=False, indent=1)

# ================= 그림 =================
fig, axs = plt.subplots(1, 3, figsize=(16.4 * CM, 6.0 * CM))
a = axs[0]
a.plot(T, Ao.max(axis=0), color='0.15', lw=1.6, label='슈트 OFF')
a.plot(T, An.max(axis=0), color='0.45', lw=1.6, ls='--', label='슈트 ON')
for nm, lo, hi in PHASES:
    a.axvspan(lo, hi, color='0.88', zorder=0)
a.set_xlabel('시간 (s)'); a.set_ylabel('ES peak 활성도 (%)')
a.set_ylim(bottom=Ao.max(axis=0).min() - 9)
a.set_title('(a) 최대 활성 근육 — 증가', fontsize=9.5, pad=4)
a.legend(loc='lower left', framealpha=1.0, fontsize=7.6); a.grid(alpha=0.3, lw=0.5)
a.set_axisbelow(True)
for s in ('top', 'right'): a.spines[s].set_visible(False)

b = axs[1]
b.plot(T, Ao.mean(axis=0), color='0.15', lw=1.6, label='슈트 OFF')
b.plot(T, An.mean(axis=0), color='0.45', lw=1.6, ls='--', label='슈트 ON')
for nm, lo, hi in PHASES:
    b.axvspan(lo, hi, color='0.88', zorder=0)
b.set_xlabel('시간 (s)'); b.set_ylabel('ES mean 활성도 (%)')
b.set_ylim(bottom=Ao.mean(axis=0).min() - 1.15)
b.set_title('(b) 76근육 평균 — 감소', fontsize=9.5, pad=4)
b.legend(loc='lower left', framealpha=1.0, fontsize=7.6); b.grid(alpha=0.3, lw=0.5)
b.set_axisbelow(True)
for s in ('top', 'right'): b.spines[s].set_visible(False)

c = axs[2]
srt = np.argsort(d)
cols = ['0.30' if x < 0 else '0.72' for x in d[srt]]
c.bar(range(n), d[srt], color=cols, edgecolor='k', lw=0.3)
c.axhline(0, color='k', lw=0.9)
c.set_xlabel('척추기립근 76개')
c.set_ylabel('Δ 시간평균 활성도 (%p)')
c.set_title('(c) 근육별 재분배', fontsize=9.5, pad=4)
c.grid(alpha=0.3, lw=0.5, axis='y'); c.set_axisbelow(True)
for s in ('top', 'right'): c.spines[s].set_visible(False)
fig.tight_layout(pad=0.9)
fig.savefig(f'{OUT}/fig7_gait_redistribution.png', dpi=450)
plt.close(fig)
print('\nSAVED', f'{OUT}/fig7_gait_redistribution.png')
print('SAVED /data/romfix_unified/gait_redistribution.json')

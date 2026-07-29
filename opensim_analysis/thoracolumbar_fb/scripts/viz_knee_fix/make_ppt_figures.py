"""발표용 결과 figure 3종 (S19 박스 / S21 걷기 / S24 나르기).

설계 원칙 — 슬라이드의 6.4 x 3.45 in 칸에 들어가므로:
  * 2패널을 6.4 in에 욱여넣으면 폰트가 판독 불가(작게) 또는 겹침(크게)이 됨.
    → 슬라이드 칸과 같은 종횡비(약 1.85)의 **단일 패널**로 통일.
  * figsize 7.4 in → 슬라이드에서 0.86배 축소. 15 pt 폰트 = 실효 13 pt.
  * 구간별 수치는 좌측 텍스트 박스와 S22 표가 담당 — 그림은 시계열 하나만.
데이터는 SO 산출물(.sto)에서 직접 재계산.
"""
import numpy as np, opensim as osim
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = fm.FontProperties(fname=KF).get_name()
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 15, 'axes.labelsize': 16, 'axes.titlesize': 17,
                     'xtick.labelsize': 15, 'ytick.labelsize': 15,
                     'legend.fontsize': 14.5, 'figure.facecolor': 'white',
                     'axes.facecolor': 'white'})

OUT = '/data/opensim_results/ppt_media'
C_OFF, C_ON, C_NL = '#C0392B', '#1F6FB2', '#9AA5AD'
FIGSIZE = (7.4, 4.0)


def load(p):
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn())); labs = list(t.getColumnLabels())
    E = [l for l in labs if l.startswith(('IL_', 'LTpL', 'LTpT'))]
    A = np.vstack([[float(t.getDependentColumn(e)[i]) for i in range(t.getNumRows())]
                   for e in E]) * 100
    return T, A.max(axis=0), A.mean(axis=0)


def style(ax):
    ax.grid(alpha=0.28, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)


def save(fig, name):
    fig.savefig(f'{OUT}/{name}', dpi=175, facecolor='white',
                bbox_inches='tight', pad_inches=0.12)
    plt.close(fig)
    print(name)


# ======================================================= 박스 들기 (S19)
R = '/data/stoop_results/box_stoop_so'
t, nl, _ = load(f'{R}/B_noload/so_B_noload_StaticOptimization_activation.sto')
_, off, _ = load(f'{R}/B_off/so_B_off_StaticOptimization_activation.sto')
_, on, _ = load(f'{R}/B_on/so_B_on_StaticOptimization_activation.sto')
fig, a = plt.subplots(figsize=FIGSIZE)
a.axvspan(1.9, 5.9, color='#F0C36D', alpha=0.18, label='박스를 든 구간')
a.plot(t, nl, color=C_NL, lw=2.0, label='무부하 (참조)')
a.plot(t, off, color=C_OFF, lw=3.0, label='박스 20 kg · 슈트 OFF')
a.plot(t, on, color=C_ON, lw=3.0, label='박스 20 kg · 슈트 ON')
i = int(np.argmax(np.where((t >= 1.9) & (t <= 5.9), off, -1)))
a.plot([t[i], t[i]], [on[i], off[i]], color='k', lw=1.6, ls=':')
a.annotate('최대 하중 시점\n37.5 % → 28.8 %  ( −23 % )',
           xy=(t[i], (off[i] + on[i]) / 2), xytext=(4.30, 8.5),
           fontsize=14.5, fontweight='bold', color='#0F5C96', ha='center', va='center',
           bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#0F5C96', lw=1.5),
           arrowprops=dict(arrowstyle='->', color='#0F5C96', lw=1.8))
a.set_xlabel('시간 (s)'); a.set_ylabel('척추기립근 활성도 ES peak (%)')
a.set_title('박스 20 kg 들기 — 허리 근육 부담', fontweight='bold', pad=10)
a.set_ylim(0, 52)
a.legend(loc='upper left', framealpha=0.95, ncol=2, columnspacing=1.0,
         handlelength=1.5)
style(a); save(fig, 'fig_box_es.png')

# ======================================================= 나르기 (S24)
Rc = '/data/carry_results'
t, off, _ = load(f'{Rc}/carry_off/so_StaticOptimization_activation.sto')
_, on, _ = load(f'{Rc}/carry_on/so_StaticOptimization_activation.sto')
fig, a = plt.subplots(figsize=FIGSIZE)
a.axvspan(0.94, 1.06, color='#7FC29B', alpha=0.30)
a.plot(t, off, color=C_OFF, lw=3.0, label='슈트 OFF')
a.plot(t, on, color=C_ON, lw=3.0, label='슈트 ON (24 N·m)')
a.axhline(100, color='#B7950B', ls=':', lw=2.2)
a.text(1.58, 103, '포화 한계 100 %', ha='right', fontsize=14,
       color='#8A6D0B', fontweight='bold')
a.annotate('mid-stance\n99.9 % → 74.5 %', xy=(1.0, 74.5), xytext=(1.30, 42),
           fontsize=14.5, fontweight='bold', color='#1E8449', ha='center', va='center',
           bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#1E8449', lw=1.5),
           arrowprops=dict(arrowstyle='->', color='#1E8449', lw=1.8))
a.set_xlabel('시간 (s)'); a.set_ylabel('척추기립근 활성도 ES peak (%)')
a.set_title('20 kg 나르기 — OFF는 100 %에 포화 (부담 과소평가)',
            fontweight='bold', pad=10)
a.set_ylim(0, 132)
a.legend(loc='lower left', framealpha=0.95, ncol=2, columnspacing=1.0,
         handlelength=1.5)
style(a); save(fig, 'fig_carry_es.png')

# ======================================================= 걷기 (S21)
Rg = '/data/gait_results'
t, off, _ = load(f'{Rg}/gait_off_tight/so_StaticOptimization_activation.sto')
_, on, _ = load(f'{Rg}/gait_on_tight/so_StaticOptimization_activation.sto')
fig, a = plt.subplots(figsize=FIGSIZE)
for nm, xv in [('heel\nstrike', 0.68), ('mid-\nstance', 1.00), ('toe-\noff', 1.36)]:
    a.axvline(xv, color='#AAA', ls=':', lw=1.5)
    a.text(xv, 49, nm, ha='center', va='top', fontsize=13.5, color='#666')
a.plot(t, off, color=C_OFF, lw=3.0, label='슈트 OFF')
a.plot(t, on, color=C_ON, lw=3.0, label='슈트 ON (24 N·m)')
a.set_xlabel('시간 (s)'); a.set_ylabel('척추기립근 활성도 ES peak (%)')
a.set_title('정상 보행 — ON / OFF 차이가 작음 (구간별 최대 4.3 %p)',
            fontweight='bold', pad=10)
a.set_ylim(0, 52)
a.legend(loc='lower left', framealpha=0.95, ncol=2, columnspacing=1.0,
         handlelength=1.5)
style(a); save(fig, 'fig_gait_es.png')

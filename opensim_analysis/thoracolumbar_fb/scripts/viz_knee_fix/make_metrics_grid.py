"""[5] 지표 재검토 + LTpL 규명 + 하단 고정 스윕 검증 그리드."""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

OUT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint')
os.makedirs(OUT, exist_ok=True)
M = json.load(open('/data/suit_span/metrics3.json'))
BM = json.load(open('/data/suit_span/bottom_moment.json'))
LA = json.load(open('/data/suit_span/ltpl_anatomy.json'))
C, OFFD = M['cond'], M['off']
GREEN, RED, ORANGE, BLUE, PURPLE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0', '#8a6fbf'

fig = plt.figure(figsize=(17.4, 12.0))
gs = fig.add_gridspec(2, 3, hspace=0.50, wspace=0.32,
                      left=0.075, right=0.975, top=0.880, bottom=0.075)
fig.suptitle('지표 재검토 + LTpL 잔존 증가 규명 + 하단 고정 스윕',
             fontsize=14.5, fontweight='bold', y=0.955)
fig.text(0.5, 0.918,
         '스툽 · 전 조건 16.5 N·m · 모델 해시 ca12f321326e · OFF 재사용  |  '
         '주의: 현 하드웨어는 L1 상단 · 허벅지 하단. 나머지는 설계 제안  |  2026-08-16',
         ha='center', fontsize=9.2, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.3, fontweight='bold', pad=8, loc='left')


# ── (1) ES peak 결정 근육 ─────────────────────────────────────
ax = fig.add_subplot(gs[0, 0]); panel(ax, '(1) ★ ES peak 를 결정한 근육')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
SEL = ['OFF', '(i) 커플 T1↔골반 16.5', '(ii) 커플 L1↔골반',
       '(iii) 경로힘 L1→허벅지', '(iv) 경로힘 T8→허벅지']
ax.text(0.0, 0.965, '조건', fontsize=8.4, fontweight='bold')
ax.text(0.50, 0.965, '1위 근육', fontsize=8.4, fontweight='bold')
ax.text(0.97, 0.965, 'peak', fontsize=8.4, fontweight='bold', ha='right')
ax.plot([0, 1], [0.935, 0.935], color='k', lw=1.0)
y = 0.87
for lab in SEL:
    d = OFFD if lab == 'OFF' else C[lab]
    nm = d['dominant'][0][0]
    pk = d['peak']
    isIL = nm.startswith('IL')
    ax.text(0.0, y, lab.replace(' 경로힘', '\n경로힘').replace(' 커플', '\n커플'),
            fontsize=7.8, va='center', linespacing=1.35)
    ax.text(0.50, y, nm, fontsize=8.2, va='center', fontweight='bold',
            color=BLUE if isIL else RED)
    ax.text(0.97, y, f'{pk:.2f}', fontsize=8.4, va='center', ha='right')
    y -= 0.155
ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 0.20, boxstyle='round,pad=0.012',
                            fc='#fdecea', ec=RED, lw=1.2))
ax.text(0.5, 0.10, 'OFF 는 IL_R10_r 이 100 % 결정.\n'
        '경로힘 조건에서는 LTpL_L5 로 순위가 뒤바뀐다.\n'
        '→ ES peak 는 재분배 상황에서 정보를 잃는다.',
        ha='center', va='center', fontsize=8.0, linespacing=1.6)

# ── (2) 3지표 병기 ────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 1:]); panel(ax, '(2) ★ 3지표 병기 — ES peak 단독이면 개선이 안 보인다')
ROWS = ['(i) 커플 T1↔골반 16.5', '(ii) 커플 L1↔골반', '(iii) 경로힘 L1→허벅지',
        '(iv) 경로힘 T8→허벅지', '경로힘 T12→허벅지', '경로힘 T4→허벅지',
        '참고: 커플 T1↔골반 24']
x = np.arange(len(ROWS))
w = 0.26
for j, (key, lab, c) in enumerate((('rel_peak', '(a) ES peak', '0.62'),
                                   ('rel_act', '(b) 활성도 합', GREEN),
                                   ('rel_force', '(c) 근력 합', BLUE))):
    v = [C[r][key] for r in ROWS]
    ax.bar(x + (j - 1) * w, v, w, color=c, ec='k', lw=.6, label=lab)
    for xi, vv in zip(x + (j - 1) * w, v):
        ax.text(xi, vv - 1.4, f'{vv:+.1f}', ha='center', va='top', fontsize=7.2,
                rotation=90)
ax.axhline(0, color='k', lw=1)
ax.set_xticks(x)
ax.set_xticklabels([r.replace(' 경로힘', '\n경로힘').replace('참고: ', '참고\n')
                    .replace('(i) 커플', '(i)\n커플').replace('(ii) 커플', '(ii)\n커플')
                    .replace('(iii) ', '(iii)\n').replace('(iv) ', '(iv)\n')
                    for r in ROWS], fontsize=7.4, linespacing=1.3)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=9)
ax.legend(fontsize=8.2, loc='lower left'); ax.grid(axis='y', alpha=.3)
ax.set_ylim(-40, 12)
k = '(iv) 경로힘 T8→허벅지'
ax.annotate('', xy=(3 + w, C[k]['rel_act']), xytext=(3 - w, C[k]['rel_peak']),
            arrowprops=dict(arrowstyle='<->', color=RED, lw=1.8))
ax.text(3.55, -11, f"(iv) peak {C[k]['rel_peak']:+.1f} % 인데\n"
        f"활성도 합은 {C[k]['rel_act']:+.1f} %", fontsize=8.4, color=RED,
        fontweight='bold', linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.32', fc='white', ec=RED, lw=1.1))

# ── (3) LTpL 구간 vs 슈트 보조 ────────────────────────────────
ax = fig.add_subplot(gs[1, 0]); panel(ax, '(3) ★ LTpL 잔존 증가의 원인')
J = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']
DEM = [130.29, 116.06, 103.43, 92.61, 83.26]
y = np.arange(len(J))[::-1]
for tag, c, lab, off in (('T8', ORANGE, 'T8 → 허벅지 (현 하단)', +0.18),
                         ('T8_sacfem', GREEN, 'T8 → 천골경유 → 허벅지', -0.18)):
    r = [BM[tag][j] / d * 100 for j, d in zip(J, DEM)]
    ax.barh(y + off, r, 0.34, color=c, ec='k', lw=.6, label=lab)
    for yi, vv in zip(y + off, r):
        ax.text(vv + 0.4, yi, f'{vv:.1f}%', va='center', fontsize=7.6)
ax.set_yticks(y); ax.set_yticklabels([j.replace('_FE', '') for j in J], fontsize=8.6)
ax.set_xlabel('보조 / 요구 비율 (%)', fontsize=8.8)
ax.legend(fontsize=7.4, loc='upper right', framealpha=.95); ax.grid(axis='x', alpha=.3)
ax.set_xlim(0, 30)
ax.text(0.98, 0.06, 'LTpL_L5 는 sacrum→lumbar5 로 L5_S1 하나만 교차.\n'
        'L5_S1 이 구조적 저보조 구간 — 천골 경유로 7.3 → 12.9 %',
        transform=ax.transAxes, fontsize=7.6, linespacing=1.5, color=RED, ha='right',
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=RED, lw=0.9))

# ── (4) 하단 고정 스윕 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1]); panel(ax, '(4) ★ 하단 고정 스윕 — 3지표')
BOT = [('T8→허벅지\n(현 하단)', '(iv) 경로힘 T8→허벅지'),
       ('T8→천골', 'T8→천골'), ('T8→장골능', 'T8→장골능'),
       ('T8→천골경유\n→허벅지', 'T8→천골경유→허벅지'),
       ('L1→천골경유\n→허벅지', 'L1→천골경유→허벅지')]
x = np.arange(len(BOT))
for j, (key, lab, c) in enumerate((('rel_peak', '(a) peak', '0.62'),
                                   ('rel_act', '(b) 활성도 합', GREEN),
                                   ('rel_force', '(c) 근력 합', BLUE))):
    v = [C[k][key] for _, k in BOT]
    ax.bar(x + (j - 1) * 0.26, v, 0.26, color=c, ec='k', lw=.6, label=lab)
ax.axhline(0, color='k', lw=1)
ax.axhline(C['(i) 커플 T1↔골반 16.5']['rel_act'], color=PURPLE, ls='--', lw=1.5)
ax.text(len(BOT) - 0.45, C['(i) 커플 T1↔골반 16.5']['rel_act'] - 1.6,
        f"이상적 분산 부여 (b) {C['(i) 커플 T1↔골반 16.5']['rel_act']:+.1f} %",
        fontsize=7.6, color=PURPLE, ha='right')
ax.set_xticks(x); ax.set_xticklabels([l for l, _ in BOT], fontsize=7.4, linespacing=1.3)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=8.8)
ax.legend(fontsize=7.6, loc='lower left'); ax.grid(axis='y', alpha=.3)
_ref = C['(i) 커플 T1↔골반 16.5']
_best = C['T8→천골경유→허벅지']
ax.text(0.5, 0.97, f"★ T8 + 천골경유 = 이상적 분산 부여의 "
        f"peak {_best['rel_peak']/_ref['rel_peak']*100:.0f} % · "
        f"활성도합 {_best['rel_act']/_ref['rel_act']*100:.0f} % · "
        f"근력합 {_best['rel_force']/_ref['rel_force']*100:.0f} %",
        transform=ax.transAxes, ha='center', va='top', fontsize=8.0,
        fontweight='bold', color=GREEN,
        bbox=dict(boxstyle='round,pad=0.32', fc='#eaf6ec', ec=GREEN, lw=1.1))
ax.set_ylim(-26, 24)

# ── (5) LTpL 변화율 ───────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(5) 조건별 LTpL 변화율')
ALL = [('L1→허벅지\n(현 하드웨어)', '(iii) 경로힘 L1→허벅지'),
       ('T8→허벅지', '(iv) 경로힘 T8→허벅지'),
       ('T8→천골', 'T8→천골'),
       ('T8→천골경유\n→허벅지', 'T8→천골경유→허벅지'),
       ('커플 T1↔골반\n16.5', '(i) 커플 T1↔골반 16.5')]
x = np.arange(len(ALL))
lt = [100 * (C[k]['group']['LTpL'] - OFFD['group']['LTpL']) / OFFD['group']['LTpL']
      for _, k in ALL]
cols = [RED if v > 5 else (GREEN if v < -5 else ORANGE) for v in lt]
ax.bar(x, lt, 0.55, color=cols, ec='k', lw=.7)
for xi, v in zip(x, lt):
    ax.text(xi, v + (1.0 if v >= 0 else -2.2), f'{v:+.1f} %', ha='center',
            fontsize=8.6, fontweight='bold')
ax.axhline(0, color='k', lw=1)
ax.set_xticks(x); ax.set_xticklabels([l for l, _ in ALL], fontsize=7.4, linespacing=1.3)
ax.set_ylabel('LTpL peak 변화율 (%)', fontsize=8.8)
ax.grid(axis='y', alpha=.3)
ax.set_ylim(min(lt) - 8, max(lt) + 8)

P = f'{OUT}/metrics_ltpl_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)

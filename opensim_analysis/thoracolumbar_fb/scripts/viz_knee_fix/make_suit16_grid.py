"""[6] 16 N·m 실검증 + 설계 레버 + 팔꿈치 근육 + 축벡터 검증 그리드."""
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

D = '/data/suit_multijoint'
OUT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint')
os.makedirs(OUT, exist_ok=True)
R = json.load(open('/data/suit_16Nm/results.json'))
EL = json.load(open(f'{D}/elbow_check.json'))
ES = json.load(open(f'{D}/elbow_ref_sens.json'))
AX = json.load(open(f'{D}/axis_table.json'))
GREEN, RED, ORANGE, BLUE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0'

fig = plt.figure(figsize=(17.0, 11.6))
gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.28,
                      left=0.055, right=0.978, top=0.885, bottom=0.065)
fig.suptitle('L-01 (C) 병기 확정 — 16 N·m 실검증 · 설계 레버 · 팔꿈치 근육',
             fontsize=14.5, fontweight='bold', y=0.958)
fig.text(0.5, 0.922,
         '스툽 · 모델 해시 ca12f321326e · tight reserve · OFF 재사용  |  '
         '토크는 독립변수, 두 조건은 곡선 위의 두 지점  |  2026-08-16',
         ha='center', fontsize=9.3, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


# ── (1) 용량–반응 곡선 ────────────────────────────────────────
ax = fig.add_subplot(gs[0, :2])
panel(ax, '(1) ★ 용량–반응 — 현 하드웨어 조건(16 N·m 실측)과 설계 목표 조건(24 N·m)')
e24 = R['ref24']['eff']
slope = R['linearity']['slope']
xs = np.linspace(0, 33, 100)
ax.plot(xs, slope * xs, '--', color='0.55', lw=1.8,
        label=f'(0, 0)–(24, {e24:+.1f}) 직선  {slope:.3f} %/N·m')
PTS = [('couple16', 'o', BLUE, '토크 커플 16.5 N·m (선형성 시험)'),
       ('path16', 'D', GREEN, '경로힘 — 현 하드웨어 조건'),
       ('leverA', '^', RED, '(A) 보조력 200 N'),
       ('leverC', 's', ORANGE, '(C) 모멘트 암 +20 mm'),
       ('leverB', 'v', '#8a6fbf', '(B) 강성 k=20')]
for k, mk, c, lab in PTS:
    d = R[k]
    ax.plot(d['torque'], d['eff'], mk, color=c, ms=11, mec='k', mew=1.0, label=lab, zorder=5)
    _off = {'couple16': (8, -14), 'path16': (-52, 4), 'leverA': (10, -4),
            'leverC': (10, -4), 'leverB': (10, 8)}.get(k, (8, -12))
    ax.annotate(f"{d['eff']:+.1f} %", (d['torque'], d['eff']), textcoords='offset points',
                xytext=_off, fontsize=8.4, fontweight='bold', color=c)
ax.plot(24.0, e24, '*', color='k', ms=18, mec='k', zorder=6, label='설계 목표 조건 24 N·m (기존)')
ax.annotate(f'{e24:+.1f} %', (24.0, e24), textcoords='offset points', xytext=(8, 6),
            fontsize=9.2, fontweight='bold')
ax.axvspan(15.7, 17.8, color=GREEN, alpha=0.15)
ax.text(16.75, ax.get_ylim()[1] * 0.06, '현 하드웨어\n15.7~17.8 N·m', ha='center',
        fontsize=8.2, color=GREEN, linespacing=1.4)
ax.set_xlabel('허리 보조 토크, 양측 합 (N·m)', fontsize=9)
ax.set_ylabel('ES peak 변화 (%) — 창내 평균', fontsize=9)
ax.grid(alpha=.3); ax.legend(fontsize=7.8, loc='lower left'); ax.set_xlim(0, 33)
ax.text(0.5, 0.06, '⚠ 선형성 이탈 — 토크커플 16.5 는 직선보다 20.6 % 더 크고,\n경로힘은 직선에서 완전히 벗어난다(효과 ≈ 0). 지시대로 여기서 중단·보고.',
        transform=ax.transAxes, ha='center', fontsize=8.4, linespacing=1.5,
        color=RED, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.35', fc='#fdecea', ec=RED, lw=1.2))

# ── (2) 근육군 재분배 진단 ───────────────────────────────────
ax = fig.add_subplot(gs[0, 2]); panel(ax, '(2) ★ 왜 경로힘은 효과가 없나 — 근육군 재분배')
G = R['groups']
labs = list(G.keys())
x = np.arange(len(labs))
w = 0.2
SER = [('OFF', 'OFF', '0.6'), ('path16', '경로힘 16.5', RED),
       ('couple16', '토크커플 16.5', BLUE), ('24', '토크커플 24', GREEN)]
for j, (k, lab, c) in enumerate(SER):
    ax.bar(x + (j - 1.5) * w, [G[l][k] for l in labs], w, color=c, ec='k', lw=.6, label=lab)
ax.set_xticks(x)
ax.set_xticklabels([l.split(' ')[0] for l in labs], fontsize=8.6)
ax.set_ylabel('창내 peak 평균 (%)', fontsize=8.8)
ax.legend(fontsize=7.4, ncol=2); ax.grid(axis='y', alpha=.3)
ax.set_ylim(0, 80)
for l, xi in zip(labs, x):
    d = G[l]['path16'] - G[l]['OFF']
    ax.text(xi - 0.5 * w, G[l]['path16'] + 1.5, f'{d:+.0f}', ha='center', fontsize=7.8,
            fontweight='bold', color=RED if d > 0 else GREEN)
ax.text(0.5, 0.055, '경로힘은 IL 을 조금 낮추지만 LTpL·LTpT 를 크게 올린다 → 순효과 ≈ 0.\n'
        '슈트가 L1→허벅지만 걸쳐 흉추 레벨에는 보조가 가지 않는다.',
        transform=ax.transAxes, ha='center', fontsize=8.0, linespacing=1.5, color='0.25',
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.6', lw=0.7))

# ── (3) 설계 레버 ─────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0]); panel(ax, '(3) ★ 설계 레버 3조건 — 경로힘 구성에서는 모두 악화')
base = R['path16']
LV = [('기준\n100 N·m·k=5', base), ('(A)\n힘 2배', R['leverA']),
      ('(B)\n강성 20', R['leverB']), ('(C)\n모멘트암\n+20 mm', R['leverC'])]
x = np.arange(len(LV))
cols = ['0.6', RED, '#8a6fbf', ORANGE]
ax.bar(x, [abs(d['eff']) for _, d in LV], 0.55, color=cols, ec='k', lw=.7)
for xi, (_, d) in zip(x, LV):
    ax.text(xi, abs(d['eff']) + 0.5, f"{d['eff']:+.1f} %", ha='center',
            fontsize=8.8, fontweight='bold')
    ax.text(xi, -2.4, f"{d['torque']:.1f} N·m", ha='center', fontsize=7.8, color='0.4')
ax.axhline(abs(base['eff']), color='0.5', ls=':', lw=1.4)
ax.set_xticks(x); ax.set_xticklabels([l for l, _ in LV], fontsize=8.0, linespacing=1.35)
ax.set_ylabel('ES peak 변화율 (%)  — 양수 = 악화', fontsize=8.8)
ax.set_ylim(-4, max(abs(d['eff']) for _, d in LV) * 1.25)
ax.grid(axis='y', alpha=.3)
ax.text(0.5, 0.90, '막대 아래 = 그 조건의 보조 토크', transform=ax.transAxes,
        ha='center', fontsize=8.0, color='0.35')

# ── (4) 팔꿈치 모멘트–각도 ────────────────────────────────────
ax = fig.add_subplot(gs[1, 1]); panel(ax, '(4) 팔꿈치 굽힘 모멘트–각도')
rows = EL['rows']
a = [r['angle'] for r in rows]
fl = [r['flex'] for r in rows]
ex = [r['ext'] for r in rows]
ax.axhspan(60, 80, color=GREEN, alpha=0.16, label='문헌 굴곡 60~80 N·m')
ax.axhspan(-50, -40, color=BLUE, alpha=0.14, label='문헌 신전 40~50 N·m')
ax.plot(a, fl, 'o-', color=RED, lw=2.2, ms=5, mec='k', label='굴근 합 (BIC+BRA+BRD)')
ax.plot(a, ex, 's-', color=BLUE, lw=1.8, ms=4, mec='k', label='신근 합 (TRI)')
pk = EL['peak']
ax.plot(pk['angle'], pk['flex'], '*', color='k', ms=17, zorder=5)
ax.annotate(f"최대 {pk['flex']:.1f} N·m @ {pk['angle']}°",
            (pk['angle'], pk['flex']), textcoords='offset points', xytext=(-10, 12),
            fontsize=8.6, fontweight='bold')
ax.axhline(0, color='0.5', lw=.8)
ax.set_xlabel('팔꿈치 굴곡각 (°)', fontsize=8.8)
ax.set_ylabel('등척 모멘트 (N·m)', fontsize=8.8)
ax.legend(fontsize=7.4, loc='lower left'); ax.grid(alpha=.3)
ok_a, ok_b = EL['ok_a'], EL['ok_b']
_ga = '통과' if ok_a else f"초과 +{pk['flex'] - 80:.1f} N·m"
_gb = '통과' if ok_b else '벗어남'
ax.text(0.5, 0.30, f'(a) 60~80 N·m : {_ga}   (b) 피크 위치 : {_gb}',
        transform=ax.transAxes, ha='center', fontsize=8.2, fontweight='bold',
        color=GREEN if (ok_a and ok_b) else ORANGE,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.6', lw=0.8))

# ── (5) 축벡터 표 ─────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(5) ★ 상지 좌표 축벡터 — 이름이 아니라 축으로 판단')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.0, 0.96, '좌표', fontsize=8.4, fontweight='bold')
ax.text(0.34, 0.96, '축벡터', fontsize=8.4, fontweight='bold')
ax.text(0.80, 0.96, '실제 운동면', fontsize=8.4, fontweight='bold')
ax.plot([0, 1], [0.925, 0.925], color='k', lw=1.0)
y = 0.83
SH = {'shoulder_elv_r': '관상면\n외전/내전', 'elv_angle_r': '**시상면**\n굴곡/신전',
      'shoulder_rot_r': '수평면\n회전', 'elbow_flexion_r': '**시상면**\n굴곡/신전',
      'pro_sup_r': '회내/회외'}
for r in AX:
    c = r['coord']
    if c not in SH:
        continue
    key = SH[c].replace('**', '')
    bold = '**' in SH[c]
    ax.text(0.0, y, c[:-2] if c.endswith('_r') else c, fontsize=8.0, family='monospace')
    v = r['axis']
    ax.text(0.34, y, f'({v[0]:+.3f}, {v[1]:+.3f}, {v[2]:+.3f})', fontsize=7.6,
            family='monospace')
    ax.text(0.80, y + 0.018, key, fontsize=7.8, linespacing=1.35,
            fontweight='bold' if bold else 'normal', color=RED if bold else '0.3')
    y -= 0.125
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.26, boxstyle='round,pad=0.012',
                            fc='#fdecea', ec=RED, lw=1.2))
ax.text(0.5, 0.15, '⚠ shoulder_elv 는 이름과 달리 관상면 외전축이다.\n'
        '앞으로 든 하중의 시상면 부하는 elv_angle 에 실린다.\n'
        '삼각근 보조 효과는 6자유도 합계 또는 elv_angle 기준으로 산출.\n'
        'tight 전후 근육 비중은 6자유도 합계 3.9 % → 98.6 %.',
        ha='center', va='center', fontsize=8.0, linespacing=1.55)

P = f'{OUT}/suit16_verification_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)

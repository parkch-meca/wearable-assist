"""[6] 복합관절 슈트 1단계 검증 그리드.

측정값만 옮긴다. 보류된 항목은 보류 사유를 그대로 표시한다.
"""
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

OUT = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint'
os.makedirs(OUT, exist_ok=True)
R = json.load(open('/data/suit_multijoint/suit_analysis.json'))
MA = json.load(open('/data/suit_multijoint/moment_arms.json'))
SH = None
p = '/data/suit_multijoint/shoulder_tight.json'
if os.path.exists(p):
    SH = json.load(open(p))

GREEN, RED, ORANGE, BLUE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0'
KS = ['2.0', '5.0', '8.0', '20.0']
KC = {'2.0': '#9ecae1', '5.0': '#4c72b0', '8.0': '#1f4e79', '20.0': '#c44e52'}

fig = plt.figure(figsize=(17.0, 12.4))
gs = fig.add_gridspec(3, 3, hspace=0.62, wspace=0.30,
                      left=0.055, right=0.978, top=0.895, bottom=0.055)
fig.suptitle('복합관절 슈트 1단계 — 직렬탄성 PathActuator 모델 검증',
             fontsize=14.5, fontweight='bold', y=0.963)
fig.text(0.5, 0.928,
         'SMA 100 N + 직렬 스프링 · 메쉬 리미터 Active 200 mm · 60 ℃ 수축률 30 %  |  '
         '부착점은 PDF 사진 판독 추정치  |  2026-08-03',
         ha='center', fontsize=9.3, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


# ── (1) 캘리브레이션 ────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 0]); panel(ax, '(1) 캘리브레이션 — 직립 60 ℃ 밴드 변위')
cal = R['calibration']
ks = [float(k) for k in KS]
disp = [cal[k]['x'] for k in KS]
ax.axhspan(10, 15, color=GREEN, alpha=0.16, label='관찰 10~15 mm')
ax.bar(range(len(KS)), disp, 0.55,
       color=[GREEN if cal[k]['ok'] else RED for k in KS], ec='k', lw=.7)
for i, (k, v) in enumerate(zip(KS, disp)):
    ax.text(i, v + 0.6, f'{v:.1f}', ha='center', fontsize=8.6, fontweight='bold')
    ax.text(i, -3.0, f"T0={cal[k]['T0']:.0f} N\nF={cal[k]['F']:.0f} N",
            ha='center', va='top', fontsize=7.6, linespacing=1.4, color='0.35')
ax.axhline(60, color='0.4', ls=':', lw=1.2)
ax.text(len(KS) - 0.5, 61, '무부하 기대 수축 60 mm', fontsize=7.8, ha='right', color='0.35')
ax.set_xticks(range(len(KS))); ax.set_xticklabels([f'k={k}' for k in KS], fontsize=8.6)
ax.set_ylabel('허벅지 밴드 상승 (mm)', fontsize=8.8)
ax.set_ylim(-15, 68); ax.legend(fontsize=8, loc='upper right')
ax.text(0.5, -0.30, 'k=2/5/8 전부 관찰 범위 재현 → PASS.  k=20 은 고정부 보강 가상 조건',
        transform=ax.transAxes, ha='center', fontsize=8.2, color='0.3')

# ── (2) ΔL + SMA/탄성 분배 ─────────────────────────────────────
CASES = [('waist_stoop', '허리 (스툽, 고관절 포함)', '요추 굴곡 합 (°)'),
         ('shoulder_flex', '어깨 굴곡', '어깨 굴곡 (°)'),
         ('elbow_flex', '팔꿈치 굴곡', '팔꿈치 굴곡 (°)')]
fig.text(0.372, 0.906, '(2) 부위별 관절각 vs 경로 신장 ΔL — SMA 수축분 / 탄성 신장분 (k=5)',
         fontsize=10.4, fontweight='bold')
inner = gs[0, 1:].subgridspec(1, 3, wspace=0.36)
for j, (key, lab, xl) in enumerate(CASES):
    a = fig.add_subplot(inner[0, j])
    S = R['stiffness'][key]['5.0']
    x = [r['angle'] for r in S]
    dl = np.array([r['dL'] for r in S])
    xs = np.array([r['x_series'] for r in S])
    xm = np.array([r['x_sma'] for r in S])
    a.plot(x, dl, color='k', lw=2.0, label='경로 ΔL')
    a.fill_between(x, 0, xm, color='#f0a04b', alpha=.75, label='SMA 수축분')
    a.fill_between(x, xm, xm + np.maximum(xs - xm, 0) * 0, color='none')
    a.plot(x, xs, color=BLUE, lw=1.6, ls='--', label='탄성 신장분')
    sl = [r['angle'] for r in S if r['slack']]
    if sl:
        a.axvline(min(sl), color=RED, lw=1.4, ls=':')
        a.text(min(sl), a.get_ylim()[1] * 0.92, f' 이완 {min(sl):.0f}°',
               fontsize=7.6, color=RED)
    a.axhline(0, color='0.5', lw=.8)
    a.set_title(lab, fontsize=9.0, pad=4)
    a.set_xlabel(xl, fontsize=8.4)
    if j == 0:
        a.set_ylabel('길이 (mm)', fontsize=8.6)
        a.legend(fontsize=7.2, loc='lower right')
    a.grid(alpha=.3)

# ── (3) 허리 보조토크 vs 24 N·m ────────────────────────────────
ax = fig.add_subplot(gs[1, :2])
panel(ax, '(3) ★ 허리 보조 토크 (양측 합) — 강성 스윕 vs 기존 5동작 24 N·m 상수 가정')
for k in KS:
    S = R['stiffness']['waist_stoop'][k]
    ax.plot([r['angle'] for r in S], [abs(r['tau']) * 2 for r in S],
            color=KC[k], lw=2.0, label=f'PathActuator k={k} N/mm')
ax.axhline(24, color=RED, lw=2.4, ls='--')
ax.text(ax.get_xlim()[1], 24.7, '기존 5동작 가정 24 N·m  (200 N × 0.12 m)',
        fontsize=9.0, color=RED, ha='right', fontweight='bold')
ax.set_xlabel('요추 굴곡 합 (°)', fontsize=9)
ax.set_ylabel('허리 보조 토크, 양측 합 (N·m)', fontsize=9)
ax.set_ylim(0, 27.5); ax.grid(alpha=.3); ax.legend(fontsize=8.2, loc='center left')
ax.annotate('', xy=(ax.get_xlim()[1] * 0.62, 24), xytext=(ax.get_xlim()[1] * 0.62, 10.4),
            arrowprops=dict(arrowstyle='<->', color=RED, lw=1.6))
ax.text(ax.get_xlim()[1] * 0.635, 17, '2.4배\n차이', fontsize=9.4, color=RED,
        fontweight='bold', va='center', linespacing=1.4)

# ── (4) 모멘트암 대조 ──────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(4) ★ 모멘트 암 대조 — 원인은 힘이 아니라 여기')
J = [j['joint'] for j in MA['joints']]
med = [j['es_med'] for j in MA['joints']]
mx = [j['es_max'] for j in MA['joints']]
su = [j['suit'] for j in MA['joints']]
y = np.arange(len(J))[::-1]
ax.barh(y + 0.22, mx, 0.30, color='#cfe3f7', ec='k', lw=.5, label='ES 최대 근속')
ax.barh(y + 0.22, med, 0.30, color=BLUE, ec='k', lw=.5, label='ES 중앙값')
ax.barh(y - 0.22, su, 0.30, color=ORANGE, ec='k', lw=.5, label='슈트 경로 (추정)')
ax.axvline(120, color=RED, lw=2.2, ls='--')
ax.text(120, len(J) - 0.35, ' 24 N·m 가\n 요구하는 값\n 120 mm', fontsize=8.2,
        color=RED, va='top', fontweight='bold', linespacing=1.4)
ax.set_yticks(y); ax.set_yticklabels([j.replace('_FE', '') for j in J], fontsize=8.4)
ax.set_xlabel('모멘트 암 (mm)', fontsize=8.8); ax.set_xlim(0, 145)
ax.legend(fontsize=7.6, loc='lower right'); ax.grid(axis='x', alpha=.3)

# ── (5) 후방 오프셋 민감도 ─────────────────────────────────────
ax = fig.add_subplot(gs[2, 0]); panel(ax, '(5) 부착점 후방 오프셋 민감도')
off = [o['off_mm'] for o in MA['offset']]
tau = [o['tau_Nm'] for o in MA['offset']]
ax.plot(off, tau, 'o-', color=ORANGE, lw=2.0, ms=6, mec='k')
ax.axhline(24, color=RED, ls='--', lw=1.8)
ax.text(off[0], 24.6, '24 N·m', fontsize=8.4, color=RED, fontweight='bold')
ax.axvline(50, color=GREEN, ls=':', lw=1.6)
ax.text(53, 30.5, '현재 추정\n50 mm', fontsize=8.0, color=GREEN, linespacing=1.4,
        bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=GREEN, lw=0.7))
ax.set_xlabel('부착점 후방 오프셋 (mm)', fontsize=8.8)
ax.set_ylabel('양측 보조 토크 (N·m)', fontsize=8.8); ax.grid(alpha=.3)
ax.text(0.5, 0.06, '24 N·m 를 맞추려면 의복이 등에서 12 cm 이상 떠 있어야 한다',
        transform=ax.transAxes, ha='center', fontsize=8.2, color='0.3',
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.6', lw=0.7))

# ── (6) 어깨 reserve before/after ──────────────────────────────
ax = fig.add_subplot(gs[2, 1]); panel(ax, '(6) 어깨 액추에이터 흡수 토크 — tight 전/후')
if SH:
    labs = [r['label'] for r in SH['bars']]
    b = [r['before'] for r in SH['bars']]
    a_ = [r['after'] for r in SH['bars']]
    x = np.arange(len(labs))
    ax.bar(x - 0.2, b, 0.4, color='0.62', ec='k', lw=.7, label='tight 전 (opt=1000)')
    ax.bar(x + 0.2, a_, 0.4, color=GREEN, ec='k', lw=.7, label='tight 후 (opt=5)')
    for xi, v in zip(x - 0.2, b):
        ax.text(xi, v * 1.05 + 0.05, f'{v:.2f}', ha='center', fontsize=7.8)
    for xi, v in zip(x + 0.2, a_):
        ax.text(xi, v * 1.05 + 0.05, f'{v:.2f}', ha='center', fontsize=7.8, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.0, rotation=12, ha='right')
    ax.set_ylabel('최대 |토크| (N·m)', fontsize=8.8)
    ax.legend(fontsize=7.8); ax.grid(axis='y', alpha=.3)
    ax.text(0.5, -0.36, SH['verdict'], transform=ax.transAxes, ha='center',
            fontsize=8.4, fontweight='bold', color=SH.get('color', '0.2'), linespacing=1.4)
else:
    ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0.02, 0.28), 0.96, 0.44, boxstyle='round,pad=0.02',
                                fc='#f4f4f4', ec='0.5', lw=1.2))
    ax.text(0.5, 0.5, '어깨 tight 재실행 진행 중\n\n'
            '모델 내장 CoordinateActuator 6개\nopt 1000 → 5 로 조임',
            ha='center', va='center', fontsize=9.4, linespacing=1.7)

# ── (7) 진행 상태 ──────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 2]); panel(ax, '(7) 지시 항목별 상태')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ITEMS = [('■0 실행 전 검증', '완료', GREEN),
         ('■1 사양 문서', '완료', GREEN),
         ('■2(1) 캘리브레이션', 'PASS', GREEN),
         ('■2(2)(3)(4)(6) 기하·스윕', '완료', GREEN),
         ('■2(5) 24 N·m 대조', '⚠ 유의차 → 중단', RED),
         ('■2(7) 설계 레버 비교', '보류', ORANGE),
         ('■3 부착점 후보', '완료', GREEN),
         ('■4 어깨 tight 점검', '진행 중' if not SH else '완료',
          ORANGE if not SH else GREEN),
         ('■5 팔꿈치 근육 추가', '보류', ORANGE)]
y = 0.96
for lab, st, c in ITEMS:
    ax.text(0.0, y, lab, fontsize=8.5)
    ax.text(0.70, y, st, fontsize=8.5, fontweight='bold', color=c)
    y -= 0.083
ax.add_patch(FancyBboxPatch((0.0, -0.03), 1.0, 0.17, boxstyle='round,pad=0.012',
                            fc='#fdecea', ec=RED, lw=1.3))
ax.text(0.5, 0.055, '보류 사유 — ES 감소율 산출은\n슈트 토크 크기를 전제로 한다.\n'
        '(3)(4) 판단 후 즉시 재개 가능.',
        ha='center', va='center', fontsize=8.2, linespacing=1.55)

P = f'{OUT}/suit_phase1_verification_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)

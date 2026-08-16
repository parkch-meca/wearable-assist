"""[D] 모멘트 암 재산출 + 어깨 토크 검산 검증 그리드."""
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
MA = json.load(open(f'{D}/moment_arm_fix.json'))
TB = json.load(open(f'{D}/torque_band.json'))
SC = json.load(open(f'{D}/shoulder_check.json'))
SA = json.load(open(f'{D}/shoulder_share_alldof.json'))
LUMB = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']
GREEN, RED, ORANGE, BLUE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0'

fig = plt.figure(figsize=(17.0, 11.4))
gs = fig.add_gridspec(2, 3, hspace=0.44, wspace=0.28,
                      left=0.055, right=0.978, top=0.885, bottom=0.065)
fig.suptitle('허리 슈트 모멘트 암 재산출 + 어깨 토크 검산',
             fontsize=14.5, fontweight='bold', y=0.958)
fig.text(0.5, 0.922,
         '경유점을 체표면(ES 후방 외피 + 피하 10 mm + 의복 5 mm)에 재배치  |  '
         '검증 게이트: 슈트 모멘트 암 > 해당 레벨 ES 최대 근속  |  2026-08-16',
         ha='center', fontsize=9.3, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


# ── (1) 레벨별 모멘트 암 4자 비교 ──────────────────────────────
ax = fig.add_subplot(gs[0, :2])
panel(ax, '(1) ★ 레벨별 모멘트 암 — ES 최대 근속 / 1차 추정(폐기) / 재산출 / 24 N·m 요구값')
env = MA['env']
conf = MA['cases']['밀착 +피하 10 mm']['ma']
bow = MA['cases']['들뜸 bowstring +피하 10 mm']['ma']
old = {'L5_S1_FE': 43.2, 'L4_L5_FE': 58.1, 'L3_L4_FE': 60.6,
       'L2_L3_FE': 55.5, 'L1_L2_FE': 46.7}
x = np.arange(len(LUMB))
w = 0.2
ax.bar(x - 1.5 * w, [env[c]['es_max'] for c in LUMB], w, color=BLUE, ec='k', lw=.6,
       label='ES 최대 근속 (기준선)')
ax.bar(x - 0.5 * w, [old[c] for c in LUMB], w, color='0.65', ec='k', lw=.6,
       label='1차 추정 (폐기) — ES 안쪽')
ax.bar(x + 0.5 * w, [conf[c] for c in LUMB], w, color=GREEN, ec='k', lw=.6,
       label='재산출 · 밀착')
ax.bar(x + 1.5 * w, [bow[c] for c in LUMB], w, color='#8fcf9f', ec='k', lw=.6,
       label='재산출 · 들뜸')
ax.axhline(120, color=RED, lw=2.2, ls='--')
ax.text(len(LUMB) - 0.4, 121.5, '24 N·m 가 요구하는 120 mm — 어떤 ES 근속보다도 크다',
        fontsize=8.8, color=RED, ha='right', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([c.replace('_FE', '') for c in LUMB], fontsize=9)
ax.set_ylabel('모멘트 암 (mm)', fontsize=9); ax.set_ylim(0, 152)
ax.legend(fontsize=8.2, loc='upper center', ncol=4, framealpha=.95); ax.grid(axis='y', alpha=.3)
for xi, c in zip(x + 0.5 * w, LUMB):
    ax.text(xi, conf[c] + 2, f'{conf[c]:.0f}', ha='center', fontsize=7.8,
            fontweight='bold', color=GREEN)

# ── (2) 게이트 판정 ────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 2]); panel(ax, '(2) 검증 게이트 — 조건별 통과 여부')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
y = 0.93
for lab in ['밀착 (ES외피+의복 5 mm)', '밀착 +피하 10 mm',
            '들뜸 bowstring (ES외피+의복)', '들뜸 bowstring +피하 10 mm']:
    c = MA['cases'][lab]
    n_ok = sum(1 for j in LUMB if c['ma'][j] > env[j]['es_max'])
    ok = c['gate']
    ax.text(0.0, y, lab, fontsize=8.4)
    ax.text(0.0, y - 0.055, f"평균 r {c['mean']:.1f} mm → {c['tau2']:.1f} N·m",
            fontsize=8.2, color='0.4')
    ax.text(0.97, y - 0.028, f'{n_ok}/5', fontsize=10.5, fontweight='bold',
            ha='right', color=GREEN if ok else RED)
    y -= 0.155
ax.add_patch(FancyBboxPatch((0.0, 0.05), 1.0, 0.26, boxstyle='round,pad=0.012',
                            fc='#fdf0e3', ec=ORANGE, lw=1.2))
ax.text(0.5, 0.18, '의복 5 mm 만으로는 2개 레벨 미달.\n'
        '슈트는 근육 표면이 아니라 피부 위에 놓이므로\n'
        '피하조직을 포함해야 전 레벨 통과한다.\n'
        '(피하 10 mm 는 가정 — L-02 민감도 대상)',
        ha='center', va='center', fontsize=8.2, linespacing=1.55)

# ── (3) 자세별 보조 토크 밴드 ──────────────────────────────────
ax = fig.add_subplot(gs[1, 0]); panel(ax, '(3) 자세별 보조 토크 밴드')
rows = TB['rows']
ang = [r['angle'] for r in rows]
tc = [r['tau_conform'] for r in rows]
tb = [r['tau_bow'] for r in rows]
ph = TB['physical']
ax.plot(ang, tc, 'o-', color=GREEN, lw=2.2, ms=6, mec='k', label='밀착 (복대 압박)')
ax.plot(ang, tb, 's--', color='0.6', lw=1.6, ms=5, mec='k', label='들뜸 (직선 근사)')
for a_, t_, p in zip(ang, tb, ph):
    if not p:
        ax.plot(a_, t_, 'x', color=RED, ms=11, mew=2.4)
ax.fill_between(ang, [min(a, b) if p else a for a, b, p in zip(tc, tb, ph)],
                [max(a, b) if p else a for a, b, p in zip(tc, tb, ph)],
                color=GREEN, alpha=0.18)
ax.axhline(24, color=RED, ls='--', lw=1.8)
ax.text(ang[-1], 24.6, '기존 가정 24 N·m', fontsize=8.4, color=RED,
        ha='right', fontweight='bold')
ax.set_xlabel('요추 굴곡 합 (°)', fontsize=8.8)
ax.set_ylabel('양측 보조 토크 (N·m)', fontsize=8.8)
ax.set_ylim(0, 27); ax.grid(alpha=.3); ax.legend(fontsize=8.0, loc='center left')
b = TB['band_physical']
ax.text(0.5, 0.06, f'물리적 성립 밴드  {b[0]:.1f} ~ {b[1]:.1f} N·m\n'
        '× = 직선이 신체를 관통 → 비물리 (밀착만 유효)',
        transform=ax.transAxes, ha='center', fontsize=8.0, linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.6', lw=0.7))

# ── (4) 시상면 단면 오버레이 ───────────────────────────────────
ax = fig.add_subplot(gs[1, 1]); panel(ax, '(4) 시상면 — 경유점 재배치 전/후')
SP = json.load(open(f'{D}/level_depths.json'))
ys = [SP[c]['jc'][1] for c in LUMB]
jx = [SP[c]['jc'][0] for c in LUMB]
bone = [SP[c]['jc'][0] - SP[c]['bone_depth'] / 1000 for c in LUMB]
esx = [SP[c]['jc'][0] - SP[c]['es_depth'] / 1000 for c in LUMB]
newx = [e - 0.015 for e in esx]
oldx = [j - o / 1000 for j, o in zip(jx, [old[c] for c in LUMB])]
ax.plot(jx, ys, 'o-', color='k', lw=1.6, ms=6, label='관절 중심 (척추)')
ax.plot(bone, ys, '^-', color='0.55', lw=1.4, ms=6, label='뼈 후방 표면')
ax.plot(esx, ys, 's-', color=BLUE, lw=1.6, ms=6, label='ES 근육 후방 외피')
ax.plot(oldx, ys, 'x--', color='0.6', lw=1.8, ms=9, mew=2.2, label='1차 경유점 (폐기)')
ax.plot(newx, ys, 'D-', color=GREEN, lw=2.4, ms=7, mec='k', label='재배치 경유점')
ax.set_xlabel('전후 위치 x (m) — 왼쪽이 후방', fontsize=8.8)
ax.set_ylabel('상하 위치 y (m)', fontsize=8.8)
ax.invert_xaxis(); ax.grid(alpha=.3); ax.legend(fontsize=7.6, loc='upper left')
ax.text(0.5, 0.045, '1차 경유점(×)이 ES 외피(■)보다 안쪽 = 근육 속',
        transform=ax.transAxes, ha='center', fontsize=8.2, color=RED,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=RED, lw=0.8))

# ── (5) 어깨 토크 검산 ─────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(5) ★ 어깨 토크 검산 — 손 검산 vs 시뮬레이션')
sel = [r for r in SC if abs(r['t'] - 3.6) < 0.05]
_DL = {'shoulder_elv_r': '어깨 거상\n(shoulder_elv)', 'elv_angle_r': '시상 굴곡\n(elv_angle)',
       'shoulder_rot_r': '어깨 회전\n(shoulder_rot)'}
labs = [_DL.get(r['dof'], r['dof']) for r in sel]
hand = [abs(r['hand_total']) for r in sel]
sim = [abs(r['so_total']) for r in sel]
x = np.arange(len(sel))
ax.bar(x - 0.2, hand, 0.4, color=ORANGE, ec='k', lw=.7, label='손 검산 (외력+팔자중)')
ax.bar(x + 0.2, sim, 0.4, color=BLUE, ec='k', lw=.7, label='시뮬레이션 (근육+액추+res)')
for xi, a_, b_ in zip(x, hand, sim):
    ax.text(xi, max(a_, b_) + 0.7, f'{abs(a_-b_)/max(a_,1e-9)*100:.1f} %',
            ha='center', fontsize=8.2, fontweight='bold', color=GREEN)
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.0, linespacing=1.4)
ax.set_ylabel('|토크| (N·m)  t = 3.6 s', fontsize=8.8)
ax.legend(fontsize=7.8, loc='upper right'); ax.grid(axis='y', alpha=.3)
ax.set_ylim(0, 30)
ax.text(0.5, 0.55, '막대 위 = 상대 오차\n\n'
        '20.8 N·m 는 shoulder_elv 가 아니라\nelv_angle(시상 굴곡축)에 있다.\n'
        '외력 작용점 오류 아님 — 축 선택 문제였다.',
        transform=ax.transAxes, ha='center', va='center', fontsize=8.2,
        linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.35', fc='#eaf6ec', ec=GREEN, lw=1.1))

P = f'{OUT}/moment_arm_verification_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)

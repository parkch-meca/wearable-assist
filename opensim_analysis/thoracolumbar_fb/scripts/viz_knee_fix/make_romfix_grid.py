"""[5] ROM 수정 + 좌팔 수정 재실행 검증 그리드.

수치를 재해석하지 않고 측정값만 옮긴다.
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

OUT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/shoulder_diag')
os.makedirs(OUT, exist_ok=True)
NEW = json.load(open('/data/romfix_unified/unified_numbers.json'))
OLD = json.load(open('/data/tight_unified/unified_numbers.json'))
FIX = json.load(open('/data/shoulder_diag/leftarm_fix.json'))
ORDER = ['squat', 'stoop', 'box', 'gait', 'carry']
NAME = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
        'gait': '맨몸 보행', 'carry': '박스 운반'}
CHANGED = {'stoop', 'box', 'carry'}
GREEN, RED, ORANGE = '#1a7f37', '#c44e52', '#b3541e'


def rel(o, n):
    o2, n2 = round(o, 2), round(n, 2)
    return round(100.0 * round(n2 - o2, 2) / o2, 1)


fig = plt.figure(figsize=(16.5, 11.4))
gs = fig.add_gridspec(3, 3, hspace=0.55, wspace=0.30,
                      left=0.055, right=0.978, top=0.900, bottom=0.055)
fig.suptitle('ROM 부호 수정 + 좌팔 운동학 수정 — 5동작 재실행 검증',
             fontsize=14.5, fontweight='bold', y=0.963)
fig.text(0.5, 0.928,
         '모델 ..._M1scap_armfix_rom.osim  |  운동학 수정: 스툽·박스 들기·박스 운반  |  '
         '스쿼트·보행은 무변경(= ROM 수정 회귀 검증)  |  2026-08-03',
         ha='center', fontsize=9.3, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.5, fontweight='bold', pad=8, loc='left')


# ── (1) ROM 수정 내용 ───────────────────────────────────────────
ax = fig.add_subplot(gs[0, 0]); panel(ax, '(1) ROM 수정 — 좌측을 우측 실측값으로')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
rows = [('shoulder_elv_l', '[−154.70, 0]', '[0, +154.70]'),
        ('shoulder_rot_l', '[−45.00, +90.84]', '[−90.44, +44.69]')]
y = 0.90
for nm, a, b in rows:
    ax.text(0.0, y, nm, fontsize=9.3, fontweight='bold', family='monospace')
    ax.text(0.05, y - 0.095, a, fontsize=8.8, family='monospace', color='0.45')
    ax.text(0.53, y - 0.095, '→', fontsize=10)
    ax.text(0.60, y - 0.095, b, fontsize=8.8, family='monospace', color=GREEN)
    y -= 0.245
ax.text(0.0, 0.36, '수정 후 검증', fontsize=9.2, fontweight='bold')
for i, s in enumerate(['좌우 동일값 입력 시 거울 자세: 최대 0.0010 cm',
                       'ROM 위반 6개 자세 전부 0건',
                       '중립자세 620근육 길이 변화 0.00000000 %',
                       'ES 76개 길이 변화 0.00000000 %',
                       '좌표 169개·총질량 77.969270 kg 불변',
                       '5동작 전 프레임 조립 성공 (재현오차 0)']):
    ax.text(0.04, 0.30 - i * 0.050, f'· {s}', fontsize=8.1)
ax.add_patch(FancyBboxPatch((0.0, -0.115), 1.0, 0.078, boxstyle='round,pad=0.010',
                            fc='#eaf6ec', ec=GREEN, lw=1.1))
ax.text(0.5, -0.076, 'ConstraintSet 0개 → 위반할 구속 자체가 없음', ha='center',
        va='center', fontsize=8.5, color=GREEN)

# ── (2) 좌팔 수정 효과 ──────────────────────────────────────────
ax = fig.add_subplot(gs[0, 1]); panel(ax, '(2) 좌팔 수정 — 손 미러오차')
labs, before, after = [], [], []
for k, v in FIX.items():
    labs.append(k)
    before.append(v['err_before'])
    after.append(max(v['err_after'], 1e-4))
x = np.arange(len(labs))
ax.bar(x - 0.2, before, 0.4, color=RED, ec='k', lw=.6, label='수정 전')
ax.bar(x + 0.2, after, 0.4, color=GREEN, ec='k', lw=.6, label='수정 후')
ax.set_yscale('log'); ax.set_ylabel('좌우 손 미러오차 (cm, 로그)', fontsize=8.8)
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.8)
ax.legend(fontsize=8.2, loc='upper right'); ax.grid(axis='y', alpha=.3, which='both')
for xi, v in zip(x - 0.2, before):
    ax.text(xi, v * 1.3, f'{v:.1f}', ha='center', fontsize=7.8)
ax.text(0.5, -0.30, '운반의 잔여 5.85 cm는 보행 몸통 회전 탓 —\n'
        '흉곽(thoracic1) 기준으로는 0.000 cm',
        transform=ax.transAxes, ha='center', fontsize=8.2, linespacing=1.5, color='0.3')

# ── (3) 회귀 검증 ───────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 2]); panel(ax, '(3) 회귀 검증 — 운동학 무변경 동작')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.0, 0.93, '스쿼트·보행은 .mot 를 바꾸지 않았으므로\n'
        '이 재실행이 곧 ROM 수정 단독의 회귀 검증이다.',
        fontsize=8.6, va='top', linespacing=1.55)
y = 0.72
for k in ('squat', 'gait'):
    d = max(abs(NEW[k][f] - OLD[k][f])
            for f in ('a_off', 'a_on', 'b_off', 'b_on', 'c_off', 'c_on'))
    ax.text(0.0, y, NAME[k], fontsize=9.3, fontweight='bold')
    ax.text(0.05, y - 0.075, '전 지표 최대 차이', fontsize=8.8,
            color=GREEN if d < 5e-3 else RED)
    ax.text(0.52, y - 0.075, f'{d:.2e} %p', fontsize=8.8, family='monospace',
            color=GREEN if d < 5e-3 else RED)
    ax.text(0.05, y - 0.145,
            f"효과(b) {rel(OLD[k]['b_off'], OLD[k]['b_on']):+.1f} % → "
            f"{rel(NEW[k]['b_off'], NEW[k]['b_on']):+.1f} %", fontsize=8.8)
    y -= 0.30
ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 0.135, boxstyle='round,pad=0.012',
                            fc='#eaf6ec', ec=GREEN, lw=1.2))
ax.text(0.5, 0.068, 'ROM 은 좌표의 허용 구간일 뿐이고, SO 재생 시\n'
        '값을 클램프하지 않는다 → 결과 불변 (실측 확인)',
        ha='center', va='center', fontsize=8.4, linespacing=1.5)

# ── (4) 주 지표 (b) 대조 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, :2]); panel(ax, '(4) 주 지표 (b) 창내 ES peak 평균 — 슈트 효과 (%)')
eo = [rel(OLD[k]['b_off'], OLD[k]['b_on']) for k in ORDER]
en = [rel(NEW[k]['b_off'], NEW[k]['b_on']) for k in ORDER]
x = np.arange(len(ORDER))
ax.bar(x - 0.2, eo, 0.4, color='0.62', ec='k', lw=.7, label='기존 (확정본)')
ax.bar(x + 0.2, en, 0.4, color=['#4c72b0' if k not in CHANGED else '#c44e52' for k in ORDER],
       ec='k', lw=.7, label='신규 (ROM+좌팔 수정)')
ax.axhline(0, color='k', lw=1)
for xi, v in zip(x - 0.2, eo):
    ax.text(xi, v + (1.4 if v >= 0 else -2.6), f'{v:+.1f}', ha='center', fontsize=8.6)
for xi, v in zip(x + 0.2, en):
    ax.text(xi, v + (1.4 if v >= 0 else -2.6), f'{v:+.1f}', ha='center', fontsize=8.6,
            fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{NAME[k]}\n({"운동학 수정" if k in CHANGED else "무변경"})'
                    for k in ORDER], fontsize=8.8, linespacing=1.6)
ax.set_ylabel('ES 부담 변화 (%)', fontsize=9)
ax.legend(fontsize=8.4, loc='upper left', framealpha=.95); ax.grid(axis='y', alpha=.3)
lo = min(min(eo), min(en)); hi = max(max(eo), max(en))
ax.set_ylim(lo - 9, hi + 17)

# ── (5) 세 지표 변화폭 ──────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(5) 지표별 효과 변화 (신규 − 기존, %p)')
w = 0.26
for j, mm in enumerate('abc'):
    d = [rel(NEW[k][f'{mm}_off'], NEW[k][f'{mm}_on'])
         - rel(OLD[k][f'{mm}_off'], OLD[k][f'{mm}_on']) for k in ORDER]
    ax.barh(np.arange(len(ORDER))[::-1] + (1 - j) * w, d, w, ec='k', lw=.6,
            label=f'({mm})')
ax.axvline(0, color='k', lw=1)
ax.set_yticks(np.arange(len(ORDER))[::-1])
ax.set_yticklabels([NAME[k] for k in ORDER], fontsize=8.6)
ax.set_xlabel('효과 변화 (%p)', fontsize=8.8)
ax.legend(fontsize=8, ncol=3, loc='lower right'); ax.grid(axis='x', alpha=.3)

# ── (6) 수치 대조표 ─────────────────────────────────────────────
ax = fig.add_subplot(gs[2, :2]); panel(ax, '(6) 수치 대조표 — 주 지표 (b)')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
cols = [0.0, 0.155, 0.275, 0.375, 0.475, 0.575, 0.675, 0.785, 0.895]
hdr = ['동작', '운동학', 'OFF 기존', 'OFF 신규', 'ON 기존', 'ON 신규',
       '효과 기존', '효과 신규', 'Δ효과']
for c, h in zip(cols, hdr):
    ax.text(c, 0.93, h, fontsize=8.7, fontweight='bold')
ax.plot([0, 1], [0.885, 0.885], color='k', lw=1.0)
y = 0.79
for k in ORDER:
    o, n = OLD[k], NEW[k]
    a, b = rel(o['b_off'], o['b_on']), rel(n['b_off'], n['b_on'])
    vals = [NAME[k], '수정' if k in CHANGED else '무변경',
            f"{o['b_off']:.2f}", f"{n['b_off']:.2f}",
            f"{o['b_on']:.2f}", f"{n['b_on']:.2f}",
            f'{a:+.1f} %', f'{b:+.1f} %', f'{b - a:+.1f} %p']
    for c, v in zip(cols, vals):
        col = 'k'
        if c == cols[-1]:
            col = GREEN if abs(b - a) < 0.5 else (ORANGE if abs(b - a) < 3 else RED)
        ax.text(c, y, v, fontsize=8.6, color=col,
                fontweight='bold' if c in (cols[-1], cols[-2]) else 'normal')
    y -= 0.145
ax.plot([0, 1], [y + 0.075, y + 0.075], color='0.6', lw=0.8)
ax.text(0.0, y - 0.01, '음수 = 슈트 착용 시 ES 부담 감소.  보행의 양수는 감소가 아니라 '
        '근육군 재분배 (§ 논문 참조).', fontsize=8.2, color='0.3')

# ── (7) 판정 ───────────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 2]); panel(ax, '(7) 판정')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
y = 0.92
for k in ORDER:
    a = rel(OLD[k]['b_off'], OLD[k]['b_on'])
    b = rel(NEW[k]['b_off'], NEW[k]['b_on'])
    d = abs(b - a)
    verd, col = ('불변', GREEN) if d < 0.5 else \
                (('경미 변화', ORANGE) if d < 3 else ('갱신 필요', RED))
    ax.text(0.0, y, NAME[k], fontsize=9.0)
    ax.text(0.52, y, f'{b - a:+.1f} %p', fontsize=8.8, color='0.35')
    ax.text(0.78, y, verd, fontsize=9.0, fontweight='bold', color=col)
    y -= 0.125
ax.add_patch(FancyBboxPatch((0.0, 0.03), 1.0, 0.25, boxstyle='round,pad=0.012',
                            fc='#f4f4f4', ec='0.45', lw=1.0))
ax.text(0.5, 0.155,
        '좌팔 오류는 OFF·ON 양쪽에 동일하게 들어가 있었으므로\n'
        '차분에서 상당 부분 상쇄됐다. 절대값(OFF·ON)이 더 크게\n'
        '움직이고 효과(차이)는 그보다 작게 움직인다.',
        ha='center', va='center', fontsize=8.2, linespacing=1.55)

P = f'{OUT}/romfix_rerun_verification_grid.png'
fig.savefig(P, dpi=155)
print('SAVED', P)

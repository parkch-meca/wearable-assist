"""[진단 산출물] 좌측 어깨 진단 결과 검증 그리드 PNG.

생성/검증 분리 원칙에 따라, 이 그림은 수치를 재해석하지 않고 측정값만 옮긴다.
"""
import os, json
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

D = '/data/shoulder_diag'
OUT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/'
       'shoulder_diag')
os.makedirs(OUT, exist_ok=True)
FIXT = json.load(open(f'{D}/fix_test.json'))
IMP = json.load(open(f'{D}/es_impact_corrected.json'))

fig = plt.figure(figsize=(16.5, 11.6))
gs = fig.add_gridspec(3, 3, hspace=0.52, wspace=0.30,
                      left=0.055, right=0.978, top=0.905, bottom=0.055)
fig.suptitle('좌측 어깨 자유도 정량 진단 — 다관절 슈트 선행 조건  (모델 미수정, 읽기 전용 진단)',
             fontsize=14, fontweight='bold', y=0.965)
fig.text(0.5, 0.932, '모델: MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim   |   '
         '2026-07-31   |   ★ 결론: 축은 정상, 결함은 ROM 부호 2개',
         ha='center', fontsize=9.5, color='0.3')

def panel(ax, title):
    ax.set_title(title, fontsize=10.5, fontweight='bold', pad=8, loc='left')

# ── (1) 축 대조: 전제 정정 ───────────────────────────────────────
ax = fig.add_subplot(gs[0, 0]); panel(ax, '(1) 어깨 관절 축 정의 — 전제 정정')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
rows = [('shoulder_elv', '(−0.99826, +0.0023, +0.058898)', '(+0.99826, −0.0023, +0.058898)'),
        ('shoulder_rot', '(+0.05889, −0.0389, +0.99750)', '(−0.05889, +0.0389, +0.99750)'),
        ('elv_angle',    '(0, +1, 0)', '(0, −1, 0)')]
ax.text(0.0, 0.93, '미러 기대식:  (ax, ay, az) → (−ax, −ay, +az)', fontsize=9,
        style='italic', color='0.25')
ax.text(0.0, 0.80, '좌표', fontsize=9, fontweight='bold')
ax.text(0.31, 0.80, '우측 축', fontsize=9, fontweight='bold')
ax.text(0.31, 0.73, '좌측 축 (실측)', fontsize=9, fontweight='bold')
y = 0.62
for nm, r, l in rows:
    ax.text(0.0, y - 0.035, nm, fontsize=8.4)
    ax.text(0.31, y, r, fontsize=7.9, family='monospace')
    ax.text(0.31, y - 0.070, l, fontsize=7.9, family='monospace')
    ax.text(0.955, y - 0.035, '✓', fontsize=13, color='#1a7f37', ha='center')
    y -= 0.185
ax.add_patch(FancyBboxPatch((0.0, 0.005), 1.0, 0.145, boxstyle='round,pad=0.012',
                            fc='#eaf6ec', ec='#1a7f37', lw=1.2))
ax.text(0.5, 0.078, '3개 축 모두 미러 규칙 정확히 만족 (오차 < 1e−6)\n'
        '→ “z성분이 미러 안 됨”이라는 기존 전제는 사실이 아님',
        ha='center', va='center', fontsize=8.6, linespacing=1.5)

# ── (2) ROM 대조: 진짜 결함 ─────────────────────────────────────
ax = fig.add_subplot(gs[0, 1]); panel(ax, '(2) ROM 대조 — 실제 결함 위치')
coords = ['shoulder_elv', 'shoulder_rot', 'elv_angle', 'elbow_flexion', 'pro_sup']
Rr = [(0, 154.70), (-90.44, 44.69), (-90, 155.16), (0, 155.27), (-90, 90)]
Ll = [(-154.70, 0), (-45.00, 90.84), (-90, 155.16), (0, 155.27), (-90, 90)]
yy = np.arange(len(coords))[::-1]
for i, (r, l) in enumerate(zip(Rr, Ll)):
    bad = not (abs(l[0] - r[0]) < .01 and abs(l[1] - r[1]) < .01)
    ax.barh(yy[i] + 0.19, r[1] - r[0], left=r[0], height=0.34,
            color='#4c72b0', ec='k', lw=.6)
    ax.barh(yy[i] - 0.19, l[1] - l[0], left=l[0], height=0.34,
            color='#c44e52' if bad else '#8fa8cc', ec='k', lw=.6)
    if bad:
        ax.text(163, yy[i], '×', fontsize=17, color='#c44e52', va='center', ha='center', fontweight='bold')
    else:
        ax.text(163, yy[i], '✓', fontsize=12, color='#1a7f37', va='center')
ax.axvline(0, color='k', lw=.9, ls='--')
ax.set_yticks(yy); ax.set_yticklabels(coords, fontsize=8.6)
ax.set_xlabel('관절각 범위 (°)', fontsize=9); ax.set_xlim(-175, 185)
ax.set_ylim(-0.7, len(coords) - 0.3)
ax.plot([], [], 's', color='#4c72b0', label='우측 (_r)')
ax.plot([], [], 's', color='#c44e52', label='좌측 (_l)')
ax.legend(fontsize=8, loc='lower left', framealpha=.95)
ax.text(0.5, -0.30, 'shoulder_elv_l · shoulder_rot_l 만 부호가 반대 → 미러 자세 입력 불가',
        transform=ax.transAxes, ha='center', fontsize=8.6, color='#c44e52')

# ── (3) 수정 전/후 말단 오차 ────────────────────────────────────
ax = fig.add_subplot(gs[0, 2]); panel(ax, '(3) ROM 부호 수정 효과 (메모리상 시험)')
poses = [r['pose'] for r in FIXT['before']]
b = [r['pos_max'] for r in FIXT['before']]
a = [max(r['pos_max'], 1e-4) for r in FIXT['after']]
x = np.arange(len(poses))
ax.bar(x - 0.2, b, 0.4, color='#c44e52', ec='k', lw=.6, label='수정 전')
ax.bar(x + 0.2, a, 0.4, color='#1a7f37', ec='k', lw=.6, label='수정 후')
ax.set_yscale('log'); ax.set_ylabel('좌우 말단 미러 위치오차 (cm, 로그)', fontsize=8.8)
ax.set_xticks(x); ax.set_xticklabels(poses, rotation=28, ha='right', fontsize=8)
ax.legend(fontsize=8.2); ax.grid(axis='y', alpha=.3, which='both')
for xi, v in zip(x - 0.2, b):
    ax.text(xi, v * 1.25, f'{v:.1f}', ha='center', fontsize=7.4)
ax.text(0.5, 0.055, '최대 90.7 cm → 0.001 cm', transform=ax.transAxes,
        ha='center', fontsize=9.5, fontweight='bold', color='#1a7f37',
        bbox=dict(boxstyle='round,pad=0.30', fc='white', ec='#1a7f37', lw=1.0))

# ── (4) 근육 정의 대칭성 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0]); panel(ax, '(4) 어깨·팔꿈치 근육 좌우 정확도')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
items = [('어깨 거상을 지나는 근육 수', '우 26 / 좌 26', True),
         ('어깨 회전 / 견갑면각', '25 / 25,  20 / 20', True),
         ('경로점 개수·부착 body', '불일치 0건', True),
         ('경로점 미러오차 (ground 기준)', '최대 0.1 mm', True),
         ('Fmax · Lopt · Lts · 건막각', '최대 상대차 0.077 %', True),
         ('ROM 수정 후 길이 좌우차', '최대 0.005 %', True),
         ('ROM 수정 후 모멘트암 좌우차', '최대 0.017 %', True),
         ('팔꿈치 굴곡 구동 근육', '우 0 / 좌 0 개', False),
         ('전완 회내외 구동 근육', '우 0 / 좌 0 개', False)]
y = 0.945
for lb, val, ok in items:
    ax.text(0.0, y, lb, fontsize=8.5, va='center')
    ax.text(0.70, y, val, fontsize=8.5, va='center', fontweight='bold',
            color='#1a7f37' if ok else '#b3541e')
    ax.text(0.985, y, '✓' if ok else '⚠', fontsize=12, va='center', ha='center',
            color='#1a7f37' if ok else '#b3541e')
    y -= 0.098
ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 0.115, boxstyle='round,pad=0.012',
                            fc='#fdf0e3', ec='#b3541e', lw=1.2))
ax.text(0.5, 0.058, '근육 정의 자체는 좌우 완전 대칭 — 결함 없음.\n'
        '단, 팔꿈치·전완은 근육이 없고 reserve 액추에이터만 구동.',
        ha='center', va='center', fontsize=8.5, linespacing=1.5)

# ── (5) 기존 5동작 영향 ─────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1:]); panel(ax, '(5) 기존 5동작 결과에 대한 영향 — 동작별 의도 기준')
names = ['맨몸 스쿼트', '맨몸 스툽', '박스 들기', '맨몸 보행', '박스 운반']
frac = [IMP[n]['frac'] for n in names]
state = [IMP[n]['state'] for n in names]
intent = ['좌우대칭', '좌우대칭', '좌우대칭', '교대(anti-phase)', '좌우대칭']
cols = ['#1a7f37' if f < 2 else ('#b3541e' if f < 20 else '#c44e52') for f in frac]
xb = np.arange(len(names))
ax.bar(xb, frac, 0.55, color=cols, ec='k', lw=.7)
for xi, f, s, it in zip(xb, frac, state, intent):
    ax.text(xi, f + 2.2, f'{f:.1f} %', ha='center', fontsize=9.5, fontweight='bold')
    ax.text(xi, -3.0, f'의도 {it}\n{s}', ha='center', va='top', fontsize=7.8,
            linespacing=1.45, color='#1a7f37' if '일치' in s else '#c44e52')
ax.set_xticks(xb); ax.set_xticklabels(names, fontsize=9.2)
ax.set_ylabel('좌팔 오류로 인한 체간 굴곡 모멘트 오차\n(해당 동작 전체 모멘트 대비 %)', fontsize=8.8)
ax.set_ylim(-15, 90); ax.grid(axis='y', alpha=.3)
ax.axhline(2, color='#1a7f37', ls='--', lw=1, )
ax.text(0.52, 7.5, '2 % — 무시 가능', fontsize=7.8, color='#1a7f37', ha='center')
ax.axhline(20, color='#c44e52', ls='--', lw=1)
ax.text(0.52, 23.0, '20 % — 재해석 필요', fontsize=7.8, color='#c44e52', ha='center')
ax.text(1.05, 74, '박스 들기: 좌수가 박스에 닿지 않은 채\n98.1 N 외력이 부여됨 (좌우 손 51 cm 이격)',
        ha='center', fontsize=8.4, linespacing=1.45,
        bbox=dict(boxstyle='round,pad=0.35', fc='#fdecea', ec='#c44e52', lw=1.1))

# ── (6) 판정 ───────────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 0]); panel(ax, '(6) 기존 5동작 판정')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
JUD = [('맨몸 스쿼트', '(a) 무시 가능', 0.0, '#1a7f37'),
       ('맨몸 스툽',   '(a) 무시 가능', 1.3, '#1a7f37'),
       ('맨몸 보행',   '(a) 무시 가능', 4.6, '#1a7f37'),
       ('박스 운반',   '(b) 논문 각주', 35.7, '#b3541e'),
       ('박스 들기',   '(c) 재해석 필요', 59.7, '#c44e52')]
y = 0.90
for nm, jd, f, c in JUD:
    ax.text(0.0, y, nm, fontsize=9.2, va='center')
    ax.text(0.42, y, f'{f:.1f} %', fontsize=9, va='center', color='0.35')
    ax.text(0.62, y, jd, fontsize=9.2, va='center', fontweight='bold', color=c)
    y -= 0.135
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.22, boxstyle='round,pad=0.012',
                            fc='#f4f4f4', ec='0.45', lw=1.0))
ax.text(0.5, 0.13, '슈트 효과(ON−OFF)는 좌팔 오류가 OFF·ON에 동일하게\n'
        '들어가므로 부분 상쇄되나, 절대값과 비선형 재분배는 영향받음.\n'
        '정확한 크기는 재실행 없이는 확정 불가.',
        ha='center', va='center', fontsize=8.2, linespacing=1.55)

# ── (7) 수정 계획 ──────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 1]); panel(ax, '(7) 수정 방안 — 4개 숫자')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.0, 0.90, 'shoulder_elv_l', fontsize=9.4, fontweight='bold', family='monospace')
ax.text(0.06, 0.79, '[−154.70, 0]  →  [0, +154.70]', fontsize=9.2, family='monospace')
ax.text(0.0, 0.64, 'shoulder_rot_l', fontsize=9.4, fontweight='bold', family='monospace')
ax.text(0.06, 0.53, '[−45.00, +90.84]  →  [−90.44, +44.69]', fontsize=8.8, family='monospace')
ax.text(0.0, 0.37, '부작용 점검 (메모리 시험 결과)', fontsize=9, fontweight='bold')
for i, s in enumerate(['좌표 집합 169개 동일',
                       '중립자세 620근육 길이 변화 0.000000 %',
                       'ES 76개 길이 변화 0.000000 %',
                       'Constraint 0개 → 0개 (영향 없음)',
                       '기본자세 새 ROM 내에 포함']):
    ax.text(0.05, 0.28 - i * 0.058, f'· {s}', fontsize=8.4)
ax.add_patch(FancyBboxPatch((0.0, -0.045), 1.0, 0.075, boxstyle='round,pad=0.010',
                            fc='#eaf6ec', ec='#1a7f37', lw=1.1))
ax.text(0.5, -0.008, 'viz-mirror 시각 보정 완전 대체 가능', ha='center', va='center',
        fontsize=8.8, fontweight='bold', color='#1a7f37')

# ── (8) 다관절 슈트 선행 검토 ───────────────────────────────────
ax = fig.add_subplot(gs[2, 2]); panel(ax, '(8) 다관절 슈트 — 측정 가능 범위')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
CAP = [('허리 (ES 76개)', '측정 가능', '#1a7f37', '현재 논문 근거'),
       ('어깨 (좌우 26개)', '측정 가능', '#1a7f37', 'ROM 수정 후'),
       ('팔꿈치', '측정 불가', '#c44e52', '구동 근육 0개'),
       ('전완·손목', '측정 불가', '#c44e52', '구동 근육 0개')]
y = 0.90
for nm, st, c, note in CAP:
    ax.text(0.0, y, nm, fontsize=9.2, va='center')
    ax.text(0.52, y, st, fontsize=9.2, va='center', fontweight='bold', color=c)
    ax.text(0.52, y - 0.062, note, fontsize=7.8, va='center', color='0.4')
    y -= 0.175
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.20, boxstyle='round,pad=0.012',
                            fc='#fdf0e3', ec='#b3541e', lw=1.2))
ax.text(0.5, 0.12, '팔꿈치를 측정 대상에 넣으려면 상완이두·삼두를\n'
        '추가한 모델이 필요 — 현 모델로는 불가.\n'
        '어깨 액추에이터 6개도 부하를 흡수하므로 점검 필요.',
        ha='center', va='center', fontsize=8.2, linespacing=1.55)

P = f'{OUT}/shoulder_diag_verification_grid.png'
fig.savefig(P, dpi=155)
print('SAVED', P)

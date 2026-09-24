"""[4] 재개 작업 검증 그리드 — 용량–반응 곡선 · 들기 다부위 · 운반 대조 · 본 렌더 포스터.

한 장으로 이번 작업 전체를 검증할 수 있게 만든다 (Grid PNG Companion Protocol).
수치는 전부 실행 산출 json 에서 읽는다 — 손으로 적지 않는다.
  /data/suit_dose/dose.json        용량–반응 4점 × 3지표
  /data/suit_box/metrics.json      들기 5조건
  /data/suit_carry/metrics.json    운반 5조건 (기존, 대조용)
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

IMG = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint'
D = json.load(open('/data/suit_dose/dose.json'))
B = json.load(open('/data/suit_box/metrics.json'))
C = json.load(open('/data/suit_carry/metrics.json'))
GREEN, RED, ORANGE, BLUE, PURPLE, GREY = ('#1a7f37', '#c44e52', '#b3541e', '#4c72b0',
                                          '#7d5ba6', '0.55')
CONDS = ['waist', 'elbow', 'elbow_ext', 'all']
CLAB = {'waist': '허리만', 'elbow': '팔꿈치\n기본안', 'elbow_ext': '팔꿈치\n연장안',
        'all': '전체 ON'}
MET = [('peak', '(a) ES peak'), ('act_sum', '(b) 활성도 합'), ('force_sum', '(c) 근력 합')]


def rel(o, n):
    o2, n2 = round(o, 3), round(n, 3)
    return 100.0 * round(n2 - o2, 3) / o2 if abs(o2) > 1e-9 else float('nan')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


def barlab(ax, bars, vals, fmt='{:+.1f}', dy=0.6, fs=7.8):
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2,
                b.get_height() + (dy if b.get_height() >= 0 else -dy),
                fmt.format(v), ha='center',
                va='bottom' if b.get_height() >= 0 else 'top', fontsize=fs)


fig = plt.figure(figsize=(18.2, 14.6))
gs = fig.add_gridspec(3, 3, hspace=0.46, wspace=0.28, height_ratios=[1, 1, 1.18],
                      left=0.060, right=0.980, top=0.900, bottom=0.035)
fig.suptitle('재개 작업 검증 — 용량–반응 곡선(스툽) · 들기 20 kg 다부위 · 본 렌더 2종',
             fontsize=15.2, fontweight='bold', y=0.963)
fig.text(0.5, 0.932,
         '모델 ThoracolumbarFB v2.0 · 척추 reserve opt 5 · 다부위는 팔꿈치근 14개 + 팔 액추에이터 opt 5 '
         '(OFF 부터 재산출) · ⚠️ 5동작 논문 수치 불변 · 2026-09-24',
         ha='center', fontsize=9.0, color='0.3')

# ── (1) 용량–반응 곡선 (a) ES peak ────────────────────────────────
ax = fig.add_subplot(gs[0, 0])
panel(ax, '(1) ★ 용량–반응 곡선 — 토크커플 (스툽)')
pts = [(v['torque'], v['rel']['peak']) for k, v in D['points'].items()
       if v['kind'] == 'couple']
pts.sort()
x = [p[0] for p in pts]
y = [p[1] for p in pts]
e24 = y[-1]
ax.plot([0, 24], [0, e24], '--', color=GREY, lw=1.6, label='선형 (두 점 비례)')
ax.plot(x, y, 'o-', color=BLUE, lw=2.4, ms=8, label='실측 (토크커플)')
for xx, yy in pts:
    ax.annotate(f'{yy:+.1f} %', (xx, yy), textcoords='offset points',
                xytext=(6, 8), fontsize=8.2, color=BLUE)
pf = D['points'].get('경로힘 16.5 N·m (현 하드웨어 기하)')
if pf:
    ax.plot([16.5], [pf['rel']['peak']], 'X', color=RED, ms=13,
            label='경로힘 16.5 (현 하드웨어 기하)')
    ax.annotate(f"{pf['rel']['peak']:+.1f} %", (16.5, pf['rel']['peak']),
                textcoords='offset points', xytext=(8, -4), fontsize=8.2, color=RED)
ax.axvline(16.5, color=ORANGE, lw=1.4, ls=':')
ax.text(16.7, e24 * 0.35, '현 하드웨어\n16.5 N·m', color=ORANGE, fontsize=8.0,
        linespacing=1.4)
ax.set_xlabel('슈트 보조 토크 (N·m, 양측 합)', fontsize=8.8)
ax.set_ylabel('ES peak 변화율 (%)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=7.6, loc='lower left')

# ── (2) 3지표 정규화 — 오목성 ────────────────────────────────────
ax = fig.add_subplot(gs[0, 1])
panel(ax, '(2) 3지표 모두 오목 — 비례 배분은 과소평가')
ax.plot([0, 100], [0, 100], '--', color=GREY, lw=1.6, label='비례 (선형 가정)')
for (k, name), c in zip(MET, (BLUE, GREEN, PURPLE)):
    xs, ys = [], []
    for lab, v in D['points'].items():
        if v['kind'] != 'couple':
            continue
        e = D['points']['토크커플 24 N·m']['rel'][k]
        xs.append(v['torque'] / 24 * 100)
        ys.append(v['rel'][k] / e * 100 if abs(e) > 1e-9 else 0.0)
    o = np.argsort(xs)
    ax.plot(np.array(xs)[o], np.array(ys)[o], 'o-', color=c, lw=2.2, ms=7, label=name)
ax.set_xlabel('토크 (24 N·m 대비 %)', fontsize=8.8)
ax.set_ylabel('효과 (24 N·m 효과 대비 %)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=7.6, loc='upper left')
f16 = D['linearity']['peak@16.5']['frac24']
f8 = D['linearity']['peak@8.0']['frac24']
ax.text(0.97, 0.06, f'8 N·m(33 %) → {f8:.0f} %\n16.5 N·m(69 %) → {f16:.0f} %',
        transform=ax.transAxes, ha='right', fontsize=8.4, color=RED,
        fontweight='bold', linespacing=1.5)

# ── (3) 들기 5조건 ES 3지표 ──────────────────────────────────────
ax = fig.add_subplot(gs[0, 2])
panel(ax, '(3) 들기 20 kg — ES 3지표 (OFF 대비)')
w = 0.26
xs = np.arange(len(CONDS))
for i, ((k, name), c) in enumerate(zip(MET, (BLUE, GREEN, PURPLE))):
    v = [rel(B['res']['off']['ES'][k], B['res'][cc]['ES'][k]) for cc in CONDS]
    bars = ax.bar(xs + (i - 1) * w, v, w, color=c, label=name)
    barlab(ax, bars, v, dy=0.35, fs=7.0)
ax.axhline(0, color='k', lw=1.0)
ax.set_xticks(xs)
ax.set_xticklabels([CLAB[c] for c in CONDS], fontsize=8.2)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=8.8)
ax.grid(alpha=.3, axis='y')
ax.legend(fontsize=7.4)

# ── (4) 들기 부위별 주동근 ───────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
panel(ax, '(4) 들기 — 부위별 주동근 활성도 (창내 평균)')
GRPS = [('ES', 'ES 계열', BLUE), ('DELT', '삼각근', ORANGE), ('ELBFLX', '팔꿈치 굴근', GREEN)]
for i, (g, name, c) in enumerate(GRPS):
    v = [rel(B['res']['off'][g]['mean'], B['res'][cc][g]['mean']) for cc in CONDS]
    bars = ax.bar(xs + (i - 1) * w, v, w, color=c, label=name)
    barlab(ax, bars, v, dy=0.35, fs=7.0)
ax.axhline(0, color='k', lw=1.0)
ax.set_xticks(xs)
ax.set_xticklabels([CLAB[c] for c in CONDS], fontsize=8.2)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=8.8)
ax.grid(alpha=.3, axis='y')
ax.legend(fontsize=7.4)

# ── (5) 가산성 — 운반 vs 들기 ────────────────────────────────────
ax = fig.add_subplot(gs[1, 1])
panel(ax, '(5) ★ 가산성 — 전체 ON = 허리 + 팔꿈치 인가')
keys = [('ES.act_sum', 'ES 활성도 합'), ('ES.force_sum', 'ES 근력 합'),
        ('ES.peak', 'ES peak'), ('ELBFLX.mean', '팔꿈치 굴근 평균')]
xs2 = np.arange(len(keys))
for i, (M, lab, c) in enumerate(((C['add'], '운반 (기존)', GREY), (B['add'], '들기 (신규)', RED))):
    v = [abs(M[k]['gap_pct']) for k, _ in keys]
    bars = ax.bar(xs2 + (i - 0.5) * 0.36, v, 0.36, color=c, label=lab)
    barlab(ax, bars, v, fmt='{:.2f}', dy=0.05, fs=7.4)
ax.axhline(5.0, color=GREEN, lw=1.6, ls='--')
ax.text(len(keys) - 0.5, 5.2, '판정 기준 ±5 %', color=GREEN, fontsize=8.0, ha='right')
ax.set_xticks(xs2)
ax.set_xticklabels([l for _, l in keys], fontsize=8.0)
ax.set_ylabel('|전체 ON − (허리+팔꿈치)| / 합 (%)', fontsize=8.6)
ax.grid(alpha=.3, axis='y')
ax.legend(fontsize=7.6)
ax.set_ylim(0, 6.2)

# ── (6) 스팬 불일치 — 삼각근 ─────────────────────────────────────
ax = fig.add_subplot(gs[1, 2])
panel(ax, '(6) ★ 스팬 불일치 — 팔꿈치 슈트가 삼각근에 주는 영향')
xs3 = np.arange(2)
for i, (M, lab, c) in enumerate(((C['res'], '운반 (기존)', GREY), (B['res'], '들기 (신규)', RED))):
    v = [rel(M['off']['DELT']['mean'], M[cc]['DELT']['mean'])
         for cc in ('elbow', 'elbow_ext')]
    bars = ax.bar(xs3 + (i - 0.5) * 0.36, v, 0.36, color=c, label=lab)
    barlab(ax, bars, v, dy=0.15, fs=7.6)
ax.axhline(0, color='k', lw=1.0)
ax.set_xticks(xs3)
ax.set_xticklabels(['기본안 (상완→전완)', '연장안 (견갑 앵커)'], fontsize=8.4)
ax.set_ylabel('삼각근 활성도 변화 (%)', fontsize=8.8)
ax.grid(alpha=.3, axis='y')
ax.legend(fontsize=7.6)

# ── (7)(8) 본 렌더 포스터 ────────────────────────────────────────
for i, (fn, cap) in enumerate((
        ('poster_stoop_waist_AvsB_v1.png',
         '(7) 본 렌더 (가) 스툽 A vs B — 직립 구간 포함 (t = 0.23 s)\n'
         '상단 앵커 높이 차(L1 vs T8)와 직립에서의 ES 증가가 보인다'),
        ('poster_carry_multijoint_v1.png',
         '(8) 본 렌더 (나) 운반 다부위 — 허리 + 팔꿈치 (t = 0.85 s)\n'
         '프리뷰 구성 그대로. 청록 = 슈트 경로 (장력에 비례)'))):
    ax = fig.add_subplot(gs[2, i])
    p = os.path.join(IMG, fn)
    if os.path.exists(p):
        ax.imshow(np.array(Image.open(p)))
    ax.axis('off')
    ax.set_title(cap, fontsize=9.2, fontweight='bold', loc='left', pad=6,
                 linespacing=1.5)

# ── (9) 판정 요약 ────────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 2])
ax.axis('off')
addB = B['add']['ES.act_sum']['gap_pct']
addC = C['add']['ES.act_sum']['gap_pct']
dB = rel(B['res']['off']['DELT']['mean'], B['res']['elbow']['DELT']['mean'])
dBx = rel(B['res']['off']['DELT']['mean'], B['res']['elbow_ext']['DELT']['mean'])
dC = rel(C['res']['off']['DELT']['mean'], C['res']['elbow']['DELT']['mean'])
dCx = rel(C['res']['off']['DELT']['mean'], C['res']['elbow_ext']['DELT']['mean'])
esB = rel(B['res']['off']['ES']['act_sum'], B['res']['waist']['ES']['act_sum'])
ebB = rel(B['res']['off']['ELBFLX']['mean'], B['res']['elbow_ext']['ELBFLX']['mean'])
lines = [
    ('■ 용량–반응 (스툽 · 토크커플)', 'k', 10.2, 'bold'),
    (f"  8 N·m → {D['points']['토크커플 8 N·m']['rel']['peak']:+.1f} %  ·  "
     f"16.5 → {D['points']['토크커플 16.5 N·m']['rel']['peak']:+.1f} %  ·  "
     f"24 → {D['points']['토크커플 24 N·m']['rel']['peak']:+.1f} %", '0.15', 9.0, None),
    (f"  곡선 오목 — 토크 33 % 에서 효과 {f8:.0f} %, 69 % 에서 {f16:.0f} %", RED, 9.0, 'bold'),
    ('  → L-01 은 "두 점 병기"가 아니라 곡선 위 두 지점으로 서술', '0.15', 9.0, None),
    ('', 'k', 4, None),
    ('■ 들기 20 kg 다부위 (신규)', 'k', 10.2, 'bold'),
    (f"  허리만 ES 활성도 합 {esB:+.1f} %  ·  팔꿈치(연장안) 굴근 {ebB:+.1f} %", '0.15', 9.0, None),
    (f"  가산성 차이 {addB:+.2f} %  (운반 {addC:+.2f} %)"
     f"  → {'재현' if abs(addB) < 5 else '불재현'}", GREEN if abs(addB) < 5 else RED,
     9.4, 'bold'),
    (f"  삼각근  기본안 {dB:+.1f} % / 연장안 {dBx:+.1f} %"
     f"  (운반 {dC:+.1f} / {dCx:+.1f} %)", '0.15', 9.0, None),
    (f"  → 스팬 불일치 {'재현' if dB > 0 and dBx < dB else '불재현'}",
     GREEN if (dB > 0 and dBx < dB) else RED, 9.4, 'bold'),
    ('', 'k', 4, None),
    ('■ 본 렌더 2종', 'k', 10.2, 'bold'),
    ('  H.264 / yuv420p / Constrained Baseline · 포스터 추출', '0.15', 9.0, None),
    ('  stoop_waist_AvsB_v1.mp4 (10.0 s) · carry_multijoint_v1.mp4 (6.1 s)',
     '0.15', 9.0, None),
    ('  기존 파일 덮어쓰지 않음 (_v1 신규)', '0.15', 9.0, None),
]
y = 0.97
for txt, col, sz, wgt in lines:
    if txt:
        ax.text(0.0, y, txt, transform=ax.transAxes, fontsize=sz, color=col,
                fontweight=wgt or 'normal', va='top')
    y -= (sz + 5.2) / 210.0

out = os.path.join(IMG, 'resume_2026-09-24_grid.png')
fig.savefig(out, dpi=112)
print('SAVED', out)

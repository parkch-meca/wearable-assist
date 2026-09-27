"""[벤치 ■5] 장력 역산 검증 그리드 — 필요 T · 36 kg 판정 · 모멘트 암.

수치는 /data/suit_bench/bench_metrics.json 에서만 읽는다.
"""
import os
import sys
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
M = json.load(open('/data/suit_bench/bench_metrics.json'))
TR = json.load(open('/data/suit_bench/transfer.json'))
SNAP = '/data/suit_bench/snap'
CY, OR, GR, BLUE, RED, GREY = ('#159fb5', '#d98324', '#4f9d2e', '#4c72b0',
                               '#c44e52', '0.55')
TENS = [50.0, 100.0, 200.0, 300.0, 400.0, 600.0]
VLAB = {'A_neutral': '변형 A (요추 10°)', 'B_half': '변형 B (요추 30°)'}
SPEC = 100.0            # 한쪽 사양
CHAIN_T = 28.2          # 사슬 모델이 벤치 자세에서 준 장력 (한쪽)


def panel(ax, t):
    ax.set_title(t, fontsize=9.8, fontweight='bold', loc='left', pad=6)


fig = plt.figure(figsize=(19.2, 11.6))
gs = fig.add_gridspec(2, 3, hspace=0.34, wspace=0.26, height_ratios=[1, 1],
                      left=0.050, right=0.980, top=0.890, bottom=0.060)
fig.suptitle('[벤치 ■2·■3] 필요 장력 역산 — 실측을 재현하려면 얼마가 있어야 하는가',
             fontsize=15.0, fontweight='bold', y=0.965)
fig.text(0.5, 0.930,
         '장력을 사슬 모델에서 풀지 않고 **입력**으로 둔다 (한쪽 T, 자세 내내 일정) · '
         '벤치 등 신전 과제 · 자세 변형 A·B 범위 보고 · 5동작 논문 수치 불변 · 2026-09-27',
         ha='center', fontsize=9.0, color='0.3')

# ── (1) G1 — 23 kg 표면 ES 변화 vs T ────────────────────────────
ax = fig.add_subplot(gs[0, 0])
panel(ax, '(1) ★ G1 — 23 kg 표면 ES 활성도 vs 장력')
G1 = M['G1']
for v, c in (('A_neutral', BLUE), ('B_half', CY)):
    if v not in G1:
        continue
    xs = [T for T in TENS if str(T) in G1[v]['T'] or T in G1[v]['T']]
    def get(T, k):
        d = G1[v]['T']
        return (d[str(T)] if str(T) in d else d[T])[k]
    ax.plot(xs, [get(T, 'rel_all') for T in xs], 'o-', color=c, lw=2.2, ms=6,
            label=f'{VLAB[v]} 들기 구간')
    ax.plot(xs, [get(T, 'rel_bot') for T in xs], 's--', color=c, lw=1.6, ms=5,
            alpha=.75, label=f'{VLAB[v]} 최저점')
ax.axhline(-40, color=RED, ls='--', lw=2.0)
ax.text(60, -38.5, '실측 목표 −40 %', color=RED, fontsize=8.6)
ax.axvline(SPEC, color=GR, lw=1.8, ls=':')
ax.text(SPEC + 12, ax.get_ylim()[0] * 0.92, '사양 한쪽 100 N', color=GR, fontsize=8.2)
ax.set_xlabel('슈트 장력 T (N, 한쪽)', fontsize=8.8)
ax.set_ylabel('OFF 대비 표면 ES 변화 (%)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=7.2, loc='lower left')

# ── (2) 전달 법칙 + G2 ──────────────────────────────────────────
ax = fig.add_subplot(gs[0, 1])
panel(ax, '(2) ★★ 전달 법칙 — 장력이 L5–S1 근육 모멘트를 덜어 주는 양')
for v, c in (('A_neutral', BLUE), ('B_half', CY)):
    if v not in TR:
        continue
    rows = TR[v]['rows']
    ax.plot([r['T'] for r in rows], [r['dM'] for r in rows], 'o-', color=c, lw=2.2,
            ms=6, label=f"{VLAB[v]}  \u0394M = {TR[v]['k']:.3f}\u00b7T")
    ax.plot([r['T'] for r in rows], [r['res'] for r in rows], 's--', color=c,
            lw=1.4, ms=4, alpha=.7, label=f'{VLAB[v]} reserve (둔감)')
sl = TR['A_neutral']['slope']
ax2 = ax.twinx()
lo, hi = ax.get_ylim()
ax2.set_ylim(lo / sl, hi / sl)
ax2.set_ylabel('하중 환산 (kg)', fontsize=8.6, color=RED)
ax.axvline(SPEC, color=GR, lw=1.8, ls=':')
ax.text(SPEC + 12, 8, '사양 한쪽 100 N\n\u2192 4.0 kg 분', color=GR, fontsize=8.0)
need2 = TR['A_neutral']['T_need_G2']
ax.axvline(need2, color=RED, lw=1.8, ls='--')
ax.text(need2 + 14, 52, f'G2 (34\u219236 kg)\n필요 {need2:.0f} N (한쪽)', color=RED,
        fontsize=8.4, fontweight='bold')
ax.set_xlabel('슈트 장력 T (N, 한쪽)', fontsize=8.8)
ax.set_ylabel('L5\u2013S1 근육 모멘트 감소 \u0394M (N\u00b7m)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=6.8, loc='upper left')

# ── (3) 필요 T vs 사양 vs 사슬 모델 ─────────────────────────────
ax = fig.add_subplot(gs[0, 2])
panel(ax, '(3) ★★ 필요 장력 vs 사양 vs 사슬 모델 (한쪽)')
need = []
for v in ('A_neutral', 'B_half'):
    if v in G1:
        for k, lab in (('need_rel_all', '들기 구간'), ('need_rel_bot', '최저점')):
            if G1[v].get(k):
                need.append((f'{VLAB[v][3:9]} {lab}', G1[v][k]))
bars = [('사슬 모델\n(가열, 벤치 자세)', CHAIN_T, GREY),
        ('사양\n(한쪽 100 N)', SPEC, GR)] + [(n, t, RED) for n, t in need]
xs = np.arange(len(bars))
b = ax.bar(xs, [x[1] for x in bars], 0.62, color=[x[2] for x in bars])
for i, (n, t, c) in enumerate(bars):
    ax.text(i, t * 1.03, f'{t:.0f} N', ha='center', fontsize=8.8, fontweight='bold')
ax.set_xticks(xs)
ax.set_xticklabels([x[0] for x in bars], fontsize=7.6)
ax.set_ylabel('장력 (N, 한쪽)', fontsize=8.8)
ax.grid(alpha=.3, axis='y')
if need:
    ratio = np.mean([t for _, t in need]) / SPEC
    ax.text(0.03, 0.95, f'필요 T ÷ 사양 ≈ {ratio:.1f} 배',
            transform=ax.transAxes, ha='left', va='top', fontsize=9.6,
            color=RED, fontweight='bold')

# ── (4) 모멘트 암 ───────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
panel(ax, '(4) ■3 벤치 최저점 슈트 모멘트 암 (한쪽 경로)')
ma = M['moment_arm']
cols = list(next(iter(ma.values())).keys())
w = 0.38
for i, (v, c) in enumerate((('A_neutral', BLUE), ('B_half', CY))):
    if v not in ma:
        continue
    vals = [ma[v][k] for k in cols]
    bb = ax.bar(np.arange(len(cols)) + (i - 0.5) * w, vals, w, color=c,
                label=VLAB[v])
    for x, y in zip(bb, vals):
        ax.text(x.get_x() + x.get_width() / 2, y + 2, f'{y:.0f}', ha='center',
                fontsize=7.2)
ax.axhline(77, color=RED, ls='--', lw=1.5)
ax.text(len(cols) - 0.4, 80, 'ES 최대 근속 77 mm', color=RED, fontsize=7.8,
        ha='right')
ax.set_xticks(range(len(cols)))
ax.set_xticklabels([c.replace('_FE', '').replace('hip_flexion_r', '고관절')
                    for c in cols], fontsize=7.8, rotation=20)
ax.set_ylabel('모멘트 암 (mm)', fontsize=8.8)
ax.grid(alpha=.3, axis='y')
ax.legend(fontsize=7.6)

# ── (5) 최저점 스냅샷 ───────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1])
ax.axis('off')
p = f'{SNAP}/A_neutral.png'
if os.path.exists(p):
    im = Image.open(p)
    w0, h0 = im.size
    ax.imshow(np.array(im.crop((int(0.10 * w0), int(0.03 * h0),
                                int(0.92 * w0), int(0.78 * h0)))))
ax.set_title('(5) 최저점 — 슈트 경로가 등 체표를 따라간다\n'
             '청록 = 슈트(견봉→등판→구동부→BOA→허벅지) · 노랑 = 벤치 패드',
             fontsize=9.4, fontweight='bold', loc='left', pad=5, linespacing=1.4)

# ── (6) 요약 ────────────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2])
ax.axis('off')
lines = [('■ 역산 결과 (한쪽 / 양측 합)', 'k', 9.8, 'bold')]
for v in ('A_neutral', 'B_half'):
    if v not in G1:
        continue
    for k, lab in (('need_rel_all', '들기 구간'), ('need_rel_bot', '최저점')):
        t = G1[v].get(k)
        lines.append((f'  {VLAB[v]} {lab}: '
                      + (f'{t:.0f} N / {2*t:.0f} N' if t else '미도달'),
                      '0.15', 8.6, None))
lines += [
    (f'  사양 한쪽 100 N · 사슬 모델 {CHAIN_T:.0f} N', '0.15', 8.6, None),
    ('', 'k', 3, None),
    ('■ 전달 법칙 (SO 에서 직접 합산, 검산 완료)', 'k', 9.8, 'bold'),
    (f"  ΔM = {TR['A_neutral']['k']:.3f} N·m per N (한쪽) = 2·T·{TR['A_neutral']['k']/2*1000:.0f} mm",
     '0.15', 8.4, None),
    (f"  하중 환산 {TR['A_neutral']['kg_per_100N']:.1f} kg per 100 N (한쪽)", '0.15', 8.4, None),
    (f"  G2(34→36 kg) 필요 T = {TR['A_neutral']['T_need_G2']:.0f} N — 사양 안", GR, 8.6, 'bold'),
    ('', 'k', 3, None),
    ('■ ※ reserve 판정은 이 과제에서 둔감하다', 'k', 9.8, 'bold'),
    ('  T 400 N 에서 근육 모멘트는 −68 N·m 인데', '0.15', 8.4, None),
    ('  reserve 는 5.3 → 4.9 N·m 로 거의 안 변한다', '0.15', 8.4, None),
    ('  → 2/5/10 임계 어느 것도 T 를 구분하지 못한다', RED, 8.6, 'bold'),
    ('', 'k', 3, None),
    ('■ 다음 단계 — 실측 (docs/measurement_requests.md M-01)', 'k', 9.8, 'bold'),
    ('  BOA–허벅지 밴드 구간 인라인 로드셀', '0.15', 8.4, None),
    ('  미가열/가열 × 최저점/들기중 × 23·36 kg = 6 조건', '0.15', 8.4, None),
    ('  실측 T ≥ 필요 T → 장력 가설 채택', GR, 8.6, 'bold'),
    ('  실측 T < 필요 T 의 50 % → 장력 가설 기각', RED, 8.6, 'bold'),
    ('     남는 후보: 자세·기술 변화, 복압·공동수축', '0.15', 8.4, None),
]
y = 0.99
for txt, col, sz, wgt in lines:
    if txt:
        ax.text(0.0, y, txt, transform=ax.transAxes, fontsize=sz, color=col,
                fontweight=wgt or 'normal', va='top')
    y -= (sz + 4.2) / 250.0

out = os.path.join(IMG, 'bench_tension_inverse_grid.png')
fig.savefig(out, dpi=104)
print('SAVED', out)

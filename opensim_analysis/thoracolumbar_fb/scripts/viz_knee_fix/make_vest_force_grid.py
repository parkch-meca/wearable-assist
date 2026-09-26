"""[정정 2·3·4] 힘 모델 재구성 검증 그리드 — 사슬 순서 · 150 mm 분배 · 3관찰 · 설계 레버.

수치는 전부 실행 산출 json 에서 읽는다.
  /data/suit_vest/force_scan.json      O1·O2 스캔 (3492 조합)
  /data/suit_vest/ext/build_info.json  조건별 장력
  /data/suit_vest/vest_so_metrics.json SO 결과 (표면 ES · 전체 ES · 보조근)
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_force_v2 as FV

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

IMG = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint'
SNAP = '/data/suit_vest/snap'
CY, OR, GR, BLUE, RED, GREY, PUR = ('#159fb5', '#d98324', '#4f9d2e', '#4c72b0',
                                    '#c44e52', '0.55', '#7d5ba6')
SCAN = json.load(open('/data/suit_vest/force_scan.json'))
BI = json.load(open('/data/suit_vest/ext/build_info.json'))
MET = (json.load(open('/data/suit_vest/vest_so_metrics.json'))
       if os.path.exists('/data/suit_vest/vest_so_metrics.json') else None)
REP = dict(L_stand=160.0, F_plat=10.0, F_hot=150.0,
           chain=FV.Chain('bi', k1=0.2, xk=180.0, k2=20.0))


def show(ax, path, title, crop=None):
    ax.axis('off')
    if not os.path.exists(path):
        ax.text(.5, .5, '없음', ha='center')
        return
    im = Image.open(path)
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h),
                      int(crop[2] * w), int(crop[3] * h)))
    ax.imshow(np.array(im))
    ax.set_title(title, fontsize=9.4, fontweight='bold', loc='left', pad=5,
                 linespacing=1.4)


def panel(ax, t):
    ax.set_title(t, fontsize=9.8, fontweight='bold', loc='left', pad=6)


fig = plt.figure(figsize=(19.2, 15.0))
gs = fig.add_gridspec(3, 3, hspace=0.38, wspace=0.26, height_ratios=[1.12, 1, 1],
                      left=0.050, right=0.980, top=0.905, bottom=0.035)
fig.suptitle('[정정 2·3·4] 힘 모델 재구성 — 구동부 + 사슬 직렬, 100 N 일괄 상한 제거',
             fontsize=15.2, fontweight='bold', y=0.968)
fig.text(0.5, 0.936,
         '사슬 순서 = 견봉(어깨끈) → 조끼 등판 → 근육옷감 구동부(천골 포함) → BOA → 허벅지 밴드 · '
         'Z_LAT 55 mm · 3관찰(O1 직립 밴드 상승 / O2 미가열 스툽 / O3 EMG −40 %) 동시 캘리브레이션 · 2026-09-26',
         ha='center', fontsize=9.0, color='0.3')

# ── (1)(2) 사슬 순서 스냅샷 ──────────────────────────────────────
show(fig.add_subplot(gs[0, 0]), f'{SNAP}/chain_order_neutral_sag.png',
     '(1) 사슬 순서 · 중립 기립\n회색=등판(강체) · 주황=구동부 200 mm · 청록=BOA · 파랑=허벅지 밴드',
     crop=(0.20, 0.04, 0.80, 1.0))
show(fig.add_subplot(gs[0, 1]), f'{SNAP}/chain_order_stoop_sag.png',
     '(2) 사슬 순서 · 스툽 t=2.75 s\n경로 870.6 → 1005.9 mm (+135.3) — 실측 줄자 150 mm 와 정합',
     crop=(0.05, 0.04, 0.95, 0.95))

# ── (3) F(ΔL) 곡선 ──────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 2])
panel(ax, '(3) ★ 장력–경로신장 곡선 — 미가열과 가열이 분리된다')
dl = np.linspace(0, 180, 361)
for lab, heated, Fh, c in (('미가열', False, None, GREY),
                           ('가열 100 N', True, 100.0, '#9ecae1'),
                           ('가열 150 N (대표)', True, 150.0, BLUE),
                           ('가열 200 N ⚠', True, 200.0, PUR),
                           ('가열 250 N ⚠', True, 250.0, RED)):
    p = dict(REP)
    if Fh:
        p = dict(REP, F_hot=Fh)
    F = [FV.solve(x, p, heated)['F'] for x in dl]
    ax.plot(dl, F, color=c, lw=2.2 if lab.startswith('가열 150') else 1.8, label=lab)
ax.axvline(150, color=GR, ls='--', lw=1.5)
ax.text(151, 8, '줄자 실측 150', color=GR, fontsize=8.0, rotation=90, va='bottom')
ax.axvline(166, color=OR, ls=':', lw=1.5)
ax.text(167, 8, '들기 최대 166', color=OR, fontsize=8.0, rotation=90, va='bottom')
ax.axhline(100, color='k', lw=1.0, alpha=.4)
ax.text(3, 103, '기존 모델의 일괄 상한 100 N', fontsize=7.8, color='0.3')
ax.set_xlabel('경로 신장 ΔL (mm)', fontsize=8.8)
ax.set_ylabel('슈트 장력 (N)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=7.4, loc='upper left')

# ── (4) 150 mm 흡수 분배 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
panel(ax, '(4) ★ 150 mm 를 무엇이 흡수하는가 (미가열)\n'
      '통과 조합은 모두 L_stand 160 mm — 구동부 40 + 사슬 110 mm')
ok = [r for r in SCAN if r['pass_']]
Ls = sorted({r['L_stand'] for r in ok}) or [160.0]
labs, act, chain = [], [], []
for L in (140.0, 160.0, 180.0):
    labs.append(f'{L:.0f} mm')
    act.append(min(150.0, 200.0 - L))
    chain.append(150.0 - min(150.0, 200.0 - L))
y = np.arange(len(labs))
ax.barh(y, act, color=OR, label='구동부 신장 (코일)')
ax.barh(y, chain, left=act, color=CY, label='사슬 (피부·끈·밴드)')
for i, (a, c) in enumerate(zip(act, chain)):
    ax.text(a / 2, i, f'{a:.0f}', ha='center', va='center', fontsize=8, color='w')
    ax.text(a + c / 2, i, f'{c:.0f} mm', ha='center', va='center', fontsize=8, color='w')
ax.set_yticks(y)
ax.set_yticklabels(labs, fontsize=9.0)
ax.invert_yaxis()
ax.set_xlabel('흡수량 (mm)', fontsize=8.8)
ax.set_ylabel('직립 구동부 길이 L_stand', fontsize=8.8)
ax.legend(fontsize=7.6, loc='center right')
ax.set_xlabel('흡수량 (mm)   ·   사슬 몫 110 mm 중 밴드가 20 mm 이하이려면 분담률 ≤ 18 %',
              fontsize=8.4)

# ── (5) O1·O2 통과 영역 ─────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1])
panel(ax, '(5) ★ O1·O2 통과 영역 — 선형 사슬은 전부 탈락')
lin = [r for r in SCAN if r['chain_kind'] == 'lin']
bi = [r for r in SCAN if r['chain_kind'] == 'bi']
ax.scatter([r['d_band'] for r in lin], [r['ratio'] for r in lin], s=14,
           c=GREY, alpha=.55, label=f'선형 사슬 ({len(lin)})')
ax.scatter([r['d_band'] for r in bi], [r['ratio'] for r in bi], s=12,
           c='#bcd6ea', alpha=.55, label=f'이중선형 ({len(bi)})')
p = [r for r in SCAN if r['pass_']]
ax.scatter([r['d_band'] for r in p], [r['ratio'] for r in p], s=52, c=RED,
           marker='*', label=f'O1+O2 통과 ({len(p)})', zorder=5)
ax.axvspan(10, 15, color=GR, alpha=.12)
ax.axhline(0.5, color=RED, ls='--', lw=1.4)
ax.text(16, 0.53, 'O2 수동/능동 ≤ 0.5', color=RED, fontsize=7.8)
ax.text(12.5, 2.6, 'O1\n10~15 mm', color=GR, fontsize=8.0, ha='center')
ax.set_xlabel('직립 가열 시 밴드 상승 (mm)  ← O1', fontsize=8.8)
ax.set_ylabel('미가열 / 가열 장력비  ← O2', fontsize=8.8)
ax.set_xlim(-10, 45)
ax.set_ylim(0, 3.0)
ax.grid(alpha=.3)
ax.legend(fontsize=7.2, loc='upper right')

# ── (6) O3 — ES 표면 변화 vs 구동기 힘 ──────────────────────────
ax = fig.add_subplot(gs[1, 2])
panel(ax, '(6) ★ O3 판정 — 표면 ES 활성도 (EMG 진폭 대응)')
if MET:
    R20 = MET['R20']
    HI = MET.get('hi', {}).get('res', {})
    order = [('cold', 0.0), ('hot100', 100.0), ('hot150', 150.0),
             ('hot200', 200.0), ('hot250', 250.0)]
    xs = [F for k, F in order if k in R20]
    ys = [R20[k]['surf']['rel']['mean'] for k, F in order if k in R20]
    yh = [HI[k]['rel_mean'] for k, F in order if k in HI]
    ax.plot(xs, ys, 'o-', color=BLUE, lw=2.0, ms=7, label='전체 창 (2.33~5.43 s)')
    if yh:
        ax.plot(xs[:len(yh)], yh, 'o-', color=RED, lw=2.4, ms=8,
                label='고장력 창 (슈트 ≥90 N, 2.33~2.67 s)')
        for x, y in zip(xs, yh):
            ax.annotate(f'{y:+.0f}%', (x, y), textcoords='offset points',
                        xytext=(4, -12), fontsize=8.0, color=RED)
    ax.axhline(-40, color=GR, ls='--', lw=1.8)
    ax.text(4, -38.5, '실측 EMG −40 % (미도달)', color=GR, fontsize=8.4)
    ax.axvspan(175, 262, color=RED, alpha=.07)
    ax.text(218, -3, 'O1 이탈', color=RED, fontsize=7.8, ha='center')
    ax.set_xlabel('구속 가열 힘 F_hot (N)   · 0 = 미가열', fontsize=8.8)
    ax.set_ylabel('OFF 대비 표면 ES 변화 (%)', fontsize=8.8)
    ax.set_ylim(-45, 2)
    ax.grid(alpha=.3)
    ax.legend(fontsize=7.4, loc='lower left')
else:
    ax.text(.5, .5, 'SO 결과 대기', ha='center')
    ax.axis('off')

# ── (7) 20 vs 36 kg + 보조근 ───────────────────────────────────
ax = fig.add_subplot(gs[2, 0])
panel(ax, '(7) 하중 20 vs 36 kg · 보조 근육 (둔근·햄스트링)')
if MET and MET.get('R36'):
    R20, R36 = MET['R20'], MET['R36']
    groups = [('ES 표면', 'surf'), ('ES 전체', 'all'), ('둔근', 'glut'),
              ('햄스트링', 'ham')]
    x = np.arange(len(groups))
    w = 0.2
    series = [('20 kg 미가열', R20.get('cold'), GREY),
              ('20 kg 가열150', R20.get('hot150'), BLUE),
              ('36 kg 미가열', R36.get('cold_36'), '#e8b4b8'),
              ('36 kg 가열150', R36.get('hot150_36'), RED)]
    for i, (lab, r, c) in enumerate(series):
        if not r:
            continue
        v = [r[g]['rel']['mean'] for _, g in groups]
        b = ax.bar(x + (i - 1.5) * w, v, w, color=c, label=lab)
        for bb, vv in zip(b, v):
            ax.text(bb.get_x() + bb.get_width() / 2,
                    bb.get_height() + (1 if vv >= 0 else -1), f'{vv:+.0f}',
                    ha='center', va='bottom' if vv >= 0 else 'top', fontsize=6.8)
    ax.axhline(0, color='k', lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([g for g, _ in groups], fontsize=8.4)
    ax.set_ylabel('OFF 대비 변화 (%)', fontsize=8.8)
    ax.grid(alpha=.3, axis='y')
    ax.legend(fontsize=7.0, ncol=2)
else:
    ax.text(.5, .5, 'SO 결과 대기', ha='center')
    ax.axis('off')

# ── (8) ■4 설계 레버 ───────────────────────────────────────────
ax = fig.add_subplot(gs[2, 1])
panel(ax, '(8) ★ 설계 레버 — 고정부 개선 vs 구동기 힘 (고장력 창)')
if MET and MET.get('hi'):
    HI = MET['hi']['res']
    keys = [('hot150', '기준 150 N', GREY), ('k2x2', '사슬 경질 2배', CY),
            ('k2x4', '사슬 경질 4배', '#0d7c8c'),
            ('hot225', '구동기 1.5배', RED)]
    labs, vals, cols = [], [], []
    for k, lab, c in keys:
        if k in HI:
            labs.append(lab)
            vals.append(HI[k]['rel_mean'])
            cols.append(c)
    b = ax.bar(range(len(labs)), vals, 0.6, color=cols)
    base = vals[0]
    for i, v in enumerate(vals):
        ax.text(i, v - 0.5, f'{v:+.1f}%', ha='center', va='top', fontsize=8.8,
                fontweight='bold')
        if i:
            ax.text(i, 0.6, f'{v-base:+.1f} %p', ha='center', fontsize=7.6, color='0.3')
    ax.axhline(0, color='k', lw=1.0)
    ax.set_xticks(range(len(labs)))
    ax.set_xticklabels(labs, fontsize=8.4)
    ax.set_ylabel('표면 ES 평균 변화 (%)', fontsize=8.8)
    ax.set_ylim(min(vals) * 1.25, 3)
    ax.grid(alpha=.3, axis='y')
    ax.text(0.02, 0.03,
            '슬립 여유(x_k)를 줄이면? 해석 결과:\n'
            '  x_k 180 → 140 mm 에서 미가열 35 → 748 N\n'
            '  메쉬 리미터가 받아 가열·미가열이 같아진다\n'
            '  → 보조는 커지나 능동 제어성을 잃는다',
            transform=ax.transAxes, ha='left', va='bottom', fontsize=7.6,
            color=RED, linespacing=1.5)
else:
    ax.text(.5, .5, 'SO 결과 대기', ha='center')
    ax.axis('off')

# ── (9) 100 N 상한 의존 결론 목록 ──────────────────────────────
ax = fig.add_subplot(gs[2, 2])
ax.axis('off')
lines = [
    ('■ 100 N 일괄 상한에 의존했던 이전 결론 (재검증 필요)', 'k', 9.8, 'bold'),
    ('  1. "직렬 강성 k 는 굴곡 구간 보조 토크에 거의 무영향"', RED, 8.6, 'bold'),
    ('     → 상한 포화가 만든 착시. ■4 패널 (8) 참조', '0.15', 8.4, None),
    ('  2. "허리 장력 79~100 N (평균 97)" = 사실상 항상 상한', RED, 8.6, 'bold'),
    ('     → 새 모델에서 미가열 10~35 N · 가열150 13~128 N', '0.15', 8.4, None),
    ('  3. 설계 레버 3조건 (힘 2배·강성 20·모멘트암 +20 mm)', RED, 8.6, 'bold'),
    ('     → 힘 2배가 상한에 걸려 있었다면 해석 무효', '0.15', 8.4, None),
    ('  4. 수동(미가열) 조건을 따로 다룬 적이 없음', '0.15', 8.4, None),
    ('     → 기존 "슈트 ON" 은 전부 가열 100 N 고정', '0.15', 8.4, None),
    ('', 'k', 3, None),
    ('■ 유지 (상한과 무관)', 'k', 9.8, 'bold'),
    ('  · 스팬 정합 원리 · 천골 경유 · 부위 간 가산성', '0.15', 8.4, None),
    ('  · 5동작 논문 수치 (토크 커플 표현, 상한 미적용)', '0.15', 8.4, None),
    ('', 'k', 3, None),
    ('■ 이번 모델의 검증되지 않은 가정', 'k', 9.8, 'bold'),
    ('  · 사슬 이중선형 (k1 0.2 / 무릎 180 mm / k2 20)', '0.15', 8.4, None),
    ('  · 밴드 분담률 ≤ 18 % (스툽에서 등판·어깨끈이 대부분 미끄러짐)', '0.15', 8.4, None),
    ('  · F_plat 10 N · 직립 구동부 160 mm', '0.15', 8.4, None),
    ('  → 모두 착용 시험으로 직접 잴 수 있는 값이다', GR, 8.6, 'bold'),
]
y = 0.995
for txt, col, sz, wgt in lines:
    if txt:
        ax.text(0.0, y, txt, transform=ax.transAxes, fontsize=sz, color=col,
                fontweight=wgt or 'normal', va='top')
    y -= (sz + 4.0) / 245.0

out = os.path.join(IMG, 'vest_force_model_grid.png')
fig.savefig(out, dpi=104)
print('SAVED', out)

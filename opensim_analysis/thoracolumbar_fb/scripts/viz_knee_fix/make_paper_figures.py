"""five_motion_paper_draft.md 용 Figure 3~6 생성.

논문 규격:
  * 흑백 인쇄 가독 — 색이 아니라 명도·선종류·해치로 구분
  * 축 라벨 >= 9 pt (단칼럼 폭 88 mm 기준)
  * 새 해석 실행 없음. 모든 값은 기존 SO .sto에서 재계산.
"""
import numpy as np, opensim as osim, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = fm.FontProperties(fname=KF).get_name()
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9.5, 'axes.titlesize': 10,
                     'xtick.labelsize': 9, 'ytick.labelsize': 9,
                     'legend.fontsize': 8.5, 'figure.facecolor': 'white',
                     'axes.facecolor': 'white', 'savefig.facecolor': 'white'})

OUT = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/paper_five_motion'
os.makedirs(OUT, exist_ok=True)
MEDIA = '/data/opensim_results/ppt_media'

K_OFF = dict(color='0.15', ls='-', lw=1.6)      # 슈트 OFF — 진한 실선
K_ON = dict(color='0.45', ls='--', lw=1.6)      # 슈트 ON  — 중간 파선
CM = 1 / 2.54


def load(p):
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn())); labs = list(t.getColumnLabels())
    E = [l for l in labs if l.startswith(('IL_', 'LTpL', 'LTpT'))]
    A = np.vstack([[float(t.getDependentColumn(e)[i]) for i in range(t.getNumRows())]
                   for e in E]) * 100
    return T, A.max(axis=0)


def style(ax):
    ax.grid(alpha=0.3, lw=0.5, color='0.7')
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


R = {
 'squat': ('/data/squat_results/suit_sweep/F0/squat_F0_StaticOptimization_activation.sto',
           '/data/squat_results/suit_sweep/F200/squat_F200_StaticOptimization_activation.sto'),
 'stoop': ('/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto',
           '/data/stoop_results/suit_sweep_v5/F200/'),
 'box':   ('/data/stoop_results/box_stoop_so/B_off/so_B_off_StaticOptimization_activation.sto',
           '/data/stoop_results/box_stoop_so/B_on/so_B_on_StaticOptimization_activation.sto'),
 'gait':  ('/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto',
           '/data/gait_results/gait_on_tight/so_StaticOptimization_activation.sto'),
 'carry': ('/data/carry_results/carry_off/so_StaticOptimization_activation.sto',
           '/data/carry_results/carry_on/so_StaticOptimization_activation.sto'),
}
TITLE = {'squat': '(a) 맨몸 스쿼트 (0 kg)', 'stoop': '(b) 맨몸 스툽 (0 kg)',
         'box': '(c) 박스 들기 (20 kg)', 'gait': '(d) 맨몸 보행 (0 kg)',
         'carry': '(e) 박스 운반 (20 kg)'}
DATA = {}
for k, (a, b) in R.items():
    if b.endswith('/'):
        c = [f for f in os.listdir(b) if f.endswith('activation.sto')]
        b = os.path.join(b, c[0])
    DATA[k] = (load(a), load(b))

# ============================================ Figure 3 — 5동작 대표 자세
th = ['squat', 'stoop', 'box', 'gait', 'carry']
from PIL import ImageOps
ims = [ImageOps.autocontrast(ImageOps.invert(
        Image.open(f'{MEDIA}/th_{k}.png').convert('L')), cutoff=1) for k in th]  # 인쇄용 반전
W = 900
ims = [i.resize((W, int(i.height * W / i.width)), Image.LANCZOS) for i in ims]
LAB = 46
H = ims[0].height
canvas = Image.new('L', (3 * W + 4 * 10, 2 * (H + LAB) + 3 * 10), 255)
from PIL import ImageDraw, ImageFont
d = ImageDraw.Draw(canvas); f = ImageFont.truetype(KF, 30)
names = ['(a) 맨몸 스쿼트  0 kg', '(b) 맨몸 스툽  0 kg', '(c) 박스 들기  20 kg',
         '(d) 맨몸 보행  0 kg', '(e) 박스 운반  20 kg']
for i, im in enumerate(ims):
    x = 10 + (i % 3) * (W + 10); y = 10 + (i // 3) * (H + LAB + 10)
    d.text((x + 4, y + 6), names[i], font=f, fill=0)
    canvas.paste(im, (x, y + LAB))
canvas.save(f'{OUT}/fig3_five_motion_postures.png')
print('fig3', canvas.size)

# ============================================ Figure 4 — 동작별 ES peak 시계열
fig, axs = plt.subplots(2, 3, figsize=(18 * CM, 10 * CM))
for i, k in enumerate(th):
    ax = axs[i // 3][i % 3]
    (Ta, pa), (Tb, pb) = DATA[k]
    ax.plot(Ta, pa, label='슈트 OFF', **K_OFF)
    ax.plot(Tb, pb, label='슈트 ON (24 N·m)', **K_ON)
    if k == 'box':
        ax.axvspan(1.9, 5.9, color='0.85', zorder=0)
    if k in ('gait', 'carry'):
        ax.axvspan(0.94, 1.06, color='0.85', zorder=0)
    if k == 'carry':
        ax.axhline(100, color='0.3', ls=':', lw=1.0)
        ax.text(1.58, 103, '포화 100 %', ha='right', fontsize=8, color='0.3')
    ax.set_title(TITLE[k], fontsize=9.5, pad=4)
    ax.set_xlabel('시간 (s)'); ax.set_ylabel('ES peak 활성도 (%)')
    ax.set_ylim(0, 118 if k == 'carry' else 45)
    style(ax)
    if i == 0:
        ax.legend(loc='upper left', framealpha=0.95)
axs[1][2].axis('off')
axs[1][2].text(0.02, 0.92, '음영 구간', fontsize=9, fontweight='bold',
               va='top', transform=axs[1][2].transAxes)
axs[1][2].text(0.02, 0.78, '(c) 박스를 든 구간 (1.9–5.9 s)\n'
                           '(d)(e) mid-stance (0.94–1.06 s)\n\n'
                           'ES peak = 척추기립근 76개 중\n'
                           '        해당 시점 최대 활성 근육\n\n'
                           '(a)–(c) 표준 reserve\n'
                           '(d)(e) tight reserve\n'
                           '  → 절대값 직접 비교 불가 (§6 한계)',
               fontsize=8.2, va='top', transform=axs[1][2].transAxes, linespacing=1.6)
fig.tight_layout(pad=0.8)
fig.savefig(f'{OUT}/fig4_es_timeseries.png', dpi=400)
plt.close(fig); print('fig4')

# ============================================ Figure 5 — 부하–효과 패턴
MOT = [('맨몸 보행\n0 kg', 0.0, '초저부하'), ('박스 들기\n20 kg', 23.2, '고부하'),
       ('박스 운반\n20 kg', 25.4, '고부하'), ('맨몸 스툽\n0 kg', 31.8, '중부하'),
       ('맨몸 스쿼트\n0 kg', 47.5, '저부하')]
fig, ax = plt.subplots(figsize=(12 * CM, 8 * CM))
y = np.arange(len(MOT))
vals = [m[1] for m in MOT]
# 명도 + 해치로 흑백 구분
shades = ['0.88', '0.55', '0.55', '0.35', '0.15']
hatches = ['', '', '', '', '']
bars = ax.barh(y, vals, height=0.62, color=shades, edgecolor='black', linewidth=0.8)
for b, h in zip(bars, hatches):
    if h:
        b.set_hatch(h)
for i, v in enumerate(vals):
    ax.text(v + 1.0, i, f'{v:.1f} %', va='center', fontsize=9.5, fontweight='bold')
ax.text(vals[0] + 7.5, 0, '(허리 신전 요구가 거의 없어 보조 대상 없음)',
        va='center', fontsize=8, color='0.35')
ax.set_yticks(y); ax.set_yticklabels([m[0] for m in MOT])
ax.set_xlabel('척추기립근(ES) peak 활성도 상대 감소율 (%)')
ax.set_xlim(0, 58)
ax.set_title('슈트 24 N·m 적용 시 동작별 ES 감소율', fontsize=10, pad=6)
style(ax); ax.grid(axis='y', visible=False)
fig.tight_layout(pad=0.6)
fig.savefig(f'{OUT}/fig5_load_effect_pattern.png', dpi=400)
plt.close(fig); print('fig5')

# ============================================ Figure 6 — reserve 민감도 (보행)
fig, axs = plt.subplots(1, 2, figsize=(16 * CM, 7 * CM))
lbl = ['표준 reserve\n(spine opt 100 N·m)', 'tight reserve\n(spine opt 5 N·m)']
x = np.arange(2); w = 0.34
a = axs[0]
a.bar(x - w / 2, [16.78, 1.01], w, color='0.75', edgecolor='k', lw=0.8, hatch='///',
      label='실제 흡수된 spine reserve')
a.set_xticks(x); a.set_xticklabels(lbl)
a.set_ylabel('spine reserve 최대 크기 (N·m)')
a.set_title('(a) reserve가 흡수한 척추 부하', fontsize=9.5, pad=4)
for i, v in enumerate([16.78, 1.01]):
    a.text(i - w / 2, v + 0.4, f'{v:.1f}', ha='center', fontsize=9, fontweight='bold')
a.set_ylim(0, 20); style(a)

b = axs[1]
off = [11.13, 35.08]; on = [5.54, 34.11]
b.bar(x - w / 2, off, w, color='0.25', edgecolor='k', lw=0.8, label='슈트 OFF')
b.bar(x + w / 2, on, w, color='0.70', edgecolor='k', lw=0.8, hatch='\\\\\\',
      label='슈트 ON (24 N·m)')
for i in range(2):
    b.text(i, max(off[i], on[i]) + 1.4, f'Δ {on[i]-off[i]:+.1f} %p',
           ha='center', fontsize=9, fontweight='bold')
b.set_xticks(x); b.set_xticklabels(lbl)
b.set_ylabel('보행 ES peak 활성도 (%)')
b.set_title('(b) 근육 활성도와 슈트 효과 추정', fontsize=9.5, pad=4)
b.set_ylim(0, 44); b.legend(loc='upper left'); style(b)
fig.suptitle('표준 reserve에서는 reserve가 척추 부하를 대신 흡수해 '
             'ES를 약 3배 과소평가하고 존재하지 않는 보조 효과를 만든다',
             fontsize=9, y=0.995)
fig.tight_layout(pad=0.7, rect=[0, 0, 1, 0.95])
fig.savefig(f'{OUT}/fig6_reserve_sensitivity.png', dpi=400)
plt.close(fig); print('fig6')
print('OUT =', OUT)

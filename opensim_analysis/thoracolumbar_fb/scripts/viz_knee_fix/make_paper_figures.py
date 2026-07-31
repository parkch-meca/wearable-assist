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
_KFNAME = fm.FontProperties(fname=KF).get_name()
plt.rcParams['font.family'] = 'sans-serif'
# 한글·라틴·기호를 모두 같은 패밀리로 렌더해 실효 크기 차이를 없앤다
plt.rcParams['font.sans-serif'] = [_KFNAME]
plt.rcParams['mathtext.fontset'] = 'dejavusans'
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


# 5동작 완전 통일 결과 (동일 모델 dc6c217f8fb6 + tight reserve)
R = {k: (f'/data/tight_unified/{k}_off/so_StaticOptimization_activation.sto',
         f'/data/tight_unified/{k}_on/so_StaticOptimization_activation.sto')
     for k in ('squat', 'stoop', 'box')}
R['gait'] = ('/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto',
             '/data/gait_results/gait_on_tight/so_StaticOptimization_activation.sto')
R['carry'] = ('/data/carry_results/carry_off/so_StaticOptimization_activation.sto',
              '/data/carry_results/carry_on/so_StaticOptimization_activation.sto')
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
# 라스터 캔버스에 글자를 그리면 논문 배치(15.5 cm)에서 4 pt 수준으로 줄어든다.
# → matplotlib 축 위에 이미지를 얹고 라벨은 실제 pt로 그린다.
th = ['squat', 'stoop', 'box', 'gait', 'carry']
from PIL import ImageOps


def _prep(k):
    im = Image.open(f'{MEDIA}/th_{k}.png').convert('L')
    im = im.crop((0, int(im.height * 0.22), im.width, im.height))   # 번인 소자막 제거
    im = ImageOps.autocontrast(ImageOps.invert(im), cutoff=1)
    hist = im.histogram()
    bg = max(range(256), key=lambda v: hist[v])
    thr = max(1, bg - 10)
    return im.point(lambda v: 255 if v >= thr else int(v * 255.0 / thr * 0.85))


NAMES = {'squat': '(a) 맨몸 스쿼트  0 kg', 'stoop': '(b) 맨몸 스툽  0 kg',
         'box': '(c) 박스 들기  20 kg', 'gait': '(d) 맨몸 보행  0 kg',
         'carry': '(e) 박스 운반  20 kg'}
FIGW = 16.4 * CM                      # 논문 배치 폭과 동일 → 라벨 pt가 인쇄 pt
fig = plt.figure(figsize=(FIGW, FIGW * 0.46))
for i, k in enumerate(th):
    ax = fig.add_subplot(2, 3, i + 1)
    ax.imshow(_prep(k), cmap='gray', vmin=0, vmax=255, aspect='auto')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color('0.45'); sp.set_linewidth(0.8)
    ax.set_title(NAMES[k], fontsize=9, pad=3, loc='left')
    ax.set_xlabel('슈트 미착용                        슈트 착용', fontsize=9, labelpad=3)
fig.add_subplot(2, 3, 6).axis('off')
fig.text(0.70, 0.30, '각 패널은 슈트 미착용(좌)과\n착용(우)을 나란히 보인다.\n\n'
                     '(a)(b)의 사각 확대창은 원본\n시각화의 요추부 확대 영역으로,\n'
                     '정량 판독용이 아니다.',
         fontsize=8.5, va='center', linespacing=1.6)
fig.tight_layout(pad=0.7)
fig.savefig(f'{OUT}/fig3_five_motion_postures.png', dpi=450)
plt.close(fig); print('fig3')

# ============================================ Figure 4 — 동작별 ES peak 시계열
fig, axs = plt.subplots(2, 3, figsize=(16.4 * CM, 9.1 * CM))
for i, k in enumerate(th):
    ax = axs[i // 3][i % 3]
    (Ta, pa), (Tb, pb) = DATA[k]
    ax.plot(Ta, pa, label='슈트 OFF', **K_OFF)
    ax.plot(Tb, pb, label='슈트 ON (24 N·m)', **K_ON)
    if k == 'squat':
        ax.axvspan(1.708, 3.292, color='0.85', zorder=0)
    if k == 'stoop':
        ax.axvspan(2.092, 3.408, color='0.85', zorder=0)
    if k == 'box':
        ax.axvspan(2.225, 5.833, color='0.85', zorder=0)
    if k in ('gait', 'carry'):
        ax.axvspan(0.94, 1.06, color='0.85', zorder=0)
    if k == 'carry':
        ax.axhline(100, color='0.3', ls=':', lw=1.0)
        ax.text(1.58, 103, '포화 100 %', ha='right', fontsize=8, color='0.3')
    ax.set_title(TITLE[k], fontsize=9.5, pad=4)
    ax.set_xlabel('시간 (s)'); ax.set_ylabel('ES peak 활성도 (%)')
    # tight 통일로 절대값이 크게 올라갔으므로 데이터에 맞춰 y축을 잡는다 (클리핑 방지)
    _top = max(pa.max(), pb.max())
    ax.set_ylim(0, 118 if k == 'carry' else max(45, _top * 1.18))
    style(ax)
    if i == 0:
        _h, _l = ax.get_legend_handles_labels()
axs[1][2].axis('off')
# 범례는 비어 있는 6번째 칸에 배치 (패널 안에 두면 곡선이나 제목을 가림)
axs[1][2].legend(_h, _l, loc='upper left', bbox_to_anchor=(0.0, 1.02),
                 fontsize=8.6, frameon=False, handlelength=1.8)
axs[1][2].text(0.02, 0.52, '음영 구간', fontsize=9, fontweight='bold',
               va='top', transform=axs[1][2].transAxes)
axs[1][2].text(0.02, 0.41, '(a)(b)(c) 슈트 작동창\n(d)(e) mid-stance\n\n'
                            'ES peak = ES 76개 중\n해당 시점 최대 활성 근육\n\n'
                            '5동작 전부 동일 모델\n+ tight reserve (척추 5 N·m)',
               fontsize=8.0, va='top', transform=axs[1][2].transAxes, linespacing=1.55)
fig.tight_layout(pad=0.8)
fig.savefig(f'{OUT}/fig4_es_timeseries.png', dpi=400)
plt.close(fig); print('fig4')

# ============================================ Figure 5 — 부하–효과 패턴
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_numbers as pn      # 표기 규칙 단일 소스 (본문·표와 동일 값 보장)
_LB = {'squat': '맨몸 스쿼트\n0 kg', 'stoop': '맨몸 스툽\n0 kg',
       'box': '박스 들기\n20 kg', 'gait': '맨몸 보행\n0 kg', 'carry': '박스 운반\n20 kg'}
_v = {k: pn.metric(k, 'b')['rel'] for k in _LB}
MOT = sorted([(_LB[k], _v[k], '') for k in _LB], key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(12.5 * CM, 8.2 * CM))
y = np.arange(len(MOT))
vals = [m[1] for m in MOT]
# 명도 + 해치로 흑백 구분
shades = ['0.15', '0.35', '0.55', '0.55', '0.88']
bars = ax.barh(y, vals, height=0.62, color=shades, edgecolor='black', linewidth=0.8)
# 값 라벨은 항상 0선 반대쪽 막대 끝 바깥에 두되, y축 눈금 라벨과 겹치지 않게 여백 확보
for i, v in enumerate(vals):
    ax.text(v + (1.4 if v > 0 else -1.4), i, f'{pn.fmt(v, 1, True)} %', va='center',
            ha='left' if v > 0 else 'right', fontsize=9.5, fontweight='bold')
_i_gait = [i for i, m in enumerate(MOT) if '보행' in m[0]]
if _i_gait:
    _i = _i_gait[0]
    ax.annotate('감소가 아니라 재분배\n(본문 §3.4 참조)', xy=(vals[_i] / 2, _i),
                xytext=(vals[_i] / 2 + 3.0, _i - 0.62), fontsize=8, color='0.30',
                ha='center', va='top')
ax.axvline(0, color='k', lw=1.0)
ax.set_yticks(y); ax.set_yticklabels([m[0] for m in MOT])
ax.set_xlabel('ES peak 활성도 변화율 (%)  ·  음수 = 감소')
ax.set_xlim(-52, 40)
ax.set_title('슈트 24 N·m 적용 시 동작별 ES 변화 (주 지표: 슈트 작동창 peak 평균)',
             fontsize=9.5, pad=6)
style(ax); ax.grid(axis='y', visible=False)
fig.tight_layout(pad=0.6)
fig.savefig(f'{OUT}/fig5_load_effect_pattern.png', dpi=400)
plt.close(fig); print('fig5')

# ============================================ Figure 6 — reserve 민감도 (보행)
fig, axs = plt.subplots(1, 2, figsize=(16.4 * CM, 7.2 * CM))
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
    b.text(i, max(off[i], on[i]) + 1.4, f'Δ {pn.fmt(on[i]-off[i], 1, True)} %p',
           ha='center', fontsize=9, fontweight='bold')
b.set_xticks(x); b.set_xticklabels(lbl)
b.set_ylabel('보행 ES peak 활성도 (%)')
b.set_title('(b) 근육 활성도와 슈트 효과 추정', fontsize=9.5, pad=4)
b.set_ylim(0, 50); b.legend(loc='upper left', framealpha=1.0, fontsize=8.0); style(b)
fig.suptitle('표준 reserve에서는 reserve가 척추 부하를 대신 흡수해 '
             'ES를 3.2배 과소평가하고 존재하지 않는 보조 효과를 만든다',
             fontsize=9, y=0.995)
fig.tight_layout(pad=0.7, rect=[0, 0, 1, 0.95])
fig.savefig(f'{OUT}/fig6_reserve_sensitivity.png', dpi=400)
plt.close(fig); print('fig6')
print('OUT =', OUT)

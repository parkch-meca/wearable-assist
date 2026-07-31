"""논문 Figure 1 (모델·슈트 모델링 개념도) / Figure 2 (해석 파이프라인) 신규 작도.

발표자료의 PowerPoint 네이티브 도형은 논문에 쓸 수 없어 별도 작도.
규격: 400 dpi 이상, 흑백 인쇄 가독(색 없이 명도·선종류로 구분), 라벨 >= 9 pt.
설계 주의: 해칭을 글자 뒤에 깔면 판독이 불가하므로 해칭은 강조 박스 1개에만,
          그 박스의 글자는 해칭이 없는 흰 패치 위에 올린다.
"""
import os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager as fm
from PIL import Image, ImageOps

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = fm.FontProperties(fname=KF).get_name()
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

OUT = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/paper_five_motion'
os.makedirs(OUT, exist_ok=True)
MEDIA = '/data/opensim_results/ppt_media'
CM = 1 / 2.54


def box(ax, x, y, w, h, fc='white', ec='k', lw=1.0, hatch=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.010',
                                fc=fc, ec=ec, lw=lw, hatch=hatch))


def arrow(ax, p0, p1, lw=1.4, color='0.25'):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>,head_width=3.4,head_length=6',
                                 lw=lw, color=color, shrinkA=0, shrinkB=0))


# ==================================================== Figure 1
fig = plt.figure(figsize=(17 * CM, 9.8 * CM))

# --- (a) 전신 모델 + 슈트 경로 ---
axA = fig.add_axes([0.015, 0.035, 0.295, 0.83]); axA.axis('off')
axA.set_xlim(0, 1); axA.set_ylim(0, 1)
sk = ImageOps.autocontrast(ImageOps.invert(
        Image.open(f'{MEDIA}/model_fullbody.png').convert('L')), cutoff=1)
axA.imshow(sk, cmap='gray', extent=[0.02, 0.60, 0.02, 0.98], aspect='auto', zorder=0)
# 노드는 해부학 위치에 맞춘다: 어깨(상부흉추) → ES(요추 후면) → 대둔근(골반 후면)
# → 서혜부(고관절 전면, 그래서 x가 전방=오른쪽으로 이동). 라벨 y는 겹침 방지를 위해 분리.
path_x = [0.245, 0.185, 0.205, 0.315]
path_y = [0.760, 0.580, 0.478, 0.418]
lbl_y = [0.815, 0.615, 0.415, 0.215]
axA.plot(path_x, path_y, color='k', lw=2.6, ls='--', zorder=3, dash_capstyle='round')
NODES = [('어깨 (상부 고정)', 'o'), ('척추기립근 라인', 's'),
         ('대둔근', '^'), ('서혜부 (하부 고정)', 'o')]
for (lb, mk), xx, yy, ly in zip(NODES, path_x, path_y, lbl_y):
    axA.plot([xx], [yy], marker=mk, ms=8, mfc='white', mec='k', mew=1.5, zorder=4)
    axA.annotate(lb, xy=(xx, yy), xytext=(0.66, ly), fontsize=8.6, va='center',
                 ha='left', zorder=5,
                 bbox=dict(boxstyle='round,pad=0.26', fc='white', ec='0.4', lw=0.7),
                 arrowprops=dict(arrowstyle='-', color='0.4', lw=0.8))
fig.text(0.162, 0.925, '(a) 근골격계 모델과 슈트 경로', ha='center', fontsize=9.5)
fig.text(0.162, 0.885, '전신 620개 근육 중 ES 76개(IL·LTpL·LTpT)를 개별 정량',
         ha='center', fontsize=8.2, color='0.25')

# --- (b) 토크 커플 모델링 ---
axB = fig.add_axes([0.345, 0.075, 0.265, 0.76]); axB.axis('off')
axB.set_xlim(0, 1); axB.set_ylim(0, 1)
fig.text(0.478, 0.925, '(b) 슈트의 해석 모델링', ha='center', fontsize=9.5)
axB.plot([0.5, 0.5], [0.22, 0.80], color='0.25', lw=3, solid_capstyle='round')
for yy, lb in [(0.80, 'thoracic1\n(흉추 1번)'), (0.22, 'pelvis\n(골반)')]:
    box(axB, 0.28, yy - 0.058, 0.44, 0.116, fc='0.92')
    axB.text(0.5, yy, lb, ha='center', va='center', fontsize=8.4, linespacing=1.3)
axB.add_patch(FancyArrowPatch((0.245, 0.715), (0.245, 0.585),
              connectionstyle='arc3,rad=0.8',
              arrowstyle='-|>,head_width=3.4,head_length=6', lw=1.8, color='k'))
axB.text(0.055, 0.650, '+24\nN·m', fontsize=9, fontweight='bold', ha='center',
         va='center', linespacing=1.3)
axB.add_patch(FancyArrowPatch((0.755, 0.325), (0.755, 0.455),
              connectionstyle='arc3,rad=0.8',
              arrowstyle='-|>,head_width=3.4,head_length=6', lw=1.8, color='k'))
axB.text(0.945, 0.390, '−24\nN·m', fontsize=9, fontweight='bold', ha='center',
         va='center', linespacing=1.3)
axB.text(0.5, 0.505, '순수 토크 커플\n(합력 0)', ha='center', va='center', fontsize=8.6,
         linespacing=1.4,
         bbox=dict(boxstyle='round,pad=0.30', fc='white', ec='0.45', lw=0.8))
axB.text(0.5, 0.055, '모멘트 암의 해부학적 배치 가정에\n의존하지 않는 보수적 표현',
         ha='center', va='center', fontsize=8.0, color='0.25', linespacing=1.5)

# --- (c) 사양 → 토크 유도 ---
axC = fig.add_axes([0.655, 0.075, 0.335, 0.76]); axC.axis('off')
axC.set_xlim(0, 1); axC.set_ylim(0, 1)
fig.text(0.822, 0.925, '(c) 액추에이터 사양에서 토크 유도', ha='center', fontsize=9.5)
STEPS = [('SMA 직물 근육\n편측 100 N × 2 = 200 N', 0.865, 'white', 0.9, False),
         ('모멘트 암\n0.10 ~ 0.13 m', 0.630, 'white', 0.9, False),
         ('보조 토크\n20 ~ 26 N·m', 0.395, '0.90', 0.9, False),
         ('해석 조건\n24 N·m  (200 N × 0.12 m)', 0.135, '0.75', 1.8, True)]
for lb, yy, fc, lw, bold in STEPS:
    box(axC, 0.05, yy - 0.083, 0.90, 0.166, fc=fc, lw=lw)
    axC.text(0.5, yy, lb, ha='center', va='center', fontsize=8.8,
             fontweight='bold' if bold else 'normal', linespacing=1.4)
for yy, op in [(0.865, '×'), (0.630, '='), (0.395, '')]:
    arrow(axC, (0.5, yy - 0.089), (0.5, yy - 0.155), lw=1.3)
    if op:
        axC.text(0.575, yy - 0.122, op, fontsize=10, color='0.2', va='center')

fig.savefig(f'{OUT}/fig1_model_and_suit.png', dpi=450, bbox_inches='tight', pad_inches=0.08)
plt.close(fig); print('fig1')


# ==================================================== Figure 2
fig, ax = plt.subplots(figsize=(17.5 * CM, 6.6 * CM))
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
STAGES = [
 ('①', '동작 생성\n· 리타겟', '합성 동작 또는 실측\n보행 데이터를 모델\n좌표로 변환', False),
 ('②', '동작\n육안 검증', '생성 주체와 분리된\n검증자가 렌더 이미지\n만으로 판정', True),
 ('③', '외력\n· 지면반력', '박스 하중·실측 GRF를\n물리적으로 정합하게\n부여', False),
 ('④', 'Static\nOptimization', '동일 동작에서 슈트\n토크만 0 / 24 N·m로\n바꿔 2회 실행', False),
 ('⑤', '근육 부담 정량\n· 시각화', 'ES peak 산출 +\nreserve 점검,\n활성도 색 매핑 영상', False),
]
n = len(STAGES); gap = 0.030
bw = (1 - (n - 1) * gap) / n
TOP, BH = 0.985, 0.735
for i, (num, hd, ds, emph) in enumerate(STAGES):
    x = i * (bw + gap)
    box(ax, x, TOP - BH, bw, BH, fc='0.93' if emph else 'white',
        lw=2.0 if emph else 1.0)
    ax.text(x + bw / 2, TOP - 0.085, num, ha='center', va='center', fontsize=13,
            fontweight='bold')
    ax.text(x + bw / 2, TOP - 0.235, hd, ha='center', va='center', fontsize=9.0,
            fontweight='bold', linespacing=1.35)
    ax.text(x + bw / 2, TOP - 0.415, ds, ha='center', va='top', fontsize=8.1,
            linespacing=1.55)
    if i < n - 1:
        arrow(ax, (x + bw + 0.003, TOP - BH / 2), (x + bw + gap - 0.003, TOP - BH / 2),
              lw=1.6)
ax.text(0.5, 0.085,
        '②단계가 관문 — 동작이 물리적으로 성립하지 않으면 이후 정량은 무의미하므로, '
        '검증 미통과 동작은 해석 대상에서 제외하고 재설계한다.',
        ha='center', va='center', fontsize=8.6,
        bbox=dict(boxstyle='round,pad=0.42', fc='white', ec='0.35', lw=1.0))
fig.savefig(f'{OUT}/fig2_pipeline.png', dpi=450, bbox_inches='tight', pad_inches=0.06)
plt.close(fig); print('fig2')
print('OUT =', OUT)

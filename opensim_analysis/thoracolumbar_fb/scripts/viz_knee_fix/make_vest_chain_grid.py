"""[정정 1] 사진 대조 검증 그리드 — 세 구동기의 힘 사슬 vs 모델 경로.

SO 실행 전 승인용. 수치는 /data/suit_vest/vest_geom.json 에서만 읽는다.
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
SNAP = '/data/suit_vest/snap'
PHOTO = '/data/suit_photos'
PDFP = '/data/wearable-assist/docs/refs/pdf_pages'
G = json.load(open('/data/suit_vest/vest_geom.json'))
CY, OR, GR, BLUE, RED, GREY = ('#159fb5', '#d98324', '#4f9d2e', '#4c72b0',
                               '#c44e52', '0.55')


def show(ax, path, title, crop=None):
    ax.axis('off')
    if not os.path.exists(path):
        ax.text(0.5, 0.5, f'없음: {os.path.basename(path)}', ha='center')
        return
    im = Image.open(path)
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h),
                      int(crop[2] * w), int(crop[3] * h)))
    ax.imshow(np.array(im))
    ax.set_title(title, fontsize=9.4, fontweight='bold', loc='left', pad=5,
                 linespacing=1.4)


fig = plt.figure(figsize=(19.2, 15.4))
gs = fig.add_gridspec(3, 4, hspace=0.20, wspace=0.16,
                      height_ratios=[1.00, 1.15, 0.82],
                      left=0.035, right=0.980, top=0.915, bottom=0.030)
fig.suptitle('[정정 1] 슈트 힘 사슬 재구성 — 제품 사진 대조 (SO 실행 전 승인용)',
             fontsize=15.4, fontweight='bold', y=0.972)
fig.text(0.5, 0.943,
         '조끼 구조: 어깨끈 → 등판 → 근육옷감 → BOA → 허벅지 밴드. '
         '직렬 사슬이므로 장력은 전 구간 동일하고, 몸에 힘이 걸리는 끝점은 어깨와 허벅지다. '
         '※ 기존 모델은 구동부 위치(L1)를 힘 작용점으로 썼다 · 2026-09-26',
         ha='center', fontsize=9.2, color='0.3')

# ── Row 1 : 제품 사진 ────────────────────────────────────────────
show(fig.add_subplot(gs[0, 0]), f'{PHOTO}/waist-suit-parts-labeled-1092.png',
     '(1) 제품 분해 — 조끼 · 근육옷감 · BOA · 허벅지 밴드\n'
     '근육옷감 윗끝은 조끼 등판에 봉제 (뼈 고정 아님)')
show(fig.add_subplot(gs[0, 1]), f'{PDFP}/crop_E_back_right.png',
     '(2) 구성 PDF 후면 — 어깨 구동기(위, 대각)와\n허리 구동기(아래) · 제어기 가방 사이',
     crop=(0.10, 0.05, 1.0, 0.95))
show(fig.add_subplot(gs[0, 2]), f'{PDFP}/crop_C_side.png',
     '(3) 측면 — 어깨 구동기 BOA 가 상완 외측에 있다\n(녹색 선: 견봉 위를 넘어 내려온다)',
     crop=(0.15, 0.03, 1.0, 0.62))
show(fig.add_subplot(gs[0, 3]), f'{PHOTO}/waist-suit-wearing-3view-893.png',
     '(4) 착용 상태 — 어깨끈이 하중을 받는 구조\n허리 밴드는 등판을 몸에 눌러 붙인다')

# ── Row 2 : 모델 경로 ───────────────────────────────────────────
for i, (fn, t, cr) in enumerate((
        ('vest_neutral_sag.png', '(5) 모델 · 중립 기립 · 시상면', (0.22, 0.05, 0.78, 1.0)),
        ('vest_neutral_post.png', '(6) 모델 · 중립 기립 · 후면', (0.28, 0.05, 0.72, 1.0)),
        ('vest_stoop_sag.png', '(7) 모델 · 스툽 t=2.75 s · 시상면', (0.05, 0.05, 0.95, 0.95)),
        ('vest_stoop_post.png', '(8) 모델 · 스툽 t=2.75 s · 후면', (0.25, 0.05, 0.75, 1.0)))):
    show(fig.add_subplot(gs[1, i]), f'{SNAP}/{fn}',
         t + '\n청록 = 허리 · 주황 = 어깨 · 연두 = 팔꿈치', crop=cr)

# ── Row 3-1 : 허리 레벨별 모멘트 암 ──────────────────────────────
ax = fig.add_subplot(gs[2, 0])
ax.set_title('(9) ★ 허리 경로 모멘트 암 — 전 레벨에 보조가 간다',
             fontsize=9.6, fontweight='bold', loc='left', pad=6)
mw = G['marm_waist']
ks = list(mw)
v = [mw[k] for k in ks]
b = ax.barh(range(len(ks)), v, color=CY)
for i, x in enumerate(v):
    ax.text(x + 1.5, i, f'{x:.0f}', va='center', fontsize=7.6)
ax.set_yticks(range(len(ks)))
ax.set_yticklabels([k.replace('_FE', '') for k in ks], fontsize=7.8)
ax.invert_yaxis()
ax.set_xlabel('슈트 모멘트 암 (mm)', fontsize=8.6)
ax.axvline(77, color=RED, ls='--', lw=1.4)
ax.text(78, len(ks) - 0.6, 'ES 최대 근속 77 mm', color=RED, fontsize=7.6)
ax.grid(alpha=.3, axis='x')
ax.set_xlim(0, 115)

# ── Row 3-2 : 어깨 스윕 ─────────────────────────────────────────
ax = fig.add_subplot(gs[2, 1])
ax.set_title('(10) ★ 어깨 후면 경로 — 부호 반전이 없다',
             fontsize=9.6, fontweight='bold', loc='left', pad=6)
sw = G['shoulder_sweep']
a = [r['angle'] for r in sw]
ax.plot(a, [r['r'] for r in sw], 'o-', color=OR, lw=2.3, label='슈트 (후면 대각 + 견봉)')
ax.plot(a, [r['delt_max'] for r in sw], ':', color=BLUE, lw=1.9, label='삼각근 최대 근속')
ax.axhline(0, color='k', lw=1.2)
ax.fill_between(a, 0, [r['r'] for r in sw], color=OR, alpha=0.12)
ax.set_xlabel('어깨 굴곡 elv_angle (°)', fontsize=8.6)
ax.set_ylabel('모멘트 암 (mm)', fontsize=8.6)
ax.grid(alpha=.3)
ax.legend(fontsize=7.4, loc='upper left')
ax.text(0.97, 0.05, '기존 전면 경로는 50° 에서 부호 반전\n→ L-08 재판정 대상',
        transform=ax.transAxes, ha='right', fontsize=8.0, color=RED,
        fontweight='bold', linespacing=1.5)

# ── Row 3-3 : 팔꿈치 스윕 ───────────────────────────────────────
ax = fig.add_subplot(gs[2, 2])
ax.set_title('(11) 팔꿈치 경로 — 견갑(조끼 요크) 기점',
             fontsize=9.6, fontweight='bold', loc='left', pad=6)
sw = G['elbow_sweep']
a = [r['angle'] for r in sw]
ax.plot(a, [r['r'] for r in sw], 'o-', color=GR, lw=2.3, label='슈트 모멘트 암')
ax.axhline(30.9, color=BLUE, ls=':', lw=1.8, label='주동근(BRA) 30.9 mm')
ax2 = ax.twinx()
ax2.plot(a, [r['L'] for r in sw], '--', color=GREY, lw=1.6, label='경로장')
ax2.set_ylabel('경로장 (mm)', fontsize=8.4, color=GREY)
ax.set_xlabel('팔꿈치 굴곡 (°)', fontsize=8.6)
ax.set_ylabel('모멘트 암 (mm)', fontsize=8.6)
ax.grid(alpha=.3)
ax.legend(fontsize=7.4, loc='lower left')

# ── Row 3-4 : 사슬 요약 표 ──────────────────────────────────────
ax = fig.add_subplot(gs[2, 3])
ax.axis('off')
L0 = G['L0']
lines = [
    ('■ 추적한 힘 사슬 (끝점까지)', 'k', 10.0, 'bold'),
    ('  허리   견봉(어깨끈) → 흉추2~요추5 등판 체표', '0.15', 8.8, None),
    (f'         → 천골 → 허벅지 밴드   경로점 14 · {L0["waist"]:.0f} mm', '0.15', 8.8, None),
    ('  어깨   흉추3 체표 → 견봉 위 → 상완 외측(삼각근 조면)', '0.15', 8.8, None),
    (f'         경로점 3 · {L0["shoulder"]:.0f} mm', '0.15', 8.8, None),
    ('  팔꿈치 견봉(조끼 요크) → 상완 전면 → 전완 커프', '0.15', 8.8, None),
    (f'         경로점 3 · {L0["elbow"]:.0f} mm', '0.15', 8.8, None),
    ('', 'k', 4, None),
    ('■ 기존 모델과의 차이', 'k', 10.0, 'bold'),
    ('  허리 상단  L1 뼈 고정 → 견봉(어깨끈)', RED, 8.8, 'bold'),
    ('  → 요추 모멘트 암은 셋 다 같다 (76~90 mm)', '0.15', 8.8, None),
    ('  → 바뀌는 것은 스팬: 흉추 모멘트 암', RED, 8.8, 'bold'),
    ('     A(L1) 0 / B(T8) T8 72·T12 83 / 조끼 T4 81 mm', RED, 8.8, 'bold'),
    ('  어깨       전면 단일 경로 → 후면 대각 + 견봉 경유', RED, 8.8, 'bold'),
    ('  팔꿈치     연장안 = 실제 제품 (변경 없음)', '0.15', 8.8, None),
    ('', 'k', 4, None),
    ('■ 힘 상한 처리 (현재 코드, 확인만)', 'k', 10.0, 'bold'),
    ('  suit_model.solve(): 가열·미가열 모두 100 N 로 잘린다', RED, 8.8, 'bold'),
    ('  스툽 허리 ΔL +150 mm → k·ΔL 750 N 이 100 N 로 포화', '0.15', 8.8, None),
    ('  → 수동/능동 구분 불가. 구속 가열 스윕 필요 (■2)', '0.15', 8.8, None),
]
y = 0.99
for txt, col, sz, wgt in lines:
    if txt:
        ax.text(0.0, y, txt, transform=ax.transAxes, fontsize=sz, color=col,
                fontweight=wgt or 'normal', va='top')
    y -= (sz + 4.2) / 250.0

out = os.path.join(IMG, 'vest_chain_verify_grid.png')
fig.savefig(out, dpi=104)
print('SAVED', out)

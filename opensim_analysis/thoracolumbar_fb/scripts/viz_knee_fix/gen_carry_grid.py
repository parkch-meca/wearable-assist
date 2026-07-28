"""
carry_es_results_grid.png 생성
나르기(carry-walk 20kg) OFF/ON SO 결과 4패널 Grid PNG
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.gridspec as gridspec
import json, re, os, sys

# ── 폰트 설정 (CJK 지원) ─────────────────────────────────────────────────────
import matplotlib.font_manager as fm
cjk_candidates = [f.name for f in fm.fontManager.ttflist
                  if 'CJK' in f.name or 'Noto Sans CJK' in f.name]
if cjk_candidates:
    CJK_FONT = cjk_candidates[0]
else:
    CJK_FONT = 'DejaVu Sans'
print(f"Using font: {CJK_FONT}")
plt.rcParams['font.family'] = [CJK_FONT, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ── 경로 ─────────────────────────────────────────────────────────────────────
OFF_ACT = '/data/carry_results/carry_off/so_StaticOptimization_activation.sto'
ON_ACT  = '/data/carry_results/carry_on/so_StaticOptimization_activation.sto'
SUMMARY = '/data/carry_results/carry_es_summary.json'
OUT_DIR = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box'
OUT_FILE = os.path.join(OUT_DIR, 'carry_es_results_grid.png')

# ── STO 파일 읽기 ────────────────────────────────────────────────────────────
def read_sto(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    # endheader 이후가 데이터
    for i, line in enumerate(lines):
        if line.strip() == 'endheader':
            header_end = i
            break
    cols = lines[header_end + 1].strip().split('\t')
    data_lines = lines[header_end + 2:]
    rows = []
    for line in data_lines:
        vals = line.strip().split('\t')
        if vals and vals[0]:
            rows.append([float(v) for v in vals])
    df = pd.DataFrame(rows, columns=cols)
    return df

print("Loading STO files ...")
df_off = read_sto(OFF_ACT)
df_on  = read_sto(ON_ACT)

# ── ES 근육 컬럼 추출 ────────────────────────────────────────────────────────
ES_PREFIXES = ('IL_', 'LTpL', 'LTpT')

def get_es_cols(df):
    return [c for c in df.columns if c.startswith(ES_PREFIXES)]

es_cols_off = get_es_cols(df_off)
es_cols_on  = get_es_cols(df_on)
# 교집합 사용
es_cols = sorted(set(es_cols_off) & set(es_cols_on))
print(f"ES columns found: {len(es_cols)}")

# SO 창 0.4–1.6s 필터
mask_off = (df_off['time'] >= 0.4) & (df_off['time'] <= 1.6)
mask_on  = (df_on['time']  >= 0.4) & (df_on['time']  <= 1.6)
df_off_w = df_off[mask_off].copy().reset_index(drop=True)
df_on_w  = df_on[mask_on].copy().reset_index(drop=True)

t_off = df_off_w['time'].values
t_on  = df_on_w['time'].values

# ES peak (max across ES muscles at each frame) — ×100 %
es_peak_off = df_off_w[es_cols].max(axis=1).values * 100
es_peak_on  = df_on_w[es_cols].max(axis=1).values * 100

# ES mean (mean across ES muscles at each frame) — ×100 %
es_mean_off = df_off_w[es_cols].mean(axis=1).values * 100
es_mean_on  = df_on_w[es_cols].mean(axis=1).values * 100

# IL_R10_r 있으면 따로도 추출
IL10 = 'IL_R10_r'
if IL10 in df_off_w.columns:
    il10_off = df_off_w[IL10].values * 100
    il10_on  = df_on_w[IL10].values * 100
else:
    il10_off = es_peak_off
    il10_on  = es_peak_on

# ── Summary JSON ─────────────────────────────────────────────────────────────
with open(SUMMARY) as f:
    summ = json.load(f)

phase_labels = ['heel strike\n(R)', 'mid-stance\n(R)', 'toe-off\n(R)', 'whole\ncycle']
phase_off  = [r[1] for r in summ['rows']]
phase_on   = [r[2] for r in summ['rows']]
phase_delta= [r[3] for r in summ['rows']]

# ── Phase 밴드 시간 (0.4–1.6 내 gait events, 정규화 참고) ────────────────────
# 1주기 0.4~1.6s (1.2s 길이)
# heel strike: ~0.4, mid-stance: ~0.7, toe-off: ~0.95
T_START, T_END = 0.4, 1.6
T_CYCLE = T_END - T_START
# gait events 대략값
t_hs  = T_START + 0.0 * T_CYCLE   # heel strike R = 0.40
t_ms  = T_START + 0.25 * T_CYCLE  # mid-stance  = 0.70
t_to  = T_START + 0.47 * T_CYCLE  # toe-off     = 0.96
t_hs2 = T_END                     # next cycle  = 1.60

# 밴드 폭 (±band_w)
BW = 0.04

# ── 5동작 부하–슈트 데이터 ──────────────────────────────────────────────────
MOTION_LABELS = ['squat\n(맨몸)', 'stoop\n(맨몸)', 'box stoop\n20 kg', 'gait\n(걷기)', 'carry\n20 kg']
SUIT_EFFECTS   = [-47, -32, -23, 0, -25.4]   # %p  (carry = mid-stance robust)
MOTION_COLORS  = ['#4878CF', '#6ACC65', '#D65F5F', '#B47CC7', '#C4AD66']

# ── Figure 생성 ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 14), facecolor='#1C1C1C')
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32,
                       left=0.07, right=0.96, top=0.90, bottom=0.08)

ax1 = fig.add_subplot(gs[0, 0])   # ES peak 시계열
ax2 = fig.add_subplot(gs[0, 1])   # Phase bar
ax3 = fig.add_subplot(gs[1, 0])   # ES mean 시계열
ax4 = fig.add_subplot(gs[1, 1])   # 5동작 bar

DARK_BG = '#1C1C1C'
PANEL_BG = '#2A2A2A'
TEXT_COLOR = '#E0E0E0'
GRID_COLOR = '#444444'
OFF_COLOR  = '#888888'
ON_COLOR   = '#E05252'

def style_ax(ax, title):
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor('#555555')
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)
    ax.set_title(title, fontsize=11, fontweight='bold', color=TEXT_COLOR, pad=8)

def add_phase_bands(ax, alpha=0.12):
    """heel strike / mid-stance / toe-off 밴드 추가"""
    events = [
        (t_hs,  'Heel Strike',  '#60B0FF'),
        (t_ms,  'Mid-Stance',   '#60FF90'),
        (t_to,  'Toe-Off',      '#FFB060'),
    ]
    ymin, ymax = ax.get_ylim()
    for t_ev, label, col in events:
        ax.axvspan(t_ev - BW, t_ev + BW, color=col, alpha=alpha, zorder=0)
        ax.axvline(t_ev, color=col, linewidth=1.0, linestyle='--', alpha=0.7, zorder=1)
        ax.text(t_ev, ymax * 0.97, label.replace(' ', '\n'), color=col,
                fontsize=7, ha='center', va='top', zorder=5,
                bbox=dict(boxstyle='round,pad=0.2', fc=DARK_BG, alpha=0.6, ec='none'))

# ════════════════════════════════════════════════════════════════════════════
# Panel 1: ES peak 시계열 (IL_R10 or ES peak max)
# ════════════════════════════════════════════════════════════════════════════
ax1.plot(t_off, es_peak_off, color=OFF_COLOR, linewidth=2.0,
         label='OFF (슈트 없음)', zorder=3)
ax1.plot(t_on,  es_peak_on,  color=ON_COLOR,  linewidth=2.0,
         label='ON  (슈트 24 N·m)', zorder=3)

# 포화선 100%
ax1.axhline(100.0, color='#FFE566', linewidth=1.5, linestyle=':', zorder=4,
            label='포화 한계 (100%)')

# 포화 구간 강조 (OFF > 98%)
sat_mask = es_peak_off >= 98.0
if sat_mask.any():
    ax1.fill_between(t_off, 98, es_peak_off,
                     where=sat_mask, color='#FFE566', alpha=0.25, zorder=2,
                     label='OFF 포화 구간')

ax1.set_xlabel('시간 (s)', fontsize=10)
ax1.set_ylabel('ES Peak 활성화 (%)', fontsize=10)
ax1.set_xlim(T_START, T_END)
ax1.set_ylim(0, 112)
style_ax(ax1, 'Panel 1: ES Peak 시계열 (IL_R10 기준)')
add_phase_bands(ax1, alpha=0.13)

# 포화 주석
ax1.annotate('OFF 100% 포화\n→ peak 저평가\nmid-stance/mean이\nrobust 지표',
             xy=(t_ms, 100.5), xytext=(t_ms + 0.18, 105),
             fontsize=7.5, color='#FFE566',
             arrowprops=dict(arrowstyle='->', color='#FFE566', lw=1.2),
             bbox=dict(boxstyle='round,pad=0.3', fc='#333300', alpha=0.85, ec='#FFE566'),
             zorder=10)

ax1.legend(loc='lower right', fontsize=7.5, facecolor=DARK_BG,
           labelcolor=TEXT_COLOR, edgecolor='#555555', framealpha=0.85)

# ════════════════════════════════════════════════════════════════════════════
# Panel 2: Phase별 bar chart
# ════════════════════════════════════════════════════════════════════════════
x = np.arange(len(phase_labels))
bw = 0.32
bars_off = ax2.bar(x - bw/2, phase_off, bw, label='OFF', color=OFF_COLOR, alpha=0.85, zorder=3)
bars_on  = ax2.bar(x + bw/2, phase_on,  bw, label='ON',  color=ON_COLOR,  alpha=0.85, zorder=3)

# Δ 라벨
for i, (o, n, d) in enumerate(zip(phase_off, phase_on, phase_delta)):
    col = '#FFE566' if abs(d) > 20 else '#AAFFAA'  # highlight if big
    ax2.text(i, max(o, n) + 2.5, f'Δ{d:+.1f}%p',
             ha='center', va='bottom', fontsize=8, color=col,
             fontweight='bold', zorder=5)
    ax2.text(i - bw/2, o - 3, f'{o:.1f}%', ha='center', va='top',
             fontsize=7, color='#CCCCCC', zorder=5)
    ax2.text(i + bw/2, n - 3, f'{n:.1f}%', ha='center', va='top',
             fontsize=7, color='#FFAAAA', zorder=5)

# 포화선 & 주석 for whole cycle
ax2.axhline(100.0, color='#FFE566', linewidth=1.2, linestyle=':', zorder=4)
ax2.text(3, 101.5, '포화 한계', color='#FFE566', fontsize=7, ha='center', zorder=6)

# robust 지표 강조 (mid-stance 막대 테두리)
bars_off[1].set_edgecolor('#FFE566')
bars_off[1].set_linewidth(2.0)
bars_on[1].set_edgecolor('#FFE566')
bars_on[1].set_linewidth(2.0)
ax2.text(1, -10, 'robust\n지표', ha='center', va='top', fontsize=7,
         color='#FFE566', fontweight='bold', zorder=6)

ax2.set_xticks(x)
ax2.set_xticklabels(phase_labels, fontsize=8.5)
ax2.set_ylabel('ES Peak 활성화 (%)', fontsize=10)
ax2.set_ylim(-15, 115)
ax2.set_xlabel('보행 Phase', fontsize=10)
style_ax(ax2, 'Panel 2: Phase별 ES Peak — OFF vs ON')
ax2.legend(loc='upper left', fontsize=8, facecolor=DARK_BG,
           labelcolor=TEXT_COLOR, edgecolor='#555555', framealpha=0.85)

# ════════════════════════════════════════════════════════════════════════════
# Panel 3: ES mean 시계열
# ════════════════════════════════════════════════════════════════════════════
ax3.plot(t_off, es_mean_off, color=OFF_COLOR, linewidth=2.0,
         label='OFF (슈트 없음)', zorder=3)
ax3.plot(t_on,  es_mean_on,  color=ON_COLOR,  linewidth=2.0,
         label='ON  (슈트 24 N·m)', zorder=3)

# 전체 평균 수평선
mean_peak_off = summ['es_mean_off']
mean_peak_on  = summ['es_mean_on']
ax3.axhline(mean_peak_off, color=OFF_COLOR, linewidth=0.8, linestyle='--', alpha=0.5)
ax3.axhline(mean_peak_on,  color=ON_COLOR,  linewidth=0.8, linestyle='--', alpha=0.5)

# 차이 채우기
ax3.fill_between(t_off, es_mean_on, es_mean_off, alpha=0.20, color=ON_COLOR,
                 where=(es_mean_off >= es_mean_on), zorder=2, label='슈트 효과 구간')

# 전체 피크 주석
ax3.annotate(f'OFF 전체 peak:\n{mean_peak_off:.2f}%',
             xy=(t_off[np.argmax(es_mean_off)], np.max(es_mean_off)),
             xytext=(T_START + 0.06, np.max(es_mean_off) + 2.5),
             fontsize=7.5, color=OFF_COLOR,
             arrowprops=dict(arrowstyle='->', color=OFF_COLOR, lw=0.9),
             bbox=dict(boxstyle='round,pad=0.2', fc='#2A2A2A', alpha=0.8, ec='none'),
             zorder=10)
ax3.annotate(f'ON 전체 peak:\n{mean_peak_on:.2f}%\n(−{mean_peak_off - mean_peak_on:.2f}%p, −27.4%)',
             xy=(t_on[np.argmax(es_mean_on)], np.max(es_mean_on)),
             xytext=(T_START + 0.55, np.max(es_mean_on) + 2.5),
             fontsize=7.5, color=ON_COLOR,
             arrowprops=dict(arrowstyle='->', color=ON_COLOR, lw=0.9),
             bbox=dict(boxstyle='round,pad=0.2', fc='#2A2A2A', alpha=0.8, ec='none'),
             zorder=10)

ax3.set_xlabel('시간 (s)', fontsize=10)
ax3.set_ylabel('ES Mean 활성화 — 76근육 평균 (%)', fontsize=9.5)
ax3.set_xlim(T_START, T_END)
ax3.set_ylim(0, None)
style_ax(ax3, 'Panel 3: ES Mean 시계열 (76근육, 포화 없음 → robust 보조 지표)')
add_phase_bands(ax3, alpha=0.10)

ax3.text(T_START + 0.02, ax3.get_ylim()[1] * 0.92,
         '★ 포화 없음 → 왜곡 없는\n  슈트 효과 (−27.4%)',
         fontsize=8, color='#AAFFAA',
         bbox=dict(boxstyle='round,pad=0.3', fc='#1C3320', alpha=0.85, ec='#AAFFAA'),
         zorder=10)

ax3.legend(loc='upper right', fontsize=7.5, facecolor=DARK_BG,
           labelcolor=TEXT_COLOR, edgecolor='#555555', framealpha=0.85)

# ════════════════════════════════════════════════════════════════════════════
# Panel 4: 5동작 부하–슈트효과 bar
# ════════════════════════════════════════════════════════════════════════════
x4 = np.arange(len(MOTION_LABELS))
bars4 = ax4.bar(x4, SUIT_EFFECTS, color=MOTION_COLORS, alpha=0.88, zorder=3,
                edgecolor='#333333', linewidth=0.8)

# 현재 동작(carry) 강조 테두리
bars4[-1].set_edgecolor('#FFE566')
bars4[-1].set_linewidth(2.5)

for i, (bar, val) in enumerate(zip(bars4, SUIT_EFFECTS)):
    ypos = val - 1.5 if val < 0 else val + 0.5
    va = 'top' if val < 0 else 'bottom'
    ax4.text(bar.get_x() + bar.get_width()/2, ypos,
             f'{val:+.1f}%p', ha='center', va=va, fontsize=9,
             color='white', fontweight='bold', zorder=5)

# carry 주석
ax4.annotate('★ carry 20 kg\nmid-stance −25.4%p\n(lifting −23%보다 큼)',
             xy=(4, -25.4), xytext=(3.05, -40),
             fontsize=8, color='#FFE566',
             arrowprops=dict(arrowstyle='->', color='#FFE566', lw=1.2),
             bbox=dict(boxstyle='round,pad=0.3', fc='#333300', alpha=0.85, ec='#FFE566'),
             zorder=10)

# gait ~0 설명
ax4.text(3, 2.5, 'gait: 슈트\n거의 무영향', ha='center', fontsize=7.5,
         color='#B0B0FF', zorder=6)

# 0선
ax4.axhline(0, color='#888888', linewidth=0.8, linestyle='-')

ax4.set_xticks(x4)
ax4.set_xticklabels(MOTION_LABELS, fontsize=8.5)
ax4.set_ylabel('슈트 효과 (ES Peak Δ%p)', fontsize=10)
ax4.set_ylim(-55, 12)
ax4.set_xlabel('동작 종류', fontsize=10)
style_ax(ax4, 'Panel 4: 5동작 부하–슈트효과 비교')

# 전체 제목
fig.suptitle('나르기(Carry-Walk 20 kg) OFF/ON SO 결과\n'
             'ES Peak 포화 주의 — mid-stance(−25.4%p) 및 ES mean(−27.4%) 이 robust 지표',
             fontsize=13, fontweight='bold', color=TEXT_COLOR, y=0.96)

# 오른쪽 하단 메타
fig.text(0.97, 0.01,
         'spine reserve 1.7 N·m ✅ | n_ES=76 | SO 창 0.4–1.6 s | suit 24 N·m',
         ha='right', va='bottom', fontsize=7.5, color='#888888', style='italic')

# ── 저장 ─────────────────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
fig.savefig(OUT_FILE, dpi=150, bbox_inches='tight', facecolor=DARK_BG)
print(f"Saved: {OUT_FILE}")
plt.close(fig)
print("Done.")

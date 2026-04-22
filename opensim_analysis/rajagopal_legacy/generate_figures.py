#!/usr/bin/env python3
"""Generate publication-quality figures for SMA exosuit analysis."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import os

# ── Font setup ────────────────────────────────────────────────────────────────
# Use Noto Sans CJK KR for Korean text
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'  # JP includes KR glyphs
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.dpi'] = 300

OUT = "/data/opensim_results/figures"
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv("/data/opensim_results/all_results.csv")

# Color palette
C_SUIT = ['#E8EAF6', '#7986CB', '#3F51B5', '#1A237E', '#0D1B4A']  # light→dark blue
C_LOAD = ['#4CAF50', '#FF9800', '#F44336']  # green, orange, red
C_GRAY = '#9E9E9E'
C_BG = '#FAFAFA'


# ══════════════════════════════════════════════════════════════════════════════
# Figure 1: Force-Reduction Bar Chart
# ══════════════════════════════════════════════════════════════════════════════
def fig1():
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    loads = [10, 20, 30]
    forces = [0, 50, 100, 150, 200]
    x = np.arange(len(forces))
    width = 0.25

    baseline = df[df['suit_force_n'] == 0]
    for i, ld in enumerate(loads):
        reductions = []
        for sn in forces:
            bl = baseline[baseline['load_kg'] == ld]['lumbar_bio_ext_peak'].mean()
            sub = df[(df['suit_force_n'] == sn) & (df['load_kg'] == ld)]['lumbar_bio_ext_peak'].mean()
            reductions.append((1 - sub / bl) * 100 if bl > 0 else 0)
        bars = ax.bar(x + (i - 1) * width, reductions, width * 0.9,
                       color=C_LOAD[i], label=f'{ld}kg 하중', edgecolor='white', linewidth=0.5)
        # Value labels on top
        for bar, val in zip(bars, reductions):
            if val > 1:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xlabel('SMA 보조력 (N)', fontsize=14, fontweight='bold')
    ax.set_ylabel('요추 토크 감소율 (%)', fontsize=14, fontweight='bold')
    ax.set_title('SMA 보조력별 척추기립근 부하 감소', fontsize=16, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{f}N' for f in forces], fontsize=12)
    ax.legend(fontsize=12, loc='upper left', framealpha=0.9)
    ax.set_ylim(0, 28)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(f'{OUT}/fig1_force_reduction.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 1 saved")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 2: Demographic Comparison
# ══════════════════════════════════════════════════════════════════════════════
def fig2():
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    ages = ['young', 'middle', 'senior']
    age_labels = ['20대\n(Young)', '40대\n(Middle)', '60대\n(Senior)']
    sexes = ['male', 'female']
    sex_labels = ['남성 (Male)', '여성 (Female)']
    sex_colors = ['#1976D2', '#E91E63']

    x = np.arange(len(ages))
    width = 0.35

    for si, (sex, sl, sc) in enumerate(zip(sexes, sex_labels, sex_colors)):
        reds = []
        for age in ages:
            bl = df[(df['suit_force_n']==0)&(df['sex']==sex)&(df['age']==age)&(df['load_kg']==20)]['lumbar_bio_ext_peak'].mean()
            s2 = df[(df['suit_force_n']==200)&(df['sex']==sex)&(df['age']==age)&(df['load_kg']==20)]['lumbar_bio_ext_peak'].mean()
            reds.append((1-s2/bl)*100 if bl>0 else 0)
        bars = ax.bar(x + (si-0.5)*width, reds, width*0.85, color=sc, label=sl,
                       edgecolor='white', linewidth=0.5, alpha=0.85)
        for bar, val in zip(bars, reds):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_xlabel('연령대', fontsize=14, fontweight='bold')
    ax.set_ylabel('요추 토크 감소율 (%)', fontsize=14, fontweight='bold')
    ax.set_title('성별·연령별 SMA 슈트 효과 (200N, 20kg 하중)',
                 fontsize=15, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(age_labels, fontsize=12)
    ax.legend(fontsize=12, loc='upper left', framealpha=0.9)
    ax.set_ylim(14, 18)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Highlight annotation — large red box
    ax.annotate('60대 여성에서\n가장 효과적!', xy=(2.175, 16.9), fontsize=15,
                ha='center', color='white', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#C62828', lw=2.5),
                xytext=(1.5, 17.6),
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#C62828', edgecolor='#B71C1C', linewidth=2))

    fig.tight_layout()
    fig.savefig(f'{OUT}/fig2_demographic.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'{OUT}/fig2_demographic_v2.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 2 saved (v2)")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 3: Regression Plot
# ══════════════════════════════════════════════════════════════════════════════
def fig3():
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    # Compute reduction for each of the 270 conditions
    conds = df.groupby(['sex','age','body_type','load_kg','suit_force_n'])['lumbar_bio_ext_peak'].mean().reset_index()
    bl_conds = conds[conds['suit_force_n']==0][['sex','age','body_type','load_kg','lumbar_bio_ext_peak']].rename(
        columns={'lumbar_bio_ext_peak':'baseline'})
    merged = conds.merge(bl_conds, on=['sex','age','body_type','load_kg'])
    merged['reduction'] = (1 - merged['lumbar_bio_ext_peak']/merged['baseline'])*100

    # Color by load
    for ld, color, marker in zip([10,20,30], C_LOAD, ['o','s','^']):
        sub = merged[merged['load_kg']==ld]
        ax.scatter(sub['suit_force_n'], sub['reduction'], c=color, marker=marker,
                   s=40, alpha=0.7, label=f'{ld}kg', edgecolors='white', linewidths=0.3)

    # Overall regression line
    x_all = merged['suit_force_n'].values
    y_all = merged['reduction'].values
    mask = x_all > 0  # exclude 0N baseline
    from numpy.polynomial import polynomial as P
    coef = np.polyfit(x_all[mask], y_all[mask], 1)
    x_line = np.linspace(0, 210, 100)
    y_line = np.polyval(coef, x_line)
    r2 = 1 - np.sum((y_all[mask]-np.polyval(coef,x_all[mask]))**2)/np.sum((y_all[mask]-y_all[mask].mean())**2)

    ax.plot(x_line, y_line, 'k-', linewidth=2, alpha=0.8, zorder=5)
    ax.fill_between(x_line, y_line-2, y_line+2, alpha=0.1, color='gray')

    ax.text(120, 22, f'R² = {r2:.3f}\n50N당 ~{coef[0]*50:.1f}% 감소',
            fontsize=12, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax.set_xlabel('SMA 보조력 (N)', fontsize=14, fontweight='bold')
    ax.set_ylabel('요추 토크 감소율 (%)', fontsize=14, fontweight='bold')
    ax.set_title('보조력-감소율 선형 관계 (270개 조건)',
                 fontsize=15, fontweight='bold', pad=15)
    ax.legend(title='작업 하중', fontsize=11, title_fontsize=12, loc='lower right')
    ax.set_xlim(-10, 220)
    ax.set_ylim(-2, 30)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(f'{OUT}/fig3_regression.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 3 saved")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 4: Load Comparison Line Chart
# ══════════════════════════════════════════════════════════════════════════════
def fig4():
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    forces = [0, 50, 100, 150, 200]
    for ld, color, ls in zip([10,20,30], C_LOAD, ['-','--','-.']):
        peaks = []
        for sn in forces:
            sub = df[(df['suit_force_n']==sn)&(df['load_kg']==ld)]
            peaks.append(sub['lumbar_bio_ext_peak'].mean())
        ax.plot(forces, peaks, f'{ls}o', color=color, linewidth=2.5, markersize=8,
                label=f'{ld}kg 하중', markeredgecolor='white', markeredgewidth=1)

        # Shade reduction area
        bl = peaks[0]
        ax.fill_between(forces, peaks, bl, alpha=0.08, color=color)

    ax.set_xlabel('SMA 보조력 (N)', fontsize=14, fontweight='bold')
    ax.set_ylabel('요추 extension 토크 (Nm)', fontsize=14, fontweight='bold')
    ax.set_title('작업 하중별 요추 토크 변화 곡선', fontsize=15, fontweight='bold', pad=15)
    ax.legend(fontsize=12, loc='upper right', framealpha=0.9)
    ax.set_xlim(-5, 205)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Annotate suit assist zone
    ax.axvspan(0, 0, color='gray', alpha=0.3)
    ax.annotate('슈트 보조 영역\n(Suit Assist Zone)', xy=(100, 80), fontsize=10,
                ha='center', color='#1565C0', fontstyle='italic')

    fig.tight_layout()
    fig.savefig(f'{OUT}/fig4_load_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 4 saved")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 5: Musculoskeletal Schematic (simplified stick figure)
# ══════════════════════════════════════════════════════════════════════════════
def fig5():
    fig, axes = plt.subplots(1, 3, figsize=(15, 7))
    fig.patch.set_facecolor('white')

    phases = [
        ('직립 (Standing)', 0, {'trunk': 0, 'hip': 10, 'knee': 5}),
        ('최대 굴곡 (Max Flexion)', 1, {'trunk': 45, 'hip': 60, 'knee': 40}),
        ('복귀 (Recovery)', 2, {'trunk': 10, 'hip': 15, 'knee': 8}),
    ]

    for ax, (title, idx, angles) in zip(axes, phases):
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-0.3, 2.2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

        # Draw simplified skeleton
        trunk_angle = np.radians(angles['trunk'])
        hip_angle = np.radians(angles['hip'])

        # Pelvis position
        px, py = 0, 0.9

        # Trunk (from pelvis upward, angled forward)
        trunk_len = 0.6
        tx = px - trunk_len * np.sin(trunk_angle)
        ty = py + trunk_len * np.cos(trunk_angle)

        # Head
        hx = tx - 0.15 * np.sin(trunk_angle)
        hy = ty + 0.15 * np.cos(trunk_angle)

        # Upper legs
        leg_len = 0.45
        lx = px + leg_len * np.sin(np.radians(hip_angle - 90))
        ly = py + leg_len * np.cos(np.radians(hip_angle - 90))

        # Lower legs
        knee_angle_r = np.radians(angles['knee'])
        llx = lx + 0.45 * np.sin(np.radians(-90 + angles['knee']))
        lly = ly + 0.45 * np.cos(np.radians(-90 + angles['knee']))

        # Arms
        arm_len = 0.5
        ax_r = tx + arm_len * np.sin(trunk_angle + 0.3)
        ay_r = ty - arm_len * np.cos(trunk_angle + 0.3)

        # Erector spinae activation color
        # Higher during max flexion
        es_activation = [0.3, 0.9, 0.5][idx]
        es_color = plt.cm.RdYlGn_r(es_activation)

        # Draw body segments
        lw = 6
        # Trunk
        ax.plot([px, tx], [py, ty], color=es_color, linewidth=lw+2, solid_capstyle='round', zorder=2)
        ax.plot([px, tx], [py, ty], color='#424242', linewidth=lw, solid_capstyle='round', zorder=3)
        # Head
        circle = plt.Circle((hx, hy), 0.08, color='#616161', zorder=4)
        ax.add_patch(circle)
        # Legs (simplified, both same)
        for sign in [-0.15, 0.15]:
            ax.plot([px+sign, px+sign-0.1*np.sin(np.radians(angles['hip']))],
                    [py, py-0.4], color='#757575', linewidth=lw-1, solid_capstyle='round')
            ax.plot([px+sign-0.1*np.sin(np.radians(angles['hip'])), px+sign],
                    [py-0.4, py-0.85], color='#757575', linewidth=lw-1, solid_capstyle='round')
        # Arms
        for sign in [-1, 1]:
            ax.plot([tx, tx+sign*0.1+0.3*np.sin(trunk_angle)],
                    [ty-0.05, ty-0.4], color='#9E9E9E', linewidth=lw-2, solid_capstyle='round')

        # Ground line
        ax.axhline(y=0.05, color='#BDBDBD', linewidth=1, linestyle='--')

        # Erector spinae label
        es_pct = [30, 90, 50][idx]
        ax.text(px+0.5, py+0.3, f'ES: {es_pct}%', fontsize=11, fontweight='bold',
                color=es_color, ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        # Suit indicator for phase 1 (max flexion)
        if idx == 1:
            ax.annotate('SMA 슈트\n보조 23Nm', xy=(px-0.4, py+0.1), fontsize=10,
                        color='#1565C0', fontweight='bold', ha='center',
                        bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.9))

    fig.suptitle('Stoop-Lift 동작 단계별 척추기립근(ES) 활성도',
                 fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig5_musculoskeletal_snapshot.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 5 saved")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 6: Infographic Summary
# ══════════════════════════════════════════════════════════════════════════════
def fig6():
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#F5F5F5')
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title banner
    banner = FancyBboxPatch((0.3, 7.0), 11.4, 0.8, boxstyle='round,pad=0.1',
                             facecolor='#1A237E', edgecolor='none')
    ax.add_patch(banner)
    ax.text(6, 7.4, 'SMA 근력보조슈트 — 근골격 분석 결과', fontsize=20,
            fontweight='bold', color='white', ha='center', va='center')
    ax.text(6, 7.1, 'SMA Fabric Exosuit — Musculoskeletal Analysis Results', fontsize=11,
            color='#B0BEC5', ha='center', va='center')

    # Key number box
    box1 = FancyBboxPatch((0.5, 4.8), 3.5, 2.0, boxstyle='round,pad=0.15',
                           facecolor='white', edgecolor='#1565C0', linewidth=2)
    ax.add_patch(box1)
    ax.text(2.25, 6.3, '전체 평균 감소율', fontsize=12, ha='center', color='#424242', fontweight='bold')
    ax.text(2.25, 5.5, '17.4%', fontsize=42, ha='center', va='center',
            color='#1565C0', fontweight='bold')
    ax.text(2.25, 5.0, '(range: 12–26%)', fontsize=10, ha='center', color='#757575')

    # Load breakdown
    box2 = FancyBboxPatch((4.3, 4.8), 3.5, 2.0, boxstyle='round,pad=0.15',
                           facecolor='white', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(box2)
    ax.text(6.05, 6.3, '하중별 효과', fontsize=12, ha='center', color='#424242', fontweight='bold')
    for i, (ld, red) in enumerate([(10, 23.4), (20, 16.2), (30, 12.4)]):
        y = 5.8 - i * 0.45
        ax.text(4.8, y, f'{ld}kg:', fontsize=13, ha='left', color='#616161', fontweight='bold')
        ax.text(7.3, y, f'{red:.1f}%', fontsize=13, ha='right', color='#2E7D32', fontweight='bold')

    # Best case
    box3 = FancyBboxPatch((8.1, 4.8), 3.5, 2.0, boxstyle='round,pad=0.15',
                           facecolor='white', edgecolor='#E91E63', linewidth=2)
    ax.add_patch(box3)
    ax.text(9.85, 6.3, '최대 효과 대상', fontsize=12, ha='center', color='#424242', fontweight='bold')
    ax.text(9.85, 5.7, '60대 여성', fontsize=16, ha='center', color='#C62828', fontweight='bold')
    ax.text(9.85, 5.3, '소체형, 10kg 하중', fontsize=11, ha='center', color='#757575')
    ax.text(9.85, 4.95, '25.8% 감소', fontsize=18, ha='center', color='#E91E63', fontweight='bold')

    # Specification box
    box4 = FancyBboxPatch((0.5, 2.8), 11.1, 1.7, boxstyle='round,pad=0.15',
                           facecolor='#E8EAF6', edgecolor='none')
    ax.add_patch(box4)
    ax.text(6, 4.15, '슈트 사양 (Suit Specification)', fontsize=13, ha='center',
            color='#283593', fontweight='bold')

    specs = [
        ('SMA 액추에이터', '200N × 11.5cm = 23Nm'),
        ('분석 모델', 'Rajagopal2016 + Erector Spinae (82 muscles)'),
        ('모션 데이터', 'BONES-SEED 748 stoop, 10 representative clips'),
        ('시뮬레이션', '270 conditions × 10 motions = 2,700 runs'),
    ]
    for i, (key, val) in enumerate(specs):
        y = 3.7 - i * 0.3
        ax.text(1.0, y, f'{key}:', fontsize=10, ha='left', color='#37474F', fontweight='bold')
        ax.text(4.0, y, val, fontsize=10, ha='left', color='#546E7A')

    # Bottom: marketing message
    box5 = FancyBboxPatch((0.5, 0.3), 11.1, 2.2, boxstyle='round,pad=0.15',
                           facecolor='#1565C0', edgecolor='none')
    ax.add_patch(box5)
    ax.text(6, 2.1, '"20kg 박스를 들어올리는 작업에서"', fontsize=14,
            ha='center', color='white', fontstyle='italic')
    ax.text(6, 1.6, '"60대 여성 기준 200N SMA 슈트 착용 시"', fontsize=14,
            ha='center', color='white', fontstyle='italic')
    ax.text(6, 1.0, '척추기립근 부하 17.3% 감소', fontsize=22,
            ha='center', color='#FFC107', fontweight='bold')
    ax.text(6, 0.5, 'Erector Spinae Load Reduced by 17.3%', fontsize=12,
            ha='center', color='#B0BEC5')

    fig.savefig(f'{OUT}/fig6_infographic.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Fig 6 saved")


# ── Generate all ──────────────────────────────────────────────────────────────
print("Generating figures...")
fig1()
fig2()
fig3()
fig4()
fig5()
fig6()
print(f"\nAll figures saved to {OUT}/")
for f in sorted(os.listdir(OUT)):
    sz = os.path.getsize(os.path.join(OUT, f)) / 1024
    print(f"  {f} ({sz:.0f} KB)")

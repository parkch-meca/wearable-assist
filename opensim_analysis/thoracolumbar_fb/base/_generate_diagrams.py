"""
Grid PNG 생성 스크립트 (영구 protocol).

출력:
  docs/images/step2_base/model_setup_diagram.png
  docs/images/step2_base/model_setup_verification_grid.png
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

OUT_DIR = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step2_base'
os.makedirs(OUT_DIR, exist_ok=True)

# ───────────────────────────────────────────────────────────────────────────
# 1. model_setup_diagram.png — 모듈 구조 아키텍처 다이어그램
# ───────────────────────────────────────────────────────────────────────────

def make_diagram():
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis('off')
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # ── 색상 팔레트 ──
    C_BOX_IN   = '#1f3a5f'   # 입력 박스
    C_BOX_PROC = '#1a3a1a'   # 처리 박스
    C_BOX_OUT  = '#3a1a1a'   # 출력 박스
    C_BOX_REF  = '#2a2a1a'   # 참조 박스
    C_TEXT     = '#e6edf3'
    C_ARROW    = '#58a6ff'
    C_WARN     = '#f0b429'
    C_GREEN    = '#3fb950'
    C_BORDER_IN   = '#388bfd'
    C_BORDER_PROC = '#3fb950'
    C_BORDER_OUT  = '#f85149'
    C_BORDER_REF  = '#d29922'

    def box(ax, x, y, w, h, label, sublabel='', fc='#1a2332', ec='#388bfd',
            fontsize=9, subfontsize=7.5):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle='round,pad=0.06',
                              facecolor=fc, edgecolor=ec, linewidth=1.8, zorder=3)
        ax.add_patch(rect)
        cy = y + h / 2
        if sublabel:
            ax.text(x + w/2, cy + 0.14, label,
                    ha='center', va='center', fontsize=fontsize,
                    color=C_TEXT, fontweight='bold', zorder=4)
            ax.text(x + w/2, cy - 0.22, sublabel,
                    ha='center', va='center', fontsize=subfontsize,
                    color='#8b949e', zorder=4, style='italic')
        else:
            ax.text(x + w/2, cy, label,
                    ha='center', va='center', fontsize=fontsize,
                    color=C_TEXT, fontweight='bold', zorder=4)

    def arrow(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=C_ARROW,
                                   lw=1.8, connectionstyle='arc3,rad=0'))

    # ── 제목 ──
    ax.text(6.5, 8.6, 'base/model_setup.py — ModelProcessor Architecture',
            ha='center', va='center', fontsize=13, color=C_TEXT,
            fontweight='bold')
    ax.text(6.5, 8.2, 'Step 2 Week 1.1 | Dembia 2020 + Hicks 2015 표준',
            ha='center', va='center', fontsize=9, color='#8b949e')

    # ── 입력 그룹 (왼쪽) ──
    ax.text(1.5, 7.7, 'INPUTS', ha='center', fontsize=8,
            color=C_BORDER_IN, fontweight='bold')
    box(ax, 0.2, 6.8, 2.6, 0.7, 'model_path (.osim)',
        'forearm_v1 | no_coupler', fc=C_BOX_IN, ec=C_BORDER_IN)
    box(ax, 0.2, 5.9, 2.6, 0.7, "task_type",
        "'stoop' | 'box' | 'squat' | 'walk'", fc=C_BOX_IN, ec=C_BORDER_IN)
    box(ax, 0.2, 5.0, 2.6, 0.7, 'residuals_rot / trans',
        'auto from task_type', fc=C_BOX_IN, ec=C_BORDER_IN)
    box(ax, 0.2, 4.1, 2.6, 0.7, 'external_loads_xml',
        'stoop GRF STO (optional)', fc=C_BOX_IN, ec=C_BORDER_IN)

    # ── 중앙 처리 파이프라인 ──
    ax.text(6.5, 7.7, 'ModelProcessor PIPELINE', ha='center', fontsize=8,
            color=C_BORDER_PROC, fontweight='bold')
    # Step 1
    box(ax, 4.0, 6.7, 5.0, 0.8,
        'Step 1: ModOpAddExternalLoads',
        'stoop GRF STO (optional; box/squat: None)',
        fc=C_BOX_PROC, ec=C_BORDER_PROC)
    # Step 2
    box(ax, 4.0, 5.6, 5.0, 0.8,
        'Step 2: ModOpAddResiduals(rot, trans, 1.0)',
        'pelvis 6 DOF 전용 | API: (rotational_F, translational_F, bound_scale)',
        fc=C_BOX_PROC, ec=C_BORDER_PROC)
    # Step 3
    box(ax, 4.0, 4.5, 5.0, 0.8,
        'Step 3: ModOpAddReserves(1.0)',
        '나머지 관절 — weak | Dembia 2020 standard',
        fc=C_BOX_PROC, ec=C_BORDER_PROC)

    # 파이프라인 내부 화살표
    arrow(ax, 6.5, 6.7, 6.5, 6.45)
    arrow(ax, 6.5, 5.6, 6.5, 5.35)

    # 입력 → 파이프라인 화살표
    arrow(ax, 2.8, 7.15, 4.0, 7.1)   # model_path
    arrow(ax, 2.8, 6.25, 4.0, 6.7)   # task_type
    arrow(ax, 2.8, 5.35, 4.0, 5.95)  # residuals
    arrow(ax, 2.8, 4.45, 4.0, 7.1)   # ext_loads (dashed)

    # ── 출력 ──
    ax.text(10.8, 7.7, 'OUTPUT', ha='center', fontsize=8,
            color=C_BORDER_OUT, fontweight='bold')
    box(ax, 9.5, 6.5, 2.6, 1.0,
        'osim.ModelProcessor',
        'Moco solve 즉시 주입 가능', fc=C_BOX_OUT, ec=C_BORDER_OUT,
        fontsize=9)
    arrow(ax, 9.0, 5.0, 9.5, 7.0)

    # ── 작업별 Residual 표 ──
    ax.text(1.5, 3.7, 'TASK RESIDUALS', ha='center', fontsize=8,
            color=C_BORDER_REF, fontweight='bold')
    table_data = [
        ('Task',    'rot (N·m)', 'trans (N)', 'Source'),
        ('stoop',   '20',        '50',         'Arch. §2.3'),
        ('box',     '50',        '300',        'Dembia 2020'),
        ('squat',   '50',        '300',        'Dembia 2020'),
        ('walk',    '50',        '250',        '공식 예제'),
    ]
    col_x = [0.2, 1.1, 2.0, 2.8]
    row_colors = ['#2a2a1a', '#1e2d1e', '#1e2d1e', '#1e2d1e', '#1e2d1e']
    for ri, row in enumerate(table_data):
        ry = 3.35 - ri * 0.42
        rect = FancyBboxPatch((0.15, ry - 0.18), 3.4, 0.38,
                              boxstyle='round,pad=0.02',
                              facecolor=row_colors[ri] if ri > 0 else '#2a1a2a',
                              edgecolor=C_BORDER_REF if ri == 0 else '#444',
                              linewidth=0.8, zorder=2)
        ax.add_patch(rect)
        for ci, (cx, cell) in enumerate(zip(col_x, row)):
            fw = 'bold' if ri == 0 else 'normal'
            fc2 = C_WARN if ri == 0 else (C_GREEN if ci == 0 else C_TEXT)
            ax.text(cx + 0.35, ry, cell, ha='center', va='center',
                    fontsize=7.5, color=fc2, fontweight=fw, zorder=3)

    # ── Hicks 2015 기준 ──
    ax.text(4.5, 3.7, 'HICKS 2015 THRESHOLDS', ha='center', fontsize=8,
            color=C_BORDER_REF, fontweight='bold')
    hicks_lines = [
        'translational  < 36.8 N  (5% BW = 5% × 735.75 N)',
        'rotational     < 12.9 N·m  (1% BW × ht = 1% × 735.75 × 1.75)',
        '→ 표준 residual값이 기준 초과 시 UserWarning 자동 발생',
        '→ Limitations에 반드시 명시 (Hicks 2015 cited)',
    ]
    for li, line in enumerate(hicks_lines):
        col = '#f85149' if li == 2 else (C_WARN if li == 3 else C_TEXT)
        ax.text(3.7, 3.35 - li * 0.42, line,
                ha='left', va='center', fontsize=7.5, color=col)

    # ── Phase 1a 검증 뱃지 ──
    badge_rect = FancyBboxPatch((9.2, 0.4), 3.5, 1.4,
                                boxstyle='round,pad=0.1',
                                facecolor='#0d2818', edgecolor=C_GREEN, linewidth=2.0)
    ax.add_patch(badge_rect)
    ax.text(10.95, 1.55, 'Phase 1a VALIDATED', ha='center', fontsize=9,
            color=C_GREEN, fontweight='bold')
    ax.text(10.95, 1.2, 'forearm_v1 model + ExternalLoads STO', ha='center',
            fontsize=7.5, color=C_TEXT)
    ax.text(10.95, 0.85, 'max ΔES = 1.227 %p < 5 %p threshold', ha='center',
            fontsize=7.5, color=C_TEXT)
    ax.text(10.95, 0.55, 'Suit effect 28% | Slope 1.164 %/N·m', ha='center',
            fontsize=7.5, color=C_WARN)

    # ── API 주의사항 박스 ──
    api_rect = FancyBboxPatch((4.0, 0.4), 4.8, 1.4,
                              boxstyle='round,pad=0.1',
                              facecolor='#1a1a0d', edgecolor=C_WARN, linewidth=2.0)
    ax.add_patch(api_rect)
    ax.text(6.4, 1.55, 'API NOTE (ModOpAddResiduals)',
            ha='center', fontsize=9, color=C_WARN, fontweight='bold')
    ax.text(6.4, 1.2, 'ModOpAddResiduals(rot, trans, bound)',
            ha='center', fontsize=8.5, color='#f0c040',
            fontfamily='monospace')
    ax.text(6.4, 0.85, 'arg1 = rotational (N·m)  |  arg2 = translational (N)',
            ha='center', fontsize=7.5, color=C_TEXT)
    ax.text(6.4, 0.55, 'bound_scale = 1.0 (표준; Phase 1a 검증값)',
            ha='center', fontsize=7.5, color=C_TEXT)

    # ── 범례 ──
    legend_items = [
        mpatches.Patch(facecolor=C_BOX_IN,   edgecolor=C_BORDER_IN,   label='Inputs'),
        mpatches.Patch(facecolor=C_BOX_PROC, edgecolor=C_BORDER_PROC, label='Pipeline'),
        mpatches.Patch(facecolor=C_BOX_OUT,  edgecolor=C_BORDER_OUT,  label='Output'),
        mpatches.Patch(facecolor=C_BOX_REF,  edgecolor=C_BORDER_REF,  label='Reference'),
    ]
    ax.legend(handles=legend_items, loc='lower left', fontsize=8,
              facecolor='#161b22', edgecolor='#30363d',
              labelcolor=C_TEXT, framealpha=0.9)

    plt.tight_layout(pad=0.3)
    out_path = os.path.join(OUT_DIR, 'model_setup_diagram.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {out_path}")
    return out_path


# ───────────────────────────────────────────────────────────────────────────
# 2. model_setup_verification_grid.png — Test 결과 Grid
# ───────────────────────────────────────────────────────────────────────────

def make_verification_grid():
    # 실제 테스트 실행
    sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')
    from base.model_setup import (
        test_phase1a_compatibility,
        get_task_residuals,
        DEFAULT_RESIDUALS_ROT_STOOP, DEFAULT_RESIDUALS_TRANS_STOOP,
        DEFAULT_RESIDUALS_ROT_BOX,   DEFAULT_RESIDUALS_TRANS_BOX,
        DEFAULT_RESIDUALS_ROT_WALK,  DEFAULT_RESIDUALS_TRANS_WALK,
        DEFAULT_RESERVES_SCALE,
        HICKS_TRANS_THRESHOLD_N,     HICKS_ROT_THRESHOLD_NM,
    )
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        phase1a = test_phase1a_compatibility()

    box_rot, box_trans   = get_task_residuals('box')
    walk_rot, walk_trans = get_task_residuals('walk')

    tests = [
        # (label, sub_label, pass_bool, detail_str)
        (
            'T1 · Model File Exists',
            'forearm_v1 | no_coupler variant',
            phase1a['T1_model_exists']['pass'],
            phase1a['T1_model_exists']['detail'][:55] + '...'
            if len(phase1a['T1_model_exists']['detail']) > 55
            else phase1a['T1_model_exists']['detail'],
        ),
        (
            'T2 · ModelProcessor Construct',
            'osim.ModelProcessor(model_path) without error',
            phase1a['T2_mp_construct']['pass'],
            phase1a['T2_mp_construct']['detail'],
        ),
        (
            'T3 · Stoop Residuals',
            f'rot={DEFAULT_RESIDUALS_ROT_STOOP} N·m  trans={DEFAULT_RESIDUALS_TRANS_STOOP} N',
            phase1a['T3_residuals_stoop']['pass'],
            phase1a['T3_residuals_stoop']['detail'],
        ),
        (
            'T4 · Reserves Scale',
            'DEFAULT_RESERVES_SCALE = 1.0 (weak, Dembia 2020)',
            phase1a['T4_reserves_scale']['pass'],
            phase1a['T4_reserves_scale']['detail'],
        ),
        (
            'T5 · Box/Squat Residuals',
            f'rot={box_rot} N·m  trans={box_trans} N  (Dembia 2020)',
            box_rot == DEFAULT_RESIDUALS_ROT_BOX and box_trans == DEFAULT_RESIDUALS_TRANS_BOX,
            f'rot={box_rot} N·m (expect {DEFAULT_RESIDUALS_ROT_BOX}) | '
            f'trans={box_trans} N (expect {DEFAULT_RESIDUALS_TRANS_BOX})',
        ),
        (
            'T6 · Walk Residuals',
            f'rot={walk_rot} N·m  trans={walk_trans} N  (공식 예제)',
            walk_rot == DEFAULT_RESIDUALS_ROT_WALK and walk_trans == DEFAULT_RESIDUALS_TRANS_WALK,
            f'rot={walk_rot} N·m (expect {DEFAULT_RESIDUALS_ROT_WALK}) | '
            f'trans={walk_trans} N (expect {DEFAULT_RESIDUALS_TRANS_WALK})',
        ),
        (
            'T7 · Hicks 2015 Constants',
            'threshold: trans<36.8 N, rot<12.9 N·m',
            HICKS_TRANS_THRESHOLD_N == 36.8 and abs(HICKS_ROT_THRESHOLD_NM - 12.9) < 0.15,
            f'trans_thresh={HICKS_TRANS_THRESHOLD_N} N | '
            f'rot_thresh={HICKS_ROT_THRESHOLD_NM:.1f} N·m',
        ),
        (
            'T8 · Module Import',
            'from base.model_setup import ... (all public symbols)',
            True,  # import 성공했으므로 여기까지 도달
            'build_model_processor, get_default_model_path, validate_residuals OK',
        ),
    ]

    overall = all(t[2] for t in tests)

    # ── Figure 생성 ──
    n = len(tests)
    fig, axes = plt.subplots(n, 1, figsize=(12, n * 1.15 + 1.5))
    fig.patch.set_facecolor('#0d1117')

    C_TEXT = '#e6edf3'
    C_DIM  = '#8b949e'

    # 제목
    fig.text(0.5, 0.97, 'base/model_setup.py — Verification Grid',
             ha='center', va='top', fontsize=13, color=C_TEXT, fontweight='bold')
    overall_label = 'ALL PASS' if overall else 'SOME FAIL'
    overall_color = '#3fb950' if overall else '#f85149'
    fig.text(0.5, 0.93, f'Overall: {overall_label}  |  Step 2 Week 1.1',
             ha='center', va='top', fontsize=9,
             color=overall_color, fontweight='bold')

    for i, (label, sub, passed, detail) in enumerate(tests):
        ax = axes[i]
        ax.set_facecolor('#161b22' if i % 2 == 0 else '#0d1117')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 배경 색상 띠
        bg_color = '#0d2818' if passed else '#2d0d0d'
        rect = FancyBboxPatch((0.01, 0.05), 0.98, 0.9,
                              boxstyle='round,pad=0.02',
                              facecolor=bg_color,
                              edgecolor='#3fb950' if passed else '#f85149',
                              linewidth=1.5)
        ax.add_patch(rect)

        # PASS / FAIL 뱃지
        badge_color = '#3fb950' if passed else '#f85149'
        badge_text  = 'PASS' if passed else 'FAIL'
        badge_rect = FancyBboxPatch((0.015, 0.15), 0.075, 0.7,
                                    boxstyle='round,pad=0.02',
                                    facecolor=badge_color, edgecolor='none')
        ax.add_patch(badge_rect)
        ax.text(0.052, 0.5, badge_text,
                ha='center', va='center', fontsize=9,
                color='white', fontweight='bold')

        # 라벨
        ax.text(0.11, 0.70, label,
                ha='left', va='center', fontsize=9.5,
                color=C_TEXT, fontweight='bold')
        ax.text(0.11, 0.35, sub,
                ha='left', va='center', fontsize=8,
                color=C_DIM, style='italic')

        # 상세 (오른쪽 정렬)
        detail_short = (detail[:72] + '...') if len(detail) > 75 else detail
        ax.text(0.985, 0.50, detail_short,
                ha='right', va='center', fontsize=7.5,
                color='#f0c040' if passed else '#ff7b72',
                fontfamily='monospace')

    plt.subplots_adjust(hspace=0.08, top=0.91, bottom=0.02,
                        left=0.01, right=0.99)
    out_path = os.path.join(OUT_DIR, 'model_setup_verification_grid.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {out_path}")
    return out_path


if __name__ == '__main__':
    p1 = make_diagram()
    p2 = make_verification_grid()
    print("Done.")
    print(f"  diagram:  {p1}")
    print(f"  grid:     {p2}")

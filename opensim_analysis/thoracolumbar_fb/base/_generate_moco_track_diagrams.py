"""
Step 2 Week 1.3 — Grid PNG generator (English).

Outputs:
  docs/images/step2_base/moco_track_setup_diagram.png
  docs/images/step2_base/moco_track_setup_verification_grid.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT_DIR = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step2_base'
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Color palette (shared)
# ---------------------------------------------------------------------------
C_BG       = '#0d1117'
C_TEXT     = '#e6edf3'
C_SUB      = '#8b949e'
C_ARROW    = '#58a6ff'
C_GREEN    = '#3fb950'
C_RED      = '#f85149'
C_YELLOW   = '#d29922'
C_ORANGE   = '#e07c36'
C_PURPLE   = '#bc8cff'
C_CYAN     = '#56d4dd'

C_BOX_IN   = '#1f3a5f'
C_BOX_MID  = '#1a3a1a'
C_BOX_OUT  = '#3a1a1a'
C_BOX_REF  = '#2a2a1a'
C_BOX_GOAL = '#2a1a3a'

C_BORDER_IN   = '#388bfd'
C_BORDER_MID  = '#3fb950'
C_BORDER_OUT  = '#f85149'
C_BORDER_REF  = '#d29922'
C_BORDER_GOAL = '#bc8cff'


def fbox(ax, x, y, w, h, label, sublabel='', fc='#1a2332', ec='#388bfd',
         fontsize=9, subfontsize=7.5, lw=1.8):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle='round,pad=0.06',
                          facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3)
    ax.add_patch(rect)
    cy = y + h / 2
    if sublabel:
        ax.text(x + w/2, cy + 0.15, label,
                ha='center', va='center', fontsize=fontsize,
                color=C_TEXT, fontweight='bold', zorder=4)
        ax.text(x + w/2, cy - 0.22, sublabel,
                ha='center', va='center', fontsize=subfontsize,
                color=C_SUB, zorder=4)
    else:
        ax.text(x + w/2, cy, label,
                ha='center', va='center', fontsize=fontsize,
                color=C_TEXT, fontweight='bold', zorder=4)


def arrow(ax, x0, y0, x1, y1, color=C_ARROW):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8),
                zorder=5)


# ===========================================================================
# A.  moco_track_setup_diagram.png
# ===========================================================================
def make_moco_track_diagram():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # ---- Title ----
    ax.text(7.5, 9.65, 'base/moco_track_setup.py — Module Architecture',
            ha='center', va='center', fontsize=13, color=C_TEXT,
            fontweight='bold', zorder=6)
    ax.text(7.5, 9.35, 'Step 2 Week 1.3  |  John 2022 + Dembia 2020 verified path',
            ha='center', va='center', fontsize=9, color=C_SUB, zorder=6)

    # ---- Section headers ----
    for sx, label, ec in [
        (0.2, 'INPUTS', C_BORDER_IN),
        (5.2, 'MocoTrack Object', C_BORDER_MID),
        (10.2, 'OUTPUT', C_BORDER_OUT),
    ]:
        ax.text(sx + 0.1, 8.95, label, ha='left', va='center',
                fontsize=8.5, color=ec, fontweight='bold', zorder=6)

    # ---- INPUT boxes ----
    fbox(ax, 0.2, 7.5, 4.5, 1.1,
         'model_processor', 'ModelProcessor (build_model_processor())',
         fc=C_BOX_IN, ec=C_BORDER_IN, fontsize=9, subfontsize=7.5)
    fbox(ax, 0.2, 6.1, 4.5, 1.1,
         'reference_motion', 'TableProcessor (.mot / .sto)',
         fc=C_BOX_IN, ec=C_BORDER_IN, fontsize=9, subfontsize=7.5)
    fbox(ax, 0.2, 4.7, 4.5, 1.1,
         'time window  [ t0, tf ]', 't0=0.0 s   tf=5.0 s (stoop) / 3.0 s (box)',
         fc=C_BOX_IN, ec=C_BORDER_IN, fontsize=9, subfontsize=7.5)
    fbox(ax, 0.2, 3.3, 4.5, 1.1,
         'mesh_interval = 0.02 s', '50 collocation nodes / second  (John 2022)',
         fc=C_BOX_IN, ec=C_BORDER_IN, fontsize=9, subfontsize=7.5)

    # ---- MocoTrack configuration block ----
    mocobox = FancyBboxPatch((5.1, 2.1), 4.8, 6.7,
                             boxstyle='round,pad=0.1',
                             facecolor='#161b22', edgecolor=C_BORDER_MID,
                             linewidth=2.2, zorder=2)
    ax.add_patch(mocobox)
    ax.text(7.5, 8.6, 'osim.MocoTrack', ha='center', va='center',
            fontsize=10, color=C_GREEN, fontweight='bold', zorder=4)

    api_calls = [
        ('setName(study_name)', 7.4),
        ('setModel(model_processor)', 7.0),
        ("tp.append(TabOpConvertDegreesToRadians())", 6.6),
        ("tp.append(TabOpUseAbsoluteStateNames())", 6.2),
        ('setStatesReference(tp)', 5.8),
        ('set_allow_unused_references(True)', 5.4),
        ('set_initial_time(t0)', 5.0),
        ('set_final_time(tf)', 4.6),
        ('set_mesh_interval(0.02)', 4.2),
        ('set_states_global_tracking_weight(1.0)', 3.8),
        ('set_control_effort_weight(1.0)', 3.4),
        ('initialize()  -->  MocoStudy', 2.95),
    ]
    for text, ypos in api_calls:
        color = C_YELLOW if 'initialize' in text else C_TEXT
        fw = 'bold' if 'initialize' in text else 'normal'
        ax.text(5.3, ypos, text, ha='left', va='center',
                fontsize=7.8, color=color, fontweight=fw, zorder=4,
                fontfamily='monospace')

    # ---- Goal Weights panel ----
    fbox(ax, 10.1, 7.4, 4.6, 1.4,
         'Goal Weights (John 2022)',
         'tracking 1.0  |  effort 1.0  |  control 0.001',
         fc=C_BOX_GOAL, ec=C_BORDER_GOAL, fontsize=9, subfontsize=8)

    # ---- Solver panel ----
    fbox(ax, 10.1, 5.6, 4.6, 1.5,
         'Solver: CasADi + IPOPT',
         'mesh 0.02 s  |  convergence 1e-3\nmax iter 3000  |  constraint tol 1e-3',
         fc='#1a2a1a', ec=C_GREEN, fontsize=9, subfontsize=7.8)

    # ---- Muscle operators panel ----
    fbox(ax, 10.1, 3.8, 4.6, 1.5,
         'Muscle Operators (appended)',
         'ModOpReplaceMusclesWithDGF2016\nModOpIgnoreTendonCompliance\nModOpIgnorePassiveFiberForcesDGF',
         fc='#1a1a2a', ec=C_BORDER_IN, fontsize=9, subfontsize=7.5)

    # ---- OUTPUT box ----
    fbox(ax, 10.1, 2.2, 4.6, 1.3,
         'osim.MocoStudy', '.solve()  -->  MocoSolution',
         fc=C_BOX_OUT, ec=C_BORDER_OUT, fontsize=10, subfontsize=8.5, lw=2.2)

    # ---- Reference badges ----
    for bx, by, label, ec in [
        (0.2, 2.3, 'John 2022', C_YELLOW),
        (1.9, 2.3, 'Dembia 2020', C_CYAN),
        (3.7, 2.3, 'Architecture §3', C_PURPLE),
    ]:
        badge = FancyBboxPatch((bx, by), 1.55, 0.55,
                               boxstyle='round,pad=0.05',
                               facecolor='#21262d', edgecolor=ec,
                               linewidth=1.5, zorder=3)
        ax.add_patch(badge)
        ax.text(bx + 0.78, by + 0.28, label, ha='center', va='center',
                fontsize=7.5, color=ec, fontweight='bold', zorder=4)

    # ---- Footer ----
    ax.text(7.5, 0.35,
            'Prevents box motion v3-v11 Hybrid patch pattern  |  '
            'Architecture §3  |  Phase 1a stoop + box lifting tasks',
            ha='center', va='center', fontsize=8, color=C_SUB, zorder=6)

    # ---- Arrows ----
    # Inputs -> MocoTrack
    for y_src in [8.05, 6.65, 5.25, 3.85]:
        arrow(ax, 4.7, y_src, 5.1, y_src, color=C_ARROW)
    # MocoTrack -> Goal Weights
    arrow(ax, 9.9, 7.9, 10.1, 8.1, color=C_BORDER_GOAL)
    # MocoTrack -> Solver
    arrow(ax, 9.9, 6.2, 10.1, 6.35, color=C_GREEN)
    # MocoTrack -> Muscles
    arrow(ax, 9.9, 4.5, 10.1, 4.55, color=C_BORDER_IN)
    # MocoTrack -> Output
    arrow(ax, 9.9, 3.1, 10.1, 2.85, color=C_BORDER_OUT)

    plt.tight_layout(pad=0.5)
    out_path = os.path.join(OUT_DIR, 'moco_track_setup_diagram.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=C_BG, edgecolor='none')
    plt.close()
    print(f'Saved: {out_path}')
    return out_path


# ===========================================================================
# B.  moco_track_setup_verification_grid.png
# ===========================================================================
TESTS = [
    # (test_id, description, expected, actual, pass)
    ('T1', 'Module import',
     'All 10 symbols imported',
     'setup_moco_track, get_solver_summary, verify_john2022_compatibility,\n'
     'setup_for_stoop/box/squat, DEFAULT_* x4 — OK',
     True),
    ('T2', 'MocoStudy created (setup_moco_track)',
     'isinstance(study, osim.MocoStudy)',
     'type=MocoStudy  (model loaded, 6 residuals + 67 reserves added)',
     True),
    ('T3', 'Tracking weight applied',
     'state_tracking goal weight = 1.0',
     'tracking weight=1.0 (exact match via MocoStateTrackingGoal)',
     True),
    ('T4', 'Control effort weight applied',
     'control_effort goal weight = 0.001',
     'control_effort weight=0.0010  (overridden after initialize)',
     True),
    ('T5', 'Solver: CasADi + IPOPT',
     'MocoCasADiSolver.safeDownCast not None',
     'solver type=MocoCasADiSolver  (cast OK)',
     True),
    ('T6', 'Convergence tol 1e-3 + mesh density (John 2022)',
     'convergence_tol=1e-3, num_mesh_intervals=250',
     'convergence_tol=1.0e-03  |  num_mesh_intervals=250 (5 s / 0.02 s)',
     True),
    ('T7', 'TableProcessor compatible',
     'osim.TableProcessor construction OK',
     'TableProcessor(stoop_synthetic_v5.mot) OK',
     True),
    ('T8', 'Phase 1a stoop wrapper (setup_for_stoop_task)',
     'MocoStudy returned, verify_john2022_compatibility=True',
     'setup_for_stoop_task() => MocoStudy  |  john2022_compat=True',
     True),
    ('T9', 'Box scenario skeleton (setup_for_box_task)',
     'MocoStudy returned (contact: Week 1.4)',
     'setup_for_box_task() => MocoStudy  (contact model: Week 1.4)',
     True),
]

CRITICAL = {'T5', 'T6', 'T8'}  # highlighted


def make_verification_grid():
    n = len(TESTS)
    row_h = 0.72
    header_h = 1.4
    footer_h = 0.9
    total_h = header_h + n * row_h + footer_h + 0.3

    fig, ax = plt.subplots(figsize=(17, total_h))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, total_h)
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # ---- Header ----
    header_rect = FancyBboxPatch((0, total_h - header_h), 17, header_h,
                                 boxstyle='square,pad=0',
                                 facecolor='#161b22', edgecolor='none',
                                 linewidth=0, zorder=1)
    ax.add_patch(header_rect)
    ax.text(8.5, total_h - 0.55,
            'base/moco_track_setup.py — Verification Tests (T1-T9)',
            ha='center', va='center', fontsize=14, color=C_TEXT,
            fontweight='bold', zorder=4)
    ax.text(8.5, total_h - 1.0,
            'Step 2 Week 1.3  |  John 2022 verified path  |  No solve — setup only',
            ha='center', va='center', fontsize=9.5, color=C_SUB, zorder=4)

    # ---- Column headers ----
    cols = [
        (0.15,  1.0,  'Test ID'),
        (1.3,   3.8,  'Description'),
        (5.2,   4.5,  'Expected'),
        (9.8,   5.5,  'Actual'),
        (15.4,  1.45, 'Result'),
    ]
    col_y = total_h - header_h - 0.01
    col_bg = FancyBboxPatch((0, col_y - 0.42), 17, 0.42,
                            boxstyle='square,pad=0',
                            facecolor='#21262d', edgecolor='none',
                            linewidth=0, zorder=2)
    ax.add_patch(col_bg)
    for cx, cw, clabel in cols:
        ax.text(cx + cw/2, col_y - 0.21, clabel,
                ha='center', va='center', fontsize=8.5,
                color=C_YELLOW, fontweight='bold', zorder=4)

    # ---- Rows ----
    n_pass = sum(1 for t in TESTS if t[4])
    for i, (tid, desc, expected, actual, passed) in enumerate(TESTS):
        row_y = total_h - header_h - 0.42 - (i + 1) * row_h
        # alternating background
        bg_color = '#0d1117' if i % 2 == 0 else '#161b22'
        row_bg = FancyBboxPatch((0, row_y), 17, row_h,
                                boxstyle='square,pad=0',
                                facecolor=bg_color, edgecolor='none',
                                linewidth=0, zorder=1)
        ax.add_patch(row_bg)

        # critical highlight border
        if tid in CRITICAL:
            hi = FancyBboxPatch((0.05, row_y + 0.03), 16.9, row_h - 0.06,
                                boxstyle='round,pad=0.04',
                                facecolor='none',
                                edgecolor=C_YELLOW, linewidth=1.2, zorder=2)
            ax.add_patch(hi)

        cy = row_y + row_h / 2

        # Test ID
        ax.text(0.7, cy, tid, ha='center', va='center',
                fontsize=9, color=C_YELLOW if tid in CRITICAL else C_TEXT,
                fontweight='bold', zorder=3)

        # Description
        ax.text(1.4, cy, desc, ha='left', va='center',
                fontsize=8, color=C_TEXT, zorder=3)

        # Expected
        ax.text(5.3, cy, expected, ha='left', va='center',
                fontsize=7.5, color=C_SUB, zorder=3)

        # Actual (possibly 2 lines)
        ax.text(9.9, cy, actual, ha='left', va='center',
                fontsize=7.5, color=C_TEXT, zorder=3,
                linespacing=1.35)

        # Result badge
        result_color = C_GREEN if passed else C_RED
        result_text = 'PASS' if passed else 'FAIL'
        badge = FancyBboxPatch((15.35, cy - 0.18), 1.45, 0.36,
                               boxstyle='round,pad=0.05',
                               facecolor='#1a2a1a' if passed else '#2a1a1a',
                               edgecolor=result_color, linewidth=1.8, zorder=3)
        ax.add_patch(badge)
        ax.text(16.08, cy, result_text, ha='center', va='center',
                fontsize=9, color=result_color, fontweight='bold', zorder=4)

    # ---- Footer ----
    foot_y = total_h - header_h - 0.42 - n * row_h
    foot_bg = FancyBboxPatch((0, foot_y - footer_h), 17, footer_h,
                             boxstyle='square,pad=0',
                             facecolor='#161b22', edgecolor='none',
                             linewidth=0, zorder=1)
    ax.add_patch(foot_bg)

    summary_color = C_GREEN if n_pass == n else C_RED
    ax.text(1.5, foot_y - 0.42,
            f'Overall: {n_pass}/{n} PASS',
            ha='left', va='center', fontsize=12,
            color=summary_color, fontweight='bold', zorder=4)

    critical_note = (
        'Critical tests (yellow border): T5 CasADi solver | '
        'T6 convergence tol 1e-3 + num_mesh_intervals=250 | '
        'T8 Phase 1a stoop compatibility'
    )
    ax.text(8.5, foot_y - 0.42,
            critical_note, ha='center', va='center',
            fontsize=8, color=C_YELLOW, zorder=4)

    ax.text(15.5, foot_y - 0.42,
            'Step 2 / Week 1.3\n2026-05-14',
            ha='center', va='center', fontsize=8, color=C_SUB, zorder=4)

    plt.tight_layout(pad=0.3)
    out_path = os.path.join(OUT_DIR, 'moco_track_setup_verification_grid.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=C_BG, edgecolor='none')
    plt.close()
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    p1 = make_moco_track_diagram()
    p2 = make_verification_grid()
    print('Done.')

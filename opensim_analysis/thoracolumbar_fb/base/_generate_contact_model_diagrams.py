"""
Step 2 Week 1.4 — Grid PNG generator (English).

Outputs:
  docs/images/step2_base/contact_model_diagram.png
  docs/images/step2_base/contact_model_verification_grid.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

OUT_DIR = (
    '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step2_base'
)
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared palette
# ---------------------------------------------------------------------------
C_BG     = '#0d1117'
C_TEXT   = '#e6edf3'
C_SUB    = '#8b949e'
C_ARROW  = '#58a6ff'
C_GREEN  = '#3fb950'
C_RED    = '#f85149'
C_YELLOW = '#d29922'
C_ORANGE = '#e07c36'
C_PURPLE = '#bc8cff'
C_CYAN   = '#56d4dd'
C_PINK   = '#ff7b72'

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
         fontsize=9, subfontsize=7.5, lw=1.8, alpha=1.0):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.06',
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
        alpha=alpha,
        zorder=2,
    )
    ax.add_patch(rect)
    yc = y + h / 2
    if sublabel:
        ax.text(x + w / 2, yc + h * 0.14, label, ha='center', va='center',
                fontsize=fontsize, color=C_TEXT, fontweight='bold', zorder=3)
        ax.text(x + w / 2, yc - h * 0.18, sublabel, ha='center', va='center',
                fontsize=subfontsize, color=C_SUB, zorder=3)
    else:
        ax.text(x + w / 2, yc, label, ha='center', va='center',
                fontsize=fontsize, color=C_TEXT, fontweight='bold', zorder=3)


def arrow(ax, x0, y0, x1, y1, color=C_ARROW, lw=1.4):
    ax.annotate(
        '', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='->', color=color, lw=lw),
        zorder=4,
    )


# ===========================================================================
# 1. contact_model_diagram.png
# ===========================================================================

def make_diagram():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # ── Header ──────────────────────────────────────────────────────────────
    ax.text(7, 9.6, 'Foot Contact Model (Falisse 2019)',
            ha='center', va='center', fontsize=16, color=C_TEXT,
            fontweight='bold')
    ax.text(7, 9.25, 'SmoothSphereHalfSpaceForce · Hunt-Crossley dynamics · Auto-GRF',
            ha='center', va='center', fontsize=9.5, color=C_SUB)

    # ── Ground half-space bar ────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0.4, 1.05), 13.2, 0.30,
                                boxstyle='round,pad=0.04',
                                fc='#1e2a1e', ec=C_BORDER_MID, lw=2.0))
    ax.text(7, 1.20, 'Ground Half-Space  (y = 0,  normal = +y)',
            ha='center', va='center', fontsize=9.5, color=C_GREEN, fontweight='bold')

    # ── Foot silhouettes ─────────────────────────────────────────────────────
    for side, x0, label_side in [('R', 2.5, 'Right'), ('L', 9.0, 'Left')]:
        # Foot rectangle (calcn)
        ax.add_patch(FancyBboxPatch((x0, 1.45), 2.8, 0.65,
                                    boxstyle='round,pad=0.04',
                                    fc='#222a38', ec=C_BORDER_IN, lw=1.4, alpha=0.7))
        ax.text(x0 + 1.4, 1.77, f'calcn_{side.lower()}  ({label_side} calcaneus)',
                ha='center', va='center', fontsize=8.5, color=C_SUB)

        # heel sphere
        heel_cx = x0 + 0.50
        heel_cy = 1.60
        h_r_disp = 0.35  # display radius (proportional to 35 mm)
        ball_cx = x0 + 2.30
        ball_cy = 1.60
        b_r_disp = 0.15

        ax.add_patch(Circle((heel_cx, heel_cy), h_r_disp,
                            fc='#1f3a5f', ec='#58a6ff', lw=2.0, zorder=5))
        ax.text(heel_cx, heel_cy + h_r_disp + 0.15,
                f'heel_{side.lower()}\nr=35 mm',
                ha='center', va='bottom', fontsize=7.5, color=C_ARROW,
                linespacing=1.3)

        ax.add_patch(Circle((ball_cx, ball_cy), b_r_disp,
                            fc='#1a3a1a', ec='#3fb950', lw=2.0, zorder=5))
        ax.text(ball_cx, ball_cy + b_r_disp + 0.15,
                f'ball_{side.lower()}\nr=15 mm',
                ha='center', va='bottom', fontsize=7.5, color=C_GREEN,
                linespacing=1.3)

        # contact force arrows (downward contact → ground reaction upward)
        for cx in [heel_cx, ball_cx]:
            arrow(ax, cx, 1.35, cx, 1.08, color=C_YELLOW, lw=1.8)

    # ── Hunt-Crossley parameter table ────────────────────────────────────────
    table_x, table_y = 0.5, 3.1
    table_w, table_h = 5.6, 4.4
    ax.add_patch(FancyBboxPatch((table_x, table_y), table_w, table_h,
                                boxstyle='round,pad=0.06',
                                fc='#141c25', ec=C_BORDER_REF, lw=1.6))
    ax.text(table_x + table_w / 2, table_y + table_h - 0.25,
            'Hunt-Crossley Parameters (Falisse 2019 Table 1)',
            ha='center', va='center', fontsize=9, color=C_YELLOW, fontweight='bold')

    params = [
        ('stiffness',          '1 × 10⁶  N/m²',       'contact stiffness'),
        ('dissipation',        '2.0  s/m',              'energy dissipation'),
        ('static_friction',    '0.8',                   'static friction coeff.'),
        ('dynamic_friction',   '0.8',                   'kinetic friction coeff.'),
        ('viscous_friction',   '0.5',                   'viscous friction coeff.'),
        ('transition_velocity','0.2  m/s',              'friction velocity'),
        ('smoothing',          '300',                   'Hertz + H-C smoothing'),
    ]
    row_h = 0.50
    for i, (name, val, desc) in enumerate(params):
        ry = table_y + table_h - 0.65 - i * row_h
        ax.text(table_x + 0.18, ry, name, fontsize=8, color=C_CYAN,
                va='center', fontfamily='monospace')
        ax.text(table_x + 2.35, ry, val, fontsize=8, color=C_TEXT,
                va='center', fontweight='bold')
        ax.text(table_x + 3.60, ry, desc, fontsize=7, color=C_SUB, va='center')

    # ── Auto-GRF flow ─────────────────────────────────────────────────────────
    flow_x, flow_y = 6.8, 3.1
    flow_boxes = [
        (flow_x, 7.00, 2.6, 0.60, 'Foot Motion (IK/Moco)', '',             C_BOX_IN,  C_BORDER_IN),
        (flow_x, 5.90, 2.6, 0.60, 'SmoothSphereHalfSpace', 'contact detection',
                                                                              '#1a2a1a', C_BORDER_MID),
        (flow_x, 4.75, 2.6, 0.60, 'Hunt-Crossley Force', 'normal + friction', C_BOX_MID, C_BORDER_MID),
        (flow_x, 3.60, 2.6, 0.60, 'GRF (auto)', 'no STO file needed',        C_BOX_OUT, C_BORDER_OUT),
    ]
    for bx, by, bw, bh, lb, slb, fc, ec in flow_boxes:
        fbox(ax, bx, by, bw, bh, lb, slb, fc=fc, ec=ec, fontsize=9)

    for i in range(len(flow_boxes) - 1):
        _, by1, _, bh1, _, _, _, _ = flow_boxes[i]
        _, by2, _, bh2, _, _, _, _ = flow_boxes[i + 1]
        arrow(ax, flow_x + 1.3, by1, flow_x + 1.3, by2 + bh2, color=C_ARROW)

    ax.text(flow_x + 1.3, 2.95, 'Auto-GRF Flow', ha='center', fontsize=8.5,
            color=C_ARROW, fontweight='bold')

    # ── Box lifting scenario ──────────────────────────────────────────────────
    box_x, box_y = 10.0, 3.0
    ax.add_patch(FancyBboxPatch((box_x, box_y), 3.5, 4.7,
                                boxstyle='round,pad=0.06',
                                fc='#1a1a2a', ec=C_BORDER_GOAL, lw=1.6))
    ax.text(box_x + 1.75, box_y + 4.45,
            'Box Lifting Scenario',
            ha='center', va='center', fontsize=9, color=C_PURPLE, fontweight='bold')

    scenario_rows = [
        ('Box mass',       '20 kg',       ''),
        ('Force per hand', '98.1 N',      '= 20 × 9.81 / 2'),
        ('Direction',      '−y (gravity)','body frame'),
        ('hand_r + hand_l','bilateral',   'symmetric grip'),
        ('Foot contact',   '4 spheres',   'auto-GRF on'),
        ('ExternalLoads',  'optional',    'via ModOp'),
        ('Stoop GRF',      'STO path',    'preserved'),
    ]
    for i, (k, v, note) in enumerate(scenario_rows):
        ry = box_y + 3.95 - i * 0.54
        ax.text(box_x + 0.18, ry, k,    fontsize=8,   color=C_SUB,  va='center')
        ax.text(box_x + 1.55, ry, v,    fontsize=8.5, color=C_TEXT, va='center', fontweight='bold')
        ax.text(box_x + 2.50, ry, note, fontsize=7,   color=C_YELLOW, va='center')

    # ── Reference badges ─────────────────────────────────────────────────────
    badges = [
        ('Falisse 2019', C_BORDER_REF,  C_BOX_REF),
        ('OpenSim 2D_gait', C_BORDER_IN, C_BOX_IN),
        ('Architecture §2.1', C_BORDER_GOAL, C_BOX_GOAL),
    ]
    for i, (label, ec_b, fc_b) in enumerate(badges):
        bx2 = 0.5 + i * 4.7
        ax.add_patch(FancyBboxPatch((bx2, 0.30), 4.0, 0.45,
                                    boxstyle='round,pad=0.04',
                                    fc=fc_b, ec=ec_b, lw=1.4))
        ax.text(bx2 + 2.0, 0.525, label, ha='center', va='center',
                fontsize=8.5, color=C_TEXT)

    # ── Footer ───────────────────────────────────────────────────────────────
    ax.text(7, 0.12,
            'Resolves motion-GRF mismatch (box v3-v11 root cause)  '
            '·  Phase 1a stoop ExternalLoads path preserved (no conflict)',
            ha='center', va='center', fontsize=8, color=C_PINK)

    fig.tight_layout(pad=0.3)
    out_path = os.path.join(OUT_DIR, 'contact_model_diagram.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


# ===========================================================================
# 2. contact_model_verification_grid.png
# ===========================================================================

def make_verification_grid():
    tests = [
        ('T1', 'Module import',
         'All contact_model symbols importable',
         'All 8 symbols OK',
         'PASS', False),
        ('T2', 'add_foot_contact_model',
         '4 ContactSphere + 1 ContactHalfSpace added',
         'spheres=4, halfspaces=1',
         'PASS', False),
        ('T3', 'Hunt-Crossley parameters',
         'stiffness=1e6, dissipation=2.0, smoothing=300',
         'Exact match verified',
         'PASS', False),
        ('T4', 'Ground plane y=0',
         'HalfSpace orientation z = -pi/2 rad',
         'z = -1.5707963 rad',
         'PASS', False),
        ('T5', 'Contact forces count == 4  [*]',
         'count_contact_forces() returns 4',
         'count = 4',
         'PASS', True),
        ('T6', 'add_hand_external_force stub',
         'Returns same model (no-op stub)',
         'Model identity preserved',
         'PASS', False),
        ('T7', 'Box scenario 98.1 N/hand',
         '20 kg × 9.81 / 2 = 98.1 N per hand',
         '98.1 N/hand, 4 spheres',
         'PASS', False),
        ('T8', 'Phase 1a compatibility  [*]',
         'Stoop ExternalLoads path unaffected',
         'Falisse compat=True; no conflict',
         'PASS', True),
        ('T9', 'moco_track_setup co-import',
         'Both modules importable together',
         'DEFAULT_MESH_INTERVAL=0.02',
         'PASS', False),
    ]

    fig_h = 7.8
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, fig_h)
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # Header
    ax.add_patch(FancyBboxPatch((0, fig_h - 0.90), 14, 0.90,
                                boxstyle='square,pad=0',
                                fc='#161b22', ec='none'))
    ax.text(7, fig_h - 0.45,
            'contact_model.py — Verification Grid (T1-T9)',
            ha='center', va='center', fontsize=14, color=C_TEXT, fontweight='bold')

    # Column headers
    col_xs  = [0.20, 0.85, 2.80, 7.20, 11.40, 13.20]
    col_lbs = ['ID',  'Test',  'Expected',  'Actual',  'Result', '']
    y_hdr   = fig_h - 1.25
    for cx, cl in zip(col_xs, col_lbs):
        ax.text(cx, y_hdr, cl, fontsize=8.5, color=C_SUB,
                fontweight='bold', va='center')
    ax.axhline(fig_h - 1.45, color='#30363d', lw=1.0)

    row_h  = 0.56
    y_top  = fig_h - 1.62

    n_pass = 0
    for i, (tid, test, expected, actual, result, critical) in enumerate(tests):
        ry = y_top - i * row_h
        is_pass = result == 'PASS'
        if is_pass:
            n_pass += 1
        result_color = C_GREEN if is_pass else C_RED
        row_fc = '#161b22' if i % 2 == 0 else '#0d1117'

        # Row background
        ax.add_patch(FancyBboxPatch((0.1, ry - row_h * 0.48), 13.8, row_h * 0.90,
                                    boxstyle='round,pad=0.02',
                                    fc=row_fc, ec='none', zorder=1))

        # Critical border (yellow)
        if critical:
            ax.add_patch(FancyBboxPatch((0.08, ry - row_h * 0.50), 13.84, row_h * 0.94,
                                        boxstyle='round,pad=0.03',
                                        fc='none', ec=C_YELLOW, lw=1.8, zorder=2))

        ax.text(col_xs[0], ry, tid,      fontsize=8.5, color=C_CYAN, va='center',
                fontweight='bold', zorder=3)
        ax.text(col_xs[1], ry, test,     fontsize=8,   color=C_TEXT, va='center', zorder=3)
        ax.text(col_xs[2], ry, expected, fontsize=7.5, color=C_SUB,  va='center', zorder=3)
        ax.text(col_xs[3], ry, actual,   fontsize=7.5, color=C_TEXT, va='center', zorder=3)

        # Result pill
        pill_x = col_xs[4]
        pill_w = 0.90
        ax.add_patch(FancyBboxPatch((pill_x, ry - 0.14), pill_w, 0.28,
                                    boxstyle='round,pad=0.04',
                                    fc=result_color + '33',
                                    ec=result_color, lw=1.2, zorder=3))
        ax.text(pill_x + pill_w / 2, ry, result, ha='center', va='center',
                fontsize=8, color=result_color, fontweight='bold', zorder=4)

    # Footer summary
    ry_footer = y_top - len(tests) * row_h - 0.05
    ax.axhline(ry_footer, color='#30363d', lw=1.0)
    overall_color = C_GREEN if n_pass == len(tests) else C_RED
    ax.text(7, ry_footer - 0.30,
            f'Overall: {n_pass}/{len(tests)} PASS  --  '
            'T5 (4 contact forces) + T8 (Phase 1a compat) [*] highlighted  [critical]',
            ha='center', va='center', fontsize=9, color=overall_color, fontweight='bold')
    ax.text(7, ry_footer - 0.58,
            'Falisse 2019 · OpenSim 2D_gait · Architecture §2.1  |  '
            'No simulation — model configuration validation only',
            ha='center', va='center', fontsize=8, color=C_SUB)

    fig.tight_layout(pad=0.3)
    out_path = os.path.join(OUT_DIR, 'contact_model_verification_grid.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    p1 = make_diagram()
    p2 = make_verification_grid()
    print('Done.')

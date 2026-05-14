"""
Step 2 Week 2 — Integration Test Grid PNG Generator (English).

Outputs:
  docs/images/step2_integration/integration_test_diagram.png
  docs/images/step2_integration/integration_test_verification_grid.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_DIR = (
    '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step2_integration'
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
C_TEAL   = '#39d353'

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
# 1. integration_test_diagram.png
# ===========================================================================

def make_diagram():
    fig, axes = plt.subplots(1, 2, figsize=(18, 11))
    fig.patch.set_facecolor(C_BG)

    # ── Main title ──────────────────────────────────────────────────────────
    fig.text(0.5, 0.975,
             'Step 2 Week 2 — Integration Pipeline (Phase 1a + Box Scenario)',
             ha='center', va='top', fontsize=14, color=C_TEXT, fontweight='bold')
    fig.text(0.5, 0.952,
             '4 base modules end-to-end · No Moco solve (setup-only)',
             ha='center', va='top', fontsize=9, color=C_SUB)

    # ── LEFT PANEL: Phase 1a Stoop Path ────────────────────────────────────
    ax = axes[0]
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 11)
    ax.axis('off')
    ax.set_facecolor(C_BG)

    ax.add_patch(FancyBboxPatch((0.1, 0.1), 7.8, 10.6,
                                boxstyle='round,pad=0.08',
                                fc='#101820', ec=C_BORDER_IN, lw=2.0))
    ax.text(4.0, 10.45, 'Phase 1a Stoop Path',
            ha='center', va='center', fontsize=12, color=C_ARROW, fontweight='bold')
    ax.text(4.0, 10.15, 'ExternalLoads STO  ·  No contact spheres',
            ha='center', va='center', fontsize=8.5, color=C_SUB)

    stoop_boxes = [
        # (x, y, w, h, label, sublabel, fc, ec)
        (1.5, 8.80, 5.0, 0.80,
         'get_default_model_path()',
         'forearm_v1 · no_coupler variant',
         C_BOX_IN, C_BORDER_IN),
        (1.5, 7.65, 5.0, 0.80,
         'build_model_processor(task="stoop")',
         'residuals rot=20 N·m / trans=50 N',
         '#1a2740', C_BORDER_IN),
        (1.5, 6.50, 5.0, 0.80,
         'SuitConfig("L20", force_N=200)',
         'torque_Nm = 200 × 0.12 = 24.0 N·m',
         C_BOX_REF, C_BORDER_REF),
        (1.5, 5.35, 5.0, 0.80,
         'ExternalLoads STO',
         'stoop_grf_v5.xml  (no contact model)',
         C_BOX_MID, C_BORDER_MID),
        (1.5, 4.20, 5.0, 0.80,
         'setup_for_stoop_task()',
         't0=0.0 s, tf=5.0 s, mesh=0.02 s',
         '#2a1a2a', C_BORDER_GOAL),
        (1.5, 3.05, 5.0, 0.80,
         'create_suit_actuators()',
         '5 × CoordinateActuator  4.8 N·m each',
         C_BOX_REF, C_BORDER_REF),
        (1.5, 1.70, 5.0, 1.00,
         'MocoStudy  (Phase 1a ready)',
         'John 2022 compat  ·  mesh 250/5 s',
         '#0f2a1a', C_BORDER_MID),
    ]
    for bx, by, bw, bh, lb, slb, fc, ec in stoop_boxes:
        fbox(ax, bx, by, bw, bh, lb, slb, fc=fc, ec=ec, fontsize=8.5)

    # Arrows
    for i in range(len(stoop_boxes) - 1):
        _, by1, _, bh1, *_ = stoop_boxes[i]
        _, by2, _, bh2, *_ = stoop_boxes[i + 1]
        arrow(ax, 4.0, by1, 4.0, by2 + bh2, color=C_ARROW, lw=1.6)

    # Badge
    ax.add_patch(FancyBboxPatch((0.4, 0.15), 7.2, 0.42,
                                boxstyle='round,pad=0.04',
                                fc='#1a1a2a', ec=C_BORDER_GOAL, lw=1.2))
    ax.text(4.0, 0.36,
            'Stoop: ExternalLoads STO preserved · No contact spheres needed',
            ha='center', va='center', fontsize=7.5, color=C_PURPLE)

    # ── RIGHT PANEL: Box Scenario Path ─────────────────────────────────────
    ax2 = axes[1]
    ax2.set_xlim(0, 8)
    ax2.set_ylim(0, 11)
    ax2.axis('off')
    ax2.set_facecolor(C_BG)

    ax2.add_patch(FancyBboxPatch((0.1, 0.1), 7.8, 10.6,
                                 boxstyle='round,pad=0.08',
                                 fc='#101510', ec=C_BORDER_MID, lw=2.0))
    ax2.text(4.0, 10.45, 'Box Scenario Path',
             ha='center', va='center', fontsize=12, color=C_GREEN, fontweight='bold')
    ax2.text(4.0, 10.15, 'Hunt-Crossley contact  ·  Bilateral hand force  ·  Suit sweep',
             ha='center', va='center', fontsize=8.5, color=C_SUB)

    box_boxes = [
        (1.5, 8.80, 5.0, 0.80,
         'build_model_processor(task="box")',
         'residuals rot=50 N·m / trans=300 N',
         '#1f3a1f', C_BORDER_MID),
        (1.5, 7.65, 5.0, 0.80,
         'mp.process()  →  base_model',
         '78 bodies · forearm_v1 · no_coupler',
         C_BOX_IN, C_BORDER_IN),
        (1.5, 6.50, 5.0, 0.80,
         'add_foot_contact_model()  [*]',
         '4 spheres  heel r=35 mm / ball r=15 mm',
         '#1a3a1a', C_BORDER_MID),
        (1.5, 5.35, 5.0, 0.80,
         'generate_box_force_sto()  [*]',
         '98.1 N/hand  t≥2.0 s  ground frame',
         C_BOX_REF, C_BORDER_REF),
        (1.5, 4.20, 5.0, 0.80,
         'add_hand_external_force_xml()  [*]',
         'hand_r + hand_l  ExternalLoads XML',
         '#2a2a1a', C_BORDER_REF),
        (1.5, 3.05, 5.0, 0.80,
         'make_suit_sweep([0..200] N)',
         '5 conditions  [0,6,12,18,24] N·m',
         C_BOX_GOAL, C_BORDER_GOAL),
        (1.5, 1.70, 5.0, 1.00,
         'setup_for_box_task()  →  MocoStudy',
         'Falisse 2019 contact  ·  t=1.0–4.0 s',
         '#0f2a1a', C_BORDER_MID),
    ]
    for bx, by, bw, bh, lb, slb, fc, ec in box_boxes:
        fbox(ax2, bx, by, bw, bh, lb, slb, fc=fc, ec=ec, fontsize=8.5)

    # Mark the 3 starred steps (contact + hand force)
    for i in [2, 3, 4]:
        bx, by, bw, bh, *_ = box_boxes[i]
        ax2.add_patch(FancyBboxPatch((bx - 0.06, by - 0.06), bw + 0.12, bh + 0.12,
                                     boxstyle='round,pad=0.04',
                                     fc='none', ec=C_YELLOW, lw=2.0, zorder=5))

    # Arrows
    for i in range(len(box_boxes) - 1):
        _, by1, _, bh1, *_ = box_boxes[i]
        _, by2, _, bh2, *_ = box_boxes[i + 1]
        arrow(ax2, 4.0, by1, 4.0, by2 + bh2, color=C_ARROW, lw=1.6)

    # Badge
    ax2.add_patch(FancyBboxPatch((0.4, 0.15), 7.2, 0.42,
                                 boxstyle='round,pad=0.04',
                                 fc='#1a2a1a', ec=C_BORDER_MID, lw=1.2))
    ax2.text(4.0, 0.36,
             '[*] Hunt-Crossley contact + Hand force — Week 2 new implementation',
             ha='center', va='center', fontsize=7.5, color=C_YELLOW)

    # ── Shared footer ────────────────────────────────────────────────────────
    fig.text(
        0.5, 0.022,
        'Phase 1a stoop preserved (ExternalLoads STO).  '
        'Box uses Hunt-Crossley contact + Hand force.  '
        '19/19 tests PASS.',
        ha='center', va='bottom', fontsize=8.5, color=C_PINK,
    )

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    out_path = os.path.join(OUT_DIR, 'integration_test_diagram.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


# ===========================================================================
# 2. integration_test_verification_grid.png
# ===========================================================================

def make_verification_grid():
    # P1-P8 results
    p_tests = [
        ('P1', 'Import Phase 1a symbols',
         '7 symbols from base.*',
         '7 symbols OK', 'PASS', False),
        ('P2', 'ModelProcessor stoop residuals',
         'rot=20 N·m, trans=50 N',
         'rot=20.0 N·m, trans=50.0 N', 'PASS', False),
        ('P3', 'SuitConfig L20 = 24 N·m',
         '200 N × 0.12 m = 24.0 N·m',
         'torque_Nm=24.0 N·m', 'PASS', False),
        ('P4', 'MocoStudy from setup_for_stoop_task',
         'isinstance(study, osim.MocoStudy)',
         'MocoStudy returned', 'PASS', False),
        ('P5', 'John 2022 compatibility  [*]',
         'verify_john2022_compatibility=True',
         'compat=True', 'PASS', True),
        ('P6', 'ExternalLoads STO loaded',
         'stoop_grf_v5.xml → ModelProcessor OK',
         'XML loaded OK', 'PASS', False),
        ('P7', 'Mesh interval 0.02 s / 250 mesh',
         'DEFAULT_MESH_INTERVAL=0.02, 250/5 s',
         '0.02 s → 250 intervals', 'PASS', False),
        ('P8', 'Suit 5 actuators 4.8 N·m each',
         '24 N·m / 5 segs = 4.8 N·m',
         '5 × 4.8 N·m = 24.0 N·m', 'PASS', False),
    ]

    # B1-B11 results
    b_tests = [
        ('B1', 'Import box-related symbols',
         '7 box symbols from base.*',
         '7 symbols OK', 'PASS', False),
        ('B2', 'ModelProcessor box residuals',
         'rot=50 N·m, trans=300 N',
         'rot=50.0, trans=300.0', 'PASS', False),
        ('B3', 'mp.process() → base_model',
         'model.getBodySet().getSize() > 0',
         '78 bodies', 'PASS', False),
        ('B4', 'add_foot_contact_model → 4 spheres  [*]',
         'count_contact_geometry spheres=4',
         'spheres=4, halfspaces=1', 'PASS', True),
        ('B5', 'count_contact_forces == 4  [*]',
         'SmoothSphereHalfSpaceForce × 4',
         'count=4', 'PASS', True),
        ('B6', 'box_force_N_per_hand = 98.1 N  [*]',
         '20 kg × 9.81 / 2 = 98.1 N',
         '98.10 N/hand', 'PASS', True),
        ('B7', 'make_suit_sweep 5 conditions',
         '[0,6,12,18,24] N·m',
         '[0.0,6.0,12.0,18.0,24.0] N·m', 'PASS', False),
        ('B8', 'MocoStudy from setup_for_box_task',
         'isinstance(study, osim.MocoStudy)',
         'MocoStudy returned, t=1.0–4.0 s', 'PASS', False),
        ('B9', 'verify_falisse2019_compatibility',
         '4 spheres + 4 forces + ≥1 halfspace',
         'compat=True', 'PASS', False),
        ('B10', 'add_hand_external_force_xml  [*]',
         'XML file generated with hand_r + hand_l',
         'XML exists, hand_r OK, hand_l OK', 'PASS', True),
        ('B11', 'generate_box_force_sto  [*]',
         'STO cols OK, 98.1 N at t≥2.0 s',
         'STO OK, cols OK, force verified', 'PASS', True),
    ]

    n_p = len(p_tests)
    n_b = len(b_tests)
    total_rows = n_p + n_b
    fig_h = 2.0 + total_rows * 0.50 + 2.0   # header + rows + section gaps + footer

    fig, ax = plt.subplots(figsize=(16, fig_h))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, fig_h)
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # ── Main header ──────────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, fig_h - 1.0), 16, 1.0,
                                boxstyle='square,pad=0',
                                fc='#161b22', ec='none'))
    ax.text(8, fig_h - 0.50,
            'Step 2 Week 2 — Integration Verification Grid (P1-P8 + B1-B11)',
            ha='center', va='center', fontsize=13, color=C_TEXT, fontweight='bold')

    # ── Column headers ───────────────────────────────────────────────────────
    col_xs  = [0.25, 0.90, 3.30, 8.00, 12.60, 14.80]
    col_lbs = ['ID', 'Test', 'Expected', 'Actual', 'Result', '']
    y_hdr   = fig_h - 1.30
    for cx, cl in zip(col_xs, col_lbs):
        ax.text(cx, y_hdr, cl, fontsize=8.5, color=C_SUB,
                fontweight='bold', va='center')
    ax.axhline(fig_h - 1.48, color='#30363d', lw=1.0)

    row_h = 0.50
    y_cursor = fig_h - 1.65

    def draw_section_header(y, label, color, ec_col):
        ax.add_patch(FancyBboxPatch((0.1, y - 0.20), 15.8, 0.38,
                                    boxstyle='round,pad=0.04',
                                    fc='#1a1a2a', ec=ec_col, lw=1.4))
        ax.text(8.0, y - 0.01, label,
                ha='center', va='center', fontsize=9.5,
                color=color, fontweight='bold')
        return y - 0.45

    def draw_row(ax, y, tid, test, expected, actual, result, critical, idx):
        is_pass = result == 'PASS'
        result_color = C_GREEN if is_pass else C_RED
        row_fc = '#161b22' if idx % 2 == 0 else '#0d1117'

        ax.add_patch(FancyBboxPatch((0.1, y - row_h * 0.48), 15.8, row_h * 0.90,
                                    boxstyle='round,pad=0.02',
                                    fc=row_fc, ec='none', zorder=1))
        if critical:
            ax.add_patch(FancyBboxPatch((0.08, y - row_h * 0.50), 15.84, row_h * 0.94,
                                        boxstyle='round,pad=0.03',
                                        fc='none', ec=C_YELLOW, lw=1.8, zorder=2))

        ax.text(col_xs[0], y, tid, fontsize=8.5, color=C_CYAN,
                va='center', fontweight='bold', zorder=3)
        ax.text(col_xs[1], y, test, fontsize=8, color=C_TEXT, va='center', zorder=3)
        ax.text(col_xs[2], y, expected, fontsize=7.5, color=C_SUB, va='center', zorder=3)
        ax.text(col_xs[3], y, actual, fontsize=7.5, color=C_TEXT, va='center', zorder=3)

        pill_x = col_xs[4]
        pill_w = 0.92
        ax.add_patch(FancyBboxPatch((pill_x, y - 0.14), pill_w, 0.28,
                                    boxstyle='round,pad=0.04',
                                    fc=result_color + '33',
                                    ec=result_color, lw=1.2, zorder=3))
        ax.text(pill_x + pill_w / 2, y, result, ha='center', va='center',
                fontsize=8, color=result_color, fontweight='bold', zorder=4)
        return is_pass

    # ── Phase 1a section ─────────────────────────────────────────────────────
    y_cursor = draw_section_header(
        y_cursor, 'Phase 1a Stoop Integration  (P1-P8)', C_ARROW, C_BORDER_IN
    )
    n_pass_p = 0
    for i, row in enumerate(p_tests):
        tid, test, expected, actual, result, critical = row
        ok = draw_row(ax, y_cursor, tid, test, expected, actual, result, critical, i)
        if ok:
            n_pass_p += 1
        y_cursor -= row_h

    # ── Box section ─────────────────────────────────────────────────────────
    y_cursor -= 0.25
    y_cursor = draw_section_header(
        y_cursor, 'Box Scenario Integration  (B1-B11)', C_GREEN, C_BORDER_MID
    )
    n_pass_b = 0
    for i, row in enumerate(b_tests):
        tid, test, expected, actual, result, critical = row
        ok = draw_row(ax, y_cursor, tid, test, expected, actual, result, critical, i)
        if ok:
            n_pass_b += 1
        y_cursor -= row_h

    # ── Footer ───────────────────────────────────────────────────────────────
    total_pass = n_pass_p + n_pass_b
    total_n = n_p + n_b
    overall_color = C_GREEN if total_pass == total_n else C_RED
    y_footer = y_cursor - 0.20
    ax.axhline(y_footer + 0.35, color='#30363d', lw=1.0)

    ax.text(8, y_footer + 0.08,
            f'Overall: {total_pass}/{total_n} PASS  ·  ALL PASS  '
            '·  [*] Critical tests highlighted in yellow',
            ha='center', va='center', fontsize=10,
            color=overall_color, fontweight='bold')
    ax.text(8, y_footer - 0.25,
            'John 2022  ·  Falisse 2019  ·  Dembia 2020  ·  Hicks 2015  '
            '|  No Moco solve — model configuration validation only',
            ha='center', va='center', fontsize=8, color=C_SUB)

    fig.tight_layout(pad=0.3)
    out_path = os.path.join(OUT_DIR, 'integration_test_verification_grid.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    p1 = make_diagram()
    p2 = make_verification_grid()
    print('Done.')

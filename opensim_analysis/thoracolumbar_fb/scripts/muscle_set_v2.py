"""Muscle Set v2: Phase 1a (114) + Lower Limb (41) = 155 muscles.

ThoracolumbarFB v2.0 (620 muscles) 모델에서 실제 존재하는 하지 근육 목록.

NOTE on missing muscles (ThoracolumbarFB v2.0 한계):
  - semimembranosus / semitendinosus: 모델에 없음 (bifemlh만 존재)
  - vastus lateralis / vastus medialis: 모델에 없음 (vas_int_r/l만 존재)
  - gluteus minimus: 모델에 없음 (glut_max/med만 존재)
  - gastrocnemius lateralis: 모델에 없음 (med_gas만 존재)

Reference:
  - Holzbaur et al. (2005) A model of the upper extremity for simulating musculoskeletal
    surgery and analyzing neuromuscular control. Ann Biomed Eng.
  - Delp et al. (1990) An interactive graphics-based model of the lower extremity
    to study orthopaedic surgical procedures. IEEE Trans Biomed Eng.
  - Bruno et al. (2015) Development and validation of a musculoskeletal model of the
    fully thoracolumbar spine. Medical Engineering & Physics.
"""

# ============================================================
# Phase 1a baseline: 114 muscles (기존 유지)
# ============================================================
PHASE1A_MUSCLES = [
    # [IL] — 24 muscles
    'IL_L1_l', 'IL_L1_r',
    'IL_L2_l', 'IL_L2_r',
    'IL_L3_l', 'IL_L3_r',
    'IL_L4_l', 'IL_L4_r',
    'IL_R10_l', 'IL_R10_r',
    'IL_R11_l', 'IL_R11_r',
    'IL_R12_l', 'IL_R12_r',
    'IL_R5_l', 'IL_R5_r',
    'IL_R6_l', 'IL_R6_r',
    'IL_R7_l', 'IL_R7_r',
    'IL_R8_l', 'IL_R8_r',
    'IL_R9_l', 'IL_R9_r',
    # [LTpT] — 42 muscles
    'LTpT_R10_l', 'LTpT_R10_r',
    'LTpT_R11_l', 'LTpT_R11_r',
    'LTpT_R12_l', 'LTpT_R12_r',
    'LTpT_R4_l', 'LTpT_R4_r',
    'LTpT_R5_l', 'LTpT_R5_r',
    'LTpT_R6_l', 'LTpT_R6_r',
    'LTpT_R7_l', 'LTpT_R7_r',
    'LTpT_R8_l', 'LTpT_R8_r',
    'LTpT_R9_l', 'LTpT_R9_r',
    'LTpT_T10_l', 'LTpT_T10_r',
    'LTpT_T11_l', 'LTpT_T11_r',
    'LTpT_T12_l', 'LTpT_T12_r',
    'LTpT_T1_l', 'LTpT_T1_r',
    'LTpT_T2_l', 'LTpT_T2_r',
    'LTpT_T3_l', 'LTpT_T3_r',
    'LTpT_T4_l', 'LTpT_T4_r',
    'LTpT_T5_l', 'LTpT_T5_r',
    'LTpT_T6_l', 'LTpT_T6_r',
    'LTpT_T7_l', 'LTpT_T7_r',
    'LTpT_T8_l', 'LTpT_T8_r',
    'LTpT_T9_l', 'LTpT_T9_r',
    # [LTpL] — 10 muscles
    'LTpL_L1_l', 'LTpL_L1_r',
    'LTpL_L2_l', 'LTpL_L2_r',
    'LTpL_L3_l', 'LTpL_L3_r',
    'LTpL_L4_l', 'LTpL_L4_r',
    'LTpL_L5_l', 'LTpL_L5_r',
    # [QL] — 36 muscles
    'QL_ant_I_2-12_1_l', 'QL_ant_I_2-12_1_r',
    'QL_ant_I_2-T12_l', 'QL_ant_I_2-T12_r',
    'QL_ant_I_3-12_1_l', 'QL_ant_I_3-12_1_r',
    'QL_ant_I_3-12_2_l', 'QL_ant_I_3-12_2_r',
    'QL_ant_I_3-12_3_l', 'QL_ant_I_3-12_3_r',
    'QL_ant_I_3-T12_l', 'QL_ant_I_3-T12_r',
    'QL_mid_L2-12_1_l', 'QL_mid_L2-12_1_r',
    'QL_mid_L3-12_1_l', 'QL_mid_L3-12_1_r',
    'QL_mid_L3-12_2_l', 'QL_mid_L3-12_2_r',
    'QL_mid_L3-12_3_l', 'QL_mid_L3-12_3_r',
    'QL_mid_L4-12_3_l', 'QL_mid_L4-12_3_r',
    'QL_post_I_1-L3_l', 'QL_post_I_1-L3_r',
    'QL_post_I_2-L2_l', 'QL_post_I_2-L2_r',
    'QL_post_I_2-L3_l', 'QL_post_I_2-L3_r',
    'QL_post_I_2-L4_l', 'QL_post_I_2-L4_r',
    'QL_post_I_3-L1_l', 'QL_post_I_3-L1_r',
    'QL_post_I_3-L2_l', 'QL_post_I_3-L2_r',
    'QL_post_I_3-L3_l', 'QL_post_I_3-L3_r',
    # [RA] — 2 muscles
    'rect_abd_l', 'rect_abd_r',
]

# ============================================================
# Lower Limb additions: 41 muscles
# (실제 모델에 존재하는 것만 포함)
# ============================================================

# Gluteus maximus — 3 bundles × 2 sides = 6
LOWER_LIMB_GLUTEUS_MAX = [
    'glut_max1_r', 'glut_max1_l',
    'glut_max2_r', 'glut_max2_l',
    'glut_max3_r', 'glut_max3_l',
]

# Gluteus medius — 3 bundles × 2 sides = 6
# NOTE: gluteus minimus NOT in ThoracolumbarFB v2.0
LOWER_LIMB_GLUTEUS_MED = [
    'glut_med1_r', 'glut_med1_l',
    'glut_med2_r', 'glut_med2_l',
    'glut_med3_r', 'glut_med3_l',
]

# Hamstrings — bifemlh (long head) + bifemsh (short head) × 2 sides = 4
# NOTE: semimembranosus, semitendinosus NOT in ThoracolumbarFB v2.0
LOWER_LIMB_HAMSTRINGS = [
    'bifemlh_r', 'bifemlh_l',
    'bifemsh_r', 'bifemsh_l',
]

# Quadriceps — rectus femoris + vastus intermedius × 2 sides = 4
# NOTE: vastus lateralis, vastus medialis NOT in ThoracolumbarFB v2.0
LOWER_LIMB_QUADRICEPS = [
    'rect_fem_r', 'rect_fem_l',
    'vas_int_r', 'vas_int_l',
]

# Iliopsoas — iliacus + psoas (TP/VB bundles) × 2 sides
# Ps_L1_VB already crosses hip; iliacus is primary hip flexor
LOWER_LIMB_ILIOPSOAS = [
    'iliacus_r', 'iliacus_l',
    'Ps_L1_VB_r', 'Ps_L1_VB_l',
    'Ps_L5_VB_r', 'Ps_L5_VB_l',
]

# Hip assistants — TFL + sartorius × 2 sides = 4
LOWER_LIMB_HIP_ASSIST = [
    'tfl_r', 'tfl_l',
    'sar_r', 'sar_l',
]

# Hip deep rotators — gemellus, quadratus femoris × 2 sides = 4
LOWER_LIMB_HIP_DEEP = [
    'gem_r', 'gem_l',
    'quad_fem_r', 'quad_fem_l',
]

# Adductor / gracilis — add_mag2, grac × 2 sides = 4
LOWER_LIMB_ADDUCTOR = [
    'add_mag2_r', 'add_mag2_l',
    'grac_r', 'grac_l',
]

# Calf — medial gastrocnemius + soleus × 2 sides = 4
# NOTE: lateral gastrocnemius NOT in ThoracolumbarFB v2.0
# Tibialis anterior + posterior for ankle stability
LOWER_LIMB_CALF = [
    'med_gas_r', 'med_gas_l',
    'soleus_r', 'soleus_l',
]

# Tibialis — for ankle/foot stability during lifting
LOWER_LIMB_TIBIALIS = [
    'tib_ant_r', 'tib_ant_l',
]

# Combine all lower limb
LOWER_LIMB_MUSCLES = (
    LOWER_LIMB_GLUTEUS_MAX +
    LOWER_LIMB_GLUTEUS_MED +
    LOWER_LIMB_HAMSTRINGS +
    LOWER_LIMB_QUADRICEPS +
    LOWER_LIMB_ILIOPSOAS +
    LOWER_LIMB_HIP_ASSIST +
    LOWER_LIMB_HIP_DEEP +
    LOWER_LIMB_ADDUCTOR +
    LOWER_LIMB_CALF +
    LOWER_LIMB_TIBIALIS
)

# ============================================================
# Combined set v2
# ============================================================
MUSCLE_SET_V2 = list(PHASE1A_MUSCLES) + LOWER_LIMB_MUSCLES

# Remove duplicates (psoas bundles may overlap with Phase 1a QL region)
MUSCLE_SET_V2 = list(dict.fromkeys(MUSCLE_SET_V2))

if __name__ == '__main__':
    print(f"Phase 1a:    {len(PHASE1A_MUSCLES)} muscles")
    print(f"Lower limb:  {len(LOWER_LIMB_MUSCLES)} muscles")
    print(f"Combined v2: {len(MUSCLE_SET_V2)} muscles (after dedup)")
    print("\n=== Lower limb breakdown ===")
    print(f"  Glut max:    {len(LOWER_LIMB_GLUTEUS_MAX)}")
    print(f"  Glut med:    {len(LOWER_LIMB_GLUTEUS_MED)}")
    print(f"  Hamstrings:  {len(LOWER_LIMB_HAMSTRINGS)}")
    print(f"  Quadriceps:  {len(LOWER_LIMB_QUADRICEPS)}")
    print(f"  Iliopsoas:   {len(LOWER_LIMB_ILIOPSOAS)}")
    print(f"  Hip assist:  {len(LOWER_LIMB_HIP_ASSIST)}")
    print(f"  Hip deep:    {len(LOWER_LIMB_HIP_DEEP)}")
    print(f"  Adductor:    {len(LOWER_LIMB_ADDUCTOR)}")
    print(f"  Calf:        {len(LOWER_LIMB_CALF)}")
    print(f"  Tibialis:    {len(LOWER_LIMB_TIBIALIS)}")
    print("\n=== Missing from ThoracolumbarFB v2.0 model ===")
    print("  gluteus minimus (glut_min): NOT IN MODEL")
    print("  semimembranosus:            NOT IN MODEL")
    print("  semitendinosus:             NOT IN MODEL")
    print("  vastus lateralis:           NOT IN MODEL")
    print("  vastus medialis:            NOT IN MODEL")
    print("  gastrocnemius lateralis:    NOT IN MODEL")

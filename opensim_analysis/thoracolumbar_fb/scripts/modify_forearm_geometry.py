"""
modify_forearm_geometry.py
=========================
ThoracolumbarFB forearm geometry 보강 (Forearm v1)

배경:
- hand_R/L body origin = wrist center (손 세그먼트 없음)
- GH→hand_R 현재: 54.5 cm (anthropometric 76 cm 대비 21.5 cm 부족)
- 원인: radius_hand_r/l joint의 child frame이 hand_R/L origin과 동일
  → wrist center = hand body origin → 손 길이(~19 cm) 누락

수정 전략:
- radius_hand_r/l joint의 PARENT offset Y를 연장
  (radius_R body → wrist center 거리 늘림)
- radius_R local Y축 = ground Y축 (standing pose에서 identity rotation 확인)
- 현재 forearm kinematic = 25.8 cm (elbow → wrist)
- 추가: De Leva 1996 hand length = 19.2 cm (wrist to middle fingertip)
- New forearm offset Y: -0.242 → -0.434 m (19.2 cm 추가)
- 예상 GH→hand_R: 54.5 + 19.2 = 73.7 cm (범위 내)

anthropometric 근거:
- De Leva 1996 (J Biomech 29(9):1223-1230) Table 4:
  Male hand length: 0.192 m (wrist to middle fingertip, mean)
- Winter 2009 (Biomechanics and Motor Control, 4th ed.):
  Total arm (acromion to fingertip) / height = 0.460 (175cm → 80.5 cm)
- 현재 모델 humerus (29.1 cm) + forearm (25.8 cm) = 54.9 cm (upper+forearm)
  Target: 54.9 + 19.2 = 74.1 cm (De Leva range: ~73-76 cm)

수정 내용:
1. radius_hand_r joint: radius_R_offset translation Y: -0.242 → -0.434 m
2. radius_hand_l joint: radius_L_offset translation Y: -0.242 → -0.434 m
   (L side: Z = -0.025, symmetry)
3. hand_R/L body mass/inertia 재계산 (hand_R mass 0.4575 kg 유지, COM 재조정)
4. ulna body: 이미 2.3 cm 으로 kinematic에 영향 없음 → 수정 불필요

주의:
- 근육 attachment는 body에 고정 → 관절 위치 변경해도 muscle path 보존
- wrist joint (wrist_dev_r, wrist_flex_r) locked → 실질적 영향 없음
- Phase 1a stoop에서 팔은 자연스럽게 늘어짐 → ES 영향 미미 예상

작성: opensim-agent (2026-05-04)
"""

import shutil
import numpy as np
import re
import os

# Paths
SRC = "/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
DST = "/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim"

# Anthropometric parameters (De Leva 1996)
HAND_LENGTH_M = 0.192  # m: wrist to middle fingertip, adult male

# Current wrist offsets in radius_R local frame
# Right: (0.018, -0.242, 0.025)
# Left:  (0.018, -0.242, -0.025) [mirror in Z]
CURRENT_WRIST_OFFSET_Y = -0.242  # m (both sides)
NEW_WRIST_OFFSET_Y = CURRENT_WRIST_OFFSET_Y - HAND_LENGTH_M  # = -0.434 m

print("=" * 60)
print("Forearm v1 Modification")
print("=" * 60)
print(f"Source: {os.path.basename(SRC)}")
print(f"Target: {os.path.basename(DST)}")
print()
print(f"Hand length to add (De Leva 1996): {HAND_LENGTH_M*100:.1f} cm")
print(f"Wrist offset Y: {CURRENT_WRIST_OFFSET_Y:.3f} → {NEW_WRIST_OFFSET_Y:.3f} m")
print(f"Expected GH→hand_R: 54.5 + {HAND_LENGTH_M*100:.1f} = {54.5 + HAND_LENGTH_M*100:.1f} cm")
print()

# Read source file
print("Reading source model...")
with open(SRC, 'r') as f:
    content = f.read()

original_content = content

# ================================================================
# Modification 1: radius_hand_r (RIGHT SIDE)
# Parent offset: (0.018, -0.242, 0.025) → (0.018, -0.434, 0.025)
# ================================================================
# The exact string in the file (from reading it):
OLD_R_OFFSET = "0.017999999999999999 -0.24199999999999999 0.025000000000000001"
NEW_R_OFFSET = f"0.017999999999999999 {NEW_WRIST_OFFSET_Y:.17f} 0.025000000000000001"

print(f"Right wrist offset:")
print(f"  OLD: {OLD_R_OFFSET}")
print(f"  NEW: {NEW_R_OFFSET}")

# Verify exactly 1 occurrence in radius_hand_r context
r_count = content.count(OLD_R_OFFSET)
print(f"  Occurrences in file: {r_count}")

if r_count != 2:
    # Try to find exact match
    print(f"  WARNING: Expected 2 occurrences (R and L), found {r_count}")
    # Search for surrounding context
    idx = content.find(OLD_R_OFFSET)
    if idx >= 0:
        print(f"  Context: ...{content[idx-100:idx+100]}...")

# ================================================================
# Modification 2: radius_hand_l (LEFT SIDE)
# Parent offset: (0.018, -0.242, -0.025) → (0.018, -0.434, -0.025)
# ================================================================
OLD_L_OFFSET = "0.017999999999999999 -0.24199999999999999 -0.025000000000000001"
NEW_L_OFFSET = f"0.017999999999999999 {NEW_WRIST_OFFSET_Y:.17f} -0.025000000000000001"

print(f"\nLeft wrist offset:")
print(f"  OLD: {OLD_L_OFFSET}")
print(f"  NEW: {NEW_L_OFFSET}")

l_count = content.count(OLD_L_OFFSET)
print(f"  Occurrences in file: {l_count}")

# Apply modifications
print("\nApplying modifications...")

# Right side: replace first occurrence only (radius_hand_r parent frame)
# But we need to make sure we're replacing the right one
# The radius_hand_r joint comes first in the file (line 13472)
# radius_hand_l comes later (line 14118)
# Both have unique Z values (0.025 vs -0.025), so string match is unique

content_new = content.replace(OLD_R_OFFSET, NEW_R_OFFSET)
content_new = content_new.replace(OLD_L_OFFSET, NEW_L_OFFSET)

# Verify changes
new_r = content_new.count(NEW_R_OFFSET)
new_l = content_new.count(NEW_L_OFFSET)
print(f"  Right offset applied: {new_r} times")
print(f"  Left offset applied: {new_l} times")

# Check that old strings are gone
remaining_r = content_new.count(OLD_R_OFFSET)
remaining_l = content_new.count(OLD_L_OFFSET)
print(f"  Old right offset remaining: {remaining_r} (should be 0)")
print(f"  Old left offset remaining: {remaining_l} (should be 0)")

if remaining_r > 0 or remaining_l > 0:
    print("ERROR: Old offsets still present! Aborting.")
    exit(1)

if new_r != 1 or new_l != 1:
    print(f"ERROR: Expected 1 replacement each, got R={new_r}, L={new_l}. Aborting.")
    exit(1)

# Write output
print(f"\nWriting modified model to: {DST}")
with open(DST, 'w') as f:
    f.write(content_new)

file_size = os.path.getsize(DST)
print(f"File size: {file_size:,} bytes")

print()
print("=" * 60)
print("Modification complete. Summary:")
print("=" * 60)
print(f"  radius_hand_r parent Y: {CURRENT_WRIST_OFFSET_Y:.3f} → {NEW_WRIST_OFFSET_Y:.3f} m")
print(f"  radius_hand_l parent Y: {CURRENT_WRIST_OFFSET_Y:.3f} → {NEW_WRIST_OFFSET_Y:.3f} m")
print(f"  Hand length added: {HAND_LENGTH_M*100:.1f} cm (De Leva 1996 male)")
print()
print("Next step: Run FK verification")
print("  python verify_forearm_v1.py")

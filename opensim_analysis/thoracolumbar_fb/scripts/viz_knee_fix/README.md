# TLFB knee collapse — 시각화 전용 fix

## 문제
MuSkeMo로 TLFB(`*_modified_no_coupler.osim`)를 import하면 무릎이 접혀서 들어온다.
MuSkeMo가 TLFB knee의 CustomJoint translation(spline)을 import 시 적용하지 못해,
tibia body 원점이 femur 원점과 ~1 cm 차이(정상 ~42 cm)로 collapse → 정강이뼈가 대퇴뼈 위로 겹침
→ 다리가 절반 높이(foot −0.495 m, 정상 −0.919 m)로 렌더된다.
(대조군 Rajagopal/Lai의 walker_knee는 MuSkeMo가 정상 처리.)

## 해결 (정량 모델 .osim 불변)
import 후 **각 뼈 mesh를 OpenSim socket-frame ground transform으로 직접 배치**.
OpenSim default pose를 정확히 재현하며, .osim·SO/Moco 분석에는 전혀 영향 없음
(OpenSim은 spline을 정상 처리하므로 정량 결과 불변).

> 주의: body empty가 아니라 **mesh**를 옮긴다. MuSkeMo body empty는 OpenSim body
> frame 원점이 아니라 COM 근처에 위치하므로 body empty를 옮기면 어긋난다. 또한 skull 등
> 일부 mesh는 PhysicalOffsetFrame에 붙어 있어 **body가 아닌 socket frame** 기준이어야 한다.

## 사용법
1. transform 추출 (opensim env, 모델 바뀔 때만 1회):
   ```
   /home/sysop/miniconda3/envs/opensim/bin/python export_mesh_xforms.py
   ```
   → `tlfb_mesh_xforms.json` (mesh basename → frame ground R,p). 이미 동봉됨.

2. 렌더 (Blender + MuSkeMo addon):
   ```
   DISPLAY=:1 blender --background --python render_knee_fixed_skeleton.py   # 불투명 골격
   DISPLAY=:1 blender --background --python render_fixed_spine.py           # 골격 + ES 근육 6mm (영상용)
   ```
   핵심 코드:
   ```python
   for o in bpy.data.objects:
       if o.type=='MESH' and o.get('MuSkeMo_type')=='GEOMETRY' and o.name in MX:
           o.parent=None
           o.matrix_world = mat_from(MX[o.name]['R'], MX[o.name]['p'])
   ```

## 검증 (OpenSim 측정값과 일치)
skull_top 0.850 m · femur −0.417..0.035 · tibia −0.832..−0.440 (무릎 end-to-end) · foot_bot −0.914 m.
산출 grid: `docs/images/literature_review/tlfb_knee_fix_grid.png`.

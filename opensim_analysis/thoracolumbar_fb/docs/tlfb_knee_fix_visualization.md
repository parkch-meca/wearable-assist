# TLFB knee collapse — 시각화 전용 fix (해결 완료)

**일자:** 2026-06-11
**방향:** MuSkeMo가 TLFB 무릎을 정상 렌더하게 만들기. **.osim 정량 모델 불변**, 시각화 단계에서만 knee 펴기.

---

## 원인 (앞선 진단에서 확정)
MuSkeMo가 TLFB knee의 OpenSim CustomJoint translation(spline)을 import 시 적용하지 못함
→ tibia body 원점이 femur 원점과 ~1 cm(정상 ~42 cm)로 collapse → 정강이뼈가 대퇴뼈 위로 겹침
→ 다리 절반 높이 렌더(foot −0.495 m). 뼈 길이 자체는 정상.

## 해결 방법
MuSkeMo import 후 **각 뼈 mesh를 OpenSim socket-frame ground transform으로 직접 배치**:

```python
# tlfb_mesh_xforms.json: mesh basename -> 그 mesh가 붙은 OpenSim frame의 ground (R,p)
for o in bpy.data.objects:
    if o.type=='MESH' and o.get('MuSkeMo_type')=='GEOMETRY' and o.name in MX:
        o.parent=None
        o.matrix_world = mat_from(MX[o.name]['R'], MX[o.name]['p'])
```

설계 포인트 (실패에서 배운 것):
- **body empty가 아니라 mesh를 옮긴다.** MuSkeMo body empty는 OpenSim body frame 원점이 아니라
  COM 근처 → body empty를 frame으로 옮기면 mesh가 어긋남(발 분리 발생).
- **mesh의 socket frame 기준.** skull 등 일부는 PhysicalOffsetFrame에 붙어 있어 body 기준이면
  0.12 m 어긋남. frame 단위로 export해야 정확.

## 검증 (OpenSim 측정값과 완전 일치)
| landmark | fix 후 scene | OpenSim |
|----------|------|---------|
| skull_top | 0.850 | 0.850 |
| femur | −0.417 .. 0.035 | hip 0.013 / knee −0.411 |
| tibia | −0.832 .. −0.440 (무릎 end-to-end) | knee −0.411 / ankle −0.854 |
| foot_bot | −0.914 | −0.919 |

→ before foot −0.495 m → after −0.914 m. 다리 정상 신전, 발 연결, 전신 비율 정상.

## 정량 분석 영향: **없음**
- `.osim` 파일 미수정. SO/Moco는 OpenSim이 spline을 정상 처리하므로 영향 0.
- fix는 Blender 씬 내 mesh 위치만 변경(렌더 전용).

## 산출물
- 스크립트: `scripts/viz_knee_fix/` (export_mesh_xforms.py, render_knee_fixed_skeleton.py, render_fixed_spine.py, tlfb_mesh_xforms.json, README)
- 검증 grid: `docs/images/literature_review/tlfb_knee_fix_grid.png`
  (BEFORE 접힘 / AFTER 골격 / AFTER 영상용 ES 6mm side·back)

## 영상 사용
`render_fixed_spine.py` = knee fix + 척추 ES 근육(6mm) → 전신 비율 정상 + ES column 표시 = 동영상 사용 가능.
**본 동영상 렌더는 사용자 승인 후 진행.**

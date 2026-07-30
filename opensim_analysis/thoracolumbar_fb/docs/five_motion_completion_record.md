# 5동작 파이프라인 완결 기록

**완결일**: 2026-07-30
**범위**: 맨몸 스쿼트 / 맨몸 스툽 / 박스 들기(20 kg) / 맨몸 보행 / 박스 운반(20 kg)
**해석**: OpenSim 4.6 Static Optimization, ThoracolumbarFB v2.0 armfix, 슈트 24 N·m 토크 커플
**논문 초안**: `docs/five_motion_paper_draft.md`
**발표자료**: `/data/opensim_results/SMA_suit_5motion_presentation.pptx` (+ `.pdf` 백업)

---

## 1. 최종 결과표

모든 값은 2026-07-30에 `*_StaticOptimization_activation.sto` 원본에서 재계산·검증함.
지표는 **ES peak** = 척추기립근 76개(IL / LTpL / LTpT) 중 해당 시점 최대 활성 근육.

| 동작 | 하중 | 지표 | 대표 시점 / 구간 | OFF (%) | ON (%) | Δ (%p) | Δ (%) |
|---|---|---|---|---:|---:|---:|---:|
| 맨몸 스쿼트 | 0 kg | ES peak | 가장 깊이 앉은 시점 (t = 2.03 s) | 18.30 | 9.61 | −8.69 | **−47.5** |
| 맨몸 스쿼트 | 0 kg | ES peak | 전주기 정점 | 23.11 | 14.45 | −8.66 | **−37.5** |
| 맨몸 스툽 | 0 kg | ES peak | 최대 굴곡 시점 (t = 2.56 s) | 28.04 | 19.12 | −8.92 | **−31.8** |
| 맨몸 스툽 | 0 kg | ES peak | 전주기 정점 | 31.90 | 22.96 | −8.94 | **−28.0** |
| 박스 들기 | 20 kg | ES peak | 최대 하중 시점 (t = 2.80 s) | 37.50 | 28.79 | −8.71 | **−23.2** |
| 박스 들기 | 20 kg | ES peak | 하중 구간 평균 (1.9–5.9 s) | 33.04 | 25.31 | −7.74 | −23.4 |
| 맨몸 보행 | 0 kg | ES peak | heel strike | 31.67 | 32.60 | **+0.93** | (+2.9) |
| 맨몸 보행 | 0 kg | ES peak | mid-stance | 24.08 | 28.34 | **+4.26** | (+17.7) |
| 맨몸 보행 | 0 kg | ES peak | toe-off / 전주기 | 35.08 | 34.11 | **−0.96** | (−2.7) |
| 박스 운반 | 20 kg | ES peak | mid-stance | 99.97 | 74.54 | **−25.42** | **−25.4** |
| 박스 운반 | 20 kg | ES peak | 전주기 (포화로 저평가) | 100.00 | 88.61 | −11.39 | −11.4 |
| 박스 운반 | 20 kg | ES_mean | 전주기 | 18.94 | 13.76 | −5.18 | **−27.4** |

보조 지표 ES_mean(전주기 정점 기준) 상대 감소율: 스쿼트 −36.1 %, 스툽 −27.5 %, 박스 들기 −9.0 %(하중 구간 한정 −28.1 %), 보행 −40.8 %(baseline 3.72 %로 비율 불안정), 운반 −27.4 %.

**핵심 관찰**: 절대 감소량이 스쿼트 −8.69, 스툽 −8.92, 박스 들기 −8.71 %p로 8.7–8.9 %p에 수렴. 고정 24 N·m 보조의 절대 기여는 동작에 무관하게 일정하고, 상대 감소율 차이는 baseline(요구 토크) 차이에서 발생.

---

## 2. 산출물 경로

### 2.1 동작 데이터 (.mot)

| 동작 | 경로 |
|---|---|
| 맨몸 스쿼트 | `/data/squat_results/` 하위 (suit_sweep 입력 kinematics) |
| 맨몸 스툽 | `/data/opensim_results/stoop_synthetic_v5.mot` |
| 박스 들기 | `/data/opensim_results/stoop_table_box_v1.mot`, `table_box_lift_v2.mot` |
| 맨몸 보행 | `/data/gait_results/` 하위 리타겟 결과 |
| 박스 운반 | `/data/carry_results/` 하위 |

### 2.2 SO 결과 (.sto) — 논문 수치의 원본

| 동작 | 슈트 OFF | 슈트 ON (24 N·m) |
|---|---|---|
| 맨몸 스쿼트 | `/data/squat_results/suit_sweep/F0/squat_F0_StaticOptimization_activation.sto` | `.../F200/squat_F200_StaticOptimization_activation.sto` |
| 맨몸 스툽 | `/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto` | `/data/stoop_results/suit_sweep_v5/F200/` |
| 박스 들기 | `/data/stoop_results/box_stoop_so/B_off/so_B_off_StaticOptimization_activation.sto` | `.../B_on/so_B_on_StaticOptimization_activation.sto` |
| 맨몸 보행 | `/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto` | `/data/gait_results/gait_on_tight/...` |
| 박스 운반 | `/data/carry_results/carry_off/so_StaticOptimization_activation.sto` | `/data/carry_results/carry_on/...` |

박스 들기에는 무부하 참조 조건 `box_stoop_so/B_noload/` 가 함께 존재한다.
보행에는 표준 reserve 조건 `gait_off/`, `gait_on/` 이 민감도 비교용으로 보존되어 있다.
`_force.sto` 는 같은 디렉터리에 병존하며 reserve 점검에 사용한다.

### 2.3 동영상 (mp4) — 모두 `/data/opensim_results/`

`squat_public_video.mp4` · `stoop_public_video.mp4` · `box_stoop_suit_video.mp4` · `gait_suit_video.mp4`(+`_loop3`) · `carry_walk_suit_video.mp4`
PowerPoint 임베드용 baseline/yuv420p 변환본과 포스터 프레임: `/data/opensim_results/ppt_media/{squat,stoop,box,gait,carry}_ppt.mp4`, `poster_*.png`

### 2.4 이미지

| 용도 | 경로 |
|---|---|
| 논문 figure (흑백 인쇄, 400 dpi) | `docs/images/paper_five_motion/fig3~fig6_*.png` |
| 발표자료 슬라이드 검증 grid | `docs/images/presentation/deck_slides_*.png` |
| 동작별 키프레임 | `docs/images/literature_review/`, `docs/images/phase2_box/` |
| 발표용 키프레임 재구성 | `/data/opensim_results/ppt_media/kf_{squat,stoop}.png` |

### 2.5 문서·발표자료

- 논문 초안: `docs/five_motion_paper_draft.md`
- 선행 Phase 1a 논문(별개): `docs/phase1a_paper_draft_v2.md`
- 발표자료: `/data/opensim_results/SMA_suit_5motion_presentation.pptx` (33장, 영상 5종 임베드 4.48 MB)
- 발표자료 PDF 백업: `/data/opensim_results/SMA_suit_5motion_presentation.pdf` (폰트 임베드, 레이아웃 보존 — 영상은 별도 재생)

---

## 3. 재현 절차

**환경**: `/home/sysop/miniconda3/envs/opensim/bin/python`, OpenSim 4.6, 렌더 시 `DISPLAY=:1`

**공통 모델**: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim`

**스크립트** (모두 `opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/`):

| 목적 | 스크립트 |
|---|---|
| 스쿼트 SO | `run_squat_so.py` |
| 박스 들기 SO | `run_box_stoop_so.py` |
| 박스 들기 분석 | `analyze_box_stoop_so.py` |
| 보행 리타겟 | `gen_gait_retarget.py` |
| 보행 SO (표준 / tight) | `gait_so.py` / `gait_so_tight.py` |
| 보행 분석 | `analyze_gait_so.py` |
| 운반 동작 생성 | `gen_carry_walk.py` |
| 운반 SO / 분석 | `carry_so.py` / `carry_analyze.py` |
| armfix 회귀 검증 | `armfix_regression.py` |
| M1 견갑 회귀 검증 | `run_m1_regression.py` |
| 논문 figure 생성 | `make_paper_figures.py` |
| 발표자료 생성 | `build_presentation.py` (+ `make_ppt_figures.py`, `make_ppt_keyframes.py`) |

**논문 수치 재검증**: `.sto`에서 전 수치를 재산출하는 검증 스크립트 로직은 `make_paper_figures.py`의 `load()`/ES 정의와 동일하다(ES = `IL_*` + `LTpL*` + `LTpT*`, n = 76).

**발표자료 재생성 + QA**:
```bash
python build_presentation.py
soffice --headless --convert-to pdf SMA_suit_5motion_presentation.pptx
pdftoppm -jpeg -r 110 deck.pdf slide          # 전 슬라이드 육안 점검
python -c "import zipfile;print([n for n in zipfile.ZipFile('deck.pptx').namelist() if n.endswith('.mp4')])"
```

---

## 4. 확립된 표준

1. **reserve tight + 활성 점검** — 저부하 동작에서는 척추 reserve `optimal_force`를 5 N·m로 제한하고 `_force.sto`에서 실제 흡수량을 확인한다. 점검 없이는 ES가 3배 과소평가되고 슈트 효과의 존재 여부까지 왜곡된다(§5 참조).
2. **ES peak를 주 지표로** — 76근육 중 최대 활성 근육. ES_mean은 비활성 근육 희석으로 부담을 과소 표현하므로 강건성 확인용 보조 지표로만 병기한다.
3. **생성/검증 분리** — 검증자에게 수치와 설계 의도를 제공하지 않고 렌더 이미지만으로 판정하게 한다. 자가 검증의 확증 편향("수치가 맞으니 그림도 맞다")을 구조적으로 차단.
4. **렌더 경로별 viz 수정 점검** — 시각화 전용 수정(손목 잠금 해제, 어깨대 미러 등)은 렌더 경로마다 개별 적용 여부를 확인한다. 한 경로에만 적용되면 산출물 간 불일치가 발생한다.
5. **전환 구간 촘촘 시퀀스 + 각도 시계열** — 자세 전환 구간은 프레임 간격을 좁혀 시퀀스를 뽑고, 관절 각도 시계열을 함께 확인해야 불연속·역방향 회전을 잡을 수 있다.
6. **viz-mirror 범위 = 어깨대 전체** — 좌우 대칭 처리는 상완만이 아니라 쇄골·견갑을 포함한 어깨대 전체에 적용한다.
7. **고활성 동영상 색 대비** — 활성도가 높은 구간이 이어지는 동영상은 windowed clim(하한 > 0)을 써야 색 차이가 보인다.
8. **발표자료 영상은 baseline/yuv420p 임베드** — `-profile:v baseline -pix_fmt yuv420p -movflags +faststart`로 변환 후 `add_movie(poster_frame_image=...)`로 임베드. 포스터 프레임 없으면 검은 사각형이 된다.

---

## 5. 미해결 / 이월 항목

### 5.1 ⭐ reserve 설정 혼재 (신규 발견, 2026-07-30)

`.osim`과 실행 스크립트를 전수 확인한 결과, tight reserve는 **5동작 전체가 아니라 보행·운반에만** 적용되어 있다.

| 동작 | 척추 reserve `optimal_force` | 실제 흡수 최대 (OFF) |
|---|---:|---:|
| 맨몸 스쿼트 | 100 N·m (표준) | 37.9 N·m |
| 맨몸 스툽 | 100 N·m (표준) | 40.1 N·m |
| 박스 들기 | 100 N·m (표준) | 58.6 N·m |
| 맨몸 보행 | **5 N·m (tight)** | 1.0 N·m |
| 박스 운반 | **5 N·m (tight)** | 1.7 N·m |

tight 설정은 보행 해석에서 문제를 발견한 뒤 도입되어 그 이후 해석에만 적용되었다.

**영향**: 동작 간 **절대** ES 활성도를 직접 비교할 수 없고, 표준 설정 3개 동작의 절대 활성도는 과소추정일 가능성이 높다. 자체 민감도 분석(`docs/suit_sweep_reserve_comparison.md`)은 stoop에서 reserve를 조이면 상대 감소율이 28.12 % → 21.25 %(−6.87 %p)로 이동함을 보고한다. 따라서 **부하–효과 단조 경향은 두 설정이 혼재된 비교**이다.
각 동작 내부에서는 OFF/ON이 동일 설정이므로 개별 동작의 슈트 효과 방향·존재 여부는 유효하다.

**조치 필요**: 전 동작 tight reserve 재해석 후 단조 경향 재확인. (본 완결 시점에는 "새 해석 실행 금지" 지시에 따라 미수행)

### 5.2 좌측 어깨 자유도

`shoulder_elv_l`의 z성분 미러가 미완이고 해당 좌표 ROM이 음수 전용으로 정의되어 있어, 팔을 든 대칭 자세에서는 시각화 단계 미러 처리에 의존한다. 5동작은 영향권 밖이나, **다관절(어깨·팔꿈치) 보조 해석 착수 전 정량 진단이 필요**하다.

### 5.3 스쿼트 조건 외부 대조 부재

대응 선행 연구(Hasenmaier 2026)가 squat 조건에서 보조 수준 간 유의차를 보고하지 않아 외부 대조가 불가능하다. 본 연구 스쿼트 값(−37.5 ~ −47.5 %)은 5동작 중 감소율이 가장 커 **실측 EMG 검증의 최우선 대상**이다.

### 5.4 기타

- 성인 남성 단일 체형 — 성별·연령 확장 미수행
- 보행·운반 GRF는 타 피험자 실측값 (효과 차이는 견고, 절대값 해석 주의)
- 운반 조건 최대 활성 근육 100 % 포화 → 보고값은 하한
- L5/S1 압축력 미산출 — Hu et al.(2026)과 동일 지표 대조를 위해 필요
- 논문 Figure 1(모델·슈트 개념도), Figure 2(파이프라인) 미작성 — 발표자료에 네이티브 도형으로만 존재

---

## 6. 문헌 오독 정정 이력 (2026-07-30)

### 6.1 무엇이 잘못되었나

내부 문헌 정리 문서가 Hasenmaier et al. (2026)의 **"10–27 % MVC"를 상대 감소율로 기록**했다. 원문에서 이 값은 **%MVC 절대 포인트 감소**이다.

**원문 확인값** (verbatim, stoop):

| 조건 | ES 활성도 |
|---|---:|
| 1) 외골격 미착용 | 69.8 %MVC |
| 2) 착용 0/0 % | 59.2 %MVC |
| 3) 착용 50/20 % | 50.7 %MVC |
| 4) 착용 100/60 % | **42.4 %MVC** |

→ **stoop 상대 감소율 = −39.3 %**
→ **squat**: 원문 "there were no significant results between the individual levels" → 상대 감소율 인용 불가

Hu et al. (2026)의 −14.9~28.6 %는 **등 근육 능동 모멘트**, −5.5~9.3 %는 **L5/S1 압축력**이며 근육 활성도가 아니다. 지표가 달라 ES 활성도와 직접 대조할 수 없다.

### 6.2 결론이 어떻게 바뀌었나

| | 정정 전 (오독 기반) | 정정 후 (원문 확인) |
|---|---|---|
| 스툽 대조 | 본 연구 23~32 %가 선행 10~27 % "범위 안" | 본 연구 28~32 %가 선행 **−39.3 %보다 작음** → 본 연구가 더 보수적 |
| 스쿼트 대조 | 본 연구 37~47 %가 선행 10~17 %를 **초과** | 선행이 유의차 미보고 → **대조 불가** |

### 6.3 정정이 반영된 위치

| 파일 | 조치 |
|---|---|
| `docs/hu2026_squat_validation_input.md` | R1 절에 정정 박스 추가, 오독 항목 취소선 처리 |
| `docs/validation_protocol_v2.md` | 정정 주석 삽입 |
| `docs/biomech_reference/squat_lift_literature.md` | 정정 주석 삽입 |
| `docs/plan_v3_videos_main.md` | 정정 주석 삽입 |
| `docs/CONTINUATION_GUIDE.md` | "10-27 % MVC" 항목에 단위 설명 추가 |
| `scripts/viz_knee_fix/make_validity_grid.py` | 파일 상단 경고 헤더 — 생성 그림 사용 금지 |
| `scripts/viz_knee_fix/make_box_status_grid.py` | 동일 |
| 발표자료 S29 | 슬라이드 전면 재작성 (제목 포함) |
| 발표자료 S31 | "선행 대비 큼" 한계 항목 삭제 → "외부 대조 불가"로 교체 |
| `docs/five_motion_paper_draft.md` §4 | 정정된 대조로 신규 작성 |

### 6.4 기존 Phase 1a 초안에 대한 수정 제안 (미반영 — 사용자 확인 필요)

`docs/phase1a_paper_draft_v2.md`는 별개 논문이므로 직접 수정하지 않았다. 다음 2개 위치가 지표를 혼동하고 있어 수정을 제안한다.

**(a) §4.1 (L166)** — 현재:
> "Our Phase 1a result at 24 N·m: **28.0–28.5% ES reduction** ... This matches the upper range of Hu et al. [2026] at their highest assist level within 0.6 percentage points — a level of quantitative agreement consistent with independent replication..."

문제: Hu et al.의 14.9–28.6 %는 **등 근육 능동 모멘트** 감소이지 근육 활성도 감소가 아니다. 서로 다른 물리량을 "0.6 %p 이내 일치"로 서술하는 것은 부적절하다.

제안: 수치 일치 주장을 삭제하고 "different quantities (muscle activation vs. active moment); the agreement is in direction and order of magnitude, not a like-for-like match"로 완화. Table 3의 열 제목도 "ES Reduction" → "Reported reduction (metric differs by study)"로 변경하고 지표를 열에 명시.

**(b) §6.5 (L248)** — 동일한 "quantitative agreement ... provides independent cross-study external validity" 서술. 같은 이유로 완화 필요.

**(c) 추가 제안** — Hasenmaier et al. (2026)은 Phase 1a의 stoop 조건과 직접 대조 가능한 유일한 문헌이므로(stoop 상대 −39.3 %), §4에 추가하면 대조의 질이 올라간다.

---

## 7. 5동작 시리즈 타임라인

| 순서 | 동작 | 완료 | 슈트 효과 (대표값) |
|---|---|---|---|
| 1 | 맨몸 스쿼트 | 2026-06-17 | −47.5 % (최대 하강 시점) |
| 2 | 맨몸 스툽 | 2026-06-14 | −31.8 % (최대 굴곡 시점) |
| 3 | 박스 들기 20 kg | 2026-07-21 | −23.2 % (최대 하중 시점) |
| 4 | 맨몸 보행 | 2026-07-27 | ≈ 0 (구간별 |ΔES| ≤ 4.3 %p) |
| 5 | 박스 운반 20 kg | 2026-07-28 | −25.4 %p (mid-stance) |
| — | 발표자료 33장 | 2026-07-29 | 영상 5종 임베드 |
| — | 논문 초안 + 완결 기록 | 2026-07-30 | 본 문서 |

박스 들기는 v3–v11b에 걸친 12회 시도 끝에 수렴하였으며, 그 과정에서 얻은 교훈(biomechanics reference 우선, 생성/검증 분리, 자세 배분 정정)이 §4 표준의 근거가 되었다.

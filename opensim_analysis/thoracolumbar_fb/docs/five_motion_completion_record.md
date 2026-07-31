# 5동작 파이프라인 완결 기록

**완결일**: 2026-07-30 (초판) · 2026-07-31 조건 통일 재해석 · **2026-07-31 최종 마감**
**범위**: 맨몸 스쿼트 / 맨몸 스툽 / 박스 들기(20 kg) / 맨몸 보행 / 박스 운반(20 kg)
**해석**: OpenSim 4.6 Static Optimization, 단일 모델 `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix` (전체 해시 `dc6c217f8fb6`), 척추 reserve opt 5 N·m, 슈트 24 N·m 토크 커플
**논문 최종본**: `docs/five_motion_paper.docx` / `.pdf` — **20쪽 A4, 그림 7 임베드, 네이티브 표 11, TOC+쪽번호, 폰트 임베드**
**논문 초안(md)**: `docs/five_motion_paper_draft.md`
**표기 규칙 단일 소스**: `scripts/viz_knee_fix/paper_numbers.py` — 논문·발표자료가 모두 이 모듈에서 수치를 읽는다
**발표자료**: `/data/opensim_results/SMA_suit_5motion_presentation.pptx` (+ `.pdf` 백업)

> ⚠️ **2026-07-31 개정 사유**: 조건 전수 감사에서 동작마다 기저 모델과 reserve 설정이 달랐음을 발견하여
> 5동작을 완전히 동일한 조건으로 재해석하였다. **초판(2026-07-30)의 수치는 폐기되었다.**
> 상세는 §1, §5.1, §6 참조.

---

## 1. 최종 결과표 (완전 통일 조건)

주 지표는 **슈트 작동창 ES peak 평균** — 슈트 토크가 최대치의 90 % 이상인 구간에서
프레임별 최대 활성 ES 근육 값의 평균. 창은 ON 조건 토크 프로파일로 정의하고 OFF에 동일 적용.

| 동작 | 하중 | OFF (%) | ON (%) | Δ (%p) | Δ (%) | 척추 reserve (N·m) |
|---|---|---:|---:|---:|---:|---:|
| 맨몸 스쿼트 | 0 kg | 60.37 | 37.88 | −22.49 | **−37.3** | 1.11 |
| 맨몸 스툽 | 0 kg | 65.30 | 43.74 | −21.56 | **−33.0** | 0.94 |
| 박스 들기 | 20 kg | 71.02 | 55.03 | −15.99 | **−22.5** | 1.63 |
| 맨몸 보행 | 0 kg | 22.41 | 27.20 | +4.79 | **+21.4** | 1.01 |
| 박스 운반 | 20 kg | 90.88 | 65.75 | −25.13 | **−27.7** | 1.70 |

**보조 지표 (민감도 분석)**

| 동작 | (a) 전주기 peak | (b) 주 지표 | (c) ES mean 창평균 |
|---|---:|---:|---:|
| 맨몸 스쿼트 | −35.1 % | **−37.3 %** | −39.0 % |
| 맨몸 스툽 | −34.2 % | **−33.0 %** | −31.1 % |
| 박스 들기 | −32.1 % | **−22.5 %** | −34.2 % |
| 맨몸 보행 | −2.8 % | **+21.4 %** | −12.0 % |
| 박스 운반 | −11.4 % | **−27.7 %** | −33.3 % |

**부하 순 단조 경향**: (b) 주 지표에서만 성립. (a)·(c)에서는 성립하지 않음.
→ "단조성으로 슈트 모델이 검증됨"이라는 서술은 폐기.

**⭐ 맨몸 보행은 감소가 아니라 재분배**
- 총량 −17.38 %p 감소 (감소 37개 / 증가 10개 / 무변화 29개)
- 최대 활성 근육 +21.4 %, 집중도(peak/mean) 11.68 → 16.10
- 장늑근(IL) −90.9 % · 최장근 요추부(LTpL) **+28.5 %** · 최장근 흉추부(LTpT) −5.7 %
- 기전: 보행은 시상면 요구가 작아 24 N·m가 과충족 → IL 비활성화. 그러나 축회전 11.63°·측굴 10.87°의
  면외 요구가 남아 LTpL_L5로 이전. 스툽은 면외 운동이 0.00°라 재분배 없음, 운반은 20 kg가 지배적이라 보조가 우세.
- 유해 여부는 본 데이터로 판단 불가 → 실측 EMG 검증 필요

**⭐ 문헌 정합** — 통일 조건 스툽 미착용 ES peak **70.37 %** ↔ Hasenmaier et al. 2026 실측 **69.8 %MVC** (0.6 %p 차)
표준 reserve 시절 값(31.9 %)은 문헌 범위(40–80 %MVC) 미달 → tight 설정이 옳았다는 독립 근거

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
| 맨몸 스쿼트 | `/data/tight_unified/squat_off/so_StaticOptimization_activation.sto` | `/data/tight_unified/squat_on/...` |
| 맨몸 스툽 | `/data/tight_unified/stoop_off/so_StaticOptimization_activation.sto` | `/data/tight_unified/stoop_on/...` |
| 박스 들기 | `/data/tight_unified/box_off/so_StaticOptimization_activation.sto` | `/data/tight_unified/box_on/...` |
| 맨몸 보행 | `/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto` | `/data/gait_results/gait_on_tight/...` |
| 박스 운반 | `/data/carry_results/carry_off/so_StaticOptimization_activation.sto` | `/data/carry_results/carry_on/...` |

이전 조건의 산출물은 대조용으로 보존되어 있다: 표준 reserve + 개별 기저 모델(`/data/squat_results/`, `/data/stoop_results/`), reserve만 통일한 중간 단계(`/data/tight_rerun/`), 보행 표준 reserve(`/data/gait_results/gait_off|on/`).
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
| **5동작 통일 재해석 (현행)** | **`rerun_unified_all.py`** |
| reserve만 통일한 중간 단계 | `rerun_tight_all.py` |
| **해석 조건 전수 감사** | **`audit_conditions.py`** |
| 통일 결과 분석·대조 | `analyze_tight_unified.py` |
| 보행 재분배 분석 | `analyze_gait_redistribution.py` |
| (구) 스쿼트 SO | `run_squat_so.py` |
| (구) 박스 들기 SO | `run_box_stoop_so.py` |
| 보행 리타겟 | `gen_gait_retarget.py` |
| 보행 SO (표준 / tight) | `gait_so.py` / `gait_so_tight.py` |
| 보행 분석 | `analyze_gait_so.py` |
| 운반 동작 생성 | `gen_carry_walk.py` |
| 운반 SO / 분석 | `carry_so.py` / `carry_analyze.py` |
| armfix 회귀 검증 | `armfix_regression.py` |
| M1 견갑 회귀 검증 | `run_m1_regression.py` |
| 논문 figure 3–7 | `make_paper_figures.py` |
| 논문 figure 1–2 (개념도) | `make_paper_figures12.py` |
| **논문 완성본 docx/pdf** | **`build_paper_docx.py`** (+ `docx_kit.py`) |
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
8. **⭐ 다동작 비교는 조건 통일을 사전에 강제** — 동작을 순차 진행하면 모델·설정이 갈라진다. (i) 해석 조건 매니페스트에 명시하고 실행 스크립트가 이를 참조, (ii) 새 동작 착수 시 `audit_conditions.py`로 기존 동작과의 일치를 자동 점검하고 다른 항목은 '의도된 차이'로 명시 기록해야 통과, (iii) 각 결과 디렉터리에 기저 모델의 reserve 제외 해시를 남긴다.
9. **⭐ 평가 지표는 결과 확인 전에 사전 정의** — 지표만 바꿔도 감소율이 10 %p 이상, 보행은 부호까지 달라진다. 포화·최대근육 전환 가능성을 사전 점검하고 복수 지표를 병기한다.
10. **⭐ 병렬 SO는 BLAS 스레드를 1로 제한** — `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. 미설정 시 프로세스마다 9코어를 잡아 스핀락 경합으로 약 1000× 느려진다(19시간에 27 % 진행). 또한 `setsid`로 분리 실행해야 셸 종료에 살아남는다.
11. **발표자료 영상은 baseline/yuv420p 임베드** — `-profile:v baseline -pix_fmt yuv420p -movflags +faststart`로 변환 후 `add_movie(poster_frame_image=...)`로 임베드. 포스터 프레임 없으면 검은 사각형이 된다.

---

## 5. 미해결 / 이월 항목

### 5.1 ✅ [해소됨] reserve 설정 및 기저 모델 혼재

**발견 (2026-07-30~31)**: 조건 전수 감사(`audit_conditions.py`)에서 동작마다 조건이 갈라져 있음을 확인하였다.

| 항목 | 스쿼트·스툽 | 박스 | 보행·운반 |
|---|---|---|---|
| 기저 모델 | `modified` | `M1scap` | `M1scap_armfix` |
| CoordinateCoupler | 4개 유지 | 0 | 0 |
| M1 견갑 | 미적용 | 적용 | 적용 |
| 좌팔 축 수정 | 미적용 | 미적용 | 적용 |
| 척추 reserve opt | 100 N·m | 100 N·m | 5 N·m |
| 실제 흡수 척추 reserve | 37.9 N·m | 58.6 N·m | 1.0 / 1.7 N·m |

그 밖에 저역통과 필터(합성 −1 vs 실측 6 Hz), 샘플링(26.7~60 Hz), **박스 들기만 지면반력 부재**도 확인되었다.
앞의 세 항목은 의도된 차이가 아니었고, 뒤의 세 항목은 동작 특성상 의도된 차이이다.

**조치 (2026-07-31)**: 스쿼트·스툽·박스를 `M1scap_armfix` + tight reserve로 재실행하여 5동작이
**완전히 동일한 모델 파일(전체 해시 `dc6c217f8fb6`)**을 공유하도록 통일하였다. 척추 reserve 실측값은
5동작 0.94–1.70 N·m로 균일하다. → **이월 항목 해소.**

**변화 크기**: 절대 baseline은 크게 이동(스쿼트 +7.7 %p), 주 지표 상대값은 0.6–3.7 %p 이동.
스쿼트가 회귀 유계(~2 %p)를 넘은 3.7 %p는 쿠플러 제약이 규정된 양팔 전방 85° 자세를 덮어쓰고 있었기
때문이며(위반량 우 39.6°·좌 130.4°, 스툽은 0.000°), 통일본이 의도한 동작을 정확히 반영한 것이다.

**폐기된 서술**: "절대 감소량 8.7–8.9 %p 일정", "단조성으로 슈트 모델 검증됨", "스쿼트 47 % 감소",
"정상 보행에 무영향" — 전 문서에서 제거·교체 완료.

### 5.2 좌측 어깨 자유도

`shoulder_elv_l`의 z성분 미러가 미완이고 해당 좌표 ROM이 음수 전용으로 정의되어 있어, 팔을 든 대칭 자세에서는 시각화 단계 미러 처리에 의존한다. 5동작은 영향권 밖이나, **다관절(어깨·팔꿈치) 보조 해석 착수 전 정량 진단이 필요**하다.

### 5.3 스쿼트 조건 외부 대조 부재

대응 선행 연구(Hasenmaier 2026)가 squat 조건에서 보조 수준 간 유의차를 보고하지 않아 외부 대조가 불가능하다. 본 연구 스쿼트 값(−37.5 ~ −47.5 %)은 5동작 중 감소율이 가장 커 **실측 EMG 검증의 최우선 대상**이다.

### 5.4 보행 재분배의 유해성 미확인 (신규)

총량은 −17.38 %p 감소하나 최대 활성 근육은 +21.4 % 증가하고 최장근 요추부에 집중된다.
어느 쪽이 지배적인지 본 데이터로 판단 불가 → **실측 EMG 검증 필요**. 재분배 기전의 해석도
활성도 패턴과 운동학에서 도출한 것이며 모멘트 암 분해로 직접 확인하지 않았다.
설계 함의로 **보행 구간 토크 저감·차단 제어**의 검토 필요가 제기되나, 이는 검증된 결론이 아니라 가설이다.

### 5.5 기타

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

## 7. 표기 규칙 및 최종 검증

### 7.1 수치 표기 규칙 (전 문서 공통)

파생값을 미반올림 원값으로 계산하고 baseline만 반올림해 인쇄하면, 독자가 인쇄된 숫자로
재계산했을 때 결과가 어긋난다(실제 7곳 발생). 이를 막기 위해 규칙을 정하고
`scripts/viz_knee_fix/paper_numbers.py` 한 곳에서 강제한다.

| 항목 | 규칙 |
|---|---|
| 활성도(OFF/ON, %) | 소수 2자리 |
| 절대차 Δ (%p) | **인쇄된 2자리 값의 차**, 소수 2자리 |
| 상대 변화율 (%) | **인쇄된 2자리 값에서 계산**, 소수 1자리 |
| reserve (N·m) | 소수 2자리 |
| 음수 기호 | U+2212 (`−`) 통일 |

→ 인쇄된 숫자만으로 모든 파생값을 재현할 수 있다. 논문·발표자료·초안·완결기록이
같은 값을 같은 표기로 쓰는지 자동 대조하여 잔존 0건을 확인하였다.

**규칙 적용으로 바뀐 값**: 박스 운반 주지표 −27.6 → **−27.7 %**(headline), 보행 ES mean
−11.9 → −12.0 %, 보행 전주기 peak −2.7 → −2.8 %, tight reserve Δ −0.96 → −0.97 %p.

### 7.2 그림 규격

전 그림의 캔버스 폭을 논문 배치 폭과 1:1로 맞춰 **선언 폰트 크기 = 인쇄 폰트 크기**가
되게 하였다(이전에는 캔버스가 커서 9 pt가 인쇄 시 6.9–8.0 pt로 축소되었다).
한글·라틴·기호를 단일 폰트 패밀리로 렌더해 실효 크기 차이를 제거하였다.

| 그림 | 캔버스 = 배치 폭 | 9 pt의 인쇄 크기 |
|---|---|---|
| Figure 1·2·3·6 | 16.4 cm | 9.0 pt |
| Figure 4·7 | 16.4 cm | 10.1 pt |
| Figure 5 | 12.5 cm | 10.1 pt |

### 7.3 독립 검증 이력

생성 주체와 분리된 검증자가 렌더 이미지만으로 판정(수치·의도 미제공).

| 라운드 | 차단 | 주요 지적 |
|---|---|---|
| 1 | 7 | 빈 페이지, 그림 번호 역순, 그림 미인용, 프레임 총계 691↔658, 범례가 데이터 가림, 표 페이지 분할, 인셋 판독 불가 |
| 2 | 1 | 절대 감소량 범위가 Table 6과 모순 |
| 3 | 0 (GO) | — |
| 4 (표기 통일 후) | 2 | Figure 5가 표와 다른 값, Figure 6(c) 텍스트 절단 |
| 5 (최종) | **0 (GO)** | 파생값 34개 전수 재계산 일치, 두 결함 수정 확인 |

---

## 8. 이번 여정에서 발견·정정한 항목 (전체 이력)

| # | 발견 | 성격 | 조치 |
|---|---|---|---|
| 1 | **문헌 오독** — Hasenmaier "10–27 % MVC"를 상대 감소율로 기록 (실제는 %MVC 절대 포인트) | 내용 오류 | 원문 verbatim 재확인, 파급 7곳 정정. stoop 상대 감소율 −39.3 % 확정 |
| 2 | **지표 혼동** — Hu et al.의 모멘트·압축력 감소를 활성도 감소와 등치 | 내용 오류 | Phase 1a 초안 §4.1 정량 일치 주장 철회, §4.1b 활성도 기반 대조 신설 |
| 3 | **reserve 설정 혼재** — tight가 보행·운반에만 적용 (스쿼트·스툽·박스는 표준) | 조건 불일치 | 전 동작 tight 재해석 |
| 4 | **기저 모델 이질성 3건** — 쿠플러 4개 유지 / M1 견갑 / armfix가 동작마다 다름 | 조건 불일치 | 전 동작을 `M1scap_armfix`로 통일 (해시 `dc6c217f8fb6`) |
| 5 | **재실행 자체의 오류** — 스쿼트·스툽을 `modified_no_coupler`로 재실행 (원본은 `modified`) | 자체 오류 | 기저 해시 대조로 발견, 올바른 기저로 재시작 |
| 6 | **쿠플러가 규정 자세를 덮어씀** — 스쿼트 양팔 전방 85°가 구현되지 않음 (위반량 좌 130.4°) | 이전 결과 오류 | 통일본이 의도한 동작을 정확히 반영 — 교정으로 처리 |
| 7 | **스레드 경합** — 병렬 SO가 19시간에 27 %만 진행 | 실행 성능 | `OMP/OPENBLAS_NUM_THREADS=1`로 약 1000× 개선 |
| 8 | **표기 편차** — 파생값을 미반올림으로 계산해 인쇄값과 불일치 7곳 | 표기 오류 | `paper_numbers.py` 단일 소스로 규칙 강제 |
| 9 | **그림 폰트 축소** — 9 pt 선언이 인쇄 시 6.9–8.0 pt | 규격 미달 | 캔버스 폭을 배치 폭과 1:1로 |

---

## 9. 다음 단계 착수 전 확인 사항

1. **⭐ 다관절 해석 착수 전 — 좌측 어깨 elv 자유도 정량 진단 필수**
   `shoulder_elv_l`의 z성분 미러가 미완이고 해당 좌표 ROM이 음수 전용으로 정의되어 있다.
   본 5동작은 영향권 밖이었으나, 어깨 보조를 포함하면 직접 영향을 받는다.
   진단 없이 착수하면 §8의 4·6번(모델 이질성·자세 덮어쓰기)과 같은 문제가 재발할 수 있다.

2. **⭐ 투고 전 — 선행 논문 2편 원문 직접 확인**
   현재 대조는 **초록 verbatim**에 근거한다. 초록만으로는 다음이 불확실하다.
   - Hasenmaier et al. 2026: MES 정규화 기준(MVC 측정 자세), 전극 위치, 보고값이 구간 평균인지 정점인지
   - Hu et al. 2026: "back muscle active moment"의 산출 정의, 시간 평균 구간
   본 연구의 ES peak(76근육 최대)와 대응 관계를 확정하려면 본문·방법 절 확인이 필요하다.
   확인 전까지 §4의 정합 서술은 "크기 수준의 대조"로 한정한다.

3. **표기 규칙 유지** — 새 수치를 추가할 때 `paper_numbers.py`를 거치지 않으면 §7.1 규칙이 깨진다.

4. **조건 통일 자동 점검** — 새 동작 착수 시 `audit_conditions.py` 실행이 필수 (§4-8 표준).

---

## 10. 5동작 시리즈 타임라인

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

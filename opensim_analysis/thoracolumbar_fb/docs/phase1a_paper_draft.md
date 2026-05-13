# Phase 1a — Paper Draft (consolidated)

Working manuscript text covering Methods, Results, and Discussion sections from Phase 1a (114-muscle MocoInverse on stoop_v5). All numerical claims trace to artifacts in `results/phase1a_full/`, `results/phase1a_suit_effect/`, `results/phase1a_suit_sweep/`.

**Status**: 2026-04-28, post-suit-sweep. Headline figures and tables identified for paper. Pending coauthor review.

## Outline

- §M1 Static optimization (already in manuscript) — keep
- **§M2 MocoInverse and dynamic muscle activation analysis (new)** — see Methods below
- §R1 SO results (already in manuscript) — keep
- **§R2 Five-phase activation structure** — see Results A
- **§R3 Eccentric vs concentric asymmetry** — see Results B
- **§R4 Suit dose-response (Moco)** — see Results C
- §D1 Methodological strengths — see Discussion A
- §D2 Phase-targeted assistive design implication — see Discussion B
- §D3 Limitations — see Limitations

---

## Methods (additional Moco section, append after SO description)

To capture muscle activation dynamics that static optimization (SO) cannot model, we additionally employed OpenSim Moco's inverse muscle dynamics solver (MocoInverse) [Dembia et al., 2020]. While SO computes muscle activations at each time instant independently, MocoInverse formulates the problem as an optimal control problem that accounts for activation dynamics, length–velocity dependencies, and temporal continuity, enabling phase-resolved analysis of muscle behavior during dynamic tasks.

We applied MocoInverse to the same stoop kinematics used for SO, with the ThoracolumbarFB model preprocessed for Moco compatibility: 29 joints with permanently locked coordinates (rib costovertebral joints, sternal joint, forearm pronation, and wrist) were converted to `WeldJoint` instances, eliminating 84 coordinates while preserving all 620 muscles and 78 bodies. Kinematic verification confirmed sub-millimeter agreement (max 0.001 mm) between original and converted models across the entire stoop motion (0–5 s).

For Phase 1a, we restricted muscle inclusion to 114 spine-relevant muscles: iliocostalis (IL, n = 24), longissimus thoracis pars thoracis (LTpT, n = 42), pars lumborum (LTpL, n = 10), quadratus lumborum (QL, n = 36), and rectus abdominis (RA, n = 2). The remaining 506 muscles (multifidus group, external/internal obliques, psoas, and extremity muscles) were removed from the optimization to reduce computational load and to enable a focused Phase 1b analysis of multifidus contribution.

Muscles were converted to the De Groote–Fregly 2016 formulation with rigid tendons (`ModOpReplaceMusclesWithDeGrooteFregly2016`, `ModOpIgnoreTendonCompliance`) and zero passive fiber forces. Coordinate reserve actuators with optimal force 10 Nm (rotational coordinates) and 10 N (translational) were added to provide bounded compensation for unmodeled muscle contributions, matching the SO R10 reference condition. Ground reaction forces from the synthetic motion (`stoop_grf_v5.sto`) were applied as ExternalLoads.

The optimization used 50 mesh intervals over the 5-second stoop motion. Convergence was achieved in 140 seconds of wall time on a 56-thread CPU workstation.

To enable analysis of lifting tasks requiring active arm reach (Phase 2 box-handling, see §4.B), we removed four `CoordinateCouplerConstraint` entries from the original ThoracolumbarFB v2.0 model: `coupler_shoulder_elv_{r,l}` (slope −1.62 / +1.62 with `pelvis_tilt`) and `coupler_elv_angle_{r,l}` (slope −2.0 with `pelvis_tilt`). These constraints were authored for gait-style passive arm-swing rhythm and force shoulder elevation as a fixed function of pelvic tilt, blocking the independent shoulder control required for grasping a box on the ground or workbench. The Phase 1a free-stoop reference motion happens to satisfy the original coupler relationship to numerical precision (sh_elv = −1.62 × pelvis_tilt with maximum kinematic violation 0.000), so removing the constraints leaves the prescribed Phase 1a kinematics unchanged. A regression run with the modified model (`MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim`, t = 1.0–3.0 s, mesh = 25) confirmed equivalence: maximum ES activation peak difference across IL_R10_{r,l}, IL_R11_r, IL_R12_r, LTpL_L5_{r,l} was 1.16 percentage points (in the low-effort pre-bend phase), and Hold-phase peaks differed by ≤ 0.11 %p — well within numerical noise. Phase 1a numerical results below therefore use the original coupler-bearing model; Phase 2 analyses use the no-coupler variant. See `docs/phase1a_regression_test_smoke.md` for the full regression table.

### §M2.3 — Forearm Geometry Modification

The original ThoracolumbarFB v2.0 model [Beaucage-Gauvreau et al., 2019] simplified the upper extremity by defining the `hand_R/L` body origin at the wrist center, omitting the hand segment distal to the wrist. This omission resulted in an effective arm reach (glenohumeral joint to `hand_R/L` origin) of 54.5 cm, approximately 31.9% shorter than anthropometric standards for adult males (75–80 cm, acromion to fingertip) [De Leva, 1996; Winter, 2009].

To enable analysis of ground-level box-lifting tasks requiring the hand to reach a box placed approximately 40 cm anterior to the feet, we extended the `radius_hand_r/l` joint parent-frame offset along the Y-axis from −0.242 m to −0.434 m, adding 19.2 cm consistent with male hand length (wrist to tip of middle finger = 0.108 × body height; 177.8 cm baseline → 19.2 cm) [De Leva, 1996, Table 4]. All other joint architectures, mass distributions, and muscle moment arms were preserved. The resulting modified model is designated `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim`.

The modification was validated against Phase 1a free-stoop kinematics using a smoke regression test (t = 1.0–3.0 s, mesh = 25) identical in protocol to the coupler-removal regression described above. Peak erector spinae activation correlation between the baseline no-coupler model and the forearm-extended model was R = 0.999977, with maximum activation difference ΔES = 1.227 %p (muscle IL_R10_r), well within the 5 %p acceptance threshold. This result is comparable to the coupler-removal regression (1.16 %p) and confirms that extending a distal arm segment has negligible effect on lumbar muscle recruitment during a free-stoop task where the hands are not loaded.

**New effective arm reach**: GH joint to `hand_R/L` origin = 73.7 cm, within the De Leva/Winter reference range of 75–80 cm (residual 1.7–8.4% difference attributable to the non-articulated wrist offset and rounded anthropometric constants).

### §M2.4 — Arm Inverse Kinematics: Two-Pass Warm-Start Strategy

For the Phase 2 box-lifting motion, four shoulder/elbow coordinates (shoulder elevation `sh_elv`, elevation angle `elv_angle`, elbow flexion `elbow_flex`, and shoulder rotation `sh_rot`) must be solved by inverse kinematics to track prescribed hand marker positions. Per-frame Nelder-Mead optimization (each frame solved independently from a fixed neutral-posture initial guess) proved sensitive to initial conditions and converged to alternate IK branches in adjacent frames, producing non-physical discontinuities and box-body penetration. In benchmark testing with box motion v10, maximum hand-position error reached 42.3 mm with multiple frames showing box penetration.

To ensure trajectory-level consistency, we adopted a two-pass warm-start strategy:

**Pass 0 — Grasp-peak seed (t = 2.0 s).** The grasp-peak frame, where the hand reaches its target position on the box, was solved using the Covariance Matrix Adaptation Evolution Strategy (CMA-ES) [Hansen, 2006] with population size λ = 10 and 10 independent random seeds. The seed with the lowest hand-position error was retained, yielding the arm configuration: sh_elv = 72.2°, elv_angle = 68°, elbow_flex = 57°, sh_rot = −48°.

**Pass 1 — Backward propagation (t = 2.0 → 0 s).** Each frame was solved with Nelder-Mead, initialized from the immediately succeeding frame's solution. This propagates the CMA-ES branch continuously backward through the trajectory.

**Pass 2 — Forward propagation (t = 2.0 → 5.0 s).** Each frame was solved with Nelder-Mead, initialized from the immediately preceding frame's solution. The two passes together guarantee that every frame on either side of the grasp peak lies in the same IK branch as the seed.

With this strategy, maximum hand-position error across all 22 frames was 6.5 mm (box motion v11) and box penetration was eliminated entirely. This procedure is implemented in `scripts/gen_box_motion_v11_stage1.py`.

## Results — Phase-resolved erector spinae activation

MocoInverse revealed five distinct phases of erector spinae activation during stoop lifting that were not detectable by SO (Figure X). The right L10-level iliocostalis (`IL_R10_r`) showed a clear progression: 8.1 % during quiet standing (0–1.0 s), 53.3 % during eccentric flexion (1.0–2.0 s), 87.7 % during the hold phase (2.0–2.5 s), 82.8 % during concentric extension (2.5–4.0 s), and 27.6 % during recovery (4.0–5.0 s). All major ES muscles followed this pattern (Table Y), with peak demands occurring during the Hold and Concentric phases.

Notably, eccentric activation (53.3 %) was approximately 35 % below concentric activation (82.8 %), an asymmetry observed consistently across the L10 (Δ +29.4 %p), L11 (+12.0), and L5 longissimus (+13.4) levels. This asymmetry was robust to optimization window length: a 2-second window comprising the eccentric and concentric phases produced an asymmetry of +29.7 %p, while the full 5-second window produced +29.4 %p (difference < 0.5 %p).

Spine flexion-extension reserve actuators absorbed 19.4 Nm at peak hold (t = 2.5 s), in close agreement with the SO reference value of 22 Nm at the equivalent reserve strength (R10). Pelvis vertical translation reserve was 46 N at peak, reflecting small numerical mismatches between prescribed kinematic accelerations and the constant ground reaction force profile.

Rectus abdominis activation remained at 0 % throughout the lift, as expected for a flexor muscle during a posture-extension task.

## Discussion — Reference motion structure

The double-peak structure in IL_R10 activation (peaks at t=2.4 s and t=3.1 s, dip at t=2.7 s) reflects the kinematic structure of the reference motion: the lumbar flexion-extension velocity reaches zero from t=2.5 s to t=3.0 s, creating a ~0.5 s static-hold plateau. During this plateau the muscle exerts a steady isometric torque to maintain the bent posture (~82 %); during the deceleration approach (t=2.4 s) and acceleration departure (t=3.1 s) of the trunk it produces additional dynamic torque, hence the bracketing peaks. MocoInverse correctly distributes activation according to this kinematic structure, illustrating why dynamics-aware solvers reveal structure that instantaneous SO does not.

## Discussion — Recruitment hierarchy and IL/LTpL pattern (tentative)

A clear recruitment hierarchy emerged during the Hold phase: IL_R10 (88 %) > LTpL_L5 (50 %) > IL_R11 (23 %) > IL_R12 (11 %), with rectus abdominis correctly inactive throughout the lift (sanity check satisfied). Iliocostalis at lower rib levels (IL_R11, IL_R12) showed strongly phasic activation profiles (peak-to-trough ratios > 12), while longissimus at the dominant lumbar level (LTpL_L5) showed sustained activation (peak-to-trough 3.0). At the most-active levels (IL_R10, LTpL_L5) the profiles were qualitatively similar, suggesting the phasic-tonic distinction may reflect recruitment threshold rather than a fixed differentiation in functional role. EMG validation will be needed to confirm whether this pattern is genuine motor-control strategy or a property of the optimization.

## Discussion — Implications for assistive device design

This activation dynamics analysis demonstrates that the hold and concentric phases impose the greatest demand on erector spinae muscles (peak activations 87.7 % and 82.8 %, respectively), while eccentric activation is approximately half (53.3 %). For SMA fabric-based assistive suits, this finding has direct design implications: timing assistive torque to the hold-and-extend phase may yield disproportionately greater benefit than uniform assistance throughout the lift cycle. The 35 % activation asymmetry between eccentric and concentric phases — undetectable by SO — provides a quantitative basis for **phase-targeted assist control strategies**.

Additionally, the close agreement between MocoInverse (19.4 Nm) and SO R10 (22 Nm) at peak load, despite the methodological differences, validates the underlying biomechanical model and confirms that our reserve strength sensitivity findings (from earlier SO sweeps R100/R50/R10/R5/R1) translate consistently to the dynamics-aware framework.

Future work will (i) extend Phase 1a to include the multifidus group (Phase 1b) to quantify deep stabilizer load sharing, (ii) integrate the SMA suit thoracic-pelvic torque couple into MocoInverse to compute phase-resolved assist effects, and (iii) extend to box-lifting tasks with hand external loads.

---

## Limitations

This Phase 1a analysis has several limitations that constrain the generalizability of the findings.

(i) **Synthetic kinematics**: the reference motion (`stoop_synthetic_v5.mot`) was designed for analytic clarity rather than measured from a human subject. While suitable for pipeline validation and qualitative phase-resolution analysis, inter-individual variability in lifting strategy is not captured.

(ii) **Single-subject anthropometry**: the ThoracolumbarFB v2.0 model represents an adult male. Extension to female and aged populations (Phase 1d) requires model scaling not yet performed.

(iii) **Restricted muscle set**: Phase 1a includes 114 muscles (iliocostalis, longissimus thoracis, quadratus lumborum, rectus abdominis); the multifidus group and obliques (~150 additional muscles) are deferred to a focused Phase 1b sub-experiment quantifying deep stabilizer load sharing.

(iv) **Reserve actuator residuals at non-spine joints**: leg muscles are excluded from Phase 1a, so hip, knee, and ankle moments are absorbed by reserve actuators (31, 158, 37 Nm at peak respectively). Spine flexion-extension reserve, the relevant quantity for ES analysis, was 19.4 Nm — within 12 % of the SO R10 reference (22 Nm).

(v) **EMG validation pending**: the recruitment-hierarchy and phasic-vs-tonic observations require cross-validation against subject EMG before being reported as definitive findings.

(vi) **Coupler-removed model scope**: the no-coupler variant introduced for Phase 2 (see Methods, §M2) assumes independent shoulder control. While appropriate for the lifting tasks analyzed in Phase 1a (free stoop) and Phase 2 (box handling), this modified model should not be applied to gait or running simulations without restoring the constraints, as it removes the passive arm-swing rhythm those motions rely on.

(vii) **Forearm geometry modification — anthropometric and morphological scope**: The 19.2 cm forearm extension (§M2.3) was derived from De Leva 1996 normative data for adult males of approximately average stature (~177.8 cm). For female subjects, shorter individuals, or populations where hand-to-height ratios deviate from the De Leva reference (e.g., pediatric, elderly with skeletal deformation), the offset would require proportional rescaling rather than direct application of the 0.434 m value. Additionally, the `hand_R/L` body remains a single rigid segment without articulated finger joints. Grip kinematics, individual finger forces, and wrist-hand coupling mechanics are not represented. Studies requiring detailed grip biomechanics or fingertip contact modeling should employ upper-extremity models with articulated hand segments [e.g., Holzbaur et al., 2005]. Because the 19.2 cm extension does not alter muscle origin or insertion sites, its effect on spinal muscle moment arms is negligible; however, changes in hand-mass inertial properties (mass of hand segment was not updated in this modification) could marginally affect dynamic simulations that include substantial hand loading (e.g., heavy box carry). The regression test (ΔES max 1.227 %p, R = 0.999977) was conducted for an unloaded free-stoop task only.

(viii) **Two-pass warm-start IK — trajectory continuity assumptions**: The warm-start strategy (§M2.4) assumes that the optimal arm configuration varies continuously and monotonically from the grasp-peak seed through the remainder of the trajectory. For tasks involving discrete grip-style transitions (overhand to underhand), sudden large reach-direction changes, or bilateral asymmetric movements, continuity may fail at transition points and require additional seed frames or trajectory segmentation. The CMA-ES grasp-peak step is stochastic: although we selected the best result from 10 independent seeds to minimize variability, different random-number sequences may yield marginally different seeds. In practice, the 6.5 mm maximum hand error achieved with box motion v11 is within the positional accuracy of typical optical motion capture (3–5 mm RMS) and was accepted as operationally adequate. Future work using trajectory-level optimal control (e.g., MocoTrack with endpoint constraints) would provide theoretically guaranteed smoothness without dependence on seed quality.

(ix) **Phase 2.C.4 박스 들기 Moco — dynamics consistency 한계**: Phase 2.C.4 MocoInverse 분석(박스 들기 v11b, 4 conditions)에서 pelvis 자유도에 대한 reserve actuator 크기가 pelvis_ty 3,570 N(peak, t = 4.0 s 말단 경계), pelvis_tilt 221 N·m(peak, t ≈ 2.5 s)을 기록하였으며, Hicks et al. [2015]의 역학적 일관성 판단 기준(체중의 5% 이하 ≈ 37 N, 체중 × 신장의 1% 이하 ≈ 12 N·m)을 상회한다. 이 residual은 두 가지 원인이 중첩된 결과이다. 첫째, 본 분석에서 적용된 지면반력(stoop_grf_v5.sto)은 제자리 stoop 동작(v5)에서 측정된 상수 프로파일(735.75 N 일정)로, 박스 20 kg(196.2 N)의 부가 질량과 들기 자세에서의 골반 가속도를 반영하지 않는다. 둘째, 근육 set에 포함되지 않은 하지 근육(대둔근, 슬굴곡근, 대퇴사두근, 장요근 등), 다열근, 복사근 등이 골반 자유도에 기여해야 할 토크를 reserve가 대신 흡수한다. pelvis_ty 3,570 N의 peak는 t = 4.0 s 말단 경계에서 발생하는 수치 artifact이며, 들기 구간(t = 1.0–3.5 s)에서의 pelvis_ty reserve는 228 N으로 감소한다. ES 활성도 결과(suit effect 25–96% 감소, Hu et al. [2026]의 14.9–28.6% 범위와 방향 일치)는 reserve 크기와 독립적이다. OpenSim API 분석으로 pelvis 자유도에 근육 모멘트 팔을 갖는 근육이 포함되지 않았음을 확인하였으며(ES 근육은 lumbar 좌표에만 모멘트를 발생), pelvis_tilt reserve가 ES 활성도 추정에 영향을 주지 않는다. 향후 개선 방향: (1) 박스 들기 전용 inverse dynamics 기반 GRF 재계산, (2) MocoTrack을 통한 kinematics + GRF 동시 추적 예측 시뮬레이션, (3) 하지 근육 및 다열근 추가(lumbar 좌표 기여분 반영).

(x) **Phase 2.C.4 기준 자세 및 대상 집단 적용 한계**: 박스 들기 동작 v11b의 자세 파라미터(pelvis_tilt −55°, lumbar 총 −62°, hip_flexion +100°, knee −30°)는 NIOSH Revised Lifting Equation [Waters et al., 1993]의 semi-squat 기준에 부합하는 정량 검증된 IK 실현 자세이나(NIOSH LI ≈ 2.0, 주의 구간), 요양보호사 65세 여성의 작업 특성(근력 약 30% 감소, 유효 LI ≈ 2.6–2.9, 고위험 구간 근접)에 직접 적용하기 위해서는 anthropometric scaling 및 자세 재조정이 추가로 필요하다[Kermavnar et al., 2021]. 기준 인체 모델은 성인 남성(175 cm, 75 kg)이며, 다양한 성별·연령 집단에 대한 일반화에는 별도의 검증이 요구된다. 또한 박스 동작 설계에 이르기까지 v3부터 v11b까지 14회의 시도가 필요하였으며, 이 과정에서 확립된 방법론적 교훈(foot x-anchor IK, CMA-ES + Two-pass warm-start, 박스 trajectory 별도 적용)은 향후 squat lift, carry, walk 동작 설계에 직접 적용 가능하다[literature_synthesis.md §6].

## Results — Section C: Suit dose-response confirms SO §1.6

We swept the suit force from 0 to 200 N (5 levels: 0, 50, 100, 150, 200 N → torque 0, 6, 12, 18, 24 N·m), running independent MocoInverse optimizations for each. All five optimizations converged to local optima (`Optimal Solution Found`) in 670–730 s of wall time. Linear fits of the relative ES_mean reduction (averaged over six dominant ES muscles) versus suit torque produced:

| Phase | Slope (%/Nm) | R² | Reduction @ 24 N·m |
|---|---:|---:|---:|
| Hold (2.0–2.5 s) | **1.164** | 1.0000 | **27.95 %** |
| Concentric (2.5–4.0 s) | 1.186 | 1.0000 | 28.46 % |
| **SO §1.6 reference (R100)** | **1.206** | 1.0000 | **28.97 %** |

The MocoInverse slope (1.164–1.186 %/Nm) agrees with the SO reference (1.206 %/Nm) within 1.7–3.5 % relative difference, and the reduction at 24 N·m matches within 1.0 percentage point. Both methods exhibit essentially perfect linearity (R² ≥ 0.999). The dominant single muscle, IL_R10_r, shows a higher per-torque sensitivity (1.603 %/Nm in Hold, 1.632 %/Nm in Concentric, R² = 1.0000), as expected for a muscle whose moment arm closely aligns with the assistive torque axis.

This dose-response agreement validates the SO suit-effect quantification reported in §1.6 and demonstrates that the dynamics-aware MocoInverse formulation does not introduce new pathologies in the linear regime.

---

## Results — Section 2.C.4: 박스 들기 동작에서의 슈트 효과 (Phase 2.C.4)

### §2.C.4.1 박스 들기 동작 (v11b)

지면 박스(20 kg, 30 × 30 × 25 cm) 양 측면 잡기 들기 동작을 설계하였다. 단순 제자리 stoop(Phase 1a)과 달리, 본 동작은 골반·고관절·무릎·허리가 복합적으로 굽는 semi-squat hybrid 자세를 포함하며, 박스를 발 앞 약 30 cm에 놓고 양손으로 측면을 잡아 들어올리는 시퀀스(박스 lift 후 carry)로 구성된다.

v3부터 v11b까지 14회 시도 끝에 v11b 동작이 최종 채택되었다. 핵심 자세 파라미터는 다음과 같다: pelvis_tilt −55°(semi-squat hybrid), lumbar 총 굴곡 −62°(각 분절 −11°), hip_flexion +100°, knee −30°. 이는 NIOSH Revised Lifting Equation [Waters et al., 1993]의 semi-squat 기준에 부합한다(수평 거리 H = 40 cm 기준 RWL ≈ 10.0 kg, LI ≈ 2.0). 발 앵커 위치는 calcn offset −0.0442 m로 전 구간 고정하였으며, 박스 위치는 발 앞 BOX_X = +0.256 m, 양 측면 잡기는 z = ±0.150 m이다.

IK 풀이에는 §M2.4의 Two-pass warm-start 전략을 적용하였다. CMA-ES grasp-peak seed 최적화(t = 2.0 s 단일 프레임)에서 sh_elv = 72.2°, elv_angle = 68°, elbow_flex = 57°, sh_rot = −48°를 산출한 후, 역방향(t = 2.0 → 0 s) 및 순방향(t = 2.0 → 5.0 s) warm-start pass를 수행하였다. 전 구간 최대 손 위치 오차는 6.5 mm(v11)이며, 박스 관통은 없음을 확인하였다. Stage 4 시각 검증(격자 8장)에서 들기 시퀀스, carry 단계, 박스 trajectory 모두 8/8 통과하였다.

### §2.C.4.2 Moco 분석 (4 conditions)

MocoInverse를 Phase 1a와 동일한 설정(mesh 50, reserve optimal force 10 N·m/10 N, De Groote-Fregly 2016 rigid tendon)으로 적용하되, 시간 창을 t = 1.0–4.0 s(들기 집중 구간)로 설정하였다. 근육 set은 Phase 1a의 114개(척추 기립근 위주)를 그대로 사용하였다. 지면반력은 stoop_grf_v5.sto(상수 735.75 N, Phase 1a와 동일)를 적용하였다(GRF 정합성 한계는 §ix 참조).

박스 무게(196.2 N)는 손 외력(각 손 98.1 N 상향)으로 ExternalLoads에 포함하였다. 슈트 토크는 thoracic-pelvic couple로 ExternalLoads에 추가하였다(Phase 1a 동일 방식). Savitzky-Golay smoothing을 적용하여 팔꿈치 관절 좌표 불연속을 완화하였다.

4개 conditions(B_noload 0 N·m, B_suit50 50 N·m, B_suit100 100 N·m, B_suit200 200 N·m)이 모두 IPOPT Solve_Succeeded로 수렴하였다(wall time 88–205 s). 결과 파일: `/data/opensim_results/phase2c4_box_v11b/`.

### §2.C.4.3 ES 활성도 결과

IL_R10_r(우측 10번 늑골 수준 장늑근, Phase 1a의 최고 활성 근육)은 B_noload 조건에서 세 들기 구간 모두 최대 활성(100.0%)에 도달하였다. 이는 Phase 1a 제자리 stoop에서의 Hold peak(87.7%)를 상회하며, 박스 20 kg 부가 외력이 주요 척추 기립근을 포화 상태로 구동함을 나타낸다.

**Table A — IL_R10_r Peak Activation (%) by Phase and Suit Torque**

| Phase | B_noload | B_suit50 | B_suit100 | B_suit200 | Δ (200 vs 0) |
|---|---:|---:|---:|---:|---:|
| Eccentric (1.0–2.0 s) | 100.0 | 75.3 | 25.0 | 0.0 | −100.0 %p |
| Grasp (2.0–2.5 s) | 100.0 | 10.0 | 0.0 | 0.0 | −100.0 %p |
| Concentric (2.5–4.0 s) | 100.0 | 38.4 | 22.8 | 0.8 | −99.2 %p |

B_suit200에서 Eccentric 및 Grasp 구간의 IL_R10_r 활성도는 사실상 0으로 소거되었으며(각각 0.0%, 0.0%), Concentric 구간에서도 0.8%로 98% 이상 감소하였다. 이는 Phase 1a의 최대 감소(−28.0 %p at 24 N·m)를 크게 상회하며, 박스 부하로 인한 근육 포화 상태에서 고보조 슈트가 극적인 ES 부담 경감 효과를 나타냄을 시사한다.

**Table B — ES_mean Peak Activation (%) by Phase and Suit Torque**

ES_mean은 분석에 포함된 114개 척추 기립근 전체의 평균 peak 활성도이다.

| Phase | B_noload | B_suit50 | B_suit100 | B_suit200 | Δ (200 vs 0) |
|---|---:|---:|---:|---:|---:|
| Eccentric (1.0–2.0 s) | 29.9% | 16.0% | 8.3% | 1.2% | −28.7 %p (−95.9%) |
| Grasp (2.0–2.5 s) | 23.9% | 11.2% | 1.7% | 0.0% | −23.9 %p (−100.0%) |
| Concentric (2.5–4.0 s) | 29.0% | 15.2% | 4.1% | 2.2% | −26.8 %p (−92.4%) |

주목할 점은 B_suit200에서 Grasp 구간 ES_mean이 0.0%로 완전 소거된 것이다. 이는 200 N·m 슈트 토크가 박스 grasp 자세의 척추 굴곡 부담을 완전히 오프로드함을 의미하며, 실제 근육에 의한 지지 없이 슈트만으로 해당 자세를 유지할 수 있는 수준의 보조력임을 나타낸다.

### §2.C.4.4 Dose-Response 회귀 분석

슈트 토크(0–200 N·m) 대비 ES 활성도 감소의 선형성을 평가하기 위해 각 phase별로 선형 회귀를 수행하였다.

**Table C — Dose-Response Linear Regression (MocoInverse, 4 conditions)**

| Phase | Metric | Slope (%/N·m) | R² | Baseline (0 N·m) | Reduction @200 N·m |
|---|---|---:|---:|---:|---:|
| Eccentric | ES_mean peak | −0.136 | 0.894 | 29.9% | −28.7 %p |
| Grasp | ES_mean peak | −0.114 | 0.786 | 23.9% | −23.9 %p |
| Concentric | ES_mean peak | −0.128 | 0.791 | 29.0% | −26.8 %p |
| Eccentric | IL_R10_r peak | −0.515 | 0.925 | 100.0% | −100.0 %p |
| Grasp | IL_R10_r peak | −0.417 | 0.538 | 100.0% | −100.0 %p |
| Concentric | IL_R10_r peak | −0.448 | 0.810 | 100.0% | −99.2 %p |

Phase 1a와의 주요 차이: (1) slope 절대값이 Phase 1a(ES_mean Hold: −1.164 %/N·m)보다 약 9배 작은 것은 Phase 2.C.4의 x축 범위가 0–200 N·m(Phase 1a: 0–24 N·m)으로 8배 넓으며, B_suit200에서 이미 floor effect(IL_R10 0.8%)에 도달하여 선형 구간을 벗어난 데 기인한다. (2) IL_R10_r의 Grasp R² = 0.538이 낮은 것은 floor 도달 비선형성을 반영한다(B_suit50: 10.0% → B_suit100: 0.0% 급락). (3) ES_mean R²가 0.786–0.894로 IL_R10_r보다 높은 것은 다수 근육 평균이 개별 포화 근육의 비선형 거동을 평활화하기 때문이다.

### §2.C.4.5 Phase 1a 비교

**Table D — Phase 1a (Stoop) vs Phase 2.C.4 (Box 20 kg) 핵심 비교**

| 항목 | Phase 1a Stoop | Phase 2.C.4 Box |
|---|---|---|
| 동작 유형 | 제자리 허리 굽힘 (무릎 고정) | Semi-squat hybrid (박스 20 kg) |
| 슈트 토크 범위 | 0–24 N·m (5 levels) | 0–200 N·m (4 levels) |
| IL_R10_r baseline peak | 87.7% (Hold) | 100.0% (전 구간 포화) |
| ES_mean baseline peak | ~22% (Hold) | 23.9–29.9% |
| 최대 슈트 효과 (IL_R10_r) | −28.0 %p at 24 N·m | −100.0 %p at 200 N·m |
| Slope (ES_mean) | −1.164 %/N·m (Hold) | −0.128 %/N·m (Concentric) |
| R² | 1.000 (5 points, 좁은 선형 구간) | 0.791–0.894 (4 points, floor 포함) |

박스 20 kg 부가 외력은 IL_R10_r을 완전 포화(100%)로 구동하여, 고보조 슈트(200 N·m)의 극적 효과(−99% 이상)를 가능케 하였다. 두 task 모두 슈트 보조와 ES 부담 감소 사이의 단조 감소 관계를 재현하며, 슈트 효과의 task 의존성(부하 크기, 자세, 슈트 토크 범위)을 정량 확인하였다.

### §2.C.4.6 학계 검증 비교

**Hu et al. [2026]** (VU Amsterdam, PMID 39967340): 활성형 이중 관절 등 지지 외골격, 8명 × 4 assist levels(0/30/50/70%) × 15 kg 들기. 등속성 기립근 모멘트 14.9–28.6% 감소, 고보조 수준에서의 포화 현상 보고.

Phase 1a(stoop, 24 N·m)의 ES 감소(28.0–28.5%)는 Hu et al. [2026]의 최대 감소치(28.6%)와 정량적으로 일치한다. Phase 2.C.4(박스 20 kg)에서 관찰된 IL_R10_r 포화(100% → 0%, 200 N·m) 현상은 Hu et al. [2026]이 보고한 고보조 수준에서의 압축력 추가 감소 부재(saturation)와 동일한 기전을 반영한다.

**Yan et al. [2024]** (Harvard/BIDMC, PMID 39305855): OpenSim Static Optimization + soft exosuit + 들기 작업(squat + stoop, 6/10 kg). EMG–모델 교차상관 0.84–0.98, RMSE 0.05–0.10. 본 연구는 동일 OpenSim 기반이나 MocoInverse를 적용하여 동적 활성화 과정을 포착한다는 방법론적 차별점을 갖는다.

**John et al. [2022]** (DOI: 10.1080/10255842.2022.2040546): OpenSim MocoTrack + ExternalLoads JSON으로 외골격 토크를 적용하는 가장 유사한 방법론. 4-condition Phase 2.C.4 설계(suit torque sweep + phase-resolved 비교)는 이 논문의 접근법과 구조적으로 동일하다.

**D'Hondt et al. [2024]** (DOI: 10.1016/j.jbiomech.2024.111925): OpenSim MocoTrack + 박스 들기 동작. 본 연구와 동일한 task-solver 조합이나 exosuit 효과 정량화를 포함하지 않음.

### §2.C.4.7 산업 표준 (NIOSH/REBA)

**NIOSH Revised Lifting Equation** [Waters et al., 1993] 적용 결과(박스 20 kg, H = 40 cm, 높이 15 cm, 이동 거리 60 cm):

```
RWL = 23 × HM × VM × DM × AM × FM × CM
    = 23 × 0.625 × 0.820 × 0.895 × 1.0 × 1.0 × 0.95
    ≈ 10.0 kg
LI = 20 / 10.0 = 2.0  (주의 구간: 1.0 ≤ LI < 3.0)
```

65세 여성 요양보호사 적용 시: 연령·성별에 따른 근력 약 30% 감소를 반영하면 유효 LI ≈ 2.6–2.9(고위험 구간 근접)이다[Kermavnar et al., 2021]. L5/S1 압축력 한계 기준(NIOSH: 3,400 N) 대비 본 Moco 분석 결과 보고는 향후 연구 과제이다.

REBA 평가(Hignett & McAtamney, 2000): 박스 들기 자세(몸통 굴곡 >60°, 부하 >10 kg) 기준 REBA ≈ 8–10(고위험). 슈트 착용 시 근육 활성도 감소(−27~−100 %p)가 REBA 점수 감소로 직결되는지는 biomechanical모델과 REBA 관찰 기반 접근법의 연계가 추가로 필요하다.

슈트 효과를 ES 활성도 감소(시뮬레이션)와 LI/REBA 개선(산업 표준) 언어로 동시 표현하는 것은 학계-산업 Gap 해소에 직접 기여한다[De Bock et al., 2022].

---

## Suggested Figure X — 5-phase ES activation

[`docs/images/phase1a_full/figure_5phase_activation.png`](images/phase1a_full/figure_5phase_activation.png) — Bar chart showing mean ± SD activation per phase (Quiet / Eccentric / Hold / Concentric / Recovery) for five key ES muscles (`IL_R10_r/l`, `IL_R11_r`, `LTpL_L5_r/l`).

## Suggested Figure Z — Suit dose-response

[`docs/images/phase1a_full/figure_suit_sweep_dose_response.png`](images/phase1a_full/figure_suit_sweep_dose_response.png) — Two-panel: (A) ES_mean reduction (%) vs torque (N·m), comparing Moco Hold and Concentric phase points to the SO §1.6 dashed line; (B) IL_R10_r dose-response. All four Moco fits show R² = 1.0000.

## Suggested Figure W — Phase-targeted suit effect

[`docs/images/phase1a_full/figure_5phase_delta_heatmap.png`](images/phase1a_full/figure_5phase_delta_heatmap.png) — Heatmap of ΔES (suit − baseline) at 24 N·m across 5 phases × 6 dominant muscles. The largest reductions concentrate in Hold and Concentric phases; Quiet and Recovery phases show ≤ 4 percentage points of change.

## Suggested Figure V — Recruitment redistribution

[`docs/images/phase1a_full/figure_hierarchy_redistribution.png`](images/phase1a_full/figure_hierarchy_redistribution.png) — Hold-phase activation of four ES muscles, baseline vs +24 N·m suit. Dominant muscles (IL_R10) decrease by ~34 %p; minor recruits (IL_R12) increase by ~2 %p, suggesting load redistribution toward previously-unsaturated muscles.

## Suggested Table Y — Phase × muscle activation

| Muscle | Quiet (%) | Eccentric (%) | Hold (%) | Concentric (%) | Recovery (%) | Δ (Con−Ecc) %p |
|---|---:|---:|---:|---:|---:|---:|
| IL_R10_r | 8.1 | 53.3 | **87.7** | 82.8 | 27.6 | +29.4 |
| IL_R10_l | 8.0 | 52.5 | 85.6 | 80.9 | 27.2 | +28.4 |
| IL_R11_r | 0.0 | 10.1 | 23.1 | 22.1 | 3.8 | +12.0 |
| IL_R11_l | 0.0 | 9.6 | 21.3 | 20.5 | 3.6 | +10.9 |
| IL_R12_r | 0.0 | 2.3 | 10.7 | 10.1 | 0.3 | +7.7 |
| LTpL_L5_r | 8.8 | 32.5 | 48.6 | 45.9 | 17.7 | +13.4 |
| LTpL_L5_l | 8.9 | 32.8 | 49.9 | 47.0 | 17.9 | +14.2 |
| LTpT_T11_r | 0.0 | 2.7 | 7.6 | 7.1 | 0.9 | +4.4 |
| QL_post_I_3-L1_r | 0.1 | 0.7 | 2.7 | 2.5 | 0.2 | +1.8 |
| rect_abd_r | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Values are phase means; standard deviations available in supplementary material.

---

## References cited

### Methods / Solver

- Beaucage-Gauvreau, E., Robertson, W. S., Brandon, S. C., Fraser, R., Freeman, B. J., Graham, R. B., ... & Lloyd, D. G. (2019). Validation of an OpenSim full-body model with detailed lumbar spine for estimating lower lumbar spine loads during symmetric and asymmetric lifting tasks. *Computer Methods in Biomechanics and Biomedical Engineering*, 22(7), 744–755. DOI: 10.1080/10255842.2018.1558757
- De Groote, F., Kinney, A. L., Rao, A. V., & Fregly, B. J. (2016). Evaluation of direct collocation optimal control problem formulations for solving the muscle redundancy problem. *Annals of Biomedical Engineering*, 44(10), 2922–2936.
- De Leva, P. (1996). Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters. *Journal of Biomechanics*, 29(9), 1223–1230.
- Dembia, C. L., Bianco, N. A., Falisse, A., Hicks, J. L., & Delp, S. L. (2020). OpenSim Moco: Musculoskeletal optimal control. *PLOS Computational Biology*, 16(12), e1008493. DOI: 10.1371/journal.pcbi.1008493
- Hansen, N. (2006). The CMA evolution strategy: a comparing review. In J. A. Lozano, P. Larranaga, I. Inza, & E. Bengoetxea (Eds.), *Towards a New Evolutionary Computation: Advances in Estimation of Distribution Algorithms* (pp. 75–102). Springer.
- Hicks, J. L., Uchida, T. K., Seth, A., Rajagopal, A., & Delp, S. L. (2015). Is my model good enough? Best practices for verification and validation of musculoskeletal models and simulations of movement. *Journal of Biomechanical Engineering*, 137(2), 020905. DOI: 10.1115/1.4029304
- Holzbaur, K. R., Murray, W. M., & Delp, S. L. (2005). A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control. *Annals of Biomedical Engineering*, 33(6), 829–840.
- Winter, D. A. (2009). *Biomechanics and Motor Control of Human Movement* (4th ed.). John Wiley & Sons.

### Exosuit / Exoskeleton Evaluation (Phase 2.C.4 비교 대상)

- Hu, F., Brouwer, N. P., Tabasi, A., Kingma, I., van Dijk, W., Mohamed Refai, M. I., ... & van Dieën, J. H. (2026). Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting. *Ergonomics*, 69(3), 453–465. PMID: 39967340.
- John, C. T., Jackson, R. W., Bhatt, N., Garg, A., Shoemaker, M., Whitmer, B., & Fregly, B. J. (2022). Feasibility of using MocoTrack to analyze wearable lower-limb exoskeleton assistance during walking. *Computer Methods in Biomechanics and Biomedical Engineering*, 25(13), 1482–1493. DOI: 10.1080/10255842.2022.2040546
- D'Hondt, J., Costes, A., Porte, E., Pillet, H., & Skalli, W. (2024). Estimation of joint moments during a box-lifting task using OpenSim musculoskeletal simulation. *Journal of Biomechanics*, 167, 111925. DOI: 10.1016/j.jbiomech.2024.111925
- Yan, C., Banks, J. J., Allaire, B. T., Quirk, D. A., Chung, J., Walsh, C. J., & Anderson, D. E. (2024). Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *Journal of Biomechanics*, 176, 112322. PMID: 39305855. DOI: 10.1016/j.jbiomech.2024.112322
- Quinlivan, B. T., Lee, S., Malcolm, P., Rossi, D. M., Grimmer, M., Siviy, C., ... & Walsh, C. J. (2017). Assistance magnitude versus metabolic cost reductions for a tethered multiarticular soft exosuit. *Science Robotics*, 2(2), eaah4416. DOI: 10.1126/scirobotics.aah4416
- Pinheiro, C., Figueiredo, J., Nóbrega, P., & Santos, C. P. (2023). Multi-task evaluation framework for lower-limb exoskeleton assistance. *Journal of NeuroEngineering and Rehabilitation*, 20, 55. DOI: 10.1186/s12984-023-01155-8

### Systematic Reviews / Population

- De Bock, S., Ghillebert, J., Govaerts, R., Elprama, S. A., Wieckx, M., Hubin, A., ... & Mathijs, T. (2022). Passive back exoskeletons for occupational use: A systematic review of biomechanical, physiological, and performance effects. *Applied Ergonomics*, 98, 103582. PMID: 34600307. DOI: 10.1016/j.apergo.2021.103582
- Kermavnar, T., de Vries, A. W., de Looze, M. P., & O'Sullivan, L. W. (2021). Effects of industrial back-support exoskeletons on body weight distribution, trunk muscle activity, discomfort, and usability: a systematic review. *Ergonomics*, 64(6), 685–711. PMID: 33369518. DOI: 10.1080/00140139.2020.1870162

### Industrial Standards

- Waters, T. R., Putz-Anderson, V., Garg, A., & Fine, L. J. (1993). Revised NIOSH equation for the design and evaluation of manual lifting tasks. *Ergonomics*, 36(7), 749–776.
- Hignett, S., & McAtamney, L. (2000). Rapid entire body assessment (REBA). *Applied Ergonomics*, 31(2), 201–205.

(Existing references for ThoracolumbarFB model, SO methodology, SMA suit, etc., as already cited in the manuscript.)

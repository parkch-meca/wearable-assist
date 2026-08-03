"""복합관절 슈트 모델 — SMA PathActuator + 직렬 스프링.

■ 왜 직렬 스프링이 필요한가
  100 N 상수 PathActuator 단독 모델은 실측을 재현하지 못한다. 직립 60 ℃ 가열 시
  무부하 기대 수축은 60 mm 인데 허벅지 밴드는 10~15 mm 만 올라간다. 45~50 mm 가
  고정부·밴드 탄성에 흡수된다는 뜻이므로, 직렬 탄성 요소가 모델에 있어야 한다.

■ 역학 모델
  경로 길이  L(θ) = L_SMA + L_series + L_webbing(강체)
  SMA        온도 T 에서 자유길이 L_free = 200·(1−ε).  메쉬 리미터로 L_SMA ≤ 200 mm.
             F_SMA = 100 · (L_SMA − L_free)/(200 − L_free)      [선형 근사, 0…100 N]
  직렬 탄성  F = T0 + k·x_s        (x_s = 착용 예압 상태로부터의 신장)
  적합       x_SMA = 200 − L_SMA (수축량),  x_s = ΔL + x_SMA

  평형:  100·(1 − x_SMA/60) = T0 + k·(ΔL + x_SMA)
      →  x_SMA = (100 − T0 − k·ΔL) / (100/60 + k),   단 x_SMA ≥ 0 (메쉬 리미터)
         x_SMA < 0 이면 SMA 가 200 mm 를 넘어야 하므로 0 으로 고정되고
         추가 길이는 전부 직렬 탄성이 흡수한다.
  힘은 SMA 차단력 100 N 을 넘지 못한다(그 이상은 메쉬가 받는다).

  ε = 0.30 (60~70 ℃) → 스트로크 60 mm,  ε = 0.40 (80 ℃) → 80 mm.

■ 부착점
  docs/refs/pdf_pages/*.png 사진 판독에서 해부학적 지표와 대조해 추정한 값이다.
  실측값이 아니므로 민감도 분석 대상이다 (suit_sensitivity 참조).
"""
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim')
D2R = np.pi / 180

# ── 사양 (docs/suit_spec_multijoint.md 와 동일 출처) ────────────────
F_MAX = 100.0          # N — 기본 소자 50 N × 2 장 (역학적 병렬)
L_ACT = 200.0          # mm — 메쉬 리미터가 보장하는 Active 길이 상한
EPS = {60: 0.30, 80: 0.40}          # 온도(℃) → 수축률
OBS_DISP = (10.0, 15.0)             # mm — 직립 60 ℃ 에서 관찰된 허벅지 밴드 상승


def stroke(eps):
    return L_ACT * eps                    # mm


def sma_force(x_sma, eps):
    """SMA 수축량 x_sma(mm) 에서의 힘 (N). 선형 근사."""
    s = stroke(eps)
    return float(np.clip(F_MAX * (1.0 - x_sma / s), 0.0, F_MAX))


def solve(dL, k, T0, eps=0.30):
    """경로 신장 dL(mm) 에서의 평형.

    반환 (F, x_sma, x_series) — 힘 N, SMA 수축량 mm, 직렬 신장량 mm.
    """
    s = stroke(eps)
    x = (F_MAX - T0 - k * dL) / (F_MAX / s + k)
    x = max(0.0, x)                        # 메쉬 리미터: SMA 는 200 mm 초과 불가
    F = min(sma_force(x, eps), F_MAX)
    if x <= 0.0:                           # 전부 직렬 탄성이 흡수
        F = min(T0 + k * dL, F_MAX)
    return F, x, dL + x


def calibrate_T0(k, target_disp=12.5, eps=0.30):
    """관찰 변위를 재현하는 예압 T0 (N). 음수면 0 으로 자른다."""
    return max(0.0, sma_force(target_disp, eps) - k * target_disp)


# ══════════════════════════════════════════════════════════════════
# 부착점 — (body, 국소좌표 m). 사진 판독 기반 추정치.
# 좌표계: +x 전방, +y 상방, +z 우측 (중립 자세 기준)
# ══════════════════════════════════════════════════════════════════
def points(side='R'):
    s = 1.0 if side == 'R' else -1.0
    fem = 'femur_r' if side == 'R' else 'femur_l'
    sc, hu, ra = f'scapula_{side}', f'humerus_{side}', f'radius_{side}'
    return {
        # 허리 — 요추 후면 → 천골 후면 → 대퇴 후면 근위(허벅지 밴드)
        'waist': [('lumbar1', (-0.050, 0.000, s * 0.040)),
                  ('sacrum', (-0.140, 0.000, s * 0.040)),
                  (fem, (-0.050, -0.150, 0.000))],
        # 어깨 — 상부 흉추 후면 → 견봉(견갑) → 삼각근 조면(상완)
        'shoulder': [('thoracic3', (-0.040, 0.000, s * 0.030)),
                     (sc, (-0.010, 0.020, s * 0.030)),
                     (hu, (0.000, -0.120, s * 0.010))],
        # 팔꿈치 — 상완 전면 근위 → 상완 전면 원위 → 전완 전면 근위(BOA 커프)
        'elbow': [(hu, (0.030, -0.030, 0.000)),
                  (hu, (0.040, -0.220, 0.000)),
                  (ra, (0.030, -0.050, 0.000))],
    }


REGIONS = ('waist', 'shoulder', 'elbow')
# 각 부위가 보조하는 대표 좌표 (모멘트암·보조토크 산출용)
DRIVEN = {'waist': ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE'],
          'shoulder': ['shoulder_elv_{s}'],
          'elbow': ['elbow_flexion_{s}']}


def build(model_path=MODEL, sides=('R', 'L')):
    """슈트 PathActuator 6개를 추가한 모델을 반환한다 (메모리, 파일 미기록)."""
    m = osim.Model(model_path)
    m.initSystem()
    bs = m.getBodySet()
    names = []
    for side in sides:
        P = points(side)
        for reg in REGIONS:
            pa = osim.PathActuator()
            nm = f'suit_{reg}_{side}'
            pa.setName(nm)
            pa.setOptimalForce(F_MAX)
            for i, (b, v) in enumerate(P[reg]):
                pa.addNewPathPoint(f'{nm}_p{i}', bs.get(b), osim.Vec3(*v))
            m.addForce(pa)
            names.append(nm)
    m.finalizeConnections()
    m.initSystem()
    return m, names


# ── 자세 설정 / 길이·모멘트암 조회 ─────────────────────────────────
def pose_state(m, pose=None, zero=True):
    m.initSystem()
    s = m.initializeState()
    cs = m.getCoordinateSet()
    if zero:
        for i in range(cs.getSize()):
            c = cs.get(i)
            if not c.getLocked(s):
                c.setValue(s, 0.0, False)
    for nm, v in (pose or {}).items():
        c = cs.get(nm)
        if not c.getLocked(s):
            c.setValue(s, v * D2R if c.getMotionType() == 1 else v, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def path_length_mm(m, s, name):
    pa = osim.PathActuator.safeDownCast(m.getForceSet().get(name))
    return pa.getGeometryPath().getLength(s) * 1000.0


def moment_arm_mm(m, s, name, coord):
    pa = osim.PathActuator.safeDownCast(m.getForceSet().get(name))
    return pa.getGeometryPath().computeMomentArm(s, m.getCoordinateSet().get(coord)) * 1000.0

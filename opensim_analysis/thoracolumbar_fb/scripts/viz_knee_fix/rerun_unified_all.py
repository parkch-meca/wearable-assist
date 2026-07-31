"""5동작 완전 통일 재실행 — M1scap_armfix + tight reserve.

목적: 5동작의 척추 reserve 설정을 완전히 동일하게 맞춘 뒤 부하–효과 패턴을 재평가.

■ 통제 원칙 — reserve만 바꾼다
  각 동작의 기존 SO 실행에서 **모델의 reserve optimal_force만** 교체하고
  운동학(.mot), 외력/GRF(ExternalLoads XML·데이터), 시간 범위, lowpass,
  SO 옵션(activation exponent 2.0, 수렴 1e-4, 최대 300회)은 원본 그대로 재사용한다.
  → 관측되는 변화가 reserve 설정 단독의 효과임이 보장된다.

■ tight reserve 정의 (gait_so_tight.py / carry_so.py와 문자 그대로 동일)
    pelvis*                        : 병진 500 N   / 회전 1000 N·m   (부유 기저 잔차 흡수, OFF/ON 상쇄)
    _FE / _LB / _AR / Abs_ (척추)  : 5 N·m         ← 표준 100에서 조임
    기타                           : 병진 100 N   / 회전 1000 N·m
    min/maxControl = ∓50 (전 액추에이터 공통)
  optimal_force를 낮추면 같은 힘을 내기 위해 더 큰 control이 필요하고,
  SO의 비용함수(activation^2)가 이를 비싸게 매겨 근육이 부하를 담당하게 된다.
  (하드 캡이 아니라 비용 기반 억제)

■ 기저 모델을 보행·운반과 동일하게 통일한다
  전 동작 = MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim (169 coord)
  이전 단계(/data/tight_rerun)는 각 동작의 원본 기저를 유지한 채 reserve만 통일했고,
  본 단계는 거기에 더해 기저 모델까지 통일한다. 두 결과를 대조하면 모델 변경분의
  실제 크기를 분리해 확인할 수 있다.
  변경 내역: 쿠플러 4개 제거(스쿼트·스툽) + M1 견갑 추가(스쿼트·스툽) + 좌팔 축 수정(전 동작).
  기존 회귀 검증 유계: 쿠플러 ≤1.16 %p, M1 0.029 %p, armfix ≤1.1 %p.
"""
import os, re, sys, time, shutil
from pathlib import Path
import opensim as osim

MODELS = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x'
OUT = Path('/data/tight_unified'); OUT.mkdir(exist_ok=True)

# 동작별 원본 실행 조건 (모델만 교체)
JOBS = {
 'squat_off': dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_motion/squat_synthetic_v1.mot',
                   ext='/data/squat_results/suit_sweep/F0/ext_loads_F0.xml',
                   t=(0.0, 5.0)),
 'squat_on':  dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_motion/squat_synthetic_v1.mot',
                   ext='/data/squat_results/suit_sweep/F200/ext_loads_F200.xml',
                   t=(0.0, 5.0)),
 'stoop_off': dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_results/stoop_v5/v5_30fps.mot',
                   ext='/data/stoop_motion/stoop_grf_v5.xml',
                   t=(0.0, 5.0)),
 'stoop_on':  dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_results/stoop_v5/v5_30fps.mot',
                   ext='/data/stoop_results/suit_sweep_v5/F200/ext_loads_F200.xml',
                   t=(0.0, 5.0)),
 'box_off':   dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_motion/box_stoop_lift_m1.mot',
                   ext='/data/stoop_results/box_stoop_so/B_off/ext_B_off.xml',
                   t=(0.0, 7.5)),
 'box_on':    dict(base=f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim',
                   mot='/data/stoop_motion/box_stoop_lift_m1.mot',
                   ext='/data/stoop_results/box_stoop_so/B_on/ext_B_on.xml',
                   t=(0.0, 7.5)),
}
SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')


def reserved_tight(src, dst):
    """gait_so_tight.py / carry_so.py의 reserved_tight()와 동일 로직."""
    m = osim.Model(src); m.initSystem(); cs = m.getCoordinateSet()
    n_spine = 0
    for i in range(cs.getSize()):
        c = cs.get(i); nm = c.getName()
        a = osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'):
            opt = 500.0 if c.getMotionType() == 1 else 1000.0
        elif any(k in nm for k in SPINE_KEYS):
            opt = 5.0; n_spine += 1
        else:
            opt = 100.0 if c.getMotionType() == 1 else 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0)
        m.addForce(a)
    m.finalizeConnections(); m.printToXML(dst)
    return n_spine


def run(tag):
    j = JOBS[tag]
    d = OUT / tag; d.mkdir(exist_ok=True)
    mres = str(d / 'model_res_tight.osim')
    n_spine = reserved_tight(j['base'], mres)
    # 외력 XML은 원본을 그대로 쓰되, datafile 상대경로 문제를 피하려 디렉터리에 복사
    ext_src = Path(j['ext'])
    ext_dst = d / ext_src.name
    shutil.copy(ext_src, ext_dst)
    # 압축 XML(한 줄)도 처리되도록 줄 단위가 아니라 전체 텍스트 정규식으로 참조를 수집
    for fn in set(re.findall(r'<(?:datafile|data_source_name)>([^<]+)<', ext_dst.read_text())):
        fn = fn.strip()
        if not fn or fn.startswith('/'):
            continue
        cand = ext_src.parent / fn
        if cand.exists() and not (d / fn).exists():
            shutil.copy(cand, d / fn)
    t0, t1 = j['t']
    tool = osim.AnalyzeTool()
    tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(t0); tool.setFinalTime(t1)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(j['mot'])
    tool.setReplaceForceSet(False)
    tool.setExternalLoadsFileName(str(ext_dst))
    so = osim.StaticOptimization()
    so.setStartTime(t0); so.setEndTime(t1)
    so.setUseMusclePhysiology(True); so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)
    setup = str(d / 'setup.xml'); tool.printToXML(setup)
    print(f'[{tag}] 척추 reserve {n_spine}개 opt=5.0 | base={Path(j["base"]).name}', flush=True)
    st = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-st:.0f}s', flush=True)


if __name__ == '__main__':
    for tag in sys.argv[1:]:
        run(tag)

"""5동작 해석 조건 전수 감사 — 실제 .osim / setup.xml / .sto / 스크립트에서만 추출.

추측 금지. 파일에서 읽어낸 것만 보고하고, 읽어낼 수 없는 항목은 UNKNOWN으로 남긴다.
"""
import re, os, json, hashlib
from pathlib import Path
import numpy as np
import opensim as osim

SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')

# 기존(현행 논문 수치) 실행 산출물 위치
RUNS = {
 'squat': dict(name='맨몸 스쿼트',
               setup_off='/data/squat_results/suit_sweep/F0/setup_F0.xml',
               setup_on='/data/squat_results/suit_sweep/F200/setup_F200.xml',
               act_off='/data/squat_results/suit_sweep/F0/squat_F0_StaticOptimization_activation.sto',
               act_on='/data/squat_results/suit_sweep/F200/squat_F200_StaticOptimization_activation.sto'),
 'stoop': dict(name='맨몸 스툽',
               setup_off='/data/stoop_results/stoop_v5/setup_so_v5.xml',
               setup_on='/data/stoop_results/suit_sweep_v5/F200/setup_F200.xml',
               act_off='/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto',
               act_on='/data/stoop_results/suit_sweep_v5/F200/suit_v5_F200_StaticOptimization_activation.sto'),
 'box':   dict(name='박스 들기',
               setup_off='/data/stoop_results/box_stoop_so/B_off/setup_B_off.xml',
               setup_on='/data/stoop_results/box_stoop_so/B_on/setup_B_on.xml',
               act_off='/data/stoop_results/box_stoop_so/B_off/so_B_off_StaticOptimization_activation.sto',
               act_on='/data/stoop_results/box_stoop_so/B_on/so_B_on_StaticOptimization_activation.sto'),
 'gait':  dict(name='맨몸 보행',
               setup_off='/data/gait_results/gait_off_tight/setup.xml',
               setup_on='/data/gait_results/gait_on_tight/setup.xml',
               act_off='/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto',
               act_on='/data/gait_results/gait_on_tight/so_StaticOptimization_activation.sto'),
 'carry': dict(name='박스 운반',
               setup_off='/data/carry_results/carry_off/setup.xml',
               setup_on='/data/carry_results/carry_on/setup.xml',
               act_off='/data/carry_results/carry_off/so_StaticOptimization_activation.sto',
               act_on='/data/carry_results/carry_on/so_StaticOptimization_activation.sto'),
}
ORDER = ['squat', 'stoop', 'box', 'gait', 'carry']


def xget(txt, tag):
    m = re.search(rf'<{tag}>([^<]*)</{tag}>', txt)
    return m.group(1).strip() if m else None


def audit_model(path):
    """모델 파일에서 직접 추출."""
    if not path or not os.path.exists(path):
        return dict(err=f'모델 파일 없음: {path}')
    s = open(path, errors='ignore').read()
    coords = re.findall(r'<Coordinate name="([^"]+)">', s)
    muscles = re.findall(r'<(Thelen2003Muscle|Millard2012EquilibriumMuscle|'
                         r'DeGrooteFregly2016Muscle) name="([^"]+)">', s)
    blocks = re.findall(r'<CoordinateActuator name="(reserve_[^"]+)">(.*?)</CoordinateActuator>',
                        s, re.S)
    opt = {}
    for nm, b in blocks:
        m = re.search(r'<optimal_force>([^<]+)</optimal_force>', b)
        if not m:
            continue
        base = nm.replace('reserve_', '')
        grp = ('pelvis' if base.startswith('pelvis')
               else 'spine' if any(k in base for k in SPINE_KEYS) else 'other')
        opt.setdefault(grp, set()).add(float(m.group(1)))
    ctrl = set()
    for nm, b in blocks:
        mn = re.search(r'<min_control>([^<]+)</min_control>', b)
        mx = re.search(r'<max_control>([^<]+)</max_control>', b)
        if mn and mx:
            ctrl.add((float(mn.group(1)), float(mx.group(1))))
    # 쿠플러 제약 / 견갑 / armfix 표식
    couplers = re.findall(r'<CoordinateCouplerConstraint name="([^"]+)">', s)
    return dict(
        file=os.path.basename(path), n_coord=len(coords), n_muscle=len(muscles),
        n_reserve=len(blocks),
        opt={k: sorted(v) for k, v in opt.items()},
        control=sorted(ctrl),
        M1_scapula=('clav_elev' in s),
        couplers=couplers,
        has_forearm_ext=('radius_hand_r' in s and '-0.434' in s),
        sha8=hashlib.sha1(s.encode()).hexdigest()[:8],
    )


def audit_setup(path):
    if not path or not os.path.exists(path):
        return dict(err=f'setup 없음: {path}')
    t = open(path, errors='ignore').read()
    return dict(
        model=xget(t, 'model_file'),
        coords_file=xget(t, 'coordinates_file'),
        ext_loads=xget(t, 'external_loads_file'),
        t0=xget(t, 'initial_time'), t1=xget(t, 'final_time'),
        so_t0=xget(t, 'start_time'), so_t1=xget(t, 'end_time'),
        lowpass=xget(t, 'lowpass_cutoff_frequency_for_coordinates'),
        act_exp=xget(t, 'activation_exponent'),
        conv=xget(t, 'convergence_criterion'),
        max_iter=xget(t, 'maximum_iterations') or xget(t, 'max_iterations'),
        use_phys=xget(t, 'use_muscle_physiology'),
        replace_fs=xget(t, 'replace_force_set'),
    )


def audit_ext(path):
    """ExternalLoads XML → 부착 body / identifier / 데이터 파일."""
    if not path or not os.path.exists(path):
        return dict(err=f'ExternalLoads 없음: {path}')
    t = open(path, errors='ignore').read()
    forces = []
    for m in re.finditer(r'<ExternalForce name="([^"]+)">(.*?)</ExternalForce>', t, re.S):
        nm, b = m.group(1), m.group(2)
        forces.append(dict(name=nm, body=xget(b, 'applied_to_body'),
                           fid=xget(b, 'force_identifier'),
                           tid=xget(b, 'torque_identifier'),
                           fexp=xget(b, 'force_expressed_in_body'),
                           pexp=xget(b, 'point_expressed_in_body')))
    return dict(file=os.path.basename(path), forces=forces,
                datafile=xget(t, 'datafile'))


def suit_torque(ext_path):
    """외력 데이터에서 실제 적용된 슈트 토크 크기·부호·축을 읽는다."""
    if not ext_path or not os.path.exists(ext_path):
        return None
    d = Path(ext_path).parent
    t = open(ext_path, errors='ignore').read()
    dfs = set(re.findall(r'<(?:datafile|data_source_name)>([^<]+)<', t))
    for fn in dfs:
        p = d / fn.strip()
        if not p.exists():
            continue
        try:
            tbl = osim.TimeSeriesTable(str(p))
        except Exception:
            continue
        labs = list(tbl.getColumnLabels())
        out = {}
        for c in labs:
            if re.match(r'^(thor|pel)_T_[xyz]$', c):
                v = np.array([float(tbl.getDependentColumn(c)[i])
                              for i in range(tbl.getNumRows())])
                if np.abs(v).max() > 1e-9:
                    out[c] = round(float(v[np.argmax(np.abs(v))]), 3)
        if out:
            return out
    return {}


def es_set(act_path):
    if not act_path or not os.path.exists(act_path):
        return None
    tbl = osim.TimeSeriesTable(act_path)
    labs = list(tbl.getColumnLabels())
    E = sorted([l for l in labs if l.startswith(('IL_', 'LTpL', 'LTpT'))])
    T = np.array(list(tbl.getIndependentColumn()))
    dt = np.diff(T)
    return dict(n_es=len(E), n_col=len(labs), sha8=hashlib.sha1(
        '|'.join(E).encode()).hexdigest()[:8],
        t0=round(float(T[0]), 4), t1=round(float(T[-1]), 4), n_rows=len(T),
        dt_med=round(float(np.median(dt)), 5) if len(dt) else None,
        dt_uniform=bool(len(dt) and np.allclose(dt, dt[0], atol=1e-6)),
        es_list=E)


def sto_header(p):
    if not p or not os.path.exists(p):
        return {}
    out = {}
    with open(p, errors='ignore') as f:
        for line in f:
            if line.strip() == 'endheader':
                break
            if '=' in line:
                k, v = line.split('=', 1)
                out[k.strip()] = v.strip()
            elif 'version' in line.lower() or 'OpenSim' in line:
                out.setdefault('note', line.strip())
    return out


REPORT = {}
for k in ORDER:
    r = RUNS[k]
    s_off = audit_setup(r['setup_off']); s_on = audit_setup(r['setup_on'])
    m_off = audit_model(s_off.get('model'))
    m_on = audit_model(s_on.get('model'))
    REPORT[k] = dict(
        name=r['name'], setup_off=s_off, setup_on=s_on,
        model_off=m_off, model_on=m_on,
        ext_off=audit_ext(s_off.get('ext_loads')),
        ext_on=audit_ext(s_on.get('ext_loads')),
        suit_off=suit_torque(s_off.get('ext_loads')),
        suit_on=suit_torque(s_on.get('ext_loads')),
        es_off=es_set(r['act_off']), es_on=es_set(r['act_on']),
        hdr=sto_header(r['act_off']),
    )

json.dump(REPORT, open('/data/tight_rerun/condition_audit.json', 'w'),
          ensure_ascii=False, indent=1, default=str)


# ===================== 출력 =====================
def col(vals):
    return ' | '.join(str(v) for v in vals)


print('=' * 118)
print('5동작 해석 조건 전수 감사  (현행 논문 수치 기준 실행본)')
print('=' * 118)


def row(label, fn, verdict_fn=None):
    vals = []
    for k in ORDER:
        try:
            vals.append(fn(REPORT[k]))
        except Exception as e:
            vals.append(f'ERR')
    same = len(set(map(str, vals))) == 1
    mark = '✅' if same else '⚠️'
    print(f'{mark} {label:34s}', end='')
    for v in vals:
        print(f' {str(v)[:19]:19s}', end='')
    print()
    return same, vals


print(f'{"":37s}', end='')
for k in ORDER:
    print(f' {REPORT[k]["name"]:19s}', end='')
print('\n' + '-' * 118)

print('\n[모델]')
row('기저 .osim 파일', lambda r: r['model_off']['file'].replace('MaleFullBodyModel_v2.0_OS4_', ''))
row('좌표 수', lambda r: r['model_off']['n_coord'])
row('근육 수', lambda r: r['model_off']['n_muscle'])
row('M1 견갑(clav_elev)', lambda r: 'YES' if r['model_off']['M1_scapula'] else 'no')
row('전완 연장(forearm_v1)', lambda r: 'YES' if r['model_off']['has_forearm_ext'] else 'no')
row('CoordinateCoupler 수', lambda r: len(r['model_off']['couplers']))
row('OFF/ON 모델 동일', lambda r: 'same' if r['model_off']['sha8'] == r['model_on']['sha8'] else 'DIFF')

print('\n[reserve]')
row('척추 opt_force', lambda r: r['model_off']['opt'].get('spine'))
row('pelvis opt_force', lambda r: r['model_off']['opt'].get('pelvis'))
row('기타 opt_force', lambda r: r['model_off']['opt'].get('other'))
row('reserve 총 개수', lambda r: r['model_off']['n_reserve'])
row('min/max control', lambda r: r['model_off']['control'])

print('\n[SO 설정]')
row('activation exponent', lambda r: r['setup_off']['act_exp'])
row('convergence', lambda r: r['setup_off']['conv'])
row('use_muscle_physiology', lambda r: r['setup_off']['use_phys'])
row('lowpass cutoff', lambda r: r['setup_off']['lowpass'])
row('시간 범위', lambda r: f"{r['setup_off']['t0']}-{r['setup_off']['t1']}")
row('OFF/ON 시간범위 동일', lambda r: 'same' if (r['setup_off']['t0'], r['setup_off']['t1']) == (r['setup_on']['t0'], r['setup_on']['t1']) else 'DIFF')

print('\n[출력 샘플링]')
row('결과 프레임 수', lambda r: r['es_off']['n_rows'])
row('샘플 간격 (s)', lambda r: r['es_off']['dt_med'])
row('균일 간격', lambda r: 'YES' if r['es_off']['dt_uniform'] else 'no')

print('\n[슈트 모델링]')
row('ON 토크 성분', lambda r: r['suit_on'])
row('OFF 토크 성분', lambda r: r['suit_off'] if r['suit_off'] else '{} (없음)')
row('슈트 부착 body', lambda r: [f['body'] for f in r['ext_on']['forces']
                                 if f['name'].startswith('suit')] or 'n/a')

print('\n[외력 · GRF]')
row('ExternalForce 개수(ON)', lambda r: len(r['ext_on']['forces']))
row('부착 body 목록(ON)', lambda r: ','.join(f['body'] for f in r['ext_on']['forces']))

print('\n[지표 산출]')
row('ES 근육 수', lambda r: r['es_off']['n_es'])
row('ES 목록 해시', lambda r: r['es_off']['sha8'])
row('활성도 컬럼 총수', lambda r: r['es_off']['n_col'])

# ES 목록이 실제로 동일한지 원소 단위 확인
sets = {k: set(REPORT[k]['es_off']['es_list']) for k in ORDER}
base = sets['gait']
print('\n[ES 근육 집합 원소 대조 — 보행 기준]')
for k in ORDER:
    d1 = sets[k] - base; d2 = base - sets[k]
    print(f'  {REPORT[k]["name"]:12s} 동일' if not d1 and not d2
          else f'  {REPORT[k]["name"]:12s} 차이: 추가{sorted(d1)[:4]} 누락{sorted(d2)[:4]}')

print('\n[.sto 헤더]')
for k in ORDER:
    h = REPORT[k]['hdr']
    print(f'  {REPORT[k]["name"]:12s} {h}')
print('\nSAVED /data/tight_rerun/condition_audit.json')

"""Analyze carry-walk OFF/ON SO: ES(IL+LTpL+LTpT) peak per gait phase + suit effect% + reserve check.
Box 20kg anterior carry -> ES higher than pure gait, continuous (no distinct lift phase).
Reports: ES peak/mean OFF vs ON, suit effect %, spine reserve check, pattern-fit vs prior 4 motions."""
import numpy as np, opensim as osim, json
from collections import defaultdict

def load(path):
    t=osim.TimeSeriesTable(path); T=np.array(list(t.getIndependentColumn())); labs=list(t.getColumnLabels())
    D={c:np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]) for c in labs}
    return T,D,labs

R='/data/carry_results'
Toff,Aoff,labs=load(R+'/carry_off/so_StaticOptimization_activation.sto')
Ton,Aon,_=load(R+'/carry_on/so_StaticOptimization_activation.sto')
ES=[l for l in labs if l.startswith(('IL_','LTpL','LTpT'))]
def stack(D): return np.vstack([D[e] for e in ES])
pk_off=stack(Aoff).max(axis=0)*100.0; pk_on=stack(Aon).max(axis=0)*100.0
mn_off=stack(Aoff).mean(axis=0)*100.0; mn_on=stack(Aon).mean(axis=0)*100.0

PH=[('heel strike (R)',0.62,0.74),('mid-stance (R)',0.94,1.06),('toe-off (R)',1.30,1.42),('whole cycle',0.40,1.60)]
print("=== 나르기(carry 20kg) ES peak (max muscle IL+LTpL+LTpT) — gait phase별 OFF vs ON ===")
print(f"{'phase':18s} {'OFF%':>7s} {'ON%':>7s} {'Δ%p':>8s} {'suit%':>8s}  해석")
rows=[]
for ph,a,b in PH:
    mo=(Toff>=a)&(Toff<=b); mn=(Ton>=a)&(Ton<=b)
    o=pk_off[mo].max(); n=pk_on[mn].max(); d=n-o; pct=(d/o*100.0 if o>1e-6 else 0.0)
    itp='슈트 보조(ES↓)' if d<-0.3 else ('슈트 방해(ES↑)' if d>0.3 else '무영향(±0.3%p내)')
    print(f"{ph:18s} {o:7.2f} {n:7.2f} {d:+8.2f} {pct:+7.1f}%  {itp}")
    rows.append((ph,round(o,2),round(n,2),round(d,2),round(pct,1)))
whole=rows[-1]
mo=(Toff>=0.4)&(Toff<=1.6)
es_mean_o=mn_off[mo].max(); es_mean_n=mn_on[(Ton>=0.4)&(Ton<=1.6)].max()
print(f"\nES mean(근육평균) whole peak: OFF {es_mean_o:.2f}% ON {es_mean_n:.2f}% "
      f"Δ{es_mean_n-es_mean_o:+.2f}%p ({(es_mean_n-es_mean_o)/es_mean_o*100:+.1f}%) [{len(ES)} ES]")

# ---- reserve check ----
Tf,Foff,flabs=load(R+'/carry_off/so_StaticOptimization_force.sto')
_,Fon,_=load(R+'/carry_on/so_StaticOptimization_force.sto')
res=[l for l in flabs if l.startswith('reserve_')]
def grp(nm):
    b=nm.replace('reserve_','')
    if b.startswith('pelvis'): return 'pelvis(잔차흡수·예상)'
    if any(k in b for k in ['_FE','_LB','_AR','Abs_']): return 'spine(작아야=ES유효)'
    if any(k in b for k in ['shoulder','elv','elbow','wrist','pro_sup','clav']): return 'arm'
    if any(k in b for k in ['hip','knee','ankle','lumbar','subtalar','mtp']): return 'leg'
    return 'other(rib등)'
g=defaultdict(lambda:[0.0,''])
for r in res:
    for tag,F in [('OFF',Foff),('ON',Fon)]:
        mx=np.abs(F[r]).max(); G=grp(r)
        if mx>g[G][0]: g[G]=[mx,f"{r.replace('reserve_','')}({tag})"]
print("\n=== reserve actuator 점검 (|force| 최대, N 또는 N·m) ===")
print(f"{'group':24s} {'max|force|':>11s}   (actuator)")
for G in ['pelvis(잔차흡수·예상)','spine(작아야=ES유효)','arm','leg','other(rib등)']:
    if G in g: print(f"{G:24s} {g[G][0]:11.1f}   {g[G][1]}")
sp=g.get('spine(작아야=ES유효)',[0,''])[0]
print(f"\n>>> spine reserve 최대 {sp:.1f} (임계 10N·m): {'⚠️ ES 과소평가 가능' if sp>10 else '✅ 작음 → ES 유효'}")

# ---- pattern fit vs prior motions ----
print("\n=== 5동작 부하–슈트효과 패턴 정합 (ES peak suit effect) ===")
prior=[('squat(맨몸)','저부하',-47.0),('stoop(맨몸)','중부하',-32.0),
       ('box_stoop 20kg','고부하 들기',-23.0),('gait(맨몸 걷기)','초저부하',-0.0),
       ('carry 20kg 걷기(본)','걷기+전방하중',whole[4])]
for nm,cat,pct in prior:
    print(f"  {nm:22s} {cat:12s} suit effect {pct:+6.1f}%")

json.dump({'rows':rows,'es_mean_off':round(float(es_mean_o),2),'es_mean_on':round(float(es_mean_n),2),
           'whole_peak_off':whole[1],'whole_peak_on':whole[2],'whole_suit_pct':whole[4],
           'spine_res':round(float(sp),1),'n_es':len(ES),
           'reserves':{G:[round(float(g[G][0]),1),g[G][1]] for G in g}},
          open(R+'/carry_es_summary.json','w'),ensure_ascii=False,indent=1)
print("\nWROTE carry_es_summary.json")

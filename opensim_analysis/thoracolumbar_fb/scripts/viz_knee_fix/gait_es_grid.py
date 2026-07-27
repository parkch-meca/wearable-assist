import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, opensim as osim, json
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); plt.rcParams['font.family']='Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus']=False
def load(p):
    t=osim.TimeSeriesTable(p); T=np.array(list(t.getIndependentColumn())); labs=list(t.getColumnLabels())
    return T,{c:np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]) for c in labs},labs
R='/data/gait_results'
To,Ao,labs=load(R+'/gait_off_tight/so_StaticOptimization_activation.sto')
Tn,An,_=load(R+'/gait_on_tight/so_StaticOptimization_activation.sto')
ES=[l for l in labs if l.startswith(('IL_','LTpL','LTpT'))]
pko=np.vstack([Ao[e] for e in ES]).max(0)*100; pkn=np.vstack([An[e] for e in ES]).max(0)*100
both=json.load(open('/tmp/both.json'))
fig=plt.figure(figsize=(16,9)); gs=fig.add_gridspec(2,3)
# A: ES peak time series OFF vs ON (tight)
axA=fig.add_subplot(gs[0,:2])
axA.plot(To,pko,'b-o',ms=3,label='OFF (슈트 0)'); axA.plot(Tn,pkn,'r-o',ms=3,label='ON (슈트 24N·m)')
for t0,lbl in [(0.68,'heel strike'),(1.00,'mid-stance'),(1.36,'toe-off')]:
    axA.axvline(t0,color='gray',ls=':',lw=1); axA.text(t0,4,lbl,rotation=90,fontsize=8,va='bottom')
axA.set_xlabel('t (s)'); axA.set_ylabel('ES peak activation (%)'); axA.set_title('걷기 ES peak 시계열 OFF vs ON (정확 reserve) — 거의 겹침=작은 효과'); axA.legend(); axA.grid(alpha=0.3)
# B: suit Δ per phase, BOTH reserve settings (honest reserve-sensitivity)
axB=fig.add_subplot(gs[0,2])
phs=['heel','mid','toe','whole']
dstd=[r[2]-r[1] for r in both["std"]]; dtight=[r[2]-r[1] for r in both["tight"]]
x=np.arange(4); w=0.38
axB.bar(x-w/2,dstd,w,label='표준 reserve',color='#9aa'); axB.bar(x+w/2,dtight,w,label='정확 reserve',color='#c0504d')
axB.axhline(0,color='k',lw=0.8); axB.set_xticks(x); axB.set_xticklabels(phs); axB.set_ylabel('ΔES ON−OFF (%p)')
axB.set_title('슈트 ΔES — reserve 설정 민감\n(방향 불확실, 크기는 둘 다 작음 |≤6%p|)',fontsize=9.5); axB.legend(fontsize=8)
# C: absolute ES std vs tight + lifting 대비
axC=fig.add_subplot(gs[1,0])
cats=['걷기\n표준','걷기\n정확','stoop\n(들기)','squat\n(들기)','box\n(들기)']
vals=[11.1,35.1,None,None,None]; sui=[-5.6,-1.0,None,None,None]
axC.bar([0,1],[11.1,35.1],0.5,color=['#9aa','#c0504d'])
axC.text(0,12,'11%',ha='center',fontsize=9); axC.text(1,36,'35%',ha='center',fontsize=9)
axC.set_xticks([0,1]); axC.set_xticklabels(['걷기 표준\nreserve','걷기 정확\nreserve']); axC.set_ylabel('ES peak (%)'); axC.set_ylim(0,44)
axC.set_title('절대 ES는 reserve 의존(11~35%)\n=교차피험자 잔차 불확실성',fontsize=9.5)
# D: interpretation
axD=fig.add_subplot(gs[1,1:]); axD.axis('off')
txt=("[4] 걷기 OFF/ON SO — 슈트가 정상 보행에 미치는 영향 (armfix, 실측 GRF x1.069)\n\n"
     "★ Robust 결론 (reserve 설정 무관):\n"
     "  · 슈트효과 |ΔES| ≤ 6%p — 들기(stoop −32%, squat −47%, box −23%)\n"
     "    보다 압도적으로 작음\n"
     "  · 들기용 슈트(24N·m 상시 신전)는 정상 보행 ES를 유의미하게\n"
     "    보조하지도, 방해하지도 않음 → '거의 무영향'\n\n"
     "● 정확(tight) reserve 기준: whole −1.0%p, mid-stance +4.3%p\n"
     "  (약간 증가=상시 신전 couple이 국소 체간모멘트와 어긋남),\n"
     "  heel +0.9, toe −1.0 → near-zero·혼합, 큰 방해는 아님\n\n"
     "● 정직한 한계:\n"
     "  · 절대 ES는 reserve 설정 의존(11~35%): 표준(opt100)은 척추부하를\n"
     "    reserve가 흡수→과소평가, 정확(opt5)은 근육이 담당(spine reserve\n"
     "    16.8→1.0N·m). 교차피험자 GRF 잔차(ty189N)가 근본 원인\n"
     "  · 슈트효과 '방향'도 reserve 민감(−5.6~+4.3%p) → 절대 sign은 불확실\n"
     "  · %감소 headline 안 씀(baseline·잔차로 불안정 — 예상대로)\n"
     "  · pelvis reserve 189N은 OFF/ON 상쇄(잔차 흡수)")
axD.text(0.0,0.99,txt,va='top',ha='left',fontsize=9.8,bbox=dict(boxstyle='round',fc='#f5f5f5',ec='#888'))
fig.suptitle('걷기 [4] OFF/ON SO — 들기용 슈트는 정상 보행에 거의 무영향 (효과 ≤6%p ≪ 들기, 2026-07-27)',fontsize=12.5,weight='bold')
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/gait_es_results_grid.png',dpi=105)
print('SAVED')

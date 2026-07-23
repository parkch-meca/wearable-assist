"""Analyze OFF/ON SO for the stoop box-lift. ES = IL + LTpL + LTpT (iliocostalis+longissimus).
Reports ES peak (max of ES-mean over time), per-phase ES mean, OFF->ON reduction %, box effect
(noload->off), and a time-series + phase plot. Compares to prior headline results."""
import numpy as np, json
from pathlib import Path
import opensim as osim
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
ROOT=Path('/data/stoop_results/box_stoop_so')
CONDS=['B_noload','B_off','B_on']
PHASES=[('reach',0.5,1.9),('liftoff',1.9,3.0),('carryup',3.0,3.5),('carry_hold',3.5,4.3),('lower',4.3,5.5),('return',5.5,6.0)]
def load(cond):
    p=ROOT/cond/f'so_{cond}_StaticOptimization_activation.sto'
    tbl=osim.TimeSeriesTable(str(p)); labs=list(tbl.getColumnLabels()); t=np.array(list(tbl.getIndependentColumn()))
    es=[l for l in labs if l.startswith(('IL_','LTpL','LTpT'))]
    A=np.array([[tbl.getDependentColumn(e)[i] for e in es] for i in range(tbl.getNumRows())])  # rows x es
    esmean=A.mean(axis=1)*100; espeakmus=A.max(axis=1)*100
    return t,esmean,espeakmus,len(es)
data={c:load(c) for c in CONDS}
nes=data['B_noload'][3]
LOAD_LO,LOAD_HI=1.9,5.4   # box-loaded window (exclude fast unloaded return transient)
def peakinfo(t,esmean):
    msk=(t>=LOAD_LO)&(t<=LOAD_HI); i=int(np.argmax(np.where(msk,esmean,-1))); return esmean[i],t[i]
print(f"ES muscles: {nes} (IL+LTpL+LTpT)   [peak within LOADED window {LOAD_LO}-{LOAD_HI}s]\n")
# loaded-window peak (fast unloaded return transient excluded)
res={}
for c in CONDS:
    t,em,_,_=data[c]; pk,pt=peakinfo(t,em); res[c]=dict(peak=pk,peak_t=pt)
    print(f"{c:9s} ES-mean loaded-peak={pk:5.2f}% @t={pt:.2f}s")
off,on,nl=res['B_off'],res['B_on'],res['B_noload']
# reduction AT the OFF peak-load moment (same instant) — the clean "at peak load" number
tt=data['B_off'][0]; pt=off['peak_t']; pk_i=int(np.argmin(np.abs(tt-pt)))
on_at_pk=data['B_on'][1][pk_i]; nl_at_pk=data['B_noload'][1][pk_i]
red_peak=(off['peak']-on_at_pk)/off['peak']*100
boxeff=(off['peak']-nl_at_pk)/nl_at_pk*100
# loaded-window mean reduction (1.9-5.4)
lmsk=(tt>=LOAD_LO)&(tt<=LOAD_HI)
off_lm=data['B_off'][1][lmsk].mean(); on_lm=data['B_on'][1][lmsk].mean()
red_loadmean=(off_lm-on_lm)/off_lm*100
print(f"\n>>> SUIT EFFECT at peak-load moment (t={pt:.2f}s): OFF {off['peak']:.2f}% -> ON {on_at_pk:.2f}%  = -{red_peak:.1f}%")
print(f">>> SUIT EFFECT loaded-window mean: OFF {off_lm:.2f}% -> ON {on_lm:.2f}%  = -{red_loadmean:.1f}%")
print(f">>> BOX LOAD effect (at peak moment): noload {nl_at_pk:.2f}% -> box {off['peak']:.2f}%  = +{boxeff:.0f}%")
# per-phase ES mean + reduction
print("\nPhase           noload   OFF     ON    suitΔ%")
tt=data['B_noload'][0]
phase_rows=[]
for pn,a,b in PHASES:
    vals={}
    for c in CONDS:
        t,em,_,_=data[c]; msk=(t>=a)&(t<=b); vals[c]=em[msk].mean() if msk.any() else float('nan')
    d=(vals['B_off']-vals['B_on'])/vals['B_off']*100 if vals['B_off']>0 else 0
    phase_rows.append((pn,vals['B_noload'],vals['B_off'],vals['B_on'],d))
    print(f"{pn:12s} {vals['B_noload']:6.2f}  {vals['B_off']:6.2f}  {vals['B_on']:6.2f}   -{d:4.1f}")
# ---- plot ----
fig,ax=plt.subplots(1,2,figsize=(15,6))
col={'B_noload':'#888','B_off':'#c0392b','B_on':'#2471a3'}
lab={'B_noload':'무부하(참조)','B_off':'박스20kg 슈트OFF','B_on':'박스20kg 슈트ON 24N·m'}
for c in CONDS:
    t,em,_,_=data[c]; ax[0].plot(t,em,color=col[c],lw=2,label=lab[c])
for pn,a,b in PHASES: ax[0].axvspan(a,b,color='k',alpha=0.03)
ax[0].axvline(off['peak_t'],color='k',ls=':',alpha=0.4)
ax[0].axvspan(5.4,6.0,color='orange',alpha=0.08)
ax[0].text(5.55,24,'급복귀\n아티팩트\n(하중X)',fontsize=8,color='#a60',ha='center',va='top')
ax[0].set_xlabel('시간 (s)'); ax[0].set_ylabel('ES 평균 활성도 (%)'); ax[0].legend(fontsize=10,loc='upper left'); ax[0].set_title(f'박스 stoop 들기 ES 활성도 (근육 {nes}개 평균)',fontweight='bold'); ax[0].grid(alpha=0.3)
ax[0].annotate(f'슈트효과 -{red_peak:.1f}%\n(최대하중 {off["peak"]:.1f}→{on_at_pk:.1f}%)',xy=(off['peak_t'],off['peak']),xytext=(off['peak_t']+0.5,off['peak']+3),fontsize=11,fontweight='bold',color='#2471a3',arrowprops=dict(arrowstyle='->',color='k'))
pn=[r[0] for r in phase_rows]; x=np.arange(len(pn)); w=0.27
ax[1].bar(x-w,[r[1] for r in phase_rows],w,color='#888',label='무부하')
ax[1].bar(x,[r[2] for r in phase_rows],w,color='#c0392b',label='슈트OFF')
ax[1].bar(x+w,[r[3] for r in phase_rows],w,color='#2471a3',label='슈트ON')
for i,r in enumerate(phase_rows):
    if r[4]>0.5: ax[1].text(i,max(r[2],r[3])+0.4,f'-{r[4]:.0f}%',ha='center',fontsize=9,color='#2471a3',fontweight='bold')
ax[1].set_xticks(x); ax[1].set_xticklabels(pn,rotation=30,ha='right'); ax[1].set_ylabel('ES 평균 활성도 (%)'); ax[1].legend(fontsize=10); ax[1].set_title('구간별 ES 활성도 + 슈트 감소율',fontweight='bold'); ax[1].grid(alpha=0.3,axis='y')
fig.suptitle(f'박스 20kg stoop 들기 — 슈트 효과: 최대하중 ES {off["peak"]:.1f}% → {on_at_pk:.1f}% (-{red_peak:.1f}%), 하중구간 평균 -{red_loadmean:.1f}%  |  근육 {nes}개',fontsize=13,fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.96])
OUT='/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_stoop_so_results.png'
fig.savefig(OUT,dpi=115,facecolor='white'); print("\nSAVED",OUT)
json.dump({'peak':{c:res[c]['peak'] for c in CONDS},'peak_t':{c:res[c]['peak_t'] for c in CONDS},
           'off_peak':off['peak'],'on_at_peak':float(on_at_pk),'suit_reduction_peak':red_peak,
           'suit_reduction_loadmean':red_loadmean,'box_effect_peak':boxeff,'n_es':nes,
           'phases':[{'phase':r[0],'noload':r[1],'off':r[2],'on':r[3],'suit_red':r[4]} for r in phase_rows]},
          open('/data/stoop_results/box_stoop_so/summary.json','w'))
print("SAVED summary.json")

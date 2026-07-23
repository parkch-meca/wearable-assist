"""Analyze OFF/ON SO for the stoop box-lift. ES = IL+LTpL+LTpT (iliocostalis+longissimus, 76).
Reports BOTH metrics: ES peak (max muscle, EMG-aligned) and ES mean (muscle avg). Suit reduction
at peak-load moment + per phase + loaded-window; box-load effect. Return handled by gentle motion."""
import numpy as np, json, os
from pathlib import Path
import opensim as osim
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
ROOT=Path('/data/stoop_results/box_stoop_so'); CONDS=['B_noload','B_off','B_on']
PHASES=[('reach',0.5,1.9),('liftoff',1.9,3.0),('carryup',3.0,3.6),('carry_hold',3.6,4.5),('lower',4.5,6.0),('return',6.0,7.5)]
LOAD_LO,LOAD_HI=1.9,5.9
def load(cond):
    p=ROOT/cond/f'so_{cond}_StaticOptimization_activation.sto'
    tbl=osim.TimeSeriesTable(str(p)); labs=list(tbl.getColumnLabels()); t=np.array(list(tbl.getIndependentColumn()))
    es=[l for l in labs if l.startswith(('IL_','LTpL','LTpT'))]
    A=np.array([[tbl.getDependentColumn(e)[i] for e in es] for i in range(tbl.getNumRows())])*100
    return t,A.max(axis=1),A.mean(axis=1),es   # t, peak(max muscle), mean, es-names
D={c:load(c) for c in CONDS}; nes=len(D['B_noload'][3]); t=D['B_noload'][0]
msk=(t>=LOAD_LO)&(t<=LOAD_HI)
def series(c,metric): return D[c][1] if metric=='peak' else D[c][2]
def peak_at(c,metric):
    s=series(c,metric); i=int(np.argmax(np.where(msk,s,-1))); return s[i],t[i],i
print(f"ES muscles: {nes} (IL+LTpL+LTpT). Loaded window {LOAD_LO}-{LOAD_HI}s\n")
summary={'n_es':nes}
for metric in ('peak','mean'):
    opk,opt,oi=peak_at('B_off',metric)
    on_at=series('B_on',metric)[oi]; nl_at=series('B_noload',metric)[oi]
    red=(opk-on_at)/opk*100; boxeff=(opk-nl_at)/nl_at*100 if nl_at>0 else 0
    olm=series('B_off',metric)[msk].mean(); onlm=series('B_on',metric)[msk].mean(); redlm=(olm-onlm)/olm*100
    lab='ES PEAK (max muscle)' if metric=='peak' else 'ES MEAN (muscle avg)'
    print(f"[{lab}]  peak-load moment t={opt:.2f}s")
    print(f"   suit: OFF {opk:.1f}% -> ON {on_at:.1f}%  = -{red:.1f}%   | loaded-mean: OFF {olm:.1f}% -> ON {onlm:.1f}% = -{redlm:.1f}%")
    print(f"   box-load effect at peak: noload {nl_at:.1f}% -> box {opk:.1f}% = +{boxeff:.0f}%\n")
    summary[metric]={'off_peak':float(opk),'on_at_peak':float(on_at),'suit_red_peak':float(red),
                     'suit_red_loadmean':float(redlm),'box_eff':float(boxeff),'peak_t':float(opt)}
# per-phase (peak metric, EMG-aligned)
print("Phase(ES peak)  noload   OFF     ON    suitΔ%")
phrows=[]
for pn,a,b in PHASES:
    pm=(t>=a)&(t<=b); v={c:series(c,'peak')[pm].mean() for c in CONDS}
    d=(v['B_off']-v['B_on'])/v['B_off']*100 if v['B_off']>0 else 0
    phrows.append((pn,v['B_noload'],v['B_off'],v['B_on'],d)); print(f"{pn:12s} {v['B_noload']:6.1f}  {v['B_off']:6.1f}  {v['B_on']:6.1f}   -{d:4.1f}")
summary['phases']=[{'phase':r[0],'noload':r[1],'off':r[2],'on':r[3],'suit_red':r[4]} for r in phrows]
# ---- plot (ES peak metric primary) ----
fig,ax=plt.subplots(1,2,figsize=(15,6))
col={'B_noload':'#888','B_off':'#c0392b','B_on':'#2471a3'}; lab={'B_noload':'무부하(참조)','B_off':'박스20kg 슈트OFF','B_on':'박스20kg 슈트ON 24N·m'}
for c in CONDS: ax[0].plot(t,series(c,'peak'),color=col[c],lw=2,label=lab[c])
for pn,a,b in PHASES: ax[0].axvspan(a,b,color='k',alpha=0.03)
P=summary['peak']; ax[0].axvline(P['peak_t'],color='k',ls=':',alpha=0.4)
ax[0].annotate(f'슈트효과 -{P["suit_red_peak"]:.0f}%\n(최대하중 {P["off_peak"]:.0f}→{P["on_at_peak"]:.0f}%)',xy=(P['peak_t'],P['off_peak']),xytext=(P['peak_t']+0.6,P['off_peak']+4),fontsize=11,fontweight='bold',color='#2471a3',arrowprops=dict(arrowstyle='->'))
ax[0].set_xlabel('시간 (s)'); ax[0].set_ylabel('ES peak 활성도 (최대근육, %)'); ax[0].legend(fontsize=10,loc='upper left'); ax[0].set_title(f'박스 stoop 들기 ES peak (EMG정렬 지표, {nes}근육 중 최대)',fontweight='bold'); ax[0].grid(alpha=0.3)
pn=[r[0] for r in phrows]; x=np.arange(len(pn)); w=0.27
ax[1].bar(x-w,[r[1] for r in phrows],w,color='#888',label='무부하'); ax[1].bar(x,[r[2] for r in phrows],w,color='#c0392b',label='슈트OFF'); ax[1].bar(x+w,[r[3] for r in phrows],w,color='#2471a3',label='슈트ON')
for i,r in enumerate(phrows):
    if r[4]>0.5: ax[1].text(i,max(r[2],r[3])+1,f'-{r[4]:.0f}%',ha='center',fontsize=9,color='#2471a3',fontweight='bold')
ax[1].set_xticks(x); ax[1].set_xticklabels(pn,rotation=30,ha='right'); ax[1].set_ylabel('ES peak 활성도 (%)'); ax[1].legend(fontsize=10); ax[1].set_title('구간별 ES peak + 슈트 감소율',fontweight='bold'); ax[1].grid(alpha=0.3,axis='y')
M=summary['mean']
fig.suptitle(f'박스 20kg stoop 들기 — 슈트효과(ES peak): 최대하중 {P["off_peak"]:.0f}%→{P["on_at_peak"]:.0f}% (-{P["suit_red_peak"]:.0f}%)  |  ES mean 지표로도 -{M["suit_red_peak"]:.0f}% (지표 무관 robust)',fontsize=12.5,fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.96])
OUT='/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_stoop_so_results.png'
fig.savefig(OUT,dpi=115,facecolor='white'); print("\nSAVED",OUT)
json.dump(summary,open(ROOT/'summary.json','w')); print("SAVED summary.json")

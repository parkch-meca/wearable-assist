import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False

cond=['맨몸 squat\n(무부하)','stoop\n(중부하)','박스 squat\n(고부하)']
off=[0.231,0.319,0.801]; on=[0.145,0.230,0.712]
pct=[37,28,11]; absred=[o-n for o,n in zip(off,on)]

fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(2,2,height_ratios=[1,1.1],hspace=0.33,wspace=0.25)
fig.suptitle("squat 슈트 효과 47% 타당성 확인 — 부하–효과 패턴 + 문헌 대조",fontsize=20,fontweight='bold',x=0.5,y=0.98)

# (1) table
axt=fig.add_subplot(gs[0,:]); axt.axis('off')
rows=[["조건","ES peak OFF","ES peak ON","% 감소","절대 감소(activation)"],
      ["맨몸 squat (무부하)","0.231","0.145","37%","0.087"],
      ["stoop (중부하)","0.319","0.230","28%","0.089"],
      ["박스 squat (고부하)","0.801","0.712","11%","0.089"]]
tb=axt.table(cellText=rows,bbox=[0.04,0.18,0.92,0.74])
tb.auto_set_font_size(False); tb.set_fontsize(13)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    if c==4 and r>0: cell.set_facecolor('#fff2cc')
    cell.set_edgecolor('#aaa')
axt.text(0.5,0.05,"★ 같은 peak 근육(IL_R11). 절대 감소량이 세 조건 모두 ~0.088로 거의 일정 → 고정 24 N·m 토크가 동일량 상쇄.",
         ha='center',fontsize=13,color='#7a0000',fontweight='bold')

# (2) % vs baseline (monotonic)
ax1=fig.add_subplot(gs[1,0])
ax1.plot(off,pct,'o-',color='#c0392b',ms=11,lw=2)
for x,y,l in zip(off,pct,cond): ax1.annotate(l.replace('\n',' '),(x,y),textcoords="offset points",xytext=(6,8),fontsize=10)
ax1.set_xlabel("부하 = ES peak OFF (활성도)",fontsize=12); ax1.set_ylabel("슈트 효과 (% 감소)",fontsize=12)
ax1.set_title("부하 ↑ → % 효과 ↓ (단조)",fontsize=13,fontweight='bold'); ax1.grid(alpha=0.3)

# (3) absolute reduction (constant)
ax2=fig.add_subplot(gs[1,1])
ax2.bar(range(3),absred,color=['#2e8b57','#e0a000','#c0392b'])
ax2.axhline(np.mean(absred),ls='--',color='#444',label=f"평균 {np.mean(absred):.3f}")
ax2.set_xticks(range(3)); ax2.set_xticklabels(cond,fontsize=10)
ax2.set_ylabel("절대 감소량 (activation)",fontsize=12); ax2.set_ylim(0,0.12)
ax2.set_title("절대 감소량 ≈ 일정 (고정 토크 특성)",fontsize=13,fontweight='bold')
for i,v in enumerate(absred): ax2.text(i,v+0.003,f"{v:.3f}",ha='center',fontsize=11,fontweight='bold')
ax2.legend(fontsize=11)

fig.text(0.04,0.025,
 "결론: 47%(hold)/37%(부하정점) 타당. ① 부하–효과 단조 + 절대감소 ~0.088 일정 = 고정토크 메커니즘.  "
 "② 슈트=thoracic/pelvis 24 N·m 순수 토크 couple(모멘트암 무관, 자세 불변, stoop과 동일 정의).\n"
 "③ 문헌 대조: 부하 squat(15kg) exo ES 감소 10–17%(P3 Hasenmaier 2026) ↔ 내 박스 squat 11% 일치.  "
 "맨몸 squat ES 18–23%MVC는 무부하라 문헌 부하 squat(30–50%MVC)보다 낮음(정상).",
 fontsize=12, color='#222')
fig.text(0.04,0.0,"한계: 박스 squat ES peak 0.80(80%MVC)은 문헌 30–50%보다 높음(박스 모션 부하/경사 더 큼) — 단 '감소%'는 문헌 일치. GRF는 준정적 근사(reserve 흡수).",
         fontsize=10.5,color='#7a0000')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/squat_47pct_validity_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)

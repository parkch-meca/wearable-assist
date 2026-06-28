import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
D=json.load(open('/tmp/cmp_render/feas_pose.json')); R={k:round(v*100,1) for k,v in D['resid'].items() if k not in ('nR','nL')}
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(17,10)); gs=fig.add_gridspec(2,3,height_ratios=[1.15,1.0],width_ratios=[1,1,1.5],hspace=0.16,wspace=0.1)
fig.suptitle("박스 양손 파지 — [0단계] 해 존재 + 생성/검증 분리 결과 (검증 미통과)",fontsize=18,fontweight='bold',y=0.99)
# top-left/mid: best renders (feas3)
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/feas3_front.png","앞 — 최신 렌더"),
                          ("/tmp/cmp_render/interf/feas3_side.png","옆 — 최신 렌더")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold')
# top-right: feasibility
axf=fig.add_subplot(gs[0,2]); axf.axis('off')
axf.text(0,1.0,"[0단계] 전 제약 동시 만족 해 = 존재 ✅",fontsize=14,fontweight='bold',color='#1a7',va='top')
axf.text(0,0.90,"제대로 된 기하(손=부피, 발=평평, 박스=테이블위)로 풀이.\n잔차(최적점, cm):",fontsize=11.5,va='top')
rows=[["제약","잔차","허용","판정"],
 ["손R 박스도달",f"{R['reachR']}cm","<4","✅"],
 ["손L 박스도달",f"{R['reachL']}cm","<4","✅"],
 ["손R/L 관통",f"{R['penR']}/{R['penL']}cm","<1","✅"],
 ["발 평평(기울기)",f"{R['foot_tilt']}cm","<2","✅"],
 ["발 들림",f"{R['foot_lift']}cm","<2","✅"],
 ["균형(COM)",f"{R['bal']}cm","<1","✅"],
 ["다리 테이블침범",f"{R['interf']}cm","<2","✅"]]
tb=axf.table(cellText=rows,bbox=[0,0.34,1.0,0.52]); tb.auto_set_font_size(False); tb.set_fontsize(10.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#dff0df')
    cell.set_edgecolor('#aaa')
axf.text(0,0.28,"→ 기하학적으로 양손 파지 해는 존재(over-constrained 아님).\n   측정 확인: 발 평평·다리 정상폭(무릎 z간격 0.17m)·관통 0.",fontsize=11,va='top',color='#225')
# bottom: verification log
axl=fig.add_subplot(gs[1,:]); axl.axis('off')
axl.text(0,1.0,"[생성/검증 분리 — 독립 검증 subagent 3회 (수치·의도 차단, 그림만 판정)]",fontsize=14,fontweight='bold',color='#a00',va='top')
log=[["회차","독립검증 결과","검증자가 잡은 문제 (수치 없이 그림만으로)","조치"],
 ["1","FAIL","발이 다리와 분리돼 떠 보임 / 박스가 테이블 위에 안 얹히고 공중에 뜸","테이블 렌더 스케일 버그(tht/2) 수정"],
 ["2","FAIL","박스 아래 테이블 안 보임(앞뷰) / 다리 개구리처럼 벌어짐 / 발 접지 불명확","측정: 다리 정상폭=렌더 모호. 반투명테이블+전신프레이밍"],
 ["3","FAIL","박스=테이블위 OK·발접지 OK·박스식별 OK (←이전 문제 해소) / 단 손가락이 박스 관통처럼 보임·상체 과도하게 수평","미해결"]]
tb2=axl.table(cellText=log,bbox=[0,0.30,1.0,0.62]); tb2.auto_set_font_size(False); tb2.set_fontsize(10)
for (r,c),cell in tb2.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    elif r==3: cell.set_facecolor('#fff2cc')
    else: cell.set_facecolor('#fbe9e7')
    cell.set_edgecolor('#aaa'); cell.set_text_props(fontsize=9.5)
axl.text(0,0.22,"★ 구조가 작동함: 독립 검증자가 매 라운드 실제 시각 문제를 잡아냄(예전 '자가검증 ✅'이 놓치던 것). 사용자가 아니라 검증자가 먼저 잡음.",fontsize=11.5,fontweight='bold',color='#a00',va='top')
axl.text(0,0.13,"남은 미해결(라운드3): ① side뷰에서 손가락이 솔리드 박스를 감싸며 내부로 들어가 보임(기하상 wrist 관통0이나 손가락 mesh가 박스에 겹침)  "
                "② 50cm 테이블+다리 테이블뒤 제약이 상체를 거의 수평으로 깊게 숙이게 함(무릎 전방=squat이 테이블에 막힘).",fontsize=10.5,va='top',color='#333')
axl.text(0,0.04,"권고: (A) 테이블을 허리높이(~75cm)로 올리면 상체 덜 숙임+손가락이 박스 옆면 파지로 자연스러워짐 → 재검증.  (B) 50cm 유지+파지 단순표현.  ⚠️ 억지 PASS 안 함.",fontsize=10.5,fontweight='bold',va='top',color='#225')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_feasibility_report.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)

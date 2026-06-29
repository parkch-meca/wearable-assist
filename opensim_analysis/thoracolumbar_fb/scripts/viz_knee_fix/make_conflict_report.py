import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(17,10)); gs=fig.add_gridspec(2,3,height_ratios=[1.0,1.05],hspace=0.18,wspace=0.08)
fig.suptitle("박스 양손 파지 — 두 방식 모두 검증 미통과 + 충돌 원인 (정직 보고)",fontsize=18,fontweight='bold',y=0.99)
imgs=[("/tmp/cmp_render/interf/feas3_side.png","① 손 닿음 우선 → 손이 박스에 닿으나\n엄지면 파지·손가락 겹침 (검증 FAIL)"),
      ("/tmp/cmp_render/interf/m1_side.png","② 손바닥 방향 우선(옆면) → 손이\n박스에서 21cm 빗나감 (off-box)"),
      ("/tmp/cmp_render/interf/m2_side.png","③ 바닥 받쳐들기 → 손이 박스 아래\n17cm 못 미침 (검증 FAIL, off-box)")]
for i,(p,t) in enumerate(imgs):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=11,fontweight='bold')
ax=fig.add_subplot(gs[1,:]); ax.axis('off')
ax.text(0,1.0,"[근본 원인 — 모델 한계, 사실]",fontsize=14,fontweight='bold',color='#a00',va='top')
ax.text(0,0.90,"• 이 모델은 손목·전완이 LOCKED: pro_sup_r(전완 회내/회외), wrist_flex_r, wrist_dev_r 모두 잠김(getLocked=True).\n"
               "  → 손 방향이 전완에 고정. 손바닥을 박스면으로 독립적으로 돌릴 수 없음. 방향 제어는 shoulder_rot(어깨회전) 하나뿐(팔 자세와 커플링).",
         fontsize=11.5,va='top')
ax.text(0,0.72,"[충돌 — 양립 불가 (전 자유도 IK로 확인)]",fontsize=14,fontweight='bold',color='#a00',va='top')
rows=[["시도","손-박스 도달","손바닥 방향","독립검증","원인"],
 ["① 손 닿음 우선","✅ 1–2cm","❌ 엄지면·손가락겹침","FAIL","방향 목적함수 없음"],
 ["② 손바닥 옆면 우선","❌ 21cm 빗남","△ 개선","off-box","방향 맞추면 손이 박스 못감"],
 ["③ 바닥 받쳐들기","❌ 17cm 못미침","palm-up 0.9","FAIL","테이블+locked손목이 받침 막음"]]
tb=ax.table(cellText=rows,bbox=[0,0.40,0.72,0.30]); tb.auto_set_font_size(False); tb.set_fontsize(10.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#fbe9e7')
    cell.set_edgecolor('#aaa')
ax.text(0.74,0.70,"[해 존재 검사 결과]\n손 위치만 보면 해 존재(①).\n그러나 '자연스러운 손바닥 파지'\n+ '손이 박스 도달'을 동시에는\n불가 — locked 손목이 둘을\n양립 못 하게 함.\n\n손 방향을 맞추려 어깨를 돌리면\n팔 자세가 바뀌어 손이 박스에서\n17–21cm 멀어짐.",fontsize=10.5,va='top',color='#333')
ax.text(0,0.35,"[★ 생성/검증 분리 작동] 독립 검증 subagent가 ①③을 그림만으로 FAIL 판정(손가락 겹침/손 허공). 제가 자가판정 안 함. 억지 PASS 안 함.",
        fontsize=11,fontweight='bold',color='#a00',va='top')
ax.text(0,0.26,"[방향 옵션 — 결정 요청]",fontsize=13,fontweight='bold',va='top')
ax.text(0,0.18,"(A) 손목/전완 잠금 해제 후 자연 파지 각도 부여 — '시각화 전용'(knee-fix 선례처럼 .osim 정량 불변, SO/ES는 손방향 무관).  ← 근본 원인 직접 해결\n"
               "(B) 테이블 ~75cm로 올림 — 덜 숙이나 손목 잠김은 그대로(손방향 미해결).\n"
               "(C) 파지 클로즈업 없이 들기 동작만 — 손-박스 근접만(v11b 영상-only 방식).\n"
               "(D) 파지 단순/추상 표현.",fontsize=11,va='top',color='#225')
ax.text(0,0.02,"제 정직한 판단: 현재 모델로 '자연스러운 양손 박스 파지 클로즈업'은 locked 손목 때문에 안 됨. (A) 시각화 전용 손목 해제가 가장 직접적.",
        fontsize=11,fontweight='bold',va='top',color='#7a0000')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_conflict_report.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)

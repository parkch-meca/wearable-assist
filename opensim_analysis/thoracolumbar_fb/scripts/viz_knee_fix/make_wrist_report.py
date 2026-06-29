import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(17,10)); gs=fig.add_gridspec(2,3,height_ratios=[1.05,1.0],hspace=0.17,wspace=0.08)
fig.suptitle("손목 잠금 시각화 해제 — palm 방향 해결(성과) + 남은 충돌(정직 보고)",fontsize=18,fontweight='bold',y=0.99)
imgs=[("/tmp/cmp_render/interf/wf75_front.png","손목해제 앞 — 양손 박스 옆면,\npalm 박스 향함 (엄지면 해결!)"),
      ("/tmp/cmp_render/interf/wf75_side.png","손목해제 옆 — 손 박스 닿으나\n팔 akimbo·위에서 접근 (검증 FAIL)"),
      ("/tmp/cmp_render/interf/wfN_side.png","팔 자연스러움 우선 — 팔꿈치 내림\n그러나 손 12cm 빗남 (off-box)")]
for i,(p,t) in enumerate(imgs):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=11,fontweight='bold')
ax=fig.add_subplot(gs[1,:]); ax.axis('off')
ax.text(0,1.0,"[성과] 손목 잠금 시각화 전용 해제 = palm 방향(5개월 근본원인) 해결",fontsize=14,fontweight='bold',color='#1a7',va='top')
ax.text(0,0.90,"• pro_sup/wrist_flex/wrist_dev를 메모리에서만 해제(.osim 디스크 locked=true 불변 확인, SO/ES는 손방향 무관 → 정량 영향 0).\n"
               "• 결과: palm normal R −0.98 / L 1.00 = 양 손바닥이 박스 옆면 향함. 엄지면 파지 해소(앞뷰에서 자연스러운 옆면 그립).\n"
               "• 손 도달도 가능(R 0.4cm, L 0.0cm). → '손바닥 방향 못 돌림'이라는 진짜 병목은 풀림.",fontsize=11.5,va='top',color='#225')
ax.text(0,0.62,"[남은 충돌] 팔 도달 ↔ 팔 자연스러움 (테이블-도달 기하)",fontsize=14,fontweight='bold',color='#a00',va='top')
rows=[["시도","손 박스 도달","palm 방향","팔 자세","독립검증"],
 ["손목해제 50cm","✅","✅","깊은 stoop·위에서","FAIL"],
 ["손목해제 75cm","✅ 0~0.4cm","✅","팔 akimbo·위에서 접근","FAIL"],
 ["+팔 자연 prior","❌ 12cm 빗남","✅","팔꿈치 내림(자연)","off-box"]]
tb=ax.table(cellText=rows,bbox=[0,0.34,0.74,0.24]); tb.auto_set_font_size(False); tb.set_fontsize(10)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#fbe9e7')
    cell.set_edgecolor('#aaa')
ax.text(0.76,0.60,"테이블 뒤에 서서(발 테이블 앞)\n테이블 위 박스를 잡으려면:\n손이 박스에 닿으려면 팔이\nakimbo/위에서 접근(부자연),\n팔을 자연스럽게(팔꿈치 내림)\n하면 손이 12cm 못 닿음.\n= 기하적 tradeoff.",fontsize=10.5,va='top',color='#333')
ax.text(0,0.28,"[★ 생성/검증 분리 작동] 독립 검증자가 매 라운드(엄지면→akimbo→위에서접근→off-box) 그림만으로 FAIL. 사용자 아닌 검증자가 잡음. 억지 PASS 안함.",
        fontsize=11,fontweight='bold',color='#a00',va='top')
ax.text(0,0.20,"[방향 옵션 — 결정 요청]",fontsize=13,fontweight='bold',va='top')
ax.text(0,0.13,"(A) 발 위치를 테이블 옆/가까이 (사람이 테이블에 다가서거나 측면 접근) — 팔이 자연스럽게 박스 옆면 도달.\n"
               "(B) 팔을 수동 포즈(자동 IK 대신) — IK는 제약만족하나 부자연 자세 양산. 손으로 자연 그립 지정.\n"
               "(C) 파지 클로즈업 없이 들기 동작만 (손-박스 근접, v11b 영상-only 방식).\n"
               "(D) 박스를 더 앞으로(테이블 가장자리) → 손이 자연 팔로 닿음.",fontsize=11,va='top',color='#225')
ax.text(0,-0.01,"정직한 판단: 손목 해제로 '손바닥 방향'은 풀렸음(핵심 진전). 남은 건 '테이블 뒤에서 박스 도달' 기하 — (A)발위치 또는 (D)박스 앞으로가 가장 현실적.",
        fontsize=11,fontweight='bold',va='top',color='#7a0000')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_wrist_unlock_report.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)

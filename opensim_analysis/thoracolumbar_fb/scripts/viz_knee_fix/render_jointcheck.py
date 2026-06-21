import bpy, os, json, mathutils, numpy as np, sys
# builds 3 poses in OpenSim via subprocess-exported jsons is heavy; instead set poses here using a prebuilt json of mesh frames per pose.
# We pass pose name + frame json path
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
FRAME=argv[0]; OUTPNG=argv[1]; BOX=argv[2] if len(argv)>2 else 'none'  # none|carry|floor
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"; RAD=0.006; D=json.load(open(FRAME)); FLOOR=-0.905
def mat_from(R,p): return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def smat(name,col,alpha=1.0,emis=0.4):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*col,1)
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=alpha
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(*[c*0.9 for c in col],1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=emis
    if alpha<1: m.blend_method='BLEND'
    return m
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM); bpy.context.view_layer.update()
wm=smat("Bone",(0.90,0.89,0.84),0.95,0.4)
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        if o.name in D['mesh']: o.parent=None; o.matrix_world=mat_from(D['mesh'][o.name]['R'],D['mesh'][o.name]['p'])
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'): bpy.data.objects.remove(o,do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']): coll.hide_render=True
# ground
bpy.ops.mesh.primitive_plane_add(size=2.6, location=(0.2,FLOOR,0)); bpy.context.object.data.materials.append(smat("g",(0.28,0.30,0.34),1,0)); bpy.context.object.name="GND"
hR=D.get('hand_R',[0,0,0.1])
if BOX=='carry':
    bpy.ops.mesh.primitive_cube_add(size=0.30, location=(hR[0],hR[1],0)); bpy.context.object.data.materials.append(smat("box",(0.62,0.45,0.24),1,0.15)); bpy.context.object.name="BOX"
elif BOX=='floor':
    bpy.ops.mesh.primitive_cube_add(size=0.30, location=(0.35,FLOOR+0.15,0)); bpy.context.object.data.materials.append(smat("box",(0.62,0.45,0.24),1,0.15)); bpy.context.object.name="BOX"
mn=[1e9]*3;mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type=='MESH' and not o.hide_render and o.name!="GND":
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2;cy=(mn[1]+mx[1])/2;cz=(mn[2]+mx[2])/2
RX,RY=820,1000; ortho=max(mx[1]-mn[1],(mx[0]-mn[0])*RY/RX)*1.12
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RX; sc.render.resolution_y=RY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(0.10,0.11,0.13,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),4.0),((cx,cy-1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'; cam.data.clip_start=0.01; cam.data.clip_end=60
loc=(cx,cy,cz+6); cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
sc.render.filepath=OUTPNG; bpy.ops.render.render(write_still=True); print("JC_DONE",OUTPNG)

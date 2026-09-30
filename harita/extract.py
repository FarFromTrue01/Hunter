import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi

W,H=2048,1281
img=np.asarray(Image.open('/home/claude/work/MAP_IMG.webp').convert('RGB')).astype(np.float32)/255
L=np.asarray(Image.open('/home/claude/work/MAP_LBL.png')).astype(np.int32)
M=json.load(open('/home/claude/work/mapgen/mapd.json'))
land=L>0
regs=M['regs']
ctry_names=sorted(set(r[0] for r in regs))
reg2c=np.zeros(143,np.int32)
for i,r in enumerate(regs): reg2c[i+1]=ctry_names.index(r[0])+1
C=reg2c[L]  # country per pixel (0 sea)

r,g,b=img[...,0],img[...,1],img[...,2]
mx=img.max(-1);mn=img.min(-1);v=mx;sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
lum=0.3*r+0.59*g+0.11*b
# hue
d=np.maximum(mx-mn,1e-6)
hue=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60

# label boundaries (region borders drawn in old map)
bnd=np.zeros_like(land)
for dy,dx in ((0,1),(1,0),(1,1),(1,-1)):
    s=np.roll(np.roll(L,dy,0),dx,1);bnd|=(s!=L)
dist_b=ndi.distance_transform_edt(~bnd)

# per-country median stats
medl=np.zeros(len(ctry_names)+1);meds=np.zeros_like(medl);medh=np.zeros_like(medl)
for k in range(1,len(ctry_names)+1):
    m=(C==k)&(dist_b>4)
    medl[k]=np.median(lum[m]);meds[k]=np.median(sat[m]);medh[k]=np.median(hue[m])
ML=medl[C];MS=meds[C]

dark=land&(lum<0.55*ML)
mount=land&(sat<np.minimum(0.22,MS*0.55))&(v>0.42)
def hdist(a,b): x=np.abs(a-b)%360;return np.minimum(x,360-x)
greenish=(hue>70)&(hue<170)
isgreenc=np.isin(C,[k for k in range(1,len(ctry_names)+1) if 70<medh[k]<170])
tree=land&greenish&(sat>0.35)&(~isgreenc | (lum<0.72*ML))&~mount

# features: dark lines far from region borders
feat=dark&(dist_b>3.5)
lab,n=ndi.label(feat,structure=np.ones((3,3)))
sizes=ndi.sum(np.ones_like(lab),lab,range(1,n+1))
objs=ndi.find_objects(lab)
hills=[];bigfeat=np.zeros_like(feat)
for i,(sz,sl) in enumerate(zip(sizes,objs)):
    if sz<3: continue
    hh=sl[0].stop-sl[0].start;ww=sl[1].stop-sl[1].start
    if sz<70 and max(hh,ww)<20:
        cy,cx=ndi.center_of_mass(lab[sl]==i+1);hills.append([round(sl[1].start+cx,1),round(sl[0].start+cy,1),ww])
    else: bigfeat[sl]|=(lab[sl]==i+1)

def comps(mask,minsz):
    lab,n=ndi.label(mask,structure=np.ones((3,3)))
    out=[]
    for i,sl in enumerate(ndi.find_objects(lab)):
        m=lab[sl]==i+1;sz=m.sum()
        if sz<minsz: continue
        cy,cx=ndi.center_of_mass(m)
        out.append([round(sl[1].start+cx,1),round(sl[0].start+cy,1),sl[1].stop-sl[1].start,sl[0].stop-sl[0].start,int(sz)])
    return out
mts=comps(ndi.binary_closing(mount,iterations=1),14)
trs=comps(tree,3)

# relief: normalized luminance with icons/lines removed
icon=ndi.binary_dilation(dark|mount|tree|(dist_b<2.5),iterations=2)
rel=np.where(land,lum/np.maximum(ML,1e-3),1.0)
w=(land&~icon).astype(np.float32)
num=ndi.gaussian_filter(rel*w,3);den=ndi.gaussian_filter(w,3)
fill=num/np.maximum(den,1e-4)
rel2=np.where(land&~icon,rel,fill)
rel2=ndi.gaussian_filter(rel2,1.2)
rel2=np.clip(rel2,0.55,1.5)
np.save('/home/claude/work/mapgen/rel.npy',rel2.astype(np.float32))
np.save('/home/claude/work/mapgen/feat.npy',bigfeat)
json.dump({'mts':mts,'trs':trs,'hills':hills},open('/home/claude/work/mapgen/icons.json','w'))
print('mountains',len(mts),'trees',len(trs),'hills',len(hills),'featpx',int(bigfeat.sum()))
Image.fromarray((np.clip((rel2-0.55)/0.95,0,1)*255).astype(np.uint8)).resize((1024,640)).save('/home/claude/work/mapgen/rel_prev.png')
Image.fromarray((bigfeat*255).astype(np.uint8)).resize((1024,640)).save('/home/claude/work/mapgen/feat_prev.png')

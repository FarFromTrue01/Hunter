import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
S=2
W,H=2048,1281
ML,MT,MR,MB=36,100,36,84   # frame margins (1x)
CW,CH=W+ML+MR,H+MT+MB
M=json.load(open('/home/claude/work/mapgen/mapd.json'))
K=json.load(open('/home/claude/work/mapgen/kingdoms.json'))
L=np.asarray(Image.open('/home/claude/work/MAP_LBL.png')).astype(np.int32)
rel=np.load('/home/claude/work/mapgen/rel.npy')
kid={k['id']:i+1 for i,k in enumerate(K['kingdoms'])}
reg2k=np.zeros(143,np.int32)
for i,r in enumerate(M['regs']): reg2k[i+1]=kid[K['old2new'][r[0]]]
KL=reg2k[L]
nk=len(K['kingdoms'])
w2,h2=W*S,H*S

def up(a,resample=Image.BILINEAR):
    return np.asarray(Image.fromarray(a.astype(np.float32),mode='F').resize((w2,h2),resample))

# --- smooth kingdom map at 2x
best=np.full((h2,w2),-1,np.float32);K2=np.zeros((h2,w2),np.uint8)
for k in range(0,nk+1):
    m=ndi.gaussian_filter(up((KL==k).astype(np.float32)),1.6)
    sel=m>best;best[sel]=m[sel];K2[sel]=k
land2=K2>0
# region map at 2x (nearest) for region borders
R2=np.asarray(Image.fromarray(L.astype(np.uint8)).resize((w2,h2),Image.NEAREST)).astype(np.int32)
R2[~land2]=0

def edges(A):
    e=np.zeros(A.shape,bool)
    for dy,dx in ((0,1),(1,0)):
        s=np.roll(np.roll(A,dy,0),dx,1);e|=(s!=A)
    return e
coast_e=edges(land2.astype(np.int32))
kb_e=edges(K2.astype(np.int32))&land2&~coast_e
kb_e=kb_e&ndi.binary_erosion(land2,iterations=3)
rb_e=edges(R2)&land2&~kb_e
rb_e&=ndi.binary_erosion(land2,iterations=4)
d_coast=ndi.distance_transform_edt(~coast_e)
d_kb=ndi.distance_transform_edt(~kb_e)
d_rb=ndi.distance_transform_edt(~rb_e)
sea_d=np.where(land2,0,d_coast)
land_d=np.where(land2,d_coast,0)

rng=np.random.default_rng(7)
def noise(scale,amp):
    n=rng.standard_normal((h2//4+2,w2//4+2)).astype(np.float32)
    n=ndi.gaussian_filter(n,scale/4)
    n=n/ (n.std()+1e-6)
    return np.asarray(Image.fromarray(n,mode='F').resize((w2,h2),Image.BICUBIC))[:h2,:w2]*amp
paper_n=noise(6,0.018)+noise(40,0.035)+noise(160,0.05)
fine=rng.standard_normal((h2,w2)).astype(np.float32)*0.012

def hexc(h): h=h.lstrip('#');return np.array([int(h[i:i+2],16)/255 for i in (0,2,4)],np.float32)
paper=hexc('#ecdcb4')
out=np.empty((h2,w2,3),np.float32)
# SEA
t=np.clip(sea_d/(260*S),0,1)**0.8
near=hexc('#9dbdb8');far=hexc('#3e6b80')
sea=near*(1-t[...,None])+far*t[...,None]
sea*= (1+paper_n[...,None]*0.35+fine[...,None]*0.5)
# ripple lines
rip=np.zeros((h2,w2),np.float32)
for i,dd in enumerate([7,15,25,37,52]):
    a=0.42*(1-i/5.5)
    rip=np.maximum(rip,a*np.clip(1.3-np.abs(sea_d-dd*S)/1.0,0,1))
ink=hexc('#2c2016')
sea=sea*(1-rip[...,None]*0.55)+hexc('#23394a')*(rip[...,None]*0.55)
# coastal shallow glow
glow=np.exp(-sea_d/(10*S))
sea=sea*(1-glow[...,None]*0.35)+hexc('#d9e6d2')*(glow[...,None]*0.35)
# LAND
kcol=np.zeros((nk+1,3),np.float32)
for i,k in enumerate(K['kingdoms']): kcol[i+1]=hexc(k['col'])
base=paper*(1+paper_n[...,None]+fine[...,None])
col=kcol[K2]
band=np.exp(-d_kb/(16*S))
cband=np.exp(-land_d/(22*S))
edge=np.maximum(band,cband*0.6)
a=0.46+0.36*edge
land=base*(1-a[...,None])+col*a[...,None]
r2=up(rel,Image.BICUBIC)
shade=1+(np.clip(r2,0.6,1.45)-1)*0.85
land=land*shade[...,None]
# beach
beach=np.clip(1-land_d/(3.5*S),0,1)
land=land*(1-beach[...,None]*0.35)+hexc('#efe2bd')*(beach[...,None]*0.35)
out=np.where(land2[...,None],land,sea)
# lines
def stroke(d,w,alpha,color):
    a=np.clip((w/2+0.6-d)/1.2,0,1)*alpha
    return a
rb_dash=((np.indices((h2,w2)).sum(0)//(5*S))%2==0)
a_rb=stroke(d_rb,1.1*S,0.38,ink)*np.where(rb_dash,1,0.25)
a_kb=stroke(d_kb,2.8*S,0.92,ink)
a_kbg=np.clip((4*S-d_kb)/(4*S),0,1)**2*0.25
a_co=stroke(np.where(land2,d_coast,d_coast),1.8*S,0.9,ink)
for a,c in ((a_rb,ink),(a_kbg,hexc('#fff4d8')),(a_kb,ink),(a_co,ink)):
    out=out*(1-a[...,None])+c*a[...,None]
out=np.clip(out,0,1)
# canvas with frame margin
Cv=np.empty((CH*S,CW*S,3),np.float32);Cv[:]=paper*0.97
cn=np.asarray(Image.fromarray(noise(30,1)).resize((CW*S,CH*S))) if False else None
Cv[MT*S:MT*S+h2,ML*S:ML*S+w2]=out
# vignette on map area
yy,xx=np.mgrid[0:h2,0:w2]
vg=((xx/w2-0.5)**2+(yy/h2-0.5)**2)
Cv[MT*S:MT*S+h2,ML*S:ML*S+w2]*=(1-0.35*vg)[...,None]
Image.fromarray((Cv*255).astype(np.uint8)).save('/home/claude/work/mapgen/base.png',optimize=False)
np.save('/home/claude/work/mapgen/K2small.npy',np.asarray(Image.fromarray(K2).resize((W,H),Image.NEAREST)))
print('ok',Cv.shape)

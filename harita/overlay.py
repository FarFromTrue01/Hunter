import json, math, numpy as np, random
from scipy import ndimage as ndi
S=2;W,H=2048,1281;ML,MT,MR,MB=36,100,36,84;CW,CH=W+ML+MR,H+MT+MB
M=json.load(open('mapd.json'));K=json.load(open('kingdoms.json'));ST=json.load(open('settle.json'));IC=json.load(open('icons.json'))
K2=np.load('K2small.npy');land=K2>0
kin={k['id']:i+1 for i,k in enumerate(K['kingdoms'])};kcol={i+1:k['col'] for i,k in enumerate(K['kingdoms'])}
random.seed(3)
def dark(h,f=0.45):
    h=h.lstrip('#');c=[int(h[i:i+2],16) for i in (0,2,4)];return '#%02x%02x%02x'%tuple(int(v*f) for v in c)
INK='#2a1d12';PAPER='#f3e6c4'
o=[]
def A(s):o.append(s)
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW*S}" height="{CH*S}">')
A('''<defs>
<filter id="halo" x="-20%" y="-40%" width="140%" height="180%"><feMorphology in="SourceAlpha" operator="dilate" radius="1.6" result="d"/><feGaussianBlur in="d" stdDeviation="0.8" result="b"/><feFlood flood-color="#f5e9c9" flood-opacity=".92"/><feComposite in2="b" operator="in" result="h"/><feMerge><feMergeNode in="h"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="haloS" x="-20%" y="-40%" width="140%" height="180%"><feMorphology in="SourceAlpha" operator="dilate" radius="1" result="d"/><feGaussianBlur in="d" stdDeviation=".6" result="b"/><feFlood flood-color="#f5e9c9" flood-opacity=".85"/><feComposite in2="b" operator="in" result="h"/><feMerge><feMergeNode in="h"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="rib" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8e2b22"/><stop offset="1" stop-color="#5e1712"/></linearGradient>
<radialGradient id="cmp" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#f6ebcf"/><stop offset="1" stop-color="#d9c79c"/></radialGradient>
</defs>''')
A(f'<g transform="translate({ML},{MT})">')
# ---- waves & ships
sea=~land;sd=ndi.distance_transform_edt(sea)
pts=[];tries=0
while len(pts)<170 and tries<20000:
    tries+=1;x=random.uniform(20,W-20);y=random.uniform(20,H-20)
    if sd[int(y),int(x)]<34: continue
    if any((x-a)**2+(y-b)**2<70**2 for a,b in pts): continue
    pts.append((x,y))
for x,y in pts:
    A(f'<path d="M{x-7:.1f},{y:.1f} q3.5,-3 7,0 t7,0" fill="none" stroke="#244154" stroke-opacity=".45" stroke-width=".9" stroke-linecap="round"/>')
def ship(x,y,s=1,flip=False):
    t=f'translate({x},{y}) scale({-s if flip else s},{s})'
    return f'<g transform="{t}" stroke="{INK}" stroke-width=".9" stroke-linejoin="round"><path d="M-14,2 Q0,9 14,2 L11,6 Q0,11 -11,6 Z" fill="#6b4a2c"/><path d="M0,1 L0,-22" fill="none"/><path d="M1,-21 Q10,-12 1,-2 Z" fill="#f2e7c9"/><path d="M-1,-18 Q-9,-10 -1,-3 Z" fill="#e6d8b4"/><path d="M0,-22 l6,2 l-6,2" fill="#8e2b22" stroke-width=".6"/></g>'
for (x,y,f) in [(1210,140,False),(560,880,True),(1990,300,False),(40,1000,True),(1150,1240,False),(1960,1240,True)]:
    if sd[min(H-1,int(y)),min(W-1,int(x))]>18: A(ship(x,y,1.05,f))
# ---- hills
for x,y,w in IC['hills']:
    if not land[int(y),int(x)]: continue
    s=max(5,min(9,w*0.9))
    A(f'<path d="M{x-s:.1f},{y+1.5:.1f} Q{x:.1f},{y-s*0.75:.1f} {x+s:.1f},{y+1.5:.1f}" fill="none" stroke="{INK}" stroke-opacity=".55" stroke-width=".9" stroke-linecap="round"/>')
# ---- trees (sorted by y)
conif={kin['nordra'],kin['valdor']}
from PIL import Image
LB=np.asarray(Image.open('/home/claude/work/MAP_LBL.png')).astype(np.int32)
_cn=sorted(set(r[0] for r in M['regs']));_r2c=np.zeros(143,np.int32)
for _i,_r in enumerate(M['regs']): _r2c[_i+1]=_cn.index(_r[0])+1
OC=_r2c[LB];_e=np.zeros(OC.shape,bool)
for dy,dx in ((0,1),(1,0)): _e|=(np.roll(np.roll(OC,dy,0),dx,1)!=OC)
d_oc=ndi.distance_transform_edt(~_e)
trs=sorted(IC['trs'],key=lambda t:t[1])
for x,y,w,h,sz in trs:
    k=int(K2[int(y),int(x)])
    if k==0 or d_oc[int(y),int(x)]<7: continue
    if any((x-r[2])**2+(y-r[3])**2<22**2 for i_,r in enumerate(M['regs']) if ST['tier'].get(str(i_+1))): continue
    s=1.0+min(sz,30)/30*0.5
    if k in conif:
        A(f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.2f})"><path d="M0,-9 L4,-1 L-4,-1 Z M0,-6 L5,3 L-5,3 Z" fill="#3f6130" stroke="{INK}" stroke-width=".7" stroke-linejoin="round"/><path d="M0,3 L0,5.5" stroke="{INK}" stroke-width=".9"/></g>')
    else:
        A(f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.2f})"><path d="M0,1 L0,5" stroke="{INK}" stroke-width=".9"/><path d="M-4.2,0.5 C-6.5,-1.5 -5,-6.5 -1.5,-6.3 C-1,-9 3.5,-9 4,-5.8 C6.8,-5 6,0.8 3,1.3 C1.5,2.6 -2.5,2.6 -4.2,0.5 Z" fill="#577a37" stroke="{INK}" stroke-width=".7"/><path d="M-2.5,-2.5 Q-1,-4.5 1,-4" fill="none" stroke="#9cbb6c" stroke-width=".7"/></g>')
# ---- mountains
mts=sorted(IC['mts'],key=lambda m:m[1]+m[3]/2)
for x,y,w,h,sz in mts:
    if not land[int(y),int(x)]: continue
    hh=max(9,min(26,h*1.25));ww=max(10,min(30,w*1.15))
    by=y+h*0.45
    peak=(x+random.uniform(-1.5,1.5),by-hh)
    L=(x-ww/2,by);R=(x+ww/2,by)
    mid=(x+ww*0.08,by)
    snow=hh>15
    d=f'M{L[0]:.1f},{L[1]:.1f} L{peak[0]:.1f},{peak[1]:.1f} L{R[0]:.1f},{R[1]:.1f} Z'
    A(f'<path d="{d}" fill="#efe3c3"/>')
    A(f'<path d="M{peak[0]:.1f},{peak[1]:.1f} L{R[0]:.1f},{R[1]:.1f} L{mid[0]:.1f},{mid[1]:.1f} Z" fill="#a38b64"/>')
    if snow:
        sy=peak[1]+hh*0.32
        A(f'<path d="M{peak[0]:.1f},{peak[1]:.1f} L{peak[0]-ww*0.17:.1f},{sy:.1f} L{peak[0]-ww*0.05:.1f},{sy-2:.1f} L{peak[0]+ww*0.04:.1f},{sy+1:.1f} L{peak[0]+ww*0.16:.1f},{sy-1:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width=".5" stroke-opacity=".6"/>')
    A(f'<path d="M{L[0]:.1f},{L[1]:.1f} L{peak[0]:.1f},{peak[1]:.1f} L{R[0]:.1f},{R[1]:.1f}" fill="none" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>')
    A(f'<path d="M{peak[0]:.1f},{peak[1]:.1f} L{mid[0]:.1f},{mid[1]:.1f}" stroke="{INK}" stroke-width=".6" stroke-opacity=".7"/>')
# ---- settlements
regs=M['regs']
TIER={'cap':0,'city':1,'town':2,'vil':3}
setl=[]
for i,r in enumerate(regs):
    rid=str(i+1);t=ST['tier'].get(rid,'vil');n=ST['names'].get(rid,r[1])
    setl.append((TIER[t],r[2],r[3],n,int(K2[int(r[3]),int(r[2])]),rid))
setl.sort()
placed=[];boxes=[];bw=[]
def overl(b):
    return any(not(b[2]<c[0] or b[0]>c[2] or b[3]<c[1] or b[1]>c[3]) for c in boxes)
def castle(x,y,k,big):
    c=kcol.get(k,'#888');s=1.25 if big else 0.95
    g=f'<g transform="translate({x:.1f},{y:.1f}) scale({s})" stroke="{INK}" stroke-width=".9" stroke-linejoin="round">'
    g+=f'<path d="M-9,4 L-9,-5 L-11,-5 L-11,-9 L-8.5,-9 L-8.5,-7.5 L-7,-7.5 L-7,-9 L-5,-9 L-5,-5 L-4,-5 L-4,-9 L-4,-12 L-6,-12 L-6,-15.5 L-3.5,-15.5 L-3.5,-14 L-1.5,-14 L-1.5,-15.5 L1.5,-15.5 L1.5,-14 L3.5,-14 L3.5,-15.5 L6,-15.5 L6,-12 L4,-12 L4,-5 L5,-5 L5,-9 L7,-9 L7,-7.5 L8.5,-7.5 L8.5,-9 L11,-9 L11,-5 L9,-5 L9,4 Z" fill="#efe2c2"/>'
    g+='<path d="M-2,4 L-2,0 Q0,-2.5 2,0 L2,4" fill="#3a2a1c"/><path d="M-7,-2 l0,2.5 M7,-2 l0,2.5 M0,-10 l0,2.5" stroke-width="1.1"/>'
    if big: g+=f'<path d="M0,-15.5 L0,-24" fill="none"/><path d="M0.4,-24 L7,-22 L0.4,-20 Z" fill="{c}" stroke-width=".6"/>'
    return g+'</g>'
def tower(x,y,k):
    c=kcol.get(k,'#888')
    return f'<g transform="translate({x:.1f},{y:.1f})" stroke="{INK}" stroke-width=".8" stroke-linejoin="round"><path d="M-4,3 L-4,-6 L-5,-6 L-5,-9 L-3,-9 L-3,-7.5 L-1,-7.5 L-1,-9 L1,-9 L1,-7.5 L3,-7.5 L3,-9 L5,-9 L5,-6 L4,-6 L4,3 Z" fill="#efe2c2"/><path d="M-1.2,3 L-1.2,0 Q0,-1.5 1.2,0 L1.2,3" fill="#3a2a1c"/><path d="M0,-9 L0,-13" fill="none"/><path d="M.3,-13 L4,-12 L.3,-11 Z" fill="{c}" stroke-width=".5"/></g>'
for tier,x,y,n,k,rid in setl:
    if k==0: continue
    rmin={0:0,1:26,2:22,3:16}[tier]
    if any((x-a)**2+(y-b)**2<(rmin if tt>=tier else max(rmin,24))**2 for a,b,tt in placed): continue
    if tier==0: fs,fw,fst,iy=15.5,'700','normal',17
    elif tier==1: fs,fw,fst,iy=12.5,'700','normal',13
    elif tier==2: fs,fw,fst,iy=10.5,'600','normal',9
    else: fs,fw,fst,iy=8.6,'400','italic',6
    ib=(x-11,y-18,x+11,y+5) if tier<2 else (x-5,y-10,x+5,y+4)
    if tier==3 and overl(ib): continue
    tw=len(n)*fs*(0.56 if tier<2 else 0.5)
    cand=[(x,y+iy+fs*0.8,'middle'),(x,y-iy-fs*0.35-(8 if tier==0 else 0),'middle'),(x+ (12 if tier<2 else 5),y+fs*0.35,'start'),(x-(12 if tier<2 else 5),y+fs*0.35,'end')]
    boxes.append(ib);bw.append(1 if tier<3 else .2)
    fit=False
    for lx,ly,anc in cand:
        x0=lx-tw/2 if anc=='middle' else (lx if anc=='start' else lx-tw);b=(x0,ly-fs*0.8,x0+tw,ly+fs*0.2)
        if not overl(b): fit=True;break
    if not fit and tier==3: boxes.pop();bw.pop();continue
    placed.append((x,y,tier))
    if tier==0: A(castle(x,y,k,True))
    elif tier==1: A(castle(x,y,k,False))
    elif tier==2: A(tower(x,y,k))
    else: A(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{INK}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="1" fill="#f3e6c4"/>')
    boxes.append(b);bw.append(1 if tier<3 else .2)
    fam='GFSBask,serif' if tier<3 else 'LoraI,serif'
    flt='halo' if tier<2 else 'haloS'
    txt=n.upper() if tier==0 else n
    ls=' letter-spacing="1.2"' if tier==0 else ''
    A(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" font-family="{fam}" font-size="{fs}" font-weight="{fw}" font-style="{fst}" fill="{INK}" filter="url(#{flt})"{ls}>{txt}</text>')
# ---- kingdom labels
for i,k in enumerate(K['kingdoms']):
    kk=i+1;m=(K2==kk)
    dt=ndi.distance_transform_edt(m)
    ys,xs=np.nonzero(m);area=len(xs)
    cx,cy=xs.mean(),ys.mean()
    # blend centroid with inner-most point
    iy,ix=np.unravel_index(np.argmax(dt*np.exp(-(((np.indices(m.shape)[1]-cx)**2+(np.indices(m.shape)[0]-cy)**2)/(2*200**2)))),m.shape)
    cov=np.cov(np.vstack([xs,ys]));ev,evec=np.linalg.eigh(cov);v=evec[:,1];ang=math.degrees(math.atan2(v[1],v[0]))
    if ang>90: ang-=180
    if ang<-90: ang+=180
    ang=max(-18,min(18,ang))
    fs=max(30,min(58,math.sqrt(area)/9.5))
    col=dark(k['col'],0.42)
    fs0=fs;best=None
    for scl in (1,0.88,0.76,0.66):
      fs=fs0*scl;tw=len(k['n'])*fs*0.95
      ca,sa=math.cos(math.radians(ang)),math.sin(math.radians(ang))
      for gy in range(0,H,14):
        for gx in range(0,W,14):
            if dt[gy,gx]<fs*0.5: continue
            pen=0
            for t in np.linspace(-0.52,0.52,24):
                for vv in (-fs*0.78,-fs*0.4,0,fs*0.3,fs*0.62):
                    px=gx+ca*t*tw-sa*vv;py=gy+sa*t*tw+ca*vv
                    if not(0<=px<W and 0<=py<H) or K2[int(py),int(px)]!=kk or dt[int(py),int(px)]<6: pen+=3;continue
                    for c,wq in zip(boxes,bw):
                        if c[0]-5<=px<=c[2]+5 and c[1]-5<=py<=c[3]+5: pen+=wq;break
            sc=pen*40+math.hypot(gx-ix,gy-iy)*0.2+(1-scl)*400
            if best is None or sc<best[0]: best=(sc,gx,gy,fs)
      if best[0]<(1-scl)*400+90: break
    fs=best[3]
    lx,ly=best[1],best[2]
    if 'lab' in k: lx,ly=k['lab']
    A(f'<g transform="translate({lx:.0f},{ly:.0f}) rotate({ang:.1f})" opacity=".78" font-family="LMCaps,GFSBask,serif" text-anchor="middle" fill="{col}">'
      f'<text y="0" font-size="{fs:.0f}" letter-spacing="{fs*0.28:.1f}" font-weight="700" style="paint-order:stroke" stroke="#f5e9c9" stroke-opacity=".55" stroke-width="2.2">{k["n"].upper()}</text>'
      f'<text y="{fs*0.62:.0f}" font-size="{fs*0.34:.0f}" letter-spacing="{fs*0.12:.1f}" font-style="italic" font-family="LoraI,serif">{k["tag"]}</text></g>')
# ---- sea labels
def sealab(x,y,t,fs=22,ang=0,sp=6):
    A(f'<text transform="translate({x},{y}) rotate({ang})" text-anchor="middle" font-family="LoraI,serif" font-style="italic" font-size="{fs}" letter-spacing="{sp}" fill="#1f3a4c" fill-opacity=".72">{t}</text>')
sealab(1010,560,'Myrr Denizi',26,-8,7)
sealab(1330,60,'Vael Okyanusu',24,0,9)
sealab(1000,1250,'Soluk Deniz',22,0,8)
sealab(1440,270,'Buz Boğazı',15,-72,4)
sealab(690,862,'Gümüş Körfez',15,-6,4)
sealab(40,660,'Batı Denizi',17,-90,6)
sealab(2020,1010,'Şafak Denizi',17,90,6)
# ---- compass
cx,cy=1085,740
A(f'<g transform="translate({cx},{cy})"><circle r="56" fill="url(#cmp)" fill-opacity=".55" stroke="{INK}" stroke-width="1.2"/><circle r="50" fill="none" stroke="{INK}" stroke-width=".6"/><circle r="36" fill="none" stroke="{INK}" stroke-width=".5" stroke-dasharray="2 3"/>')
for i in range(32):
    a=i*math.pi/16;r1=50;r2=46 if i%2 else 42
    A(f'<line x1="{r1*math.sin(a):.1f}" y1="{-r1*math.cos(a):.1f}" x2="{r2*math.sin(a):.1f}" y2="{-r2*math.cos(a):.1f}" stroke="{INK}" stroke-width=".6"/>')
for i in range(8):
    a=i*math.pi/4+math.pi/8;L=30
    A(f'<path transform="rotate({math.degrees(a)})" d="M0,-{L} L4,0 L0,4 L-4,0 Z" fill="#b89a66" stroke="{INK}" stroke-width=".6"/>')
for i in range(4):
    a=i*90;L=62 if i==0 else 52
    A(f'<g transform="rotate({a})"><path d="M0,-{L} L7,0 L0,0 Z" fill="#3a2a1c"/><path d="M0,-{L} L-7,0 L0,0 Z" fill="#f3e6c4" stroke="{INK}" stroke-width=".7"/><path d="M0,-{L} L7,0 L-7,0 Z" fill="none" stroke="{INK}" stroke-width=".9"/></g>')
A(f'<circle r="4" fill="#8e2b22" stroke="{INK}" stroke-width=".8"/>')
for t,x,y in (('K',0,-70),('G',0,82),('D',75,5),('B',-75,5)):
    A(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="GFSBask,serif" font-weight="700" font-size="16" fill="{INK}">{t}</text>')
A('</g>')
A('</g>')
# ---- frame
A(f'<rect x="{ML-10}" y="{MT-10}" width="{W+20}" height="{H+20}" fill="none" stroke="{INK}" stroke-width="3"/>')
A(f'<rect x="{ML-4}" y="{MT-4}" width="{W+8}" height="{H+8}" fill="none" stroke="{INK}" stroke-width="1"/>')
A(f'<rect x="{ML-16}" y="{MT-16}" width="{W+32}" height="{H+32}" fill="none" stroke="#8e6b3a" stroke-width="1.2"/>')
for i in range(0,W+20,24):
    A(f'<rect x="{ML-10+i}" y="{MT-10}" width="12" height="4" fill="{INK}" fill-opacity=".85"/><rect x="{ML-10+i}" y="{MT+H+6}" width="12" height="4" fill="{INK}" fill-opacity=".85"/>')
for (x,y) in ((ML-10,MT-10),(ML+W+10,MT-10),(ML-10,MT+H+10),(ML+W+10,MT+H+10)):
    A(f'<g transform="translate({x},{y})"><rect x="-13" y="-13" width="26" height="26" fill="{PAPER}" stroke="{INK}" stroke-width="2"/><path d="M0,-9 L9,0 L0,9 L-9,0 Z" fill="#8e2b22" stroke="{INK}" stroke-width="1"/><circle r="2.5" fill="{PAPER}"/></g>')
# ---- title banner
tx=CW/2
A(f'<g transform="translate({tx},40)"><path d="M-330,-26 L330,-26 L352,0 L330,26 L-330,26 L-352,0 Z" fill="url(#rib)" stroke="{INK}" stroke-width="2"/><path d="M-322,-19 L322,-19 L340,0 L322,19 L-322,19 L-340,0 Z" fill="none" stroke="#e8c77a" stroke-width="1.2"/>'
  f'<path d="M-352,0 L-400,-18 L-388,0 L-400,18 Z M352,0 L400,-18 L388,0 L400,18 Z" fill="#6a1a14" stroke="{INK}" stroke-width="1.5"/>'
  f'<text y="10" text-anchor="middle" font-family="LMCaps,GFSBask,serif" font-weight="700" font-size="30" letter-spacing="12" fill="#f6e3b0">YEDİ KRALLIK</text></g>')
A(f'<text x="{tx}" y="81" text-anchor="middle" font-family="LoraI,serif" font-style="italic" font-size="12" letter-spacing="3" fill="{INK}" fill-opacity=".8">Elonth ve komşu diyarlar · Maceracılar Loncası kayıtlarından çizilmiştir</text>')
# ---- legend (bottom margin)
ly=MT+H+50
items=[]
lx=ML+20
A(f'<text x="{lx}" y="{ly+4}" font-family="LMCaps,GFSBask,serif" font-size="13" font-weight="700" letter-spacing="3" fill="{INK}">LEJANT</text>')
lx+=112
A(castle(lx,ly+6,1,True));A(f'<text x="{lx+18}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Başkent</text>');lx+=100
A(castle(lx,ly+6,1,False));A(f'<text x="{lx+16}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Şehir</text>');lx+=80
A(tower(lx,ly+4,1));A(f'<text x="{lx+10}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Kasaba</text>');lx+=85
A(f'<circle cx="{lx}" cy="{ly}" r="2.6" fill="{INK}"/><circle cx="{lx}" cy="{ly}" r="1" fill="{PAPER}"/><text x="{lx+9}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Köy</text>');lx+=60
A(f'<line x1="{lx}" y1="{ly}" x2="{lx+30}" y2="{ly}" stroke="{INK}" stroke-width="2.6"/><text x="{lx+38}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Krallık sınırı</text>');lx+=140
A(f'<line x1="{lx}" y1="{ly}" x2="{lx+30}" y2="{ly}" stroke="{INK}" stroke-width="1" stroke-dasharray="5 5" stroke-opacity=".6"/><text x="{lx+38}" y="{ly+5}" font-family="GFSBask,serif" font-size="13" fill="{INK}">Bölge sınırı</text>');lx+=135
for i,k in enumerate(K['kingdoms']):
    A(f'<rect x="{lx}" y="{ly-7}" width="16" height="12" fill="{k["col"]}" fill-opacity=".8" stroke="{INK}" stroke-width=".8"/><text x="{lx+21}" y="{ly+4}" font-family="GFSBask,serif" font-size="13" fill="{INK}">{k["n"]}</text>')
    lx+=len(k['n'])*8+44
# scale bar
sx=CW-ML-230;A(f'<g transform="translate({sx},{ly})"><text x="0" y="-12" font-family="LoraI,serif" font-style="italic" font-size="11" fill="{INK}">Ölçek · fersah</text>')
for i in range(4):
    A(f'<rect x="{i*50}" y="-4" width="50" height="7" fill="{INK if i%2==0 else PAPER}" stroke="{INK}" stroke-width=".8"/><text x="{i*50}" y="18" text-anchor="middle" font-family="GFSBask,serif" font-size="10" fill="{INK}">{i*25}</text>')
A(f'<text x="200" y="18" text-anchor="middle" font-family="GFSBask,serif" font-size="10" fill="{INK}">100</text></g>')
A('</svg>')
open('overlay.svg','w').write('\n'.join(o))
print('placed settlements',len(placed))

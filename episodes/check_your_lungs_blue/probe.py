from PIL import Image; import numpy as np, glob, json
fs=sorted(glob.glob('frames/b*.png'))
out=[]
for i,f in enumerate(fs):
    a=np.array(Image.open(f).convert('RGB')).astype(int)  # crop x0=370,y0=280
    R,G,B=a[...,0],a[...,1],a[...,2]
    m=(R>200)&(G>130)&(B<120)&(R-B>110)
    side=np.zeros_like(m); side[:,30:62]=1; side[:,142:172]=1
    ys=np.where((m&side.astype(bool)).sum(1)>3)[0]
    ey=float(np.median(ys))+280 if len(ys)>10 else None
    eyr=(int(ys.min())+280,int(ys.max())+280) if len(ys)>10 else None
    c=a[:,100]  # x=470
    blue=(c[:,2]>200)&(c[:,0]<200); gold=(c[:,0]>200)&(c[:,1]>120)&(c[:,2]<140)
    out.append(dict(i=i,ey=ey,er=eyr,blue=int(blue.sum()),gold=int(gold.sum()),
       bmax=int(np.where(blue)[0].max())+280 if blue.any() else None,
       gmax=int(np.where(gold)[0].max())+280 if gold.any() else None))
json.dump(out,open('probe.json','w'))
for o in out[::15]: print(o)

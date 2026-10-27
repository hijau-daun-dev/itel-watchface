import sys,struct
from collections import Counter
def runlen(px,i,cap=127):
    n=1
    while i+n<len(px) and n<cap and px[i+n]==px[i]: n+=1
    return n
def enc(px,MINRUN=3,LMAX=127,RMAX=127):
    out=bytearray(); i=0; w=len(px)
    while i<w:
        r=runlen(px,i,RMAX)
        if r>=MINRUN:
            out.append(0x80|r); out+=px[i]; i+=r; continue
        j=i
        while j<w and j-i<LMAX and (j-i>125 or runlen(px,j,MINRUN)<MINRUN): j+=1
        out.append(j-i); out+=b''.join(px[i:j]); i=j
    return bytes(out)
C=Counter(); shown=Counter()
for f in sys.argv[1:]:
    d=open(f,'rb').read()
    nimg,nel,ver=struct.unpack_from('<HBB',d,0)
    els=[struct.unpack_from('<IHHHHHBBBBBB',d,4+20*i) for i in range(nel)]
    t=4+20*nel; sizes=struct.unpack_from('<%dI'%nimg,d,t)
    offs=[t+4*nimg]
    for s in sizes: offs.append(offs[-1]+s)
    for (off,idx,w,h,x,y,cnt,typ,g,b,p1,p2) in els:
        if b==0: continue
        bpp=3 if typ&0x80 else 2
        for k in range(cnt):
            o=offs[idx+k]
            h2=(struct.unpack_from('<I',d,o)[0]&0x1fffff)//4
            rows=struct.unpack_from('<%dI'%h2,d,o)
            for v in rows:
                p=o+(v&0x1fffff); e=p+(v>>21); raw=d[p:e]
                px=[]
                while p<e:
                    c=d[p]; p+=1
                    if c&0x80: px+= [d[p:p+bpp]]*(c&0x7f); p+=bpp
                    else: px+=[d[p+i*bpp:p+i*bpp+bpp] for i in range(c)]; p+=bpp*c
                ok=enc(px)==raw
                C[(b,ok)]+=1
                if not ok and shown[b]<3:
                    shown[b]+=1
                    def tok(bs):
                        r=[];q=0
                        while q<len(bs):
                            c=bs[q];q+=1
                            if c&0x80: r.append('R%d:%s'%(c&0x7f,bs[q:q+bpp].hex()));q+=bpp
                            else: r.append('L%d:%s'%(c,bs[q:q+bpp*c].hex()));q+=bpp*c
                        return r
                    a=tok(raw);bb=tok(enc(px))
                    for z in range(min(len(a),len(bb))):
                        if a[z]!=bb[z]: print(f[-9:],b,'orig',a[max(0,z-2):z+3],'\n   mine',bb[max(0,z-2):z+3]); break
print(C)

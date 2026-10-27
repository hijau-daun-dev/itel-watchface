import sys,struct
from collections import Counter
stats=Counter()
for f in sys.argv[1:]:
    d=open(f,'rb').read()
    nimg,nel,ver=struct.unpack_from('<HBB',d,0)
    els=[struct.unpack_from('<IHHHHHBBBBBB',d,4+20*i) for i in range(nel)]
    t=4+20*nel; sizes=struct.unpack_from('<%dI'%nimg,d,t)
    offs=[t+4*nimg]
    for s in sizes: offs.append(offs[-1]+s)
    for (off,idx,w,h,x,y,cnt,typ,g,b,p1,p2) in els:
        alpha=typ>>7; bpp=3 if alpha else 2
        for k in range(cnt):
            o=offs[idx+k]; sz=sizes[idx+k]
            if b==0:
                stride=(w*bpp+3)&~3
                ok = sz==stride*h
                stats[('raw',ok)]+=1
                if not ok: print(f,'raw mismatch',idx+k,sz,stride*h,w,h,typ)
                continue
            rows=struct.unpack_from('<%dI'%h,d,o)
            pos=4*h; bad=None; ctrl=Counter()
            for r,v in enumerate(rows):
                ro=v&0x1fffff; rl=v>>21
                if ro!=pos: bad=('rowoff',r,ro,pos); break
                p=o+ro; e=p+rl; n=0
                while p<e:
                    c=d[p]; p+=1
                    if c&0x80: n+=c&0x7f; p+=bpp; ctrl['run0' if c==0x80 else 'run']+=1
                    else: n+=c; p+=bpp*c; ctrl['lit0' if c==0 else 'lit']+=1
                if p!=e or n!=w: bad=('row',r,n,w,p-e); break
                pos+=rl
            if bad is None and ((pos+3)&~3)!=sz: bad=('tail',pos,sz)
            if bad is None and any(d[o+pos:o+sz]): bad=('padnz',d[o+pos:o+sz])
            stats[('rle',b,alpha,bad is None)]+=1
            if bad: print(f.split('/')[-1],'idx',idx+k,'type',typ,'b',b,w,h,bad)
print(stats)

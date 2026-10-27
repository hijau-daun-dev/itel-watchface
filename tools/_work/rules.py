import sys,struct
from collections import Counter
C=Counter()
ex=[]
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
                p=o+(v&0x1fffff); e=p+(v>>21)
                toks=[]
                while p<e:
                    c=d[p]; p+=1
                    if c&0x80: toks.append(('R',c&0x7f,[d[p:p+bpp]])); p+=bpp
                    else: toks.append(('L',c,[d[p+i*bpp:p+i*bpp+bpp] for i in range(c)])); p+=bpp*c
                for i,(t_,n,px) in enumerate(toks):
                    C[(b,t_,'len',min(n,3) if n<127 else 127)]+=1
                    if t_=='L':
                        eq=sum(px[j]==px[j+1] for j in range(n-1))
                        if eq: C[(b,'L has adjacent eq')]+=1
                        tri=any(px[j]==px[j+1]==px[j+2] for j in range(n-2))
                        if tri: C[(b,'L has triple')]+=1
                    if i>0 and toks[i-1][0]==t_=='L': C[(b,'LL adjacent')]+=1; 
                    if i>0 and toks[i-1][0]=='L' and t_=='L' and toks[i-1][1]<127: C[(b,'LL adj, prev<127')]+=1
                    if i>0 and toks[i-1][0]=='R'==t_ and toks[i-1][2]==px and toks[i-1][1]<127: C[(b,'RR same px prev<127')]+=1
                    if i>0 and t_=='R' and toks[i-1][0]=='L' and toks[i-1][2][-1]==px[0]: C[(b,'L then R same px')]+=1
                    if i>0 and t_=='L' and toks[i-1][0]=='R' and toks[i-1][2][0]==px[0]: C[(b,'R then L same px')]+=1
                    if t_=='L' and n>=2 and len(ex)<5 and any(px[j]==px[j+1] for j in range(n-1)): ex.append((f[-9:],[(a,bb,[x.hex() for x in cc]) for a,bb,cc in toks]))
for k,v in sorted(C.items(),key=str): print(k,v)
for e in ex[:3]: print(e)

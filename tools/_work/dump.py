import sys,struct,glob
for f in sys.argv[1:]:
    d=open(f,'rb').read()
    nimg,nel,hb=struct.unpack_from('<HBB',d,0)
    print(f.split('/')[-1],len(d),'nimg',nimg,'nel',nel,'b3',hb)
    for i in range(nel):
        r=d[4+20*i:24+20*i]
        off,idx,w,h,x,y,cnt,typ,g,b,u=struct.unpack('<IHHHHHBBBBH',r)
        print(f'  off={off:6x} idx={idx:3d} w={w:3d} h={h:3d} x={x:3d} y={y:3d} cnt={cnt:2d} type={typ:2d} g={g:02x} b={b:02x} u={u}')
    t=4+20*nel
    sizes=struct.unpack_from('<%dI'%nimg,d,t)
    end=t+4*nimg
    print('  table end',hex(end),'sum',end+sum(sizes),'=? len',len(d))

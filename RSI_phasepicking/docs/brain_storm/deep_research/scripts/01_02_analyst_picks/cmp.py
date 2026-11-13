import sys,re,collections
q=open(sys.argv[1]).read(); ph=open(sys.argv[2]).read().splitlines()
qp={}
for p in re.findall(r'<pick .*?</pick>',q,re.S):
    st=re.search(r'stationCode="([^"]*)" channelCode="([^"]*)"',p).groups()
    g=lambda tag: (re.search(f'<{tag}>([^<]*)</{tag}>',p) or [None,'-'])[1]
    unc=re.search(r'<uncertainty>([^<]*)</uncertainty>',p)
    qp[(st[0],st[1],g('phaseHint'))]=(g('onset'),unc.group(1) if unc else '-',g('evaluationMode'))
c=collections.Counter()
for l in ph[1:]:
    f=l.split()
    if len(f)<12: continue
    key=(f[1],f[2],f[7]); qual=f[10]; onset=f[9]
    c[(qual,onset)+qp.get(key,('missing',))]+=1
for k,v in sorted(c.items()): print(k,v)
print('phase lines',len(ph)-1,'qml picks',len(qp))

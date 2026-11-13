import sys,json,re,urllib.request,collections
fn=sys.argv[1]; n=int(sys.argv[2])
rows=json.load(open(fn)); evs=list(dict.fromkeys(r['ev'] for r in rows))[:n]
c=collections.Counter(); tot=collections.Counter(); cd=collections.Counter(); td=collections.Counter()
for e in evs:
    t=urllib.request.urlopen(f"https://service.scedc.caltech.edu/fdsnws/event/1/query?eventid={e}&includearrivals=true",timeout=120).read().decode()
    pk={}
    for p in re.findall(r'<pick (publicID="[^"]*").*?</pick>',t,re.S): pass
    for m in re.finditer(r'<pick publicID="([^"]*)">(.*?)</pick>',t,re.S):
        p=m.group(2); g=lambda tag:(re.search(f'<{tag}>([^<]*)</{tag}>',p) or [None,'-'])[1]
        pk[m.group(1)]=(g('phaseHint'),g('evaluationMode'))
    arr=[]
    for m in re.finditer(r'<arrival .*?<pickID>([^<]*)</pickID>.*?<distance>([^<]*)</distance>.*?</arrival>',t,re.S):
        if m.group(1) in pk: arr.append((float(m.group(2))*111.19,)+pk[m.group(1)])
    for ph in 'PS':
        a=sorted([x for x in arr if x[1]==ph])
        for i,(d,_,mode) in enumerate(a):
            rk='rank1-5' if i<5 else ('rank6-10' if i<10 else 'rank>10')
            tot[(ph,rk)]+=1; c[(ph,rk)]+=mode=='manual'
            db='<50km' if d<50 else ('50-100' if d<100 else '>100')
            td[(ph,db)]+=1; cd[(ph,db)]+=mode=='manual'
print(fn,'events',len(evs))
for k in sorted(tot): print('  ',k,f'manual={c[k]/tot[k]:.2f} n={tot[k]}')
for k in sorted(td): print('  ',k,f'manual={cd[k]/td[k]:.2f} n={td[k]}')

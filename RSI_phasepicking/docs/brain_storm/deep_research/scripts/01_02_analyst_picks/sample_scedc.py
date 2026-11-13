# usage: python3 -I sample_scedc.py outdir label start end nsample minmag maxmag
import sys,re,random,urllib.request,collections,json,os,time
out,label,start,end,n,mmin,mmax=sys.argv[1:8]
n=int(n)
base="https://service.scedc.caltech.edu/fdsnws/event/1/query"
u=f"{base}?starttime={start}&endtime={end}&minmagnitude={mmin}&maxmagnitude={mmax}&format=text"
txt=urllib.request.urlopen(u,timeout=120).read().decode()
ids=[l.split('|')[0].strip() for l in txt.splitlines() if l and not l.startswith('#') and l.split('|')[7].strip()=='eq' and l.split('|')[8].strip()=='l']
mags={l.split('|')[0].strip():float(l.split('|')[10]) for l in txt.splitlines() if l and not l.startswith('#')}
random.seed(0); sel=random.sample(ids,min(n,len(ids)))
rows=[]
for e in sel:
    try:
        t=urllib.request.urlopen(f"{base}?eventid={e}&includearrivals=true",timeout=120).read().decode()
    except Exception as ex:
        continue
    o=re.search(r'<origin .*?</origin>',t,re.S).group(0)
    oms=re.findall(r'<evaluationMode>(\w+)</evaluationMode>',o); oss=re.findall(r'<evaluationStatus>(\w+)</evaluationStatus>',o)
    for p in re.findall(r'<pick .*?</pick>',t,re.S):
        g=lambda tag: (re.search(f'<{tag}>([^<]*)</{tag}>',p) or [None,'-'])[1]
        unc=re.search(r'<uncertainty>([^<]*)</uncertainty>',p)
        rows.append(dict(ev=e,mag=mags[e],ostat=(oms[-1] if oms else '-')+'/'+(oss[-1] if oss else '-'),ph=g('phaseHint'),onset=g('onset'),unc=unc.group(1) if unc else '-',mode=g('evaluationMode'),pol=g('polarity')))
    time.sleep(0.2)
json.dump(rows,open(os.path.join(out,label+'.json'),'w'))
print(label,'events in window',len(ids),'sampled',len(sel),'picks',len(rows))

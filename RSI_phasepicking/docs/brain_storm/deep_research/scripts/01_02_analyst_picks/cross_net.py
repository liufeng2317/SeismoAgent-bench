# Compare NC-analyst and CI-analyst picks on the same station/phase for events both networks reviewed.
import sys,re,json,urllib.request,datetime,time,collections
files=sys.argv[1:]
cands=[]
for fn in files:
    for s in open(fn,errors='ignore').read().splitlines():
        if not (s[:4].isdigit() and len(s)>150): continue
        try:
            la=int(s[16:18])+int(s[19:23])/6000; lo=-(int(s[23:26])+int(s[27:31])/6000)
            md=int(s[70:73] or 0)/100
        except: continue
        if s[163]=='F' and 35.0<la<38.2 and -121.0<lo<-116.5 and md>=1.5:
            t=datetime.datetime.strptime(s[:12],'%Y%m%d%H%M')+datetime.timedelta(seconds=int(s[12:16])/100)
            cands.append((s[136:146].strip(),t,la,lo,md))
import random; random.seed(3); random.shuffle(cands); print('candidates',len(cands),file=sys.stderr)
def picks(url):
    t=urllib.request.urlopen(url,timeout=120).read().decode()
    out={}
    for p in re.findall(r'<pick .*?</pick>',t,re.S):
        w=re.search(r'networkCode="([^"]*)" stationCode="([^"]*)" channelCode="([^"]*)"',p).groups()
        g=lambda tag: (re.search(f'<{tag}>([^<]*)</{tag}>',p) or [None,'-'])[1]
        tv=g('value'); unc=re.search(r'<uncertainty>([^<]*)</uncertainty>',p)
        ts=datetime.datetime.fromisoformat(tv.replace('Z',''))
        out.setdefault((w[0],w[1],g('phaseHint')[:1]),[]).append((ts,g('evaluationMode'),g('onset'),unc.group(1) if unc else '-',w[2]))
    return out
rows=[]
for ncid,t,la,lo,md in cands[:int(120)]:
    try:
        q=f"https://service.scedc.caltech.edu/fdsnws/event/1/query?starttime={(t-datetime.timedelta(seconds=5)).isoformat()}&endtime={(t+datetime.timedelta(seconds=5)).isoformat()}&format=text"
        txt=urllib.request.urlopen(q,timeout=60).read().decode()
        ci=[l.split('|')[0].strip() for l in txt.splitlines() if l and not l.startswith('#')]
        if len(ci)!=1: continue
        a=picks(f"https://service.scedc.caltech.edu/fdsnws/event/1/query?eventid={ci[0]}&includearrivals=true")
        b=picks(f"https://service.ncedc.org/fdsnws/event/1/query?eventid={ncid}&includearrivals=true")
        for k in set(a)&set(b):
            for pa in a[k]:
                for pb in b[k]:
                    if pa[1]=='manual' and pb[1]=='manual':
                        rows.append(dict(nc=ncid,ci=ci[0],key=k,dt=(pa[0]-pb[0]).total_seconds(),ci_on=pa[2],nc_on=pb[2],ci_unc=pa[3],nc_unc=pb[3],ci_ch=pa[4],nc_ch=pb[4],mag=md))
        time.sleep(0.2)
    except Exception as ex:
        print('err',ncid,ex,file=sys.stderr)
json.dump(rows,open(sys.argv[0].replace('cross_net.py','cross_rows.json'),'w'),default=str)
print('pairs',len(rows), 'events',len(set(r['nc'] for r in rows)))

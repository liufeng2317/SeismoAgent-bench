import sys,urllib.request,random,re,collections,time
start,end,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
base="https://service.ncedc.org/fdsnws/event/1/query"
txt=urllib.request.urlopen(f"{base}?starttime={start}&endtime={end}&minlatitude=36.5&maxlatitude=42&minlongitude=-125&maxlongitude=-119.5&format=text",timeout=300).read().decode()
evs=[l.split('|') for l in txt.splitlines() if l and not l.startswith('#') and l.split('|')[13].strip()=='earthquake']
def geysers(f): la,lo=float(f[2]),float(f[3]); return 38.7<la<38.9 and -122.95<lo<-122.65
random.seed(1)
for name,grp in [('geysers',[f for f in evs if geysers(f)]),('other',[f for f in evs if not geysers(f)])]:
    sel=random.sample(grp,min(n,len(grp))); c=collections.Counter()
    for f in sel:
        t=urllib.request.urlopen(f"{base}?eventid={f[0]}",timeout=120).read().decode()
        o=re.search(r'<origin .*?</origin>',t,re.S).group(0)
        st=re.findall(r'<evaluationStatus>(\w+)</evaluationStatus>',o)
        m=float(f[10] or -9); bin_='M<1' if m<1 else ('1-2' if m<2 else ('2-2.5' if m<2.5 else 'M>=2.5'))
        c[(bin_,st[-1] if st else '-')]+=1; time.sleep(0.1)
    print(name,'n_total',len(grp),dict(sorted(c.items())))

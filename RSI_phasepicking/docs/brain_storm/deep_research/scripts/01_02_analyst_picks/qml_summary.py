import sys,re,collections
for fn in sys.argv[1:]:
    t=open(fn).read()
    o=re.search(r'<origin .*?</origin>',t,re.S)
    om=re.search(r'<evaluationMode>(\w+)</evaluationMode>\s*<evaluationStatus>(\w+)</evaluationStatus>',o.group(0)) if o else None
    if o:
        oo=o.group(0); om1=re.findall(r'<evaluationMode>(\w+)</evaluationMode>',oo); os_=re.findall(r'<evaluationStatus>(\w+)</evaluationStatus>',oo)
    picks=re.findall(r'<pick .*?</pick>',t,re.S)
    c=collections.Counter()
    for p in picks:
        g=lambda tag: (re.search(f'<{tag}>([^<]*)</{tag}>',p) or [None,'-'])[1]
        unc=re.search(r'<uncertainty>([^<]*)</uncertainty>',p)
        c[(g('phaseHint'),g('onset'),unc.group(1) if unc else '-',g('evaluationMode'),g('evaluationStatus'))]+=1
    mag=re.search(r'<mag>\s*<value>([^<]*)',t)
    print(fn, 'mag',mag.group(1) if mag else '?', 'origin', o and (om1[:1],os_[:1]), 'npicks',len(picks))
    for k,v in sorted(c.items()): print('   ',k,v)

import sys,json,collections
for fn in sys.argv[1:]:
    rows=json.load(open(fn)); print('#####',fn)
    ev=collections.Counter(); 
    seen={}
    for r in rows: seen[r['ev']]=r['ostat']
    print(' origin status of events:',collections.Counter(seen.values()))
    for ost in sorted(set(seen.values())):
        rr=[r for r in rows if r['ostat']==ost]
        for ph in 'PS':
            x=[r for r in rr if r['ph']==ph]
            if not x: continue
            m=sum(r['mode']=='manual' for r in x)
            print(f'  {ost} {ph}: n={len(x)} manual={m/len(x):.2f}')
            c=collections.Counter((r['unc'],r['onset'][:3],r['mode'][:4]) for r in x)
            print('     ',dict(sorted(c.items())))

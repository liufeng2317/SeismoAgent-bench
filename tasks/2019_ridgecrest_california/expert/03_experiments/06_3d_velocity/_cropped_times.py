"""Exact case-specific travel-time cropping; no resampling or velocity changes."""
from pathlib import Path
import hashlib,json,os
import numpy as np
from scipy.interpolate import RegularGridInterpolator

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):
    temp=path.with_name(path.name+'.tmp')
    with temp.open('w') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
def header(path):
    lines=Path(path).read_text().splitlines();a=lines[0].split();shape=tuple(map(int,a[:3]));origin=np.array(list(map(float,a[3:6])));step=np.array(list(map(float,a[6:9])))
    assert a[9:]==['TIME','FLOAT'];return lines,shape,origin,step

def search_bounds(controls):
    lows=[];highs=[]
    for p in controls:
        rows=[s.split() for s in Path(p).read_text().splitlines() if s.startswith('LOCGRID ')]
        assert len(rows)==1;a=rows[0];n=np.array(list(map(int,a[1:4])));o=np.array(list(map(float,a[4:7])));d=np.array(list(map(float,a[7:10])))
        # Conservatively include one entire LOCGRID cell beyond n*spacing.
        lows.append(o-d);highs.append(o+(n+1)*d)
    return np.min(lows,axis=0),np.max(highs,axis=0)

def crop(source,destination,bounds):
    source=Path(source);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    sh=source.with_suffix('.hdr');dh=destination.with_suffix('.hdr');marker=destination.with_suffix('.crop.json')
    lines,shape,origin,step=header(sh);lo,hi=bounds
    first=np.floor((lo-origin)/step).astype(int);last=np.ceil((hi-origin)/step).astype(int)
    assert np.all(first>=0) and np.all(last<shape),(first,last,shape)
    size=last-first+1;start=origin+first*step;slices=tuple(slice(int(a),int(b)+1) for a,b in zip(first,last))
    identity=dict(source=str(source.resolve()),source_header_sha256=sha(sh),source_sha256=sha(source),first=first.tolist(),last_inclusive=last.tolist())
    if marker.exists():
        m=json.loads(marker.read_text());assert m['input']==identity and sha(destination)==m['cropped_sha256'] and sha(dh)==m['cropped_header_sha256'];return m
    full=np.memmap(source,mode='r',dtype=np.float32,shape=shape)
    temporary=destination.with_name(destination.name+'.tmp');full[slices].tofile(temporary);os.replace(temporary,destination)
    lines[0]=' '.join([*(str(int(v)) for v in size),*(f'{v:.12g}' for v in start),*(f'{v:.12g}' for v in step),'TIME','FLOAT'])
    dh.write_text('\n'.join(lines)+'\n')
    stored=np.memmap(destination,mode='r',dtype=np.float32,shape=tuple(size))
    assert np.array_equal(stored,full[slices])
    m=dict(input=identity,cropped_sha256=sha(destination),cropped_header_sha256=sha(dh),source_bytes=source.stat().st_size,cropped_bytes=destination.stat().st_size,values_bitwise_identical=True)
    write_json(marker,m);return m

def predict(directory,p,stations):
    result=np.empty(len(p))
    for (sid,phase),q in p.groupby(['instrument_id','phase']):
        buf=Path(directory)/f'time.{phase}.{stations.loc[sid,"nll_station"]}.time.buf'
        _,shape,origin,step=header(buf.with_suffix('.hdr'));axes=tuple(o+np.arange(n)*d for o,n,d in zip(origin,shape,step));grid=np.memmap(buf,mode='r',dtype=np.float32,shape=shape)
        result[q.index]=RegularGridInterpolator(axes,grid,bounds_error=True)(q[['x_km','y_km','depth_km']].to_numpy())
    return result

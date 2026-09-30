#!/usr/bin/env python3
"""Side-by-side maps of workflow outputs and native reference catalogs."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
from pathlib import Path
import importlib.util
import tarfile
import hashlib
import numpy as np
import pandas as pd
import yaml
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
OUT=HERE/'export/11_plot_catalog_maps'
CASE=HERE.parents[2]/'data/2019_ridgecrest_california'
START=pd.Timestamp('2019-07-04T15:35:29.4Z'); END=pd.Timestamp('2019-07-07T00:00:00Z')
LON=(-117.90,-117.20); LAT=(35.45,36.05)
SPEC=importlib.util.spec_from_file_location('reference_readers',HERE/'02_diagnostics/05_review_catalog.py')
reader=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(reader)

def selected(df):
    t=(df.time>=START)&(df.time<END)
    finite=np.isfinite(df[['latitude','longitude']]).all(axis=1)
    box=df.latitude.between(*LAT)&df.longitude.between(*LON)
    return df[t&finite&box].copy(),dict(time_window_rows=int(t.sum()),invalid_coordinates=int((t&~finite).sum()),outside_map=int((t&finite&~box).sum()))

def main():
    threadpool_limits(1); OUT.mkdir(parents=True,exist_ok=True)
    source=HERE/'export/10_validate_catalog/events.csv'
    events=pd.read_csv(source)
    refs,files=reader.read_references()
    rosspath=CASE/'data/catalogs/ROSS2019_SCIENCE/raw/ROSS2019_SCIENCE__catalog_qtm.tar.gz'
    cols=['year','month','day','hour','minute','second','reference_id','latitude','longitude','depth_km','magnitude','qID','cID','nbranch','qnpair','qndiffP','qndiffS','rmsP','rmsS','eh','ez','et','latC','lonC','depC']
    with tarfile.open(rosspath,'r:gz') as archive:
        with archive.extractfile('ridgecrest_qtm.cat') as stream:
            ross=pd.read_csv(stream,sep=r'\s+',names=cols,dtype={'reference_id':str})
    assert len(ross)==111918 and ross.reference_id.is_unique
    ross['time']=reader.dates(ross,['year','month','day','hour','minute','second'])
    refs['Ross_relocated']=ross[ross.nbranch>1].copy()
    frames={}
    for name,prefix in [('Ours_GaMMA','gamma_'),('Ours_NonLinLoc','')]:
        d=pd.DataFrame(dict(event_id=events.event_id,time=pd.to_datetime(events[prefix+'origin_time'],format='ISO8601',utc=True),
                            latitude=events[prefix+'latitude'],longitude=events[prefix+'longitude'],
                            native_status=events.status,in_v1_working_catalog=events.in_v1_working_catalog))
        frames[name]=d
    for key in ['Official','Liu','Shelly','Ross_relocated']: frames[key]=refs[key]
    titles={'Ours_GaMMA':'Ours: GaMMA','Ours_NonLinLoc':'Ours: NonLinLoc','Official':'Reference: Official',
            'Liu':'Reference: Liu','Shelly':'Reference: Shelly','Ross_relocated':'Reference: Ross relocated'}
    stats=[]; memberships=[]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
        'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'axes.linewidth':.6,'savefig.facecolor':'white'})
    for variant in ['all_candidates','working_subset']:
        fig,axes=plt.subplots(2,3,figsize=(9.0,7.1),sharex=True,sharey=True,layout='constrained')
        for i,((key,full),ax) in enumerate(zip(frames.items(),axes.flat)):
            own=key.startswith('Ours_')
            population=full[full.in_v1_working_catalog] if own and variant=='working_subset' else full
            d,selection=selected(population)
            assert len(d)>0
            ax.scatter(d.longitude,d.latitude,s=.8,c='#252525',alpha=.35,linewidths=0,rasterized=True)
            ax.set_xlim(*LON);ax.set_ylim(*LAT);ax.set_aspect(1/np.cos(np.deg2rad(np.mean(LAT))))
            ax.set_xticks([-117.8,-117.5,-117.2]);ax.set_yticks([35.5,35.75,36.0])
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{abs(x):.1f}'))
            ax.set_title(f'{chr(97+i)}  {titles[key]}',loc='left',fontweight='bold')
            ax.text(.97,.97,f'N = {len(d):,}',ha='right',va='top',transform=ax.transAxes,fontsize=8,color='black')
            if i>=3: ax.set_xlabel('Longitude (°W)')
            if i%3==0: ax.set_ylabel('Latitude (°N)')
            record=dict(figure=variant,catalog=key,native_population_rows=len(full),population_after_quality_selection=len(population),
                        plotted_rows=len(d),plotted_start_utc=d.time.min().isoformat(),plotted_end_utc=d.time.max().isoformat(),
                        source_first_event_utc=full.time.min().isoformat(),source_last_event_utc=full.time.max().isoformat(),**selection)
            record['plotted_nll_rejected']=int(d.native_status.eq('REJECTED').sum()) if own else 0
            stats.append(record)
            idfield='event_id' if own else 'reference_id'
            membership=d[[idfield,'time','latitude','longitude']].rename(columns={idfield:'native_id'}).copy()
            membership['figure']=variant;membership['catalog']=key;memberships.append(membership)
        stem=OUT/f'0{1 if variant=="all_candidates" else 2}_{variant}_maps'
        for ext in ('png','pdf'): fig.savefig(stem.with_suffix('.'+ext),dpi=300)
        plt.close(fig)
        print('Saved',stem.name,flush=True)
    statistics=pd.DataFrame(stats); statistics.to_csv(OUT/'selection_summary.csv',index=False)
    pd.concat(memberships,ignore_index=True).to_csv(OUT/'plotted_events.csv',index=False)
    rossall,_=selected(ross); rossrel,_=selected(refs['Ross_relocated'])
    assert len(rossrel)==int((rossall.nbranch>1).sum())
    # Reference rows must be identical across both figures.
    for key in refs:
        if key not in frames: continue
        a=statistics[statistics.catalog.eq(key)].plotted_rows
        assert a.nunique()==1
    fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,rosspath,*files.values(),HERE/'02_diagnostics/05_review_catalog.py',Path(__file__)]}
    summary=dict(start_utc=START.isoformat(),end_utc=END.isoformat(),longitude_bounds=list(LON),latitude_bounds=list(LAT),
        depth_filter=None,magnitude_filter=None,ross_all_rows_in_scope=len(rossall),ross_relocated_rows_in_scope=len(rossrel),
        checks_passed=True,input_sha256=fingerprints)
    (OUT/'run.yaml').write_text(yaml.safe_dump(summary,sort_keys=False))
    lines=['# Workflow and reference catalog maps','',
        'These are direct side-by-side epicenter distributions, not matching-rate curves. **Ours: GaMMA** and **Ours: NonLinLoc** are outputs of our workflow. Every panel labeled **Reference:** contains a published/operational catalog. This is an expert baseline comparison, not a claim of reproducing any single paper.','',
        '## Figures','',
        '- `01_all_candidates_maps.png/pdf`: both workflow panels start from all 9,942 associated candidates, using their respective origin times and coordinates. NLL rejected solutions remain visible here as candidate positions; this is not an accepted-event map. Their counts are listed below.',
        '- `02_working_subset_maps.png/pdf`: both workflow panels start from the same 6,520 stage-10 working-event IDs. Each panel then applies the common time/coordinate mask to its own solution. Reference panels are unchanged. A reference is not retrospectively filtered by our quality labels.',
        '- `selection_summary.csv`: exact source coverage extrema, population selections, in-window/out-of-map counts and plotted counts.',
        '- `plotted_events.csv`: the exact ID/time/location membership of every panel; no random thinning.',
        '', '## Common plotting rules','',
        f'Time: [{START.isoformat()}, {END.isoformat()}). Map: latitude {LAT}, longitude {LON}, inclusive. The start reproduces the existing shared comparison interval, beginning at the first local Shelly event. First/last event timestamps describe observed catalog extent, not proof of continuous detection or completeness.',
        'Each catalog uses its native origin times and locations. No magnitude or depth filter is applied. Identical point size (0.8 pt²), opacity (0.35), color and latitude-corrected map aspect are used throughout. N counts every plotted row; overplotting can hide individual points. Apparent sharpness also depends on location methods and selection, not just event-detection performance.',
        'GaMMA and NLL panel counts may differ at the map/time boundaries, despite sharing the same input candidate IDs. The working cohort was defined using NLL region membership in stage 10. These figures do not introduce new event matches, fit parameters or overwrite v1. No reference mainshock stars are placed on our panels, to avoid implying that the unresolved workflow hypocenters equal the official locations.',
        '', '## Ross selection','',
        f'The local archive contains {len(ross):,} rows with unique event IDs and 25 native columns. The plotted Ross product requires nbranch > 1. In the common map/time scope, the archive contains {len(rossall):,} rows, of which {len(rossrel):,} satisfy this relocation flag. Single-branch rows are not silently presented as successful relative relocations. This map adds Ross spatial context only; stage-10 matched-pair statistics still exclude Ross.',
        '', '## Panel populations','', '| Figure | Catalog | Plotted events | NLL rejected candidates |','| --- | --- | ---: | ---: |']
    for r in stats: lines.append(f"| {r['figure']} | {r['catalog']} | {r['plotted_rows']:,} | {r['plotted_nll_rejected'] if r['catalog'].startswith('Ours') else '—'} |")
    lines.extend(['','Depth sections are deliberately separate work: depth datums and a shared section geometry need explicit treatment before interpreting structural differences in depth. The workflow locations and mainshock uncertainty flags remain unchanged.'])
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print(statistics[['figure','catalog','plotted_rows','plotted_nll_rejected']].to_string(index=False),flush=True)
if __name__=='__main__':main()

"""One bounded, read-only time/depth review of the existing full catalog."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / 'export/06_full_catalog/52_full_catalog'
OUT = SOURCE / 'diagnostics/time_depth'
BASE = HERE / 'export/01_baseline/10_validate_catalog'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    e = pd.read_csv(SOURCE/'working_catalog.csv').set_index('event_id')
    b = pd.read_csv(BASE/'events.csv').set_index('event_id').loc[e.index]
    a = pd.read_csv(SOURCE/'branch_locations.csv')
    a = a[a.branch.eq('absolute_all')].set_index('event_id').loc[e.index]
    e['time_change_s'] = (pd.to_datetime(e.origin_time, utc=True)-pd.to_datetime(b.origin_time, utc=True)).dt.total_seconds()
    e['joint_minus_absolute_time_s'] = (pd.to_datetime(e.origin_time, utc=True)-pd.to_datetime(a.origin_time, utc=True)).dt.total_seconds()
    e['joint_minus_absolute_depth_km'] = e.depth_km-a.depth_km
    e['baseline_azimuth_gap_deg'] = b.azimuth_gap_deg
    e['baseline_depth_sigma_km'] = b.posterior_sigma_depth_km
    e['support_group'] = np.select([e.cc_all_instruments.eq(0),e.cc_all_instruments.le(2)],['No CC','1–2 instruments'],default='>=3 instruments')
    p = pd.read_csv(SOURCE/'phases.csv')
    old = pd.read_csv(BASE/'phases.csv', low_memory=False)
    p = p[p.absolute_used].merge(old[['pick_id','event_id','phase','time_utc','predicted_travel_time_s','residual_s_nll']],on=['pick_id','event_id','phase'],suffixes=('','_v1'),validate='one_to_one')
    assert (pd.to_datetime(p.time_utc,utc=True)==pd.to_datetime(p.time_utc_v1,utc=True)).all()
    # Validate native residual convention rather than assuming its sign.
    p['baseline_residual_s'] = (pd.to_datetime(p.time_utc,utc=True)-pd.to_datetime(p.event_id.map(b.origin_time),utc=True)).dt.total_seconds()-p.predicted_travel_time_s
    discrepancy = (p.baseline_residual_s-p.residual_s_nll).abs().dropna()
    assert discrepancy.max()<0.002, discrepancy.max()
    p['current_residual_s'] = -p.candidate_residual_s  # solver stores predicted minus observed
    p = p[np.isfinite(p.baseline_residual_s)&np.isfinite(p.current_residual_s)]
    for phase in ['P','S']:
        q=p[p.phase.eq(phase)].groupby('event_id')
        for label in ['baseline','current']:
            col=label+'_residual_s'
            e[f'{label}_{phase}_mean_s']=q[col].mean()
            e[f'{label}_{phase}_rms_s']=q[col].agg(lambda x:np.sqrt(np.mean(x*x)))
        e[f'{phase}_count']=q.size()
    e['baseline_S_minus_P_s']=e.baseline_S_mean_s-e.baseline_P_mean_s
    e['current_S_minus_P_s']=e.current_S_mean_s-e.current_P_mean_s
    rows=[]
    for name,g in [('All',e),*list(e.groupby('support_group',sort=False))]:
        rows.append(dict(group=name,n=len(g),boundary=int(g.candidate_depth_boundary.sum()),boundary_pct=100*g.candidate_depth_boundary.mean(),median_time_change_s=g.time_change_s.median(),median_abs_time_change_s=g.time_change_s.abs().median(),median_depth_change_km=g.depth_change_km.median(),p90_abs_depth_change_km=g.depth_change_km.abs().quantile(.9),spearman_time_depth=g.time_change_s.corr(g.depth_change_km,method='spearman'),median_joint_absolute_time_s=g.joint_minus_absolute_time_s.median(),median_joint_absolute_depth_km=g.joint_minus_absolute_depth_km.median(),median_gap_deg=g.baseline_azimuth_gap_deg.median(),median_depth_sigma_km=g.baseline_depth_sigma_km.median(),**{c: g[c].median() for c in ['baseline_P_mean_s','current_P_mean_s','baseline_S_mean_s','current_S_mean_s','baseline_P_rms_s','current_P_rms_s','baseline_S_rms_s','current_S_rms_s','baseline_S_minus_P_s','current_S_minus_P_s']}))
    stats=pd.DataFrame(rows);stats.to_csv(OUT/'group_summary.csv',index=False)
    ref=pd.read_csv(SOURCE/'reference_comparison.csv')
    original=ref[ref.branch.eq('original_nll')].set_index(['catalog','event_id','reference_id'])
    joint=ref[ref.branch.eq('joint_all')].set_index(['catalog','event_id','reference_id'])
    assert original.index.is_unique and joint.index.is_unique and set(original.index)==set(joint.index)
    paired=joint[['origin_difference_s','horizontal_km','absolute_depth_km']].join(original[['origin_difference_s','horizontal_km','absolute_depth_km']],rsuffix='_original').reset_index().merge(e[['support_group']],left_on='event_id',right_index=True,validate='many_to_one')
    rr=[]
    for cat,r in paired.groupby('catalog'):
        for group,g in [('All',r),*list(r.groupby('support_group',sort=False))]:
            rr.append(dict(catalog=cat,group=group,n=len(g),original_time_abs_median_s=g.origin_difference_s_original.abs().median(),current_time_abs_median_s=g.origin_difference_s.abs().median(),median_paired_time_error_change_s=(g.origin_difference_s.abs()-g.origin_difference_s_original.abs()).median(),time_worse_pct=100*(g.origin_difference_s.abs()>g.origin_difference_s_original.abs()).mean(),original_horizontal_median_km=g.horizontal_km_original.median(),current_horizontal_median_km=g.horizontal_km.median(),original_depth_median_km=g.absolute_depth_km_original.median(),current_depth_median_km=g.absolute_depth_km.median()))
    rs=pd.DataFrame(rr);rs.to_csv(OUT/'reference_by_support.csv',index=False)
    cols=['support_group','cc_all_instruments','absolute_instruments','candidate_depth_boundary','baseline_azimuth_gap_deg','baseline_depth_sigma_km','time_change_s','depth_change_km','joint_minus_absolute_time_s','joint_minus_absolute_depth_km','baseline_P_mean_s','current_P_mean_s','baseline_S_mean_s','current_S_mean_s','baseline_P_rms_s','current_P_rms_s','baseline_S_rms_s','current_S_rms_s']
    e[cols].to_csv(OUT/'event_diagnostics.csv')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axs=plt.subplots(1,3,figsize=(12,3.5),constrained_layout=True)
    for group,color in [('No CC','#999999'),('1–2 instruments','#d95f02'),('>=3 instruments','#1b9e77')]:
        g=e[e.support_group.eq(group)]
        axs[0].scatter(g.depth_change_km,g.time_change_s,s=3,alpha=.25,color=color,rasterized=True)
        for ax,col in [(axs[1],'time_change_s'),(axs[2],'depth_change_km')]:
            x=np.sort(g[col].abs());ax.plot(x,np.arange(1,len(x)+1)/len(x),color=color,label=f'{group} (n={len(g)})')
    axs[0].set(xlabel='Depth change (km)',ylabel='Origin-time change (s)')
    axs[1].set(xlabel='Absolute origin-time change (s)',ylabel='Cumulative fraction')
    axs[2].set(xlabel='Absolute depth change (km)',ylabel='Cumulative fraction')
    axs[2].legend(frameon=False,fontsize=7)
    for ax,l in zip(axs,'abc'):ax.text(0,1.04,l,transform=ax.transAxes,fontweight='bold',fontsize=12)
    for ext in ['png','pdf']:fig.savefig(OUT/f'time_depth_support.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    print('Residual sign check max error:',discrepancy.max(),'s; common original absolute picks:',len(p))
    print(stats.to_string(index=False));print(rs.to_string(index=False))

if __name__=='__main__':main()

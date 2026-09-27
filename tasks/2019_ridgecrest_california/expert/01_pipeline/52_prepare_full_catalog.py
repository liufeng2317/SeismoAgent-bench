"""Prepare one fixed full-working-catalog application; no parameter search."""
from pathlib import Path
import importlib.util
import json
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'export/52_full_catalog'
spec = importlib.util.spec_from_file_location('full52_helpers', HERE / '03_experiments/15_confirmation/_confirmation.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def main():
    dest = OUT / 'inputs'
    dest.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(C.ORIGINAL / 'events.csv')
    original = pd.read_csv(C.ORIGINAL / 'phases.csv', low_memory=False)
    parts = [original]
    sources = [C.ORIGINAL / 'events.csv', C.ORIGINAL / 'phases.csv', Path(__file__), Path(C.__file__)]
    for stage in ['50_uncertain_depth_pairs', '51_confirmation']:
        path = HERE / 'export' / stage / 'inputs/all_phases.csv'
        sources.append(path)
        parts.append(pd.read_csv(path, low_memory=False))
    combined = pd.concat(parts, ignore_index=True)
    # Duplicated IDs must retain their actual measurement identity, not merely their name.
    identity = ['pick_id', 'event_id', 'instrument_id', 'phase', 'time_utc', 'source_channels']
    assert not combined[identity].drop_duplicates().duplicated('pick_id').any()
    available = combined.drop_duplicates('pick_id').copy()
    pool = events[events.in_v1_working_catalog].sort_values('event_id').reset_index(drop=True)
    assert len(pool) == 6520 and len(events) == 9942
    available = available[available.event_id.isin(pool.event_id)].copy()
    assert not available.duplicated(['event_id', 'instrument_id', 'phase']).any()
    ph = original[original.event_id.isin(pool.event_id) & ~original.instrument_id.isin(C.held())]
    counts = ph.assign(is_s=ph.phase.eq('S')).groupby('event_id').agg(n=('pick_id','size'), n_s=('is_s','sum')).reindex(pool.event_id, fill_value=0)
    pool['role'] = 'working'
    pool['auxiliary_eligible'] = (counts.n.ge(10) & counts.n_s.ge(3)).to_numpy()
    pairs = set()
    for label, data, options in [('nearest', original, {'nearest': True}), ('original_support', original, {}), ('augmented_support', available, {}), ('depth_envelope', available, {'envelope': True})]:
        print('Pair nomination:', label, flush=True)
        nominated, _ = C.ranked_pairs(pool, pool, data, **options)
        pairs |= nominated
        print('Cumulative pairs:', len(pairs), flush=True)
    for stage in ['50_uncertain_depth_pairs', '51_confirmation']:
        path = HERE / 'export' / stage / 'inputs/pair_status.csv'
        prior = pd.read_csv(path)
        pairs |= set(map(tuple, prior[['event_id_a','event_id_b']].to_numpy()))
        sources.append(path)
    print('Building phase edges', len(pairs), flush=True)
    edges, status = C.edges_for(pairs, available, set(pool.event_id))
    used = set(edges.pick_id_a) | set(edges.pick_id_b)
    for name, frame in [('events', pool), ('all_phases', available), ('picks', available[available.pick_id.isin(used)]), ('differential_times', edges), ('pair_status', status)]:
        frame.to_csv(dest / (name + '.csv'), index=False)
    C.save(OUT / 'design.json', {'scope': 'All 6520 original working events; 9942 master IDs retained in final output.',
        'authorization': 'User requested full-scale application and reference comparisons after the completed campaign.',
        'method': 'Fixed stage50/51 objective and measurement rules; expand pairs over all working events. Union original nearest/support, augmented support, depth-envelope pairs and previous pairs.',
        'observations': 'Original observations plus all previously admitted stage50/51 additions. No new picker inference: additional-pick coverage is heterogeneous.',
        'status': 'Full-scale candidate evaluation, not round31, not blind confirmation, not automatic adoption.',
        'working_events': len(pool), 'master_events': len(events), 'phases': len(available), 'pairs': len(pairs), 'candidate_edges': len(edges),
        'source_sha256': {str(p): C.sha(p) for p in sources}})
    (OUT / 'README.md').write_text('''# Full working-catalog application

Status: preparing the fixed joint candidate for all 6,520 v1 working events. All 9,942 master records will be retained. This user-authorized full-scale evaluation follows the failed stage51 depth safeguard; it is not a new parameter scan or blind confirmation. V1 remains unchanged.

Use original picks and all already-qualified stage50/51 observations; expand the fixed CC graph over all working events. Added EQ S remains relative-only. Additional-pick coverage is heterogeneous. Non-working events and their mainshock uncertainty remain outside this relocation scope. Original magnitudes will be preserved as baseline estimates, not re-estimated at new locations.

`inputs/` stores the cohort, phases and candidate pairs; `cc_processing/` holds intermediate waveform windows. Logs are under `01_pipeline/logs/52_full_catalog/`. Final comparisons retain original reference identities and report all flags without selective removal.
''')
    print(json.dumps({k:v for k,v in json.loads((OUT/'design.json').read_text()).items() if k != 'source_sha256'}, indent=2), flush=True)


if __name__ == '__main__':
    main()

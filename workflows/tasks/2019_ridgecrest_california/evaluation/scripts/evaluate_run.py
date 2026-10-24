#!/usr/bin/env python3
"""Evaluate one completed agent run against the case references.

Each run keeps its own evaluation next to its record (the task-level
``evaluation/`` directory stays the cross-run comparison):

  <run>/evaluation/match_statistics.json        per-run match statistics
  <run>/evaluation/figures/01_run_vs_references  reference vs expert vs run
  <run>/evaluation/figures/02_run_correspondence matched-pair diagnostics

Usage:
  python evaluate_run.py --run-dir runs/tools/claude/glm-5.3/20261015T020300Z

The matcher, criteria and figure conventions are shared with
``plot_evaluation_comparison.py`` (imported as a library), so per-run numbers
are directly comparable with the cross-run statistics.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

TASK = Path(__file__).resolve().parents[2]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


comparison = _load_module('evaluation_comparison',
                          Path(__file__).with_name('plot_evaluation_comparison.py'))
three_way = _load_module('evaluation_three_way',
                         Path(__file__).with_name('plot_evaluation_comparison_three_way.py'))


def _run_layout(task_dir, run_dir):
    """Parse runs/<variant>/<harness>/<model>/<run_id> and read the record."""
    try:
        parts = run_dir.resolve().relative_to(task_dir.resolve()).parts
    except ValueError:
        raise SystemExit(f'run directory is not inside the task package: {run_dir}')
    if len(parts) != 5 or parts[0] != 'runs':
        raise SystemExit('run directory must be '
                         '<task>/runs/<variant>/<harness>/<model>/<run_id>: '
                         f'{run_dir}')
    record_path = run_dir / 'record' / 'run_result.json'
    record = {}
    if record_path.is_file():
        try:
            record = json.loads(record_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            record = {}
    return {'variant': parts[1], 'harness': parts[2], 'model': parts[3],
            'run_id': parts[4], 'path': Path(*parts).as_posix(),
            'record_state': record.get('state'),
            'started_at': record.get('started_at'),
            'finished_at': record.get('finished_at')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-dir', type=Path, default=TASK)
    parser.add_argument('--run-dir', type=Path, required=True,
                        help='run directory: runs/<variant>/<harness>/<model>/<run_id>')
    parser.add_argument('--label', help='display label (default: "<harness> <model> (<variant>)")')
    args = parser.parse_args()

    run_dir = (args.run_dir if args.run_dir.is_absolute() else Path.cwd() / args.run_dir).resolve()
    run = _run_layout(args.task_dir, run_dir)
    catalog = run_dir / 'work' / 'catalog.csv'
    if not catalog.is_file():
        raise SystemExit(f'no candidate catalog to evaluate: {catalog} '
                         f"(record state: {run['record_state']})")

    agent_key = f"agent_{run['variant']}"
    label = args.label or f"{run['harness']} {run['model']} ({run['variant']})"
    cfg, audit, populations, inputs = comparison.load_references()
    rows = comparison.read_ours(catalog, 'origin_time_utc')
    if not rows:
        raise SystemExit(f'no catalog rows inside the evaluation window: {catalog}')
    color, linestyle = comparison.agent_run_style(agent_key)
    agent = comparison.as_record(agent_key, label, color, rows)
    agent['linestyle'] = linestyle
    populations.append(agent)
    inputs[agent_key] = {'path': str(catalog.relative_to(args.task_dir)),
                         'plotted_records': len(rows), 'run_id': run['path']}

    stats = comparison.compute_stats(populations, focus_agent=agent_key)
    out = run_dir / 'evaluation'
    figures = out / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    with comparison.house.publication_style():
        shelly = next(r for r in populations if r['key'] == 'shelly')
        expert = next(r for r in populations if r['key'] == 'expert')
        three_pops = [dict(shelly, label='reference'), dict(expert, label='expert'), agent]
        three_way.plot_three_way(figures, cfg, audit, three_pops, agent_key,
                                 stem='01_run_vs_references')
        comparison.fig_correspondence(figures, cfg, audit, populations, stats,
                                      focus_agent=agent_key,
                                      stem='02_run_correspondence')

    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'run': {**run, 'catalog': 'work/catalog.csv', 'plotted_records': len(rows)},
        'populations': {r['key']: {'label': r['label'], 'records': len(r['rows']),
                                   'color': r['color']} for r in populations},
        'inputs': inputs,
        'statistics': stats,
    }
    (out / 'match_statistics.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    versus = stats[agent_key]['versus']['expert']
    print(f"{run['path']}: {len(rows):,} events in window; vs expert "
          f"{versus['matched']:,} matched (precision {versus['precision']:.1%}, "
          f"recall {versus['recall']:.1%})")
    print(f'Evaluation: {out}')


if __name__ == '__main__':
    main()

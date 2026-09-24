"""Source registry validation and file inventory, independent of evaluation."""
from datetime import timedelta
from pathlib import Path
import math
import re

import yaml

from .catalog import sha256, utc


class SourceError(ValueError):
    """Invalid source metadata or an integrity mismatch."""


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise SourceError(f'Duplicate YAML key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def require(condition, message):
    if not condition:
        raise SourceError(message)


def case_path(case, value):
    """Resolve declared paths relative to the case, including local symlink targets."""
    require(isinstance(value, str) and bool(value), 'Expected a nonempty case-relative path')
    path = Path(value)
    require(not path.is_absolute() and '..' not in path.parts, f'Path must stay inside case: {value}')
    result = (case / path).resolve()
    require(result.is_relative_to(case.resolve()), f'Symlink escapes case: {value}')
    return result


def validate_sources(cfg, case):
    require(isinstance(cfg, dict), 'Source configuration must be a mapping')
    require(cfg.get('schema_version') == 2, 'Expected schema_version: 2; legacy cases need explicit source-registry migration')
    require(cfg.get('case_id') == case.name, 'case_id must match the case directory')
    try:
        groups, sources = cfg['source_groups'], cfg['sources']
        require(isinstance(groups, dict) and bool(groups), 'Source groups cannot be empty')
        require(isinstance(sources, dict) and bool(sources), 'Source products cannot be empty')
        for group in groups.values():
            require(case_path(case, group['readme']).is_file(), 'Source group README must exist')
        for key, spec in sources.items():
            require(isinstance(key, str) and bool(key), 'Source product key must be a nonempty string')
            require(spec['source_ref'] in groups, f'Unknown source group: {key}')
            case_path(case, spec['path'])
            require(re.fullmatch('[0-9a-f]{64}', spec['expected_sha256']) is not None, f'Invalid SHA-256: {key}')
            require(spec['unit'] in {'event', 'relative_event', 'phase_pick', 'focal_mechanism'}, f'Unknown record unit: {key}')
            require(spec['format'] in {'text', 'csv', 'xlsx', 'xml', 'zip', 'tar.gz', 'json'}, f'Unknown file format: {key}')
            require(isinstance(spec['parser'], str) and bool(spec['parser']), f'Missing parser identifier: {key}')
            require(isinstance(spec['version'], str) and bool(spec['version']), f'Missing version label: {key}')
        audit = cfg.get('reference_audit')
        if audit:
            selected = audit['event_sources']
            require(isinstance(selected, list) and selected and len(selected) == len(set(selected)), 'Audit source list must be nonempty and unique')
            require(set(selected) <= set(sources), 'Audit refers to unknown source products')
            require(all(sources[key]['unit'] in {'event', 'relative_event', 'focal_mechanism'} for key in selected), 'Phase picks cannot be parsed as catalog records')
            require(sources[audit['phase_source']]['unit'] == 'phase_pick', 'Phase source must declare phase_pick units')
            require(audit['anchor_source'] in selected, 'Anchor source must be a selected catalog')
            aliases = audit.get('subsets', {})
            require(not set(aliases) & set(sources), 'Subset names must not overwrite source products')
            for subset in aliases.values():
                require(subset['source'] in selected, 'Unknown subset source')
                require(subset['operator'] in {'gt', 'eq'}, 'Unsupported subset operator')
                require(isinstance(subset['field'], str) and bool(subset['field']), 'Subset field is required')
                require('value' in subset, 'Subset comparison value is required')
            names = audit['stage_names']; boundaries = audit['stage_boundaries']
            require(isinstance(names, list) and names and all(isinstance(n, str) and n for n in names), 'Stage labels must be nonempty strings')
            require(len(names) == len(set(names)) and len(boundaries) == len(names) + 1, 'Invalid stage labels or boundary count')
            valid_anchors = {'window_start', 'window_end'} | set(cfg['scientific_design']['anchor_event_ids'])
            for boundary in boundaries:
                require(boundary['anchor'] in valid_anchors, 'Unknown stage anchor')
                offset = boundary.get('offset_s', 0)
                require(isinstance(offset, (int, float)) and not isinstance(offset, bool) and math.isfinite(offset), 'Stage offsets must be finite seconds')
            for pair in audit['overlap_diagnostic']['pairs']:
                require(len(pair) == 2 and set(pair) <= set(selected) | set(aliases), 'Unknown overlap source/subset')
    except (KeyError, TypeError, AttributeError) as exc:
        raise SourceError(f'Malformed or missing source field: {exc}') from exc
    return cfg


def load_case(case):
    case = Path(case).resolve()
    cfg = yaml.load((case / 'analysis/processing.yaml').read_text(), Loader=UniqueKeyLoader)
    return validate_sources(cfg, case)


def inventory(cfg, case, verify=False):
    """Do not equate a missing local payload with missing release provenance."""
    products = {}
    for key, spec in cfg['sources'].items():
        path = case_path(case, spec['path'])
        exists = path.is_file()
        record = {field: spec[field] for field in ('source_ref', 'path', 'unit', 'format', 'parser', 'version', 'expected_sha256')}
        record.update(local_status='present' if exists else 'missing', size_bytes=path.stat().st_size if exists else None,
                      integrity='not_checked')
        if verify and exists:
            actual = sha256(path)
            record.update(actual_sha256=actual, integrity='verified' if actual == spec['expected_sha256'] else 'mismatch')
        products[key] = record
    return {'case_id': cfg['case_id'], 'schema_version': cfg['schema_version'],
            'config_sha256': sha256(case / 'analysis/processing.yaml'),
            'source_groups': cfg['source_groups'], 'products': products,
            'interpretation': 'Source-file inventory only; record counts, scientific completeness and evaluation readiness are not inferred.'}


def resolve_stages(design, audit, anchors):
    window = design['candidate_window']
    start, end = utc(window['start_utc']), utc(window['end_utc'])
    times = dict(anchors, window_start=start, window_end=end)
    points = []
    for boundary in audit['stage_boundaries']:
        require(boundary['anchor'] in times, f'Unresolved stage anchor: {boundary["anchor"]}')
        points.append(times[boundary['anchor']] + timedelta(seconds=boundary.get('offset_s', 0)))
    names = audit['stage_names']
    require(len(points) == len(names) + 1, 'Stages require one more boundary than labels')
    require(points[0] == start and points[-1] == end, 'Stages must cover the candidate source-audit window')
    require(all(a < b for a, b in zip(points, points[1:])), 'Stage boundaries must strictly increase')
    return list(zip(names, points, points[1:]))


def select_subset(rows, spec):
    require(spec['operator'] in {'gt', 'eq'}, 'Unsupported subset operator')
    result = []
    for row in rows:
        require(spec['field'] in row, f'Missing subset field: {spec["field"]}')
        value = row[spec['field']]
        matches = value > spec['value'] if spec['operator'] == 'gt' else value == spec['value']
        if matches:
            result.append(row)
    return result
